from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),


    # Users Management
    path('api/users/', include('users.urls')),

    # Admin Management
    path('api/admin-management/', include('admin_management.urls')),

    # Product-Account-Transaction 
    path('api/product-account-transaction/', include('product_account_transaction.urls'))
    
]
