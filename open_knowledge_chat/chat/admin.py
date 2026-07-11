from django.contrib import admin

from chat.models import ConversationSession


@admin.register(ConversationSession)
class ConversationSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'profile', 'modified')
    list_filter = ('user',)
    search_fields = ('title', 'user__username')
