from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# ---------- Your existing models (keep all of them) ----------
class Community(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

class Property(models.Model):
    STATUS_CHOICES = [('occupied', 'Occupied'), ('vacant', 'Vacant')]
    unit_number = models.CharField(max_length=20, unique=True)
    owner_name = models.CharField(max_length=200)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='vacant')
    def __str__(self):
        return f"Unit {self.unit_number} - {self.owner_name}"

class Announcement(models.Model):
    CATEGORY_CHOICES = [('general', 'General'), ('emergency', 'Emergency'), ('maintenance', 'Maintenance'), ('event', 'Event')]
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    is_emergency = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True)
    def __str__(self):
        return self.title

class Fee(models.Model):
    STATUS_CHOICES = [('unpaid', 'Unpaid'), ('paid', 'Paid'), ('overdue', 'Overdue')]
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='fees')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    description = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.property.unit_number} - ${self.amount} - {self.status}"

class Payment(models.Model):
    METHOD_CHOICES = [('cash', 'Cash'), ('bank_transfer', 'Bank Transfer'), ('credit_card', 'Credit Card'), ('check', 'Check')]
    fee = models.ForeignKey(Fee, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash')
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    notes = models.TextField(blank=True)
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            import random, datetime
            self.receipt_number = f"RCP-{datetime.date.today().strftime('%Y%m%d')}-{random.randint(1000,9999)}"
        super().save(*args, **kwargs)
        total_paid = self.fee.payments.aggregate(total=models.Sum('amount'))['total'] or 0
        self.fee.status = 'paid' if total_paid >= self.fee.amount else 'unpaid'
        self.fee.save()
    def __str__(self):
        return f"Receipt {self.receipt_number} - ${self.amount}"

class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')]
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='requests')
    resident_name = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_to = models.CharField(max_length=100, blank=True)
    def __str__(self):
        return f"{self.property.unit_number} - {self.title}"

class ResidentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resident_profile')
    property = models.ForeignKey('Property', on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    move_in_date = models.DateField(null=True, blank=True)
    def __str__(self):
        property_info = f" - {self.property.unit_number}" if self.property else ""
        return f"{self.user.username}{property_info}"

class ParkingSpot(models.Model):
    spot_number = models.CharField(max_length=10, unique=True)
    property = models.ForeignKey('Property', on_delete=models.SET_NULL, null=True, blank=True, related_name='parking_spots')
    is_covered = models.BooleanField(default=False)
    is_reserved = models.BooleanField(default=False)
    def __str__(self):
        status = f"→ {self.property.unit_number}" if self.property else "Available"
        return f"Spot {self.spot_number} - {status}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    reply = models.TextField(blank=True, null=True)
    replied_at = models.DateTimeField(blank=True, null=True)
    def __str__(self):
        return f"From {self.sender.username}: {self.subject}"

class Conversation(models.Model):
    resident = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_resident')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_admin', null=True, blank=True)
    subject = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_closed = models.BooleanField(default=False)
    def __str__(self):
        return f"Conversation: {self.subject}"

class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.sender.username}: {self.message[:30]}"

# ---------- NEW SOCIAL MODELS ----------
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, max_length=500)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

# Auto-create UserProfile when a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Friendship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('blocked', 'Blocked'),
    ]
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_friend_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_friend_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.status})"

class PrivateConversation(models.Model):
    participants = models.ManyToManyField(User, related_name='private_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation between {', '.join([u.username for u in self.participants.all()])}"

class PrivateMessage(models.Model):
    conversation = models.ForeignKey(PrivateConversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"

@receiver(post_save, sender=User)
def add_staff_as_friends(sender, instance, created, **kwargs):
    if created:
        staff_users = User.objects.filter(is_staff=True)
        for staff in staff_users:
            if staff != instance:
                Friendship.objects.get_or_create(from_user=staff, to_user=instance, defaults={'status': 'accepted'})
                Friendship.objects.get_or_create(from_user=instance, to_user=staff, defaults={'status': 'accepted'})