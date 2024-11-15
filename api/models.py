from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))
        if not username:
            raise ValueError(_("The Username field must be set"))

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    points = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username


class Game(models.Model):
    player1 = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="games_as_player1"
    )
    player2 = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="games_as_player2"
    )
    winner = models.CharField(max_length=200, null=True, blank=True)
    is_complete = models.BooleanField(default=False)
    time_limit = models.DurationField(default=timedelta(days=1))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Game between {self.player1.username if self.player1 else '[Deleted User]'} and {self.player2.username if self.player2 else '[Deleted User]'}"

    # Additional helper methods
    def is_active(self):
        return not self.is_complete

    def get_player_names(self):
        return {
            'player1': self.player1.username if self.player1 else '[Deleted User]',
            'player2': self.player2.username if self.player2 else '[Deleted User]',
        }

    def build_board(self):
        all_moves = self.moves.all()
        board = [[0] * 8 for _ in range(8)]
        for move in all_moves:
            player = 1
            if move.move_order % 2 == 1:
                player = 2
            board[move.row][move.column] = player
        return board

    def check_winner(self):
        board = self.build_board()

        def check_direction(i, j, di, dj, player):
            count = 0
            for k in range(4):
                if 0 <= i + di * k < 8 and 0 <= j + dj * k < 8 and board[i + di * k][j + dj * k] == player:
                    count += 1
                else:
                    break
            return count == 4

        for i in range(8):
            for j in range(8):
                if board[i][j] == 0:
                    continue
                player = board[i][j]

                # Check all directions: right, down, and diagonals
                if (check_direction(i, j, 0, 1, player) or
                        check_direction(i, j, 1, 0, player) or
                        check_direction(i, j, 1, 1, player) or
                        check_direction(i, j, 1, -1, player)):
                    return player

        return None

    def get_turn(self):
        if self.winner:
            return None
        else:
            all_moves = self.moves.all()
            if len(all_moves) % 2 == 0:
                return self.player1
            else:
                return self.player2

    def time_remaining(self):
        if self.is_complete:
            return timedelta(seconds=0)

        now = timezone.now()
        elapsed_time = now - self.updated_at
        remaining_time = self.time_limit - elapsed_time

        if remaining_time < timedelta(seconds=0):
            #TODO: We should also add a winner here
            return timedelta(seconds=0)

        return remaining_time


class Move(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="moves")
    player = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    row = models.PositiveSmallIntegerField()
    column = models.PositiveSmallIntegerField()
    move_order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['move_order']

    def __str__(self):
        return f"Move {self.move_order} in Game {self.game.id} by {self.player.username} at ({self.row}, {self.column})"
