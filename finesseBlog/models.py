from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings

# Create your models here.

class User(AbstractUser):
    bio = models.TextField(blank=True, null=True)
    stack = models.CharField(max_length=500, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_img', blank=True, null=True)
    facebook = models.URLField(max_length=255, blank=True, null=True)
    youtube = models.URLField(max_length=255, blank=True, null=True)
    instagram = models.URLField(max_length=255, blank=True, null=True)
    twitter = models.URLField(max_length=255, blank=True, null=True)
    tiktok = models.URLField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username 
    
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    class StatusChoices(models.TextChoices):
        DRAFT = 'Draft'
        PUBLISH = 'Publish'
    
    title = models.CharField(max_length=200)
    header_image = models.ImageField(upload_to='post_img', null=True, blank=True)
    slug = models.SlugField(max_length=250, unique_for_date='publish')
    content = models.TextField()
    publish = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    status = models.CharField(max_length=8, choices=StatusChoices.choices, default=StatusChoices.PUBLISH)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Like', related_name='liked_posts', blank=True)

    class Meta:
        ordering = ['-publish']

        indexes= [
            models.Index(fields=['-publish']),
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return self.title
    
class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey('Post', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'post')  # Ensures a user can only like a post once

    def __str__(self):
        return f"{self.user} likes {self.post}"
    
class Comment(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_comments')

    class Meta:
        ordering = ['created_at']

class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='post_images/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.post.title}"

    