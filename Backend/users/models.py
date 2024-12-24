from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin, Group, Permission


# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, withdrawal_password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email is Required."))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)

        # Password reset
        if withdrawal_password:
            user.set_withdrawal_password(withdrawal_password)
        user.save(using=self.db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        
        return self.create_user(email, password, **extra_fields)


class Register(AbstractBaseUser, PermissionsMixin):
    VIP_LEVELS = [
        (1, 'VIP 1'),
        (2, 'VIP 2'),
        (3, 'VIP 3'),
        (4, 'VIP 4'),
    ]
     
    fullname = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=60)
    phone_number = models.CharField(max_length=100, blank=True, null=True)
    withdrawal_password = models.CharField(max_length=100, blank=True, null=True)
    inviteCode = models.CharField(max_length=8, unique=True, blank=True, null=True)
    click_count = models.PositiveIntegerField(default=0)
    last_click_time = models.DateTimeField(null=True, blank=True)
    vip_level = models.PositiveSmallIntegerField(choices=VIP_LEVELS, default=1)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    groups = models.ManyToManyField(Group, related_name='usermanager_set', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='register_set', blank=True)

    objects = UserManager()

    USERNAME_FIELDS = 'email'
    REQUIRED_FIELDS = ['fullname', 'username']

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return self.email
    
    def get_short_name(self):
        return self.fullname.split()[0] if self.fullname else self.username
    
    def get_absolute_url(self):
        return reverse("user-detail", kwargs={"pk": self.pk})
    

    def set_withdrawal_password(self, raw_password):
        if raw_password:
            self.withdrawal_password = make_password(raw_password)
            self.save(update_fields=['withdrawal_password'])
            print(f"Withdrawal password set for user {self.email}: {self.withdrawal_password}")
    
    def check_withdrawal_password(self, raw_password):
        print(f"Checking withdrawal password for user {self.email}")
        print(f"Stored password: {self.withdrawal_password}")

        if not self.withdrawal_password:
            return False
        
        return check_password(raw_password, self.withdrawal_password)
    

class Profile(models.Model):
    user = models.OneToOneField(Register, on_delete=models.CASCADE, related_name='profile')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    todays_commission = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    wallet_address = models.CharField(max_length=50, blank=True, null=True)
    referral_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    referral_count = models.PositiveIntegerField(default=0)
    referred_users = models.ManyToManyField(Register, related_name='referrers', blank=True)
    referral_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    has_newbie_bonus = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def referal_count(self):
        return self.referred_users.count()