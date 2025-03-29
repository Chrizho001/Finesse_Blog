from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Post
from .serializers import PostSerializer
from django.db.models import Count

# Create your views here.

@api_view(['GET'])
def post_list(request):
    posts = Post.objects.annotate(likes_count=Count('likes'))
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def post_detail(request, post):
    posts = get_object_or_404(Post, slug=post)
    serializer = PostSerializer(posts)
    return Response(serializer.data)
