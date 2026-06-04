from django.db import models
from django.contrib.auth.models import User
from accounts.models import Profile
from django.utils import timezone
from datetime import datetime

class Venue(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.name} (Cap: {self.capacity})"

class Event(models.Model):
    STATUS_CHOICES = [
        ('PENDING','Pending'),
        ("APPROVED",'Approved'),
        ("REJECTED", 'Rejected'),    
    ]
    organizer = models.ForeignKey(User,on_delete=models.CASCADE)
    venue = models.ForeignKey(Venue , on_delete=models.SET_NULL , null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    poster = models.ImageField(upload_to='event_posters/',null=True,blank=True)
    expected_crowd =  models.IntegerField()

    status = models.CharField(max_length=10,choices=STATUS_CHOICES , default = "PENDING")
    night_event_warning = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    start_datetime = models.DateTimeField(blank=True, null=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    is_published = models.BooleanField(default=False)
    college_profile = models.ForeignKey(Profile, null=True,blank = True,on_delete=models.CASCADE)
    bus_route = models.FileField(upload_to='bus_routes/', null=True, blank=True)
    is_general = models.BooleanField(default=False)
    ai_warnings = models.TextField(blank=True, null=True)
    ai_venue_reason = models.TextField(blank=True, null=True)
    predicted_crowd = models.IntegerField(null=True, blank=True)
    crowd_confidence = models.CharField(max_length=50,blank=True,null=True)
    ai_crowd_reason = models.TextField(blank=True,null=True)
    registration_start = models.DateTimeField(null=True, blank=True)
    registration_end = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    def __str__(self):
            return self.title
    

class EventRegistration(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete= models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)
    
    unique_pass = models.CharField(max_length=20, blank=True, null=True)
    qr_code_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    pass_generated = models.BooleanField(default=False)
    pass_active = models.BooleanField(default=False)  
    verified = models.BooleanField(default=False)    
    verified_at = models.DateTimeField(blank=True, null=True) 

    class Meta:
         unique_together = ('student','event')

    def __str__(self):
        return f"{self.student} → {self.event}"
    
class StudentCertificate(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    certificate_file = models.FileField(upload_to="certificates/")
    photo = models.ImageField(upload_to="student_photos/", blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class WaitlistEntry(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    event   = models.ForeignKey(Event, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'event')
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.student} → waitlist for {self.event}"
    
class EventFeedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    student    = models.ForeignKey(User, on_delete=models.CASCADE)
    event      = models.ForeignKey(Event, on_delete=models.CASCADE)
    rating     = models.IntegerField(choices=RATING_CHOICES)
    comment    = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'event')

    def __str__(self):
        return f"{self.student} → {self.event} ({self.rating}★)"
    
class EventLogisticsAssignment(models.Model):
    """Admin assigns a teacher to manage passes/scanning for an event."""
    event = models.OneToOneField(
        Event, on_delete=models.CASCADE, related_name='logistics_assignment'
    )
    assigned_teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='logistics_assignments'
    )
    assigned_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='logistics_assigned_by'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.event.title} → {self.assigned_teacher.get_full_name()}"