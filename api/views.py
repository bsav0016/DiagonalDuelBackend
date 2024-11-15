from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated


#class UserViewSet(viewsets.ModelViewSet):
    #queryset = User.objects.all()
    #serializer_class = UserSerializer