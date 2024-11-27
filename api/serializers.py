from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import CustomUser, Game, Move, MatchmakingQueue


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")
        user = authenticate(username=username, password=password)
        if user is None:
            raise AuthenticationFailed("Invalid credentials.")
        if not user.is_active:
            raise AuthenticationFailed("User is inactive.")
        return user

    def create_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    def get_user_games(self, user):
        player1_games = Game.objects.filter(player1=user)
        player2_games = Game.objects.filter(player2=user)

        user_games = player1_games | player2_games
        sorted_games = sorted(user_games, key=lambda game: game.updated_at, reverse=True)

        games_data = [GameSerializer(game).data for game in sorted_games]
        return games_data


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', "email"]
        read_only_fields = ['id', 'date_joined', 'password']


class MoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Move
        fields = ['id', 'player', 'row', 'column']
        read_only_fields = ['id']

    player = CustomUserSerializer(read_only=True)


class GameSerializer(serializers.ModelSerializer):
    player1 = serializers.StringRelatedField(read_only=True)
    player2 = serializers.StringRelatedField(read_only=True)
    moves = MoveSerializer(many=True, read_only=True)

    class Meta:
        model = Game
        fields = ['id', 'player1', 'player2', 'winner', 'time_limit', 'updated_at', 'moves']
        read_only_fields = ['id', 'updated_at']


class MatchmakingQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchmakingQueue
        fields = ['id', 'user', 'joined_at']
