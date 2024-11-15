from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import timedelta


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

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        blank=True
    )

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

    def is_active(self):
        return not self.is_complete

    def get_player_names(self):
        return {
            'player1': self.player1.username if self.player1 else '[Deleted User]',
            'player2': self.player2.username if self.player2 else '[Deleted User]',
        }

    def get_turn(self):
        if self.winner:
            return None
        else:
            all_moves = self.moves.all()
            if len(all_moves) % 2 == 0:
                return self.player1
            else:
                return self.player2


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
