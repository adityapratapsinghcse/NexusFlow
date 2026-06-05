from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect ,get_object_or_404
from .models import CollegeData , COLLEGES ,Profile
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User, Group 
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode , urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.contrib.auth.forms import SetPasswordForm
from django.utils.encoding import force_str
from django.contrib.auth import logout
from django.utils.timezone import now
from events.models import Event, EventRegistration, Venue, EventLogisticsAssignment
from django.db.models import Q
from datetime import timedelta
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from notifications.models import Notification
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .decorators import role_required
from django.db.models import Count, Avg
from django.db.models.functions import TruncMonth
from datetime import timedelta 
from django.utils import timezone
from django.conf import settings

@login_required
def student_ban_list(request):
    if not request.user.groups.filter(name="Admin").exists():
        return redirect("main_page")
    profiles = Profile.objects.select_related('user','college_data').filter(
        college_data__role='Student'
    )
    return render(request, "ban_list.html", {"profiles": profiles})

@login_required
def toggle_ban(request, user_id):
    if not request.user.groups.filter(name="Admin").exists():
        return redirect("main_page")
    profile = get_object_or_404(Profile, user_id=user_id)
    if request.method == "POST":
        profile.is_banned = not profile.is_banned
        profile.ban_reason = request.POST.get("reason", "").strip() or None
        profile.save()
        action = "banned" if profile.is_banned else "unbanned"
        messages.success(request, f"Student {action} successfully.")
    return redirect("student_ban_list")

#-------------------------------!!  MAIN DASHBOARD LOGIC  !!-----------------------------------------
def dashboard(request):
    today = now().date()
    next_month = today + timedelta(days=60) 
    events = Event.objects.filter(status="APPROVED",
                                  start_datetime__date__range=[today, next_month] # DB Query
                                  ).order_by("start_datetime")
    return render(request, "main.html", {"events": events})

#-----------------------------------------------------------------------------------------------------


#------------------------------------!!  LOGIN LOGIC  !!----------------------------------------------
def login_view(request):
    context = {
            'colleges': COLLEGES
    }
    if request.method == "POST":
        college_id = request.POST.get('username')
        password = request.POST.get('password')
        college_name = request.POST.get('college_name')

        user = authenticate(request, username=college_id, password=password)

        if user is not None:
            if not hasattr(user, 'profile'):
                messages.error(request, "User profile not found. Contact admin.")
                return render(request, "login.html", context)
            
            if user.profile.college_name != college_name:
                messages.error(request, "College name does not match our records.")
                return render(request, "login.html", context)
            
            if user.profile.is_banned == True:
                messages.error(request,"Your Id is Banned From the Admin Please Contact In Person")
                return render(request, "login.html", context)
            
            login(request, user)

            if user.is_superuser:
                return redirect('/dev_admin/')

            elif user.groups.filter(name='Admin').exists():
                return redirect('admin_dashboard')

            elif user.groups.filter(name='Teacher').exists():
                return redirect('teacher_dashboard')

            elif user.groups.filter(name='Student').exists():
                return redirect('student_dashboard')
            
            messages.error(request, "You do not have permission to access any dashboard.")
            return render(request, "login.html", context)
        else:
            messages.error(request,"Invalid College ID or Password.")
    return render(request, "login.html" ,context)

#-----------------------------------------------------------------------------------------------------

#------------------------------------!! REGISTER LOGIC  !!----------------------------------------------

def register_view(request):
    context = {
            'colleges': COLLEGES
    }
    if request.method == "POST":
        role = request.POST.get('role')
        f_name = request.POST.get('first_name','').strip()
        l_name = request.POST.get('last_name','').strip()
        college_id = request.POST.get('college_id')
        college_name = request.POST.get('college_name')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'register.html',context)


        try:
            record = CollegeData.objects.get(college_id=college_id)
        except CollegeData.DoesNotExist:
            messages.error(request, "This ID is not registered with the college.")
            return render(request, "register.html",context)

        if record.f_name.strip().lower() != f_name.lower() or record.l_name.strip().lower() != l_name.lower():
            messages.error(request, "Name does not match college records.")
            return render(request, "register.html", context)


        if record.role != role:
            messages.error(request, "Role does not match college records.")
            return render(request, "register.html",context)
        
        if college_name != record.college:
            messages.error(request, "College name does not match college records.")
            return render(request, "register.html",context)

        if email.lower() != record.email.lower():
            messages.error(request, "Email does not match college records.")
            return render(request, "register.html",context)
        
        if User.objects.filter(username=college_id).exists():
            messages.error(request, "This account already exists.")
            return render(request, "register.html",context)
        
        user = User.objects.create_user(
            username=record.college_id,
            password=password,
            email=email,
            first_name=f_name,
            last_name=l_name
        )
        Profile.objects.create(
            user=user,
            college_data=record,
            college_name=college_name,
            phone=record.phone,
        )

        group = Group.objects.get(name=role)
        user.groups.add(group)

        messages.success(request, "Registration successful!")
        return redirect('login')
    
    return render(request, 'register.html',context)

#-----------------------------------------------------------------------------------------------------

#------------------------------------!! PASSWORD RESET  !!----------------------------------------------

# Import tracking mechanics from your models file
from .models import log_action 

@login_required
def account_dashboard_hub(request):
    """
    Renders the central dynamic profile workspace. 
    By default, it targets the main 'profile' Identity Matrix panel.
    """
    return render(request, "profile.html", {
        'active_tab': 'profile'
    })

@login_required
def account_security_tab(request):
    """
    Renders the left-side navigation view contextually initialized to 
    the secure verification token link generator tab panel.
    """
    return render(request, "profile.html", {
        'active_tab': 'password'
    })

@login_required
def account_logs_tab(request):
    """
    Pulls logging items matching this specific logged-in user link block.
    """
    # Fetch live streams where actor equals current logged-in identity
    user_logs = request.user.audit_actions.all()[:10]
    return render(request, "profile.html", {
        'active_tab': 'logs',
        'user_logs': user_logs
    })

def reset_pass(request):
    """
    Your verified matching logic. Validates identification criteria against User registries,
    serializes system web signatures, and dispatches an alert email.
    """
    if request.method == "POST":
        f_name = request.POST.get('first_name', '').strip()
        l_name = request.POST.get('last_name', '').strip()
        college_id = request.POST.get('college_id', '').strip()
        email = request.POST.get('email', '').strip()
        
        try:
            user = User.objects.get(username=college_id, email=email, first_name=f_name, last_name=l_name)

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            reset_url = request.build_absolute_uri(reset_path) 

            context = {
                'first_name': user.first_name,
                'reset_url': reset_url,
            }
            html_content = render_to_string('password_reset_email.html', context)
            text_content = strip_tags(html_content)

            subject = "Reset Your NexusFlow Password"
            send_mail(
                    subject,
                    text_content,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    html_message=html_content,
                    fail_silently=False,
                )

            log_action(
                actor=user,
                action='PASS_RESET_REQUESTED', # Map contextual actions safely
                target_user=user,
                notes='System identity verified. Secure recovery security token emailed.',
                request=request
            )

            messages.success(request, "Verification successful! Check your Gmail for the link.")
            return render(request, "password_reset.html")

        except User.DoesNotExist:
            messages.error(request, "Identity verification failed. Details do not match.")
            
    return render(request, "password_reset.html")


def reset_confirm(request, uidb64, token):
    """
    Validates recovery link hashes and overrides the underlying credentials map.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                
                # Log modification trace to audit logs tracking ledger
                log_action(
                    actor=user,
                    action='PASS_RESET_CONFIRMED',
                    target_user=user,
                    notes='System user successfully overrode operational authorization keys via recovery token.',
                    request=request
                )
                
                messages.success(request, "Password reset successful! You can now login.")
                return redirect('login')
            else:
                return render(request, "reset_password.html", {"form": form, "validlink": True})
        else:
            form = SetPasswordForm(user)
        return render(request, "reset_password.html", {"form": form, "validlink": True})
    else:
        return render(request, "reset_password.html", {"validlink": False})


def check_email_exists(request):
    """
    Asynchronous JSON verification interface helper checking database fields.
    """
    email = request.GET.get('email', None)
    data = {
        'is_taken': User.objects.filter(email__iexact=email).exists()
    }
    return JsonResponse(data)
#-----------------------------------------------------------------------------------------------------


#------------------------------------!! STUDENT DASHBOARD  !!----------------------------------------------

@login_required
@role_required(['Student'])
def student_dashboard(request):
    today = now().date()
    next_days = today + timedelta(days=7)
    
    student_college = request.user.profile.college_name 
    
    events = Event.objects.filter(
        status="APPROVED",
        date__range=[today, next_days],
    ).filter(
        Q(college_profile__college_name=student_college) | Q(is_general=True)
    ).order_by("date")
    
    registration_count = EventRegistration.objects.filter(student=request.user).count()
    approved_events_count = Event.objects.filter(
        status="APPROVED",
        date__gte=today,
    ).filter(
        Q(college_profile__college_name=student_college) | Q(is_general=True)
    ).count()
    venue_count = Venue.objects.count()
    
    # Unified Notifications Dispatch
    recent_notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:4]
    
    # Check if there are any unread notifications to activate the glowing badge dot
    # Adjust field names ('is_read' vs 'is_unread') based on your precise database Schema
    is_read = Notification.objects.filter(is_read=False).exists()
    
    return render(request, "student_dashboard.html", {
        "name": request.user.get_full_name() or request.user.username,
        "events_this_week": events,
        "registration_count": registration_count,
        "approved_events_count": approved_events_count,
        "venue_count": venue_count,
        "recent_notifications": recent_notifications,
        "has_unread": is_read
    })

#-----------------------------------------------------------------------------------------------------

#------------------------------------!! TEACHER DASHBOARD  !!----------------------------------------------

@login_required
@role_required(['Teacher'])
def teacher_dashboard(request):
    
    organizer = request.user
    seven_days_ago = datetime.now() - timedelta(days=7)


    events = Event.objects.filter(organizer=organizer,date__gte=seven_days_ago)
    total_events = events.count()
    pending_approvals = events.filter(status='PENDING').count()
    total_reach = EventRegistration.objects.filter(event__organizer=organizer).count()
    my_recent_events = events.order_by('-date')[:5]

    recent_registrations = EventRegistration.objects.filter(
        event__organizer=request.user
    ).select_related('event', 'student').order_by('-registered_at')[:5]

    recent_notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:3]

    assigned_logistics = EventLogisticsAssignment.objects.filter(
        assigned_teacher=request.user
    ).select_related('event', 'event__venue', 'assigned_by').order_by('-assigned_at')[:5]

    context = {
        'total_events': total_events,
        'pending_approvals': pending_approvals,
        'total_reach': total_reach,
        'my_recent_events': my_recent_events,
        'recent_registrations': recent_registrations,
        'recent_notifications': recent_notifications,
        'assigned_logistics': assigned_logistics,
    }
    return render(request, "teacher_dashboard.html", context)
#-----------------------------------------------------------------------------------------------------

#------------------------------------!! ADMIN DASHBOARD  !!----------------------------------------------


@login_required
@role_required(['Admin'])
def admin_dashboard(request):
    today = timezone.now()
    # Existing stats
    total_students      = User.objects.filter(groups__name='Student').count()
    total_teachers      = User.objects.filter(groups__name='Teacher').count()
    pending_approvals   = Event.objects.filter(status='PENDING').count()
    active_events_count = Event.objects.filter(status='APPROVED').count()
    total_registrations = EventRegistration.objects.count()
    recent_requests     = Event.objects.all().order_by('-created_at')[:5]

    # Monthly registrations (last 6 months)
    monthly_regs = list(
        EventRegistration.objects
        .filter(registered_at__gte=today - timedelta(days=180))
        .annotate(month=TruncMonth('registered_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    # Top 5 venues by event count
    top_venues = list(
        Venue.objects.annotate(event_count=Count('event'))
        .order_by('-event_count')[:5]
        .values('name', 'event_count')
    )

    # Events per college
    events_by_college = list(
        Event.objects.values('college_profile__college_name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Recent audit log entries
    from accounts.models import AuditLog
    recent_audit = AuditLog.objects.select_related('actor','event')[:10]
    recent_notifications = Notification.objects.filter(
        role='ADMIN'
    ).order_by('-created_at')[:5]
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'pending_approvals': pending_approvals,
        'active_events_count': active_events_count,
        'total_registrations': total_registrations,
        'recent_requests': recent_requests,
        'monthly_regs': monthly_regs,
        'top_venues': top_venues,
        'events_by_college': events_by_college,
        'recent_audit': recent_audit,
        'recent_notifications': recent_notifications,
    }
    return render(request, "admin_dashboard.html", context)
#-----------------------------------------------------------------------------------------------------

#------------------------------------!! PROFILE LOGIC  !!----------------------------------------------

@login_required
def profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        if phone == str(request.user.profile.phone or ""):
            messages.info(request, "Phone number is unchanged.")
            return redirect("profile")
        if phone:
            profile.phone = phone
            profile.save(update_fields=['phone'])
            messages.success(request, "Profile updated successfully.")
        else:
            messages.error(request, "Phone number cannot be empty.")
        return redirect('profile')
    return render(request, "profile.html")

#-----------------------------------------------------------------------------------------------------

#------------------------------------!! LOGOUT LOGIC  !!----------------------------------------------

def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out successfully.")
    return redirect('login')

#-----------------------------------------------------------------------------------------------------

@login_required
@role_required(['Admin'])
def venue_management(request):
    # Process Creation Operations Inline to prevent view context switching
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        capacity = request.POST.get('capacity')
        location = request.POST.get('location', '').strip()

        if not name or not capacity or not location:
            messages.error(request, "All infrastructure parameters are required.")
        elif Venue.objects.filter(name__iexact=name).exists():
            messages.error(request, f"Configuration Fault: A venue named '{name}' is already registered.")
        else:
            Venue.objects.create(name=name, capacity=capacity, location=location, is_active=True)
            messages.success(request, f"Venue asset '{name}' was deployed successfully.")
            return redirect('venue_management')

    # Query Set Compilation with dynamic hosted counts aggregation
    venues = Venue.objects.annotate(event_count=Count('event')).order_by('name')
    return render(request, 'venue_management.html', {'venues': venues})


@login_required
@role_required(['Admin'])
def toggle_venue(request, venue_id):
    # Restrict modifications to POST requests for system mutation security
    if request.method == 'POST':
        venue = get_object_or_404(Venue, id=venue_id)
        venue.is_active = not venue.is_active
        venue.save()
        
        status_string = "OPERATIONAL" if venue.is_active else "DECOMMISSIONED"
        messages.success(request, f"Ecosystem state updated: '{venue.name}' marked {status_string}.")
    else:
        messages.error(request, "Invalid protocol invocation method.")
        
    return redirect('venue_management')

@login_required
@role_required(['Admin'])
def audit_log_view(request):
    from accounts.models import AuditLog
    logs = AuditLog.objects.select_related(
        'actor', 'event', 'target_user'
    ).order_by('-timestamp')[:200]
    return render(request, 'audit_log.html', {'logs': logs})