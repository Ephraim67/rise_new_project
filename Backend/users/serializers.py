from rest_framework import serializers
from .models import Register, Profile
from django.contrib.auth.hashers import make_password
import uuid


class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = Register
        fields = ["id", "fullname", "email", "username", "phone_number", "withdrawal_password", "password", "confirm_password", "inviteCode", "click_count", "last_click_time", "vip_level", "is_active", "is_staff", "date_joined"]
        extra_kwargs = {
            'password': {'write_only': True},
            'withdrawal_password': {'write_only': True},
            'inviteCode': {'required': False, 'allow_blank': True},
            # 'balance': {'read_only': True}
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        
        invite_code = data.get("inviteCode")
        if invite_code and not Register.objects.filter(inviteCode=invite_code).exists():
            raise serializers.ValidationError("Invalid invite code.")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        hashed_password = make_password(password)

        # Generate a unique invite code
        while True:
            name_part = validated_data.get('username', 'user')[:4].upper()
            random_number = f"{uuid.uuid4().int % 10000:04}"
            invite_code = f"{name_part}{random_number}"

            # Check if invite is unique
            if not Register.objects.filter(inviteCode=invite_code).exists():
                break

        validated_data['inviteCode'] = invite_code

        user = Register.objects.create(password=hashed_password, **validated_data)
        return user
    
class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    referral_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'user',
            'balance',
            'todays_commission',
            'wallet_address',
            'referral_code',
            'referral_count',
            'referred_users',
            'referral_earnings',
        ]

    def get_referral_count(self, obj):
        return obj.referral_count()
