from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Decorator to restrict view access to admin users only.
    """
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if request.user.user_type != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapped_view


def student_required(view_func):
    """
    Decorator to restrict view access to student users only.
    """
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if request.user.user_type != 'user':
            messages.error(request, 'Access denied. Student access only.')
            return redirect('admin_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapped_view
