from django.urls import path
from .views import UserRegistrationView, LoginView,GameListCreateView, MoveCreateView, LogoutView


urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('games/', GameListCreateView.as_view(), name='game-list-create'),
    path('games/<int:pk>/moves/', MoveCreateView.as_view(), name='move-create'),
]
