from rest_framework import status, generics
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from .models import Game
from .serializers import (GameSerializer, MoveSerializer, UserRegistrationSerializer, LoginSerializer,
                          CustomUserSerializer)
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
        print(request.data)
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validate(data=request.data)
            token = serializer.create_token(user)
            games_data = serializer.get_user_games(user)

            return Response({
                "username": user.username,
                "email": user.email,
                "token": token,
                "games": games_data
            }, status=status.HTTP_200_OK)
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request, format=None):
        if not request.user or not request.user.is_authenticated:
            return Response({"detail": "User is not authenticated."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            request.user.auth_token.delete()
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({"detail": "No active session to log out from."}, status=status.HTTP_400_BAD_REQUEST)


class GameListCreateView(generics.ListCreateAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer

    def perform_create(self, serializer):
        player1 = self.request.data.get('player1')
        player2 = self.request.data.get('player2')
        time_limit = self.request.data.get('time_limit', 3600)
        game = GameService.start_game(player1, player2, time_limit)
        serializer.save(id=game.id)


class MoveCreateView(APIView):
    def post(self, request, game_id, format=None):
        player = request.data.get('player')
        row = request.data.get('row')
        column = request.data.get('column')

        try:
            if not (0 <= row < 8) or not (0 <= column < 8):
                return Response({"detail": "Invalid row or column."}, status=status.HTTP_400_BAD_REQUEST)

            game = Game.objects.get(id=game_id)

            board = GameService.build_board(game)
            if board[row][column] != 0:
                return Response({"detail": "Position already occupied."}, status=status.HTTP_400_BAD_REQUEST)

            move = GameService.make_move(game, player, row, column)
            return Response(MoveSerializer(move).data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Game.DoesNotExist:
            return Response({"detail": "Game not found."}, status=status.HTTP_404_NOT_FOUND)

