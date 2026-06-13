from django.contrib import admin

from document.models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created']
    list_filter = ['user']
    search_fields = ['name']
