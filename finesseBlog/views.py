from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Post, OneTimePassword
from .serializers import PostSerializer, UserRegisterSerializer, LoginSerializer
from django.db.models import Count
from .utils import send_code_to_user

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


class TestAuthenticationView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            'msg' : 'it works'
        }
        return Response(data, status=status.HTTP_200_OK)


