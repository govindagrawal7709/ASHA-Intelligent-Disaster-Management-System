from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    ROLE_CHOICES = (
        ('victim', 'Victim'),
        ('volunteer', 'Volunteer'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=20)

    # Volunteer-only fields
    full_name = models.CharField(max_length=100, blank=True)
    skills_bio = models.TextField(max_length=500, blank=True)
    # Location fields (for volunteers)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    # Timestamp for last location update (volunteer or admin)
    location_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
    def save(self, *args, **kwargs):
        """
        Update location_updated_at when latitude/longitude change.
        This ensures admin edits also update the timestamp.
        """
        try:
            old = Profile.objects.get(pk=self.pk)
        except Profile.DoesNotExist:
            old = None

        if old is None:
            # New profile — if lat/lon provided, set timestamp now
            if self.latitude is not None or self.longitude is not None:
                self.location_updated_at = timezone.now()
        else:
            # If either coordinate changed, update timestamp
            lat_changed = (old.latitude != self.latitude)
            lon_changed = (old.longitude != self.longitude)
            if lat_changed or lon_changed:
                self.location_updated_at = timezone.now()

        super().save(*args, **kwargs)


class ReliefRequest(models.Model):
    REQUEST_TYPE_CHOICES = [
        ('Medical', 'Medical'),
        ('Food', 'Food'),
        ('Water', 'Water'),
        ('Shelter', 'Shelter'),
        ('Rescue', 'Rescue'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Assigned', 'Assigned'),
        ('En Route', 'En Route'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_requests')
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPE_CHOICES)
    description = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    assigned_to_volunteer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_request_type_display()} request by {self.requester.username} ({self.status})"


from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Ensure a Profile exists for every User.
    - Creates a Profile when a new User is created.
    - Saves Profile when User is saved (keeps things in sync).
    """
    if created:
        # default role could be left blank or set to 'victim' by default
        Profile.objects.create(user=instance, role='victim', phone_number='')
    else:
        # if a profile exists, save it (no-op if nothing changed)
        try:
            instance.profile.save()
        except Profile.DoesNotExist:
            # create if missing for any reason
            Profile.objects.create(user=instance, role='victim', phone_number='')