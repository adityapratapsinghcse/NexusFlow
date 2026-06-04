from django.db import models
from django.contrib.auth.models import User

ROLE_CHOICES = [
    ('Student', 'Student'),
    ('Teacher', 'Teacher'),
    ('Admin', 'Admin'),
]

COLLEGES=[
    ('UCER',"United College of Engineering and Research"),
    ('UIT','United Institute of Technology'),
    ('UIP','United College of Pharmacy'),
    ('UIM','United Institute of Management')
]

class CollegeData(models.Model):
    college_id = models.CharField(max_length=20, unique=True)
    college = models.CharField(max_length=100, choices=COLLEGES)
    f_name = models.CharField(max_length=100)
    l_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    father_name = models.CharField(max_length=100, blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    branch = models.CharField(max_length=50, blank=True, null=True)  # for HODs/admin
    designation = models.CharField(max_length=50, blank=True, null=True)  # for teachers
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
        
    def __str__(self):
        return f"{self.f_name} {self.l_name} ({self.college_id})"
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    college_data = models.OneToOneField(CollegeData, on_delete=models.CASCADE,null=True ,blank = True)
    college_name = models.CharField(max_length=100, choices=COLLEGES)
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True, null=True)

class StudentProxy(CollegeData):
    class Meta:
        proxy = True
        verbose_name = "Student"
        verbose_name_plural = "Students"


class TeacherProxy(CollegeData):
    class Meta:
        proxy = True
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"


class AdminProxy(CollegeData):
    class Meta:
        proxy = True
        verbose_name = "Admin"
        verbose_name_plural = "Admins"

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('EVENT_APPROVED', 'Event Approved'),
        ('EVENT_REJECTED', 'Event Rejected'),
        ('PASS_PUBLISHED', 'Passes Published'),
        ('VENUE_OVERRIDE', 'Venue Override'),
        ('CERT_UPLOADED',  'Certificate Uploaded'),
        ('REG_CANCELLED',  'Registration Cancelled'),
        ('STUDENT_BANNED', 'Student Banned'),
        ('STUDENT_UNBANNED','Student Unbanned'),
        ('LOGISTICS_ASSIGNED', 'Logistics Assigned'),   # ← ADD THIS
        ('PASS_PUBLISHED_ADMIN', 'Passes Published by Admin'),
        ('PASS_RESET_REQUESTED', 'Password Reset Requested'),
        ('PASS_RESET_CONFIRMED', 'Password Reset Confirmed'),
        ('PASS_PUBLISHED_ADMIN', 'Passes Published by Admin'),
        ('PASS_DEACTIVATED',     'Passes Deactivated by Admin'),
    ]
    actor       = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='audit_actions'
    )
    action = models.CharField(max_length=25, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_targets'
    )
    event       = models.ForeignKey(
        'events.Event', on_delete=models.SET_NULL, null=True, blank=True
    )
    notes       = models.TextField(blank=True)
    timestamp   = models.DateTimeField(auto_now_add=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'

    def __str__(self):
        return f"{self.actor} — {self.action} @ {self.timestamp:%Y-%m-%d %H:%M}"


# Helper — call this from any view that does an admin action
def log_action(actor, action, event=None, target_user=None, notes='', request=None):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        event=event,
        target_user=target_user,
        notes=notes,
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
    )