from rest_framework import serializers
from models import CustomUser, Game, Move


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'points', 'is_active', 'is_staff', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'password']


class GameSerializer(serializers.ModelSerializer):
    player1 = CustomUserSerializer(read_only=True)
    player2 = CustomUserSerializer(read_only=True)
    winner = CustomUserSerializer(read_only=True, required=False)
    moves = MoveSerializer(many=True, read_only=True)

    time_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ['id', 'player1', 'player2', 'winner', 'is_complete', 'time_limit', 'created_at', 'updated_at', 'moves', 'time_remaining']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_time_remaining(self, obj):
        return str(obj.time_remaining())


class MoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Move
        fields = ['id', 'player', 'row', 'column', 'move_order']
        read_only_fields = ['id']

    player = CustomUserSerializer(read_only=True)
