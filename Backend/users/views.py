from django.shortcuts import render
from .serializers import RegisterSerializer, ProfileSerializer
from .models import Register, Profile
from .authentication import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions
from rest_framework.views import APIView


# Create your views here.
class RegisterView(generics.CreateAPIView):
    queryset = Register.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class UserInfoView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = RegisterSerializer(user)
        return Response(serializer.data)
    
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    
    def patch(self, request):
        profile = request.user.profile
        wallet_address = request.data.get('wallet_address')

        if wallet_address:
            profile.wallet_address = wallet_address
            profile.save()
            return Response({'message': 'Wallet address updated successfully.'}, status=200)
        return Response({'error': 'No valid data provided.'}, status=400)