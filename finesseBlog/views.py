from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import generics
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from .models import Post, OneTimePassword, Comment, User
from .serializers import PostSerializer, UserRegisterSerializer, LoginSerializer, CommentSerializer, PasswordResetRequestSerializer, SetNewPasswordSerializer, LogoutUserSerializer, CreateCommentSerializer
from django.db.models import Count
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .utils import send_code_to_user



class PostDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.select_related('author', 'category').prefetch_related('post_comments', 'post_comments__author', 'images').annotate(likes_count=Count('likes'))
    serializer_class = PostSerializer
    lookup_field = 'slug'


    def get_permissions(self):
        # Ensure only authenticated users can perform write actions to a post
        self.permission_classes = [AllowAny]
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()


    def get_queryset(self):
        # Ensure only the author can update/delete
        qs = super().get_queryset()
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            qs = qs.filter(author=self.request.user)
        return qs

    def perform_update(self, serializer):
        # Ensure author isn't changed
        serializer.save(author=self.request.user)

    def perform_destroy(self, instance):
        # Double-check author before delete
        if instance.author != self.request.user:
            raise PermissionDenied("You can only delete your own posts.")
        instance.delete()



class PostListCreateApiView(generics.ListCreateAPIView):
    queryset = Post.objects.select_related('author', 'category').prefetch_related('post_comments', 'post_comments__author', 'images').annotate(likes_count=Count('likes'))
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    


class UserPostListApiView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.select_related('author').prefetch_related('post_comments', 'post_comments__author', 'images').annotate(likes_count=Count('likes'))
    serializer_class = PostSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(author=self.request.user)
    

# class PostDetailApiView(generics.RetrieveAPIView):
#     queryset = Post.objects.select_related('author').prefetch_related('post_comments', 'post_comments__author', 'images').annotate(likes_count=Count('likes'))
#     serializer_class = PostSerializer
#     lookup_field = 'slug'

class RegisterUserView(GenericAPIView):
    serializer_class=UserRegisterSerializer

    def post(self, request):
        user_data = request.data
        serializer = self.serializer_class(data=user_data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            user= serializer.data
            # Call send email function
            send_code_to_user(user['email'])
            print(user)
            return Response(
                {
                    'data' : user,
                    'message' : f'hi {user['first_name']} thanks for signing up, a passcode has been to your email'
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyUserEmail(GenericAPIView):
    def post(self, request):
        otpCode = request.data.get('otp')
        if not otpCode:
            return Response({'message': 'OTP code is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_code_obj = OneTimePassword.objects.get(code=otpCode)
            user = user_code_obj.user
            if not user.is_verified:
                user.is_verified=True
                user.save()
                return Response({
                    'message': 'account email verified successfuly'
                }, status=status.HTTP_200_OK)
            return Response({
                'message' : 'code is invalid, user is already verified'
            }, status=status.HTTP_204_NO_CONTENT)
        
        except OneTimePassword.DoesNotExist:
            return Response({'message': 'passcode not provided'}, status=status.HTTP_404_NOT_FOUND)



class LogInUserView(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request':request})
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)





class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context = {'request' : request})
        serializer.is_valid(raise_exception=True)
        return Response({
            'message': "A link has been sent to your email to reset your password."
        }, status=status.HTTP_200_OK)
    
class PasswordResetConfirm(GenericAPIView):

    def get(self, request, uidb64, token):
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id = user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({
                    'message' : "token is invalid or has expired"
                }, status=status.HTTP_401_UNAUTHORIZED)
            return Response({
                'success' : True,
                'message' : "credentials is valid",
                'uidb64' : uidb64,
                'token':token
            }, status=status.HTTP_200_OK)

        except DjangoUnicodeDecodeError:
            return Response({
                    'message' : "token is invalid or has expired"
                }, status=status.HTTP_401_UNAUTHORIZED)
        

class SetNewPassword(GenericAPIView):
    serializer_class=SetNewPasswordSerializer
    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'message': 'password reset successful'}, status=status.HTTP_200_OK)
    

class LogoutUserView(GenericAPIView):
    serializer_class = LogoutUserSerializer
    permission_classes = [IsAuthenticated]


    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)



class CommentCreateApiView(GenericAPIView):
    serializer_class = CreateCommentSerializer
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context = {'request' : request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)







