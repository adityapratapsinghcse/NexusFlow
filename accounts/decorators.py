from django.http import HttpResponseForbidden
from functools import wraps

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                if hasattr(request.user, 'profile') and request.user.profile.college_data.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You do not have permission to view this page.")
        return _wrapped_view
    return decorator