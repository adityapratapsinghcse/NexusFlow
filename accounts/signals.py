from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from .models import Profile


# 2️⃣ Assign group AFTER college_data is set
@receiver(post_save, sender=Profile)
def assign_group(sender, instance, **kwargs):
    if instance.college_data:
        role = instance.college_data.role
        group, _ = Group.objects.get_or_create(name=role)
        instance.user.groups.set([group])

# 3️⃣ Prevent reuse of same CollegeData
@receiver(pre_save, sender=Profile)
def prevent_profile_collision(sender, instance, **kwargs):
    if instance.college_data:
        exists = Profile.objects.filter(
            college_data=instance.college_data
        ).exclude(pk=instance.pk).exists()

        if exists:
            raise ValidationError("This College ID is already registered.")
