from rest_framework import serializers
from .models import Post, PostImage, User, Comment
from django.contrib.auth import get_user_model

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'bio', 'stack', 'profile_picture', 'facebook', 'youtube', 'twitter', 'tiktok']

    

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    password2 = serializers.CharField(max_length=68, min_length=6, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'username', 'password', 'password2', ]

    def validate(self, attrs):
        password = attrs.get('password', '')
        password2 = attrs.get('password2', '')
        if password != password2:
            raise serializers.ValidationError('passwords do not match')
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2') # just simply pop out password2 and then spread the validated data but i'll go with option 2 which is to manually insert the data
        user = User.objects.create_user(**validated_data) # recieving the spreaded data
        # user = User.objects.create_user(
        #     email=validated_data['email'],
        #     username=validated_data.get('username'),
        #     first_name = validated_data.get('first_name'),
        #     last_name = validated_data.get('last_name'),
        #     password = validated_data.get('password'),
        # )

        return user




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
