from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterUserView.as_view(), name='register'),
    path('posts', views.post_list, name='post_list'),
    path('posts/<slug:post>', views.post_detail, name='post_detail'),
]