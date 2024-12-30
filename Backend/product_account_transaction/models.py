from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from users.models import Register
from uuid import uuid4


class VIPLevel(models.Model):
    level = models.PositiveIntegerField(unique=True)
    min_amount = models.DecimalField(max_digits=15, decimal_places=2)
    max_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    single_product_percentage = models.DecimalField(max_digits=4, decimal_places=2)
    combined_product_percentage = models.DecimalField(max_digits=4, decimal_places=2)
    products_per_section = models.PositiveIntegerField()
    min_profit_range = models.DecimalField(max_digits=15, decimal_places=2)
    max_profit_range = models.DecimalField(max_digits=15, decimal_places=2)


    def get_profit_percentage(self, is_combined):
        """
        Return the profit percentage based on whether the product is combined or single
        """
        return self.combined_product_percentage if is_combined else self.single_product_percentage
    
    @classmethod
    def get_vip_level_for_balance(cls, balance):
        """
        Get the VIP Level for a given balance
        """
        return cls.objects.filter(min_amount__lte=balance).filter(
            models.Q(max_amount__get=balance) | models.Q(max_amount__isnull=True)
        ).first()
    

    

class Product(models.Model):
    """Models for Individual products"""
    
    PRODUCT_STATUS = (
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('completed', 'Completed')
    )

    user = models.ForeignKey(Register, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_combined = models.BooleanField(default=False)
    combined_group_id = models.UUIDField(null=True, blank=False)
    status = models.CharField(max_length=20, choices=PRODUCT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)


    def calculate_profit(self):
        """
        Calculate profit for this product based on VIP level
        """
        vip_level = VIPLevel.get_vip_level_for_balance(self.user.balance)
        if not vip_level:
            raise ValueError("No VIP Level match this user's balance.")
        
        percentage = vip_level.get_profit_percentage(self.is_combined)
        return (self.amount * percentage) / Decimal('100.0')
    
class Submission(models.Model):
    user = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='submission')
    product = models.ManyToManyField(Product)
    total_profit = models.DecimalField(max_digits=10, decimal_places=2)

    

class ProductTransactionRecord(models.Model):
    """Logs all transaction for products based on their status"""
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='transaction_records')
    user = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='product_transactions')
    status = models.CharField(max_length=20, choices=Product.PRODUCT_STATUS)
    transaction_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.product.id} - {self.status}"
    
    class Meta:
        db_table = 'product_transaction_records'
        verbose_name = 'Product Transaction Record'
        verbose_name_plural = 'Product Transaction Records'
        ordering = ['-transaction_time']
    


class Balance(models.Model):
    user = models.OneToOneField(
        Register, 
        on_delete=models.CASCADE, 
        related_name='balance'
    )
    balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    frozen_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    cumulative_withdrawal = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    profit_earned = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total profit earned by the user"
    )
    is_pending = models.BooleanField(
        default=False,
        help_text="Indicates if account is pending due to negative balance or no clicks remaining"
    )
    negative_threshold = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Minimum balance threshold before account goes pending"
    )
    click_remaining = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of clicks remaining for the user"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_balances'
        verbose_name = 'User Balance'
        verbose_name_plural = 'User Balances'

    def get_vip_level(self):
        """Get user's current VIP based on the b"""
        return VIPLevel.objects.get(
            min_amount_lte = self.balance,
            max_amount_gte = self.balance
        )

    def can_process_combined_products(self, products):
        """Check if balance is sufficient for combined products"""
        total_amount = sum(product.amount for product in products)
        return self.balance >= total_amount

    def process_product_submission(self, product):
        """Process a product submission and update balance/profits"""
        profit = product.calculate_profit()

        if product.is_combined and not self.can_process_combined_products([product]):
            product.status = 'pending'
            product.save()
            return False

        self.profit_earned += profit
        self.balance -= product.amount
        self.save()

        product.status = 'completed'
        product.save()
        return True

    def process_combined_products(self, products):
        """Process multiple combined products"""
        if not self.can_process_combined_products(products):
            for product in products:
                product.status = 'pending'
                product.save()
            return False

        total_profit = sum(product.calculate_profit() for product in products)

    def get_total_balance(self):
        """Calculate total balance including frozen funds"""
        return self.balance + self.frozen_balance

    def deduct_balance(self, amount):
        """
        Deduct balance and update pending status
        
        Args:
            amount (Decimal): Amount to deduct from balance
            
        Raises:
            ValueError: If amount is negative or greater than current balance
        """
        if amount < 0:
            raise ValueError("Cannot deduct negative amount")
        if amount > self.balance:
            raise ValueError("Insufficient balance")

        self.balance -= amount
        self.click_remaining = max(0, self.click_remaining - 1)
        self.is_pending = (self.balance <= self.negative_threshold or 
                          self.click_remaining <= 0)
        self.save()

    def fund_account(self, amount):
        """
        Fund the account and clear pending status if conditions are met
        
        Args:
            amount (Decimal): Amount to add to balance
            
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError("Cannot fund with negative amount")

        self.balance += amount
        if self.balance > self.negative_threshold and self.click_remaining > 0:
            self.is_pending = False
        self.save()

    def __str__(self):
        return (f"{self.user.email} - Balance: {self.balance}, "
                f"Clicks Remaining: {self.click_remaining} "
                f"(Pending: {self.is_pending})")
    

    def add_profit(self, amount):
        """
        Add profit to user's account
        
        Args:
            amount (Decimal): Amount of profit to add
            
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError("Profit amount cannot be negative")
        self.profit_earned += amount
        self.balance += amount
        self.save()


class Recharge(models.Model):
    """Handles deposits made by users."""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - Deposit: {self.amount} - {self.status}"
    
    class Meta:
        db_table = 'deposits'
        verbose_name = 'Deposit'
        verbose_name_plural = 'Deposits'
        ordering = ['-created_at']

# Recharger Transaction Model
class RechargeTransactionRecord(models.Model):
    """Logs all deposite transactions"""
    deposit = models.ForeignKey('product_account_transaction.Recharge', on_delete=models.CASCADE, related_name='transaction_records')
    user = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='deposit_transactions')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed')])
    transaction_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - Deposit Record - {self.status}"
    
    class Meta:
        db_table = 'deposit_transaction_records'
        verbose_name = 'Deposit Transaction Record'
        verbose_name_plural = 'Deposit Transaction Records'
        ordering = ['-transaction_time']

# Withdrawal Model
class Withdrawal(models.Model):
    """Handles withdrawal made by users"""
    users = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed')])
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - Withdrawa: {self.amount} - {self.status}"
    
    class Meta:
        db_table = 'withdrawals'
        verbose_name = 'Withdrawal'
        verbose_name_plural = 'Withdrawals'
        ordering = ['-created_at']

# Withdrawal Transaction Record
class WithdrawalTransactionRecord(models.Model):
    """Log all withdrawal transactions."""
    withdrawal = models.ForeignKey('Withdrawal', on_delete=models.CASCADE, related_name='transaction_records')
    user = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='withdrawal_transactions')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('rejected', 'Rejected')])
    transaction_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - Withdrawal Record - {self.status}"
    
    class Meta:
        db_table = 'withdrawal_transaction_records'
        verbose_name = 'Withdrawal Transaction Record'
        verbose_name_plural = 'Withdrawal Transaction Records'
        ordering = ['-transaction_time']

