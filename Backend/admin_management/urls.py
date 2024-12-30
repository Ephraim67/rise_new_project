from django.urls import path
from .views import (
    AdminLoginView,
    AdminUserListView,
    AdminUserDetailView,
    AdminUserBlockUnblockView,
    AdminUserDeleteView,
    AdminUserSearchView,
    AdvancedUserFilterView,
    AdminUserManagementView,
    AdminDepositeManagementView

)

urlpatterns = [
    # Login admin view
    path('login/', AdminLoginView.as_view(), name='admin-login'),

    # List all users
    path('users/', AdminUserListView.as_view(), name='admin-user-list'),

    # Get Specific user
    path('users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),

    # Block and Unblock user
    path('users/<int:pk>/toggle-status/', AdminUserBlockUnblockView.as_view(), name='admin-user-toggle-status'),

    # Delete user
    path('users/<int:pk>/delete/', AdminUserDeleteView.as_view(), name='admin-user-delete'),

    # Search users
    path('users/search/', AdminUserSearchView.as_view(), name='admin-user-search'),

    # Advance user filter
    path('users/filter/', AdvancedUserFilterView.as_view(), name='admin-user-filter'),
    
    # user management
    path('users/create', AdminUserManagementView.as_view(), name='admin-user-create'),

    # Frozen user account
    path('users/<int:user_id>/freeze/', AdminUserManagementView.as_view(), name='admin-user-freeze'),

    # Deposite management
    path('deposite/', AdminDepositeManagementView.as_view(), name='admin-deposite'),
]
