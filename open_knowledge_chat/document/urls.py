from django.urls import path

from document import views

app_name = 'document'

urlpatterns = [
    path('documents/', views.DocumentIndexView.as_view(), name='index'),
    path('documents/upload/', views.DocumentUploadView.as_view(), name='upload'),
    path('documents/<int:pk>/status/', views.DocumentStatusView.as_view(), name='status'),
    path('documents/<int:pk>/preview/', views.DocumentPreviewView.as_view(), name='preview'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='delete'),
]
