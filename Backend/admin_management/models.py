from django.db import models
from django.conf import settings
import logging

# Create your models here.
logger = logging.getLogger('admin_action')

class AdminAuditLog(models.Model):
    """
    Audit log for tracking admin actions
    """
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admin_actions'
    )

    action_type = models.CharField(max_length=50)
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )

    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(null=True, blank=True)

    def log_action(self, action_type, target_user, details=None):
        """
        Create a new audit log entry
        """
        return self.objects.create(
            admin_user = self.admin_user,
            action_type=action_type,
            target_user=target_user,
            details=details or {}
        )

class SoftDeleteUser(models.Model):
    """
    Extended user model with soft delete functionality
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def soft_delete(self):
        """
        Soft delete user
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """
        Restore soft deleted user
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save()

        