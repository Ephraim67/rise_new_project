from django.urls import path
from .views import (
    VIPLevelListView,
    VIPLevelDetailView,
    SubmitProductView,
)

urlpatterns = [
    # vip level endpoitns
    path('vip-levels/', VIPLevelListView.as_view(), name='vip-levels'),
    path('vip-levels/<int:pk>/', VIPLevelDetailView.as_view(), name='vip-level-detail'),

    # Product submission endpoint
    path('products/submit/', SubmitProductView.as_view(), name='submit-product')
]
