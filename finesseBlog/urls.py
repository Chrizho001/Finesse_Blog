from django.urls import path
from . import views
from .views import PasswordResetConfirm

app_name = 'finesseBlog'



urlpatterns = [
    path('register/', views.RegisterUserView.as_view(), name='register'),
    path('posts/', views.PostListCreateApiView.as_view(), name='post_list_create'),
    path('user-posts', views.UserPostListApiView.as_view(), name='user_post_list'),
    path('posts/<slug:slug>/', views.PostDetailApiView.as_view(), name='post_detail'),
    path('verify-email/', views.VerifyUserEmail.as_view(), name='verify_email'),
    path('login/', views.LogInUserView.as_view(), name='login'),
    path('logout/', views.LogoutUserView.as_view(), name='logout'),
    path('comments/', views.CommentCreateApiView.as_view(), name='comment'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/<uidb64>/<token>',views.PasswordResetConfirm.as_view(), name='password-reset-confirm'),
    path('set-new-password/', views.SetNewPassword.as_view(), name='set-new-password'),
]