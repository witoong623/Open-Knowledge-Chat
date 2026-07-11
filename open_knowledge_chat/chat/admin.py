from django.contrib import admin

from chat.models import ChatProfile, ConversationSession


@admin.register(ConversationSession)
class ConversationSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'profile', 'modified')
    list_filter = ('user',)
    search_fields = ('title', 'user__username')


@admin.register(ChatProfile)
class ChatProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'model_key', 'modified')
    list_filter = ('model_key', 'owner')
    search_fields = ('name',)
