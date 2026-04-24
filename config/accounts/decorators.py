from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def artist_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == "artist":
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper


def dealer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == "dealer":
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper


def user_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == "user":
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper
