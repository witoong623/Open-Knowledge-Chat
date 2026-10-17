from django.urls import path

from document import views

app_name = 'document'

urlpatterns = [
    path('documents/', views.index, name='index'),
    path('documents/upload/', views.upload, name='upload'),
    path('documents/website/', views.upload_website, name='upload_website'),
    path('documents/<int:pk>/status/', views.status, name='status'),
    path('documents/<int:pk>/preview/', views.preview, name='preview'),
    path('documents/<int:pk>/delete/', views.delete, name='delete'),
]
