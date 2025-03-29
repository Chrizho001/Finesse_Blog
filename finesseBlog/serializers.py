from rest_framework import serializers
from .models import Post, PostImage, User, Comment
from django.contrib.auth import get_user_model

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'bio', 'stack', 'profile_picture', 'facebook', 'youtube', 'twitter', 'tiktok']

    # def create(self, validated_data):
    #     email = validated_data['email']
    #     username = validated_data['username']
    #     first_name = validated_data['first_name']
    #     last_name = validated_data['last_name']
    #     password = validated_data['password']

    #     user = get_user_model()
    #     new_user = user.objects.create(email=email, username=username, first_name=first_name, last_name=last_name )
    #     new_user.set_password(password)
    #     new_user.save()
    #     return new_user




class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ['id', 'image', 'uploaded_at']
        read_only_fields = ['uploaded_at']  # User can't set this

    # Return the full image URL
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['image'] = instance.image.url  # e.g., "/media/post_images/2025/03/28/cat.jpg"
        return rep


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ['content', 'created_at', 'author']



class PostSerializer(serializers.ModelSerializer):
    post_comments = CommentSerializer(many=True, read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    # author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    author = UserSerializer(read_only=True)
    likes_count = serializers.IntegerField(source='likes.count', read_only=True) # Use annotated field in the views
    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'content', 'header_image', 'images', 'author', 'status', 'publish', 'likes_count', 'post_comments']
        read_only_fields = ['id']

    def validate_title(self, value):
        if value.strip() == "":
            raise serializers.ValidationError("Title cannot be empty or just whitespace.")
        return value
    
    def validate_content(self, value):
        if value.strip() == "":
            raise serializers.ValidationError("Content cannot be empty or just whitespace.")
        return value
    
    def validate_slug(self, value):
        if not value.islower():
            raise serializers.ValidationError("Slug must be all lowercase.")
        return value
