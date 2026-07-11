from django.urls import path

from profiles import views

app_name = 'profiles'

urlpatterns = [
    path('profiles/', views.ProfileListView.as_view(), name='list'),
    path('profiles/new/', views.ProfileCreateView.as_view(), name='create'),
    path('profiles/<int:pk>/', views.ProfileDetailView.as_view(), name='detail'),
    path('profiles/<int:pk>/edit/', views.ProfileUpdateView.as_view(), name='edit'),
    path('profiles/<int:pk>/delete/', views.ProfileDeleteView.as_view(), name='delete'),
]
