from django.contrib import admin
from .models import CustomUser, Game, Move, MatchmakingQueue


admin.site.register(CustomUser)
admin.site.register(Game)
admin.site.register(Move)
admin.site.register(MatchmakingQueue)
