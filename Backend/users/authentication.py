from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenViewBase
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['fullname'] = user.fullname
        token['email'] = user.email
        token['phone_number'] = user.phone_number
        token['withdrawal_password'] = user.withdrawal_password
        token['inviteCode'] = user.inviteCode
        token['is_active'] = user.is_active
        
        return token

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = User.objects.filter(email=email).first()
            if user and user.check_password(password):
                refresh = self.get_token(user)
                return {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            else:
                raise serializers.ValidationError({"detail": "Invalid email or password"})
        else:
            raise serializers.ValidationError({"detail": "Must include email and password"})

class CustomTokenObtainPairView(TokenViewBase):
    serializer_class = CustomTokenObtainPairSerializer

@api_view(['POST'])
def custom_token_obtain_pair(request):
    serializer = CustomTokenObtainPairSerializer(data=request.data)
    try:
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
