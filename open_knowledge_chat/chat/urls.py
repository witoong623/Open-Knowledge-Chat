from django.urls import path

from chat import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_index, name='index'),
    path('sessions/new/', views.new_session, name='new_session'),
    path('sessions/<int:pk>/messages/', views.message_log, name='message_log'),
    path('sessions/<int:pk>/message/', views.send_message, name='send_message'),
    path('sessions/<int:pk>/message/stream/', views.message_stream, name='stream_message'),
]
