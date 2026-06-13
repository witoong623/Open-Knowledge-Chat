from django.urls import path

from document import views

app_name = 'document'

urlpatterns = [
    path('documents/', views.DocumentIndexView.as_view(), name='index'),
]
