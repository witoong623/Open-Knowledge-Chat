from django.urls import path

from chat import views

app_name = 'chat'

urlpatterns = [
    path('', views.ChatIndexView.as_view(), name='index'),
    path('sessions/new/', views.NewSessionView.as_view(), name='new_session'),
    path('sessions/<int:pk>/messages/', views.MessageLogView.as_view(), name='message_log'),
    path('sessions/<int:pk>/message/', views.SendMessageView.as_view(), name='send_message'),
    path('sessions/<int:pk>/message/stream/', views.MessageStreamView.as_view(), name='stream_message'),
    path('profiles/', views.ProfileListView.as_view(), name='profiles'),
    path('profiles/new/', views.ProfileCreateView.as_view(), name='profile_create'),
    path('profiles/<int:pk>/', views.ProfileDetailView.as_view(), name='profile_detail'),
    path('profiles/<int:pk>/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('profiles/<int:pk>/delete/', views.ProfileDeleteView.as_view(), name='profile_delete'),
]
