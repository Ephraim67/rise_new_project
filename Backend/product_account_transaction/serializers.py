from rest_framework import serializers
from .models import (
    VIPLevel,
    Product,
    ProductTransactionRecord,
    Balance,
    Recharge,
    RechargeTransactionRecord,
    Withdrawal,
    WithdrawalTransactionRecord
)

class VIPLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = VIPLevel
        fields = '__all__'
        


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['created_at', 'status']

class ProductTransactionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTransactionRecord
        fields = '__all__'
        read_only_fields = ['transaction_time']

class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Balance
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'profit_earned', 'is_pending']

class RechargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recharge
        fields = '__all__'
        read_only_fields = ['created_at', 'completed_at']

class RechargeTransactionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RechargeTransactionRecord
        fields = '__all__'
        read_only_fields = ['transaction_time']

class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = '__all__'
        read_only_fields = ['created_at', 'completed_at']

class WithdrawalTransactionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalTransactionRecord
        fields = '__all__'
        read_only_fields = ['transaction_time']
