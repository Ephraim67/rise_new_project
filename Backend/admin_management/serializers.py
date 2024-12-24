from rest_framework import serializers
from django.contrib.auth import get_user_model
from datetime import datetime
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.message))
        return value

class AdminUserSerializer(serializers.ModelSerializer):
    """
    Serializer for admin user management
    """
    registration_date = serializers.DateTimeField(source='date_joined', read_only=True)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id',
            'fullname',
            'email',
            'username',
            'phone_number',
            'withdrawal_password',
            'password',
            'confirm_password',
            'inviteCode',
            'click_count',
            'last_click_time',
            'vip_level',
            'is_active',
            'is_staff',
            'registration_date'  # Include the alias field
        ]
        read_only_fields = ['id', 'registration_date']
    
    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        
        return attrs


class AdminUserManagementSerializer(serializers.Serializer):
    """
    Enhanced serializer for admin user management
    """
    VIP_LEVELS = [
        (1, 'VIP 1'),
        (2, 'VIP 2'),
        (3, 'VIP 3'),
        (4, 'VIP 4'),
    ]
    fullname = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(max_length=60, required=True)
    phone_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    withdrawal_password = serializers.CharField(max_length=100, required=True)
    inviteCode = serializers.CharField(max_length=8, required=True)
    click_count = serializers.IntegerField(default=0, min_value=0)
    last_click_time = serializers.DateTimeField(required=True)
    vip_level = serializers.ChoiceField(choices=VIP_LEVELS, required=True)
    is_active = serializers.BooleanField(required=True)
    is_staff = serializers.BooleanField(required=True)
    date_joined = serializers.DateTimeField(default=datetime.now)

    def validate_email(self, value):
        """
        Check if the email is unique
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value
    
    def create(self, validated_data):
        """
        Create a new user
        """
        return User.objects.create_user(**validated_data)
    