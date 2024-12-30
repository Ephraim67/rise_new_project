import pytz
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from django.db.models import Q
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from datetime import datetime
from rest_framework.permissions import AllowAny, IsAdminUser
from django.utils.timezone import now as timezone_now
from .models import AdminAuditLog, SoftDeleteUser
from product_account_transaction.models import Recharge, ProductTransactionRecord
from .serializers import AdminUserSerializer, AdminLoginSerializer
from product_account_transaction.serializers import RechargeSerializer
from .permissions import IsAdminUserOrSuperuser
from users.serializers import RegisterSerializer

# Create your views here.

User = get_user_model()

# Admin login
class AdminLoginView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated access

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    def get(self, request):
        return Response({
            "message": "Please use POST method to login",
            "required_fields": {
                "email": "your admin email",
                "password": "your password"
            }
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            # Check if user exists and is staff/superuser
            try:
                user = User.objects.get(email=email)
                if not (user.is_staff or user.is_superuser):
                    return Response(
                        {'error': 'User is not an admin'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Authenticate user
            user = authenticate(request, email=email, password=password)
            if user:
                # Generate tokens
                refresh = RefreshToken.for_user(user)

                # Log successful login
                now = datetime.now(pytz.UTC)
                user.last_login = now
                user.save()

                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'email': user.email,
                    'is_superuser': user.is_superuser,
                    'is_staff': user.is_staff,
                    'last_login': now.isoformat()
                })

            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# admin user list view
class AdminUserListView(generics.ListAPIView):
    """
    List all user for admin
    Endpoint: GET /api/admin-management/users
    """ 
    serializer_class = AdminUserSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        status_filter = self.request.query_params.get('status')
        if status_filter:
            return User.objects.filter(is_active=(status_filter.lower() == 'active'))
        return User.objects.all()
    

class AdminUserDetailView(generics.RetrieveAPIView):
    """
    Retrieve specific user details
    Endpoint: GET /api/admin-management/users/<pk>/
    """
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [AllowAny]

class AdminUserBlockUnblockView(APIView):
    """
    Block or Unblock a user
    Endpoint: POST /api/admin-management/users/<pk>/toggle-status/
    """
    permission_classes = [AllowAny]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            user.is_active = not user.is_active
            user.save()

            action = "unblocked" if user.is_active else "blocked"
            return Response({
                'message': f'User {action} successfully',
                'user_id': user.id,
                'is_active': user.is_active
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        

class AdminUserDeleteView(generics.DestroyAPIView):
    """
    Permanetly delete a user
    Endpoint: Delete /api/admin-management/users/<pk>/delete/
    """
    def destroy(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            user_id = user.id
            user.delete()
            return Response({
                'message': 'User deleted successfully',
                'user_id': user_id
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Failed to delete user',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AdminUserSearchView(generics.ListAPIView):
    """
    Search users by username, email, or other criteria
    Endpoint: GET /api/admin/users/search/?q=<search_term>
    """
    serializer_class = AdminUserSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        query = self.request.quer_params.get('q', '')
        if not query:
            return User.objects.none()
        
        return User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(fullname__icontains=query)
        )
    
class AdvancedUserFilterView(generics.ListAPIView):
    """
    Advanced user filtering with multiple criteria
    """
    permission_classes = [AllowAny]
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        queryset = User.objects.all()

        filters = {
            'username': self.request.query_params.get('username'),
            'email': self.request.query_params.get('email'),
            'is_active': self.request.query_params.get('status'),
            'date_joined__gte': self.request.query_params.get('joined_after'),
            'date_joined__lte': self.request.query_params.get('joined_before')
        }

        filters = {k: v for k, v in filters.items() if v is not None}

        return queryset.filter(**filters)
    
class AdminUserManagementView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Create a new user from admin account
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            if request.data.get('is_staff'):
                user.is_staff = True
                user.save()

            AdminAuditLog.objects.create(
                admin_user=request.user,
                action_type='user_creation',
                target_user=user,
                details={
                    'created_by': request.user.username,
                    'user_email': user.email
                }
            )

            return Response({
                'message': 'User Created Successfully',
                'user_id': user.id 
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, user_id):
        """
        Freeze user account
        """
        try:
            user = User.objects.get(id=user_id)

            user.is_active = False
            user.save()

            SoftDeleteUser.objects.get_or_create(
                user=user,
                defaults={
                    'is_deleted': True, 'deleted_at': timezone_now()
                }
            )

            AdminAuditLog.objects.create(
                admin_user=request.user,
                action_type='user_frozen',
                target_user=user,
                details={
                    'frozen_by': request.user.username
                }
            )

            return Response({
                'message': 'User account frozen successfully',
                'user_id': user.id
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        

class AdminDepositeManagementView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        Fetch all deposite with optional filtering by status.
        Example: /admin/deposites/?status=pending
        """
        status = request.query_params.get('status')
        deposits = Recharge.objects.all()
        if status:
            deposits = deposits.filter(status=status)

        serializer = RechargeSerializer(deposits, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """
        Approve a pending deposit or deposit directly to user account
        """
        action = request.data.get('action') # 'approve' or 'deposit'
        if action == 'approve':
            deposit_id = request.data.get('deposit_id')
            return self.approve_deposit(deposit_id)
        elif action == 'direct_deposit':
            user_id = request.data.get('user_id')
            amount = request.data.get('amount')
            return self.direct_deposit(user_id, amount)
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
        
    def approve_deposit(self, deposit_id):
        try:
            deposit = Recharge.objects.get(id=deposit_id, status='pending')
            user = deposit.user


            # Update user balance
            user.balance.balance += deposit.amount
            user.balance.save()

            # Update deposit status
            deposit.status = 'completed'
            deposit.completed_at = timezone_now()
            deposit.save()

            # Update transaction records to completed
            transaction_records = deposit.transaction_records.first()
            if transaction_records:
                transaction_records.status = 'completed'
                transaction_records.transaction_time = timezone_now()
                transaction_records.save()

            return Response({'message': 'Deposit approved successfully'}, status=status.HTTP_200_OK)
        except Recharge.DoesNotExist:
            return Response({'error': 'Deposit not found'}, status=status.HTTP_404_NOT_FOUND)
        
    def direct_deposit(self, user_id, amount):
        try:
            user = User.objects.get(id=user_id)
            if float(amount) <= 0:
                return Response({'error': 'Amount must be greater than zero'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update user balance
            user.balance.balance += float(amount)
            user.balance.save()

            # Create a successful recharge and transaction record
            deposit = Recharge.object.create(
                user=user,
                amount=amount,
                status='completed',
                completed_at = timezone_now()
            )

            ProductTransactionRecord.objects.create(
                user=user,
                recharge=deposit,
                status='completed',
                transaction_time = timezone_now()
            )

            return Response({'message': 'Deposit successful'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)



        