from django.urls import path
from .views import UserRegistrationView, LoginView, UserGamesView, MoveCreateView, LogoutView, MatchmakingView
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('games/', UserGamesView.as_view(), name='user-games'),
    path('games/<int:game_id>/moves/', MoveCreateView.as_view(), name='move-create'),
    path('matchmaking/', MatchmakingView.as_view(), name='matchmaking'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
