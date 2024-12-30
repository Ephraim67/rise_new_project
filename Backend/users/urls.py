from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, CustomTokenObtainPairView, UserProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    path('token/', CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path('token/refresh/', TokenRefreshView.as_view(), name="token_refresh"),
    path('api-auth/', include("rest_framework.urls")),

    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/update/', UserProfileView.as_view(), name='user-profile-update'),
]
