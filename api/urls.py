from django.urls import path
from .views import UserRegistrationView, LoginView,GameListCreateView, GameTimeRemainingView, MoveCreateView


urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('login/', LoginView.as_view(), name='login'),
    path('games/', GameListCreateView.as_view(), name='game-list-create'),
    path('games/<int:pk>/time-remaining/', GameTimeRemainingView.as_view(), name='game-time-remaining'),
    path('games/<int:pk>/moves/', MoveCreateView.as_view(), name='move-create'),
]
