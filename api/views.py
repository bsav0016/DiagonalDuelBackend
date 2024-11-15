from rest_framework import status, generics
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from .models import Game
from .serializers import GameSerializer, MoveSerializer, UserRegistrationSerializer
from .services import GameService


class UserRegistrationView(APIView):
    def post(self, request, format=None):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "User created successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request, format=None):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key}, status=status.HTTP_200_OK)
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)


class GameListCreateView(generics.ListCreateAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer

    def perform_create(self, serializer):
        player1 = self.request.data.get('player1')
        player2 = self.request.data.get('player2')
        time_limit = self.request.data.get('time_limit', 3600)
        game = GameService.start_game(player1, player2, time_limit)
        serializer.save(id=game.id)


class GameTimeRemainingView(APIView):
    def get(self, request, pk, format=None):
        try:
            game = Game.objects.get(pk=pk)
            remaining_time = GameService.get_remaining_time(game)
            return Response({"remaining_time": remaining_time}, status=status.HTTP_200_OK)
        except Game.DoesNotExist:
            return Response({"detail": "Game not found."}, status=status.HTTP_404_NOT_FOUND)


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

