from rest_framework import serializers
from .models import Post, PostImage, User, Comment, Category
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_str, smart_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import send_normal_email
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


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
        # password = attrs.get('password', '')
        # password2 = attrs.get('password2', '')
        password = attrs['password']
        password2 = attrs['password2']
        if password != password2:
            raise serializers.ValidationError('passwords do not match')
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2') # just simply pop out password2 and then spread the validated data but i'll go with option 2 which is to manually insert the data
        user = User.objects.create_user(**validated_data) # recieving the spreaded data
        return user




class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ['id', 'image', 'uploaded_at']
        read_only_fields = ['uploaded_at']  

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

class CreateCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)  # Display author details, not editable
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())  # Input post ID
    content = serializers.CharField(max_length=1000, required=True)  # Comment text

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Comment content cannot be empty.")
        return value

    def create(self, validated_data):
        # Automatically set the author to the current user
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class PostSerializer(serializers.ModelSerializer):
    post_comments = CommentSerializer(many=True, read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), allow_null=True)
    # author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    author = UserSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True) # Use annotated field in the views
    slug = serializers.SlugField(required=False, allow_blank=True)  # Optional for PATCH
    publish = serializers.DateTimeField(required=False)  # Optional for PATCH

    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'content', 'header_image', 'images', 'author', 'category', 'status', 'publish', 'likes_count', 'post_comments', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'likes_count', 'post_comments', 'images']

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
    def create(self, validated_data):
        # Set author to the logged-in user
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    first_name = serializers.CharField(max_length=255, read_only=True)
    last_name = serializers.CharField(max_length=255, read_only=True)
    access_token = serializers.CharField(max_length=255, read_only=True)
    refresh_token = serializers.CharField(max_length=255, read_only=True)
    
    # Only the email and password are actualy used for login


    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'access_token', 'refresh_token']

   
    def validate(self, attrs):
        email = attrs['email']
        password = attrs['password']
        request = self.context.get('request')
        user = authenticate(request, email=email, password=password)
        if not user:
            raise AuthenticationFailed('invalid credentials try again')
        
        if not user.is_verified:
            raise AuthenticationFailed('Email is not verified')
        
        user_token=user.tokens()
        if not user_token or 'access' not in user_token or 'refresh' not in user_token:
            raise serializers.ValidationError('Unable to generate tokens')

        return {
            'email':user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'access_token' : str(user_token.get('access')),
            'refresh_token' : str(user_token.get('refresh'))

        }

        
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        fields = ['email']

    def validate(self, attrs):
        # get the email sent by the user
        email = attrs.get('email')
        # Check if email is in our database
        if User.objects.filter(email=email).exists():
            # get the user
            user=User.objects.get(email=email)
            # encode the user id
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            # generate a token for the user
            token = PasswordResetTokenGenerator().make_token(user)
            request = self.context.get('request')
            # Get the site domain
            site_domain = get_current_site(request).domain
            # get the endpoint/view for the password reset
            relative_link = reverse(
                'finesseBlog:password-reset-confirm',
                kwargs={'uidb64': uidb64, 'token': token}
            )
            abslink=f'http://{site_domain}{relative_link}'
            email_body = f"Hi use the link below to reset your password \n {abslink}"
            data = {
                'email_body' : email_body,
                'email_subject' : "Reset Your Password",
                'to_email':user.email
            }
            send_normal_email(data)

        return super().validate(attrs)

class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=100, min_length=6, write_only=True)
    confirm_password = serializers.CharField(max_length=100, min_length=6, write_only=True)
    uidb64=serializers.CharField(write_only=True)
    token=serializers.CharField(write_only=True)

    class Meta:
        fields = ['password', 'confirm_password', 'uidb64', 'token']


    def validate(self, attrs):
        try:
            token=attrs.get('token')
            uidb64=attrs.get('uidb64')
            password=attrs.get('password')
            confirm_password=attrs.get('confirm_password')

            # decode the user id and get the user
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('reset link is invalid or has expired', 401)
            if password != confirm_password:
                raise AuthenticationFailed('passwords do not match')
            user.set_password(password)
            user.save()
            return user 
        except Exception as e:
            return AuthenticationFailed('link is invalid or has expired')
        

class LogoutUserSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    default_error_message = {
        'bad_token' : ('Token is invalid or has expired')
    }

    def validate(self, attrs):
        self.token = attrs.get('refresh_token')
        return attrs
    
    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            return self.fail('bad_token')
            
        







    









