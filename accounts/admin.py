from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import CollegeData, StudentProxy, TeacherProxy, AdminProxy, Profile, AuditLog
from .resources import StudentResource, TeacherResource, AdminResource
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Inline admin for Profile
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'

# Custom UserAdmin
class CustomUserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

    # This prevents showing the inline for new users before they are created
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

# Unregister default User admin
admin.site.unregister(User)
# Register custom User admin
admin.site.register(User, CustomUserAdmin)


@admin.register(StudentProxy)
class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ('college_id', 'f_name','l_name', 'branch', 'dob')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='Student')
    

@admin.register(TeacherProxy)
class TeacherAdmin(ImportExportModelAdmin):
    resource_class = TeacherResource
    list_display = ('college_id','f_name','l_name', 'branch', 'dob')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='Teacher')


@admin.register(AdminProxy)
class AdminAdmin(ImportExportModelAdmin):
    resource_class = AdminResource
    inlines = [ProfileInline]
    list_display = ('college_id', 'f_name','l_name', 'email', 'phone', 'branch','college', 'address', 'dob', 'role')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='Admin')
    
    def get_phone(self, obj):
        return obj.profile.phone if hasattr(obj, 'profile') else None
    get_phone.short_description = 'Phone'


admin.site.register(CollegeData)  # Optional: Register base model if needed

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ('timestamp', 'actor', 'action', 'event', 'target_user', 'ip_address')
    list_filter   = ('action',)
    search_fields = ('actor__username', 'notes')
    readonly_fields = ('actor','action','event','target_user','notes','timestamp','ip_address')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False