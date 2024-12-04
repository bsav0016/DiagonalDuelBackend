from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import F, Q
from django.utils.timezone import now, make_aware, is_aware
from django.db import transaction
from datetime import timedelta
from .models import Game, MatchmakingQueue
from .serializers import (GameSerializer, MoveSerializer, UserRegistrationSerializer, LoginSerializer,
                          CustomUserSerializer, MatchmakingQueueSerializer)
from .services import GameService


class UserRegistrationView(APIView):
    def post(self, request, format=None):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            serialized_user = CustomUserSerializer(user)
            return Response({
                    "user": serialized_user.data,
                    "token": access_token
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny, ]

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validate(data=request.data)
            tokens = serializer.create_tokens(user)
            games_data = serializer.get_user_games(user)

            matchmaking_entries = MatchmakingQueue.objects.filter(user=user)
            matchmaking_times = []
            for matchmaking_entry in matchmaking_entries:
                matchmaking_times.append(matchmaking_entry.time_limit.days)

            return Response({
                "username": user.username,
                "email": user.email,
                "refresh_token": tokens['refresh'],
                "access_token": tokens['access'],
                "games": games_data,
                "matchmaking": matchmaking_times
            }, status=status.HTTP_200_OK)
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            if self.request.data.get('all'):
                token: OutstandingToken
                for token in OutstandingToken.objects.filter(user=request.user):
                    _, _ = BlacklistedToken.objects.get_or_create(token=token)
                return Response({"message": "All refresh tokens blacklisted"})
            refresh_token = request.data.get('refresh')
            token = RefreshToken(token=refresh_token)
            token.blacklist()
            return Response({"message": "Logout completed"}, status=status.HTTP_200_OK)
        except Exception as e:
            Response({"detail": "Error: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MatchmakingView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        time_limit_days = request.data.get('time_limit_days', 1)
        time_limit = timedelta(days=time_limit_days)
        if MatchmakingQueue.objects.filter(user=user).filter(time_limit=time_limit).exists():
            return Response(
                {"detail": "User is already in the matchmaking queue for this time limit."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                opponent_entry = MatchmakingQueue.objects.exclude(user=user).filter(time_limit=time_limit).first()
                if opponent_entry:
                    game = Game.objects.create(player1=opponent_entry.user, player2=user, time_limit=time_limit)
                    opponent_entry.delete()
                    return Response(GameSerializer(game).data, status=status.HTTP_201_CREATED)

                queue_entry = MatchmakingQueue.objects.create(user=user, time_limit=timedelta(days=time_limit_days))
                return Response(
                    {
                        "detail": "No opponents available. You have been added to the queue.",
                        "queue": MatchmakingQueueSerializer(queue_entry).data,
                    },
                    status=status.HTTP_200_OK,
                )
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request, *args, **kwargs):
        user = request.user
        matchmaking_entries = MatchmakingQueue.objects.filter(user=user)
        matchmaking_times = []
        for matchmaking_entry in matchmaking_entries:
            matchmaking_times.append(matchmaking_entry.time_limit.days)

        return Response(
            {"matchmaking": matchmaking_times},
            status=status.HTTP_200_OK
        )

    def delete(self, request):
        user = request.user
        time_limit_days = request.data.get('time_limit_days', 1)
        time_limit = timedelta(days=time_limit_days)
        try:
            matchmaking_queue = MatchmakingQueue.objects.filter(time_limit=time_limit).get(user=user)
        except MatchmakingQueue.DoesNotExist:
            return Response(
                {"detail": "User not in matchmaking queue."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        matchmaking_queue.delete()
        return Response(
            {"message": "User removed from matchmaking queue."},
            status=status.HTTP_200_OK,
        )


class UserGamesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        current_time_utc = now()
        if not is_aware(current_time_utc):
            current_time_utc = make_aware(current_time_utc)
        user_games = Game.objects.filter(
            Q(player1=user) | Q(player2=user)
        )

        timed_out_games = user_games.filter(
            winner__isnull=True,
            updated_at__lte=current_time_utc - F('time_limit')
        )

        for game in timed_out_games:
            if game.player1 == game.get_turn():
                game.winner = f"{game.player2.username} wins by timeout"
            else:
                game.winner = f"{game.player1.username} wins by timeout"
            game.save()
        sorted_games = user_games.order_by('-updated_at')

        serializer = GameSerializer(sorted_games, many=True)
        return Response({"games": serializer.data}, status=200)


class MoveCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id, format=None):
        user = request.user

        if not user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        row = request.data.get('row')
        column = request.data.get('column')

        try:
            if not (0 <= row < 8) or not (0 <= column < 8):
                return Response({"detail": "Invalid row or column."}, status=status.HTTP_400_BAD_REQUEST)

            game = Game.objects.get(id=game_id)

            board = GameService.build_board(game)
            if not GameService.is_valid(board, row, column):
                return Response({"detail": "Invalid move."}, status=status.HTTP_400_BAD_REQUEST)

            move = GameService.make_move(game, user, row, column)
            return Response(MoveSerializer(move).data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Game.DoesNotExist:
            return Response({"detail": "Game not found."}, status=status.HTTP_404_NOT_FOUND)
