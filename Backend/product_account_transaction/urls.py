from django.urls import path
from .views import (
    VIPLevelListView,
    VIPLevelDetailView,
    SubmitProductView,
    RechargeView,
    ProductTransactionRecordViewSet,
    RechargeTransactionRecordViewSet,
    WithdrawalTransactionRecordViewSet,
)

urlpatterns = [
    # vip level endpoitns
    path('vip-levels/', VIPLevelListView.as_view(), name='vip-levels'),
    path('vip-levels/<int:pk>/', VIPLevelDetailView.as_view(), name='vip-level-detail'),

    # Product submission endpoint
    path('products/submit/', SubmitProductView.as_view(), name='submit-product'),

    # Recharge endpoint
    path('recharge/', RechargeView.as_view(), name='recharge'),

    # Withdrawal endpoint
    

    # Product transaction record endpoint
    path('product-transaction-records/', ProductTransactionRecordViewSet.as_view({'get': 'list'}), name='product-transaction-records'),
    path('product-transaction-records/<int:pk>/', ProductTransactionRecordViewSet.as_view({'get': 'retrieve'}), name='product-transaction-record'),
    path('withdrawal-transaction-records/', WithdrawalTransactionRecordViewSet.as_view({'get': 'list'}), name='withdrawal-transaction-records'),
    path('withdrawal-transaction-records/<int:pk>/', WithdrawalTransactionRecordViewSet.as_view({'get': 'retrieve'})),
    path('recharge-transaction-records/', RechargeTransactionRecordViewSet.as_view({'get': 'list'}), name='recharge-transaction-records'),
]
