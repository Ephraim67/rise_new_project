from django.shortcuts import render
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .models import VIPLevel, Product
from .serializers import VIPLevelSerializer, ProductSerializer
from decimal import Decimal
from uuid import uuid4

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

