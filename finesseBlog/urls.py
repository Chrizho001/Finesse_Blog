from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterUserView.as_view(), name='register'),
    path('posts', views.post_list, name='post_list'),
    path('posts/<slug:post>', views.post_detail, name='post_detail'),
    path('verify-email/', views.VerifyUserEmail.as_view(), name='verify_email'),
    path('login/', views.LogInUserView.as_view(), name='login'),
    path('profile/', views.TestAuthenticationView.as_view(), name='profile'),
]