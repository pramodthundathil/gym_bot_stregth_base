# middleware.py
import threading

_thread_local = threading.local()

class CurrentUserMiddleware:
    """Middleware to store the current user in thread-local storage"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_local.user = getattr(request, 'user', None)
        response = self.get_response(request)
        return response

def get_current_user():
    """Helper function to get current user from anywhere"""
    return getattr(_thread_local, 'user', None)
