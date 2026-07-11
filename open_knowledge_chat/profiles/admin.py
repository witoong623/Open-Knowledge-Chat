from django.contrib import admin

from profiles.models import ChatProfile


@admin.register(ChatProfile)
class ChatProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'model_key', 'modified')
    list_filter = ('model_key', 'owner')
    search_fields = ('name',)
