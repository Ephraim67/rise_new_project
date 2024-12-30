from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from .models import VIPLevel, Product, ProductTransactionRecord, RechargeTransactionRecord, WithdrawalTransactionRecord, Recharge, Withdrawal
from .serializers import VIPLevelSerializer, ProductSerializer, ProductTransactionRecordSerializer, RechargeTransactionRecordSerializer, WithdrawalTransactionRecordSerializer, RechargeSerializer, WithdrawalSerializer
from decimal import Decimal
from django.conf import settings
from uuid import uuid4
from django_filters.rest_framework import DjangoFilterBackend

# Create your views here.

class VIPLevelListView(ListAPIView):
    queryset = VIPLevel.objects.all()
    serializer_class = VIPLevelSerializer

class VIPLevelDetailView(RetrieveAPIView):
    queryset = VIPLevel.objects.all()
    serializer_class = VIPLevelSerializer

class SubmitProductView(APIView):
    def post(self, request):
        user = request.user
        products_data = request.data.get('products', [])
        combined_group_id = None
        total_profit = Decimal('0.0')

        for product_data in products_data:
            amount = Decimal(product_data['amount'])
            is_combined = product_data.get('is_combined', False)

            vip_level = VIPLevel.get_vip_level_for_balance(user.balance)
            if not vip_level:
                return Response(
                    {"error": "User balance does not match any VIP level."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            
            if user.balance < amount:
                is_combined = True
                status_text = 'pending'
                combined_group_id = combined_group_id or uuid4()
            else:
                status_text = 'submitted'
                user.balance -= amount

            # Create the product
            product = Product.objects.create(
                user=user,
                amount=amount,
                is_combined=is_combined,
                combined_group_id=combined_group_id if is_combined else None,
                status=status_text,

            )
            total_profit += product.calculate_profit()

        user.save()
        return Response(

            {"message": "Products submitted successfully.", "total_profit": str(total_profit)},
            status=status.HTTP_201_CREATED,
        )
    
class ProductTransactionRecordViewSet(ModelViewSet):
    queryset = ProductTransactionRecord.objects.all()
    serializer_class = ProductTransactionRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'transaction_time']

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

class RechargeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount')
        try:
            amount = Decimal(amount)
            if amount <= 0:
                return Response({'error': 'Amount must be greater than zero.'}, status=400)
        except(ValueError, TypeError):
            return Response({'error': 'Invalid amount provided.'}, status=400)
        
        # Create a pending deposit record
        recharge = Recharge.objects.create(
            user=request.user,
            amount=amount,
            status='pending',
        )

        # Create a pending transaction record
        RechargeTransactionRecord.objects.create(
            user=request.user,
            recharge=recharge,
            amount=amount,
            status='pending',
        )

        # Admin contact links
        telegram_link = f"https://t.me/{settings.TELEGRAM_ADMIN_USERNAME}"
        whatsapp_link = f"https://wa.me/{settings.WHATSAPP_ADMIN_PHONE_NUMBER}?text=Hello,%20I%20would%20like%20to%20proceed%20with%20my%20deposit%20of%20{amount}."

        return Response(
            {
                'message': 'Deposit request received. Please proceed with the payment.',
                'recharge_id': recharge.id,
                'status': recharge.status,
                'telegram_link': telegram_link,
                'whatsapp_link': whatsapp_link,
            },
            status=201,
        )

class RechargeTransactionRecordViewSet(ModelViewSet):
    queryset = RechargeTransactionRecord.objects.all()
    serializer_class = RechargeTransactionRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

class WithdrawalTransactionRecordViewSet(ModelViewSet):
    queryset = WithdrawalTransactionRecord.objects.all()
    serializer_class = WithdrawalTransactionRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

