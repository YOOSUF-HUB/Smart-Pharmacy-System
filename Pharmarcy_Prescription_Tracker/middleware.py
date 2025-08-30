class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add no-cache headers to authenticated requests
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
        return response
    

class RoleBasedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request before view is called
        path = request.path
        
        # Only check for unauthorized access, not override decorators
        if request.user.is_authenticated:
            # Check specific path patterns, but don't redirect admins from customer pages
            # Let the view decorator handle that specific permission check
            
            # Only redirect if trying to access a dashboard that's clearly for another role
            if '/dashboard/admin/' in path and request.user.role != 'admin':
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("You must be an admin to access this page.")
                
            if '/dashboard/pharmacist/' in path and request.user.role != 'pharmacist':
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("You must be a pharmacist to access this page.")
                
            if '/dashboard/cashier/' in path and request.user.role != 'cashier':
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("You must be a cashier to access this page.")
                
            if '/dashboard/customer/' in path and request.user.role != 'customer':
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("You must be a customer to access this page.")
        
        response = self.get_response(request)
        return response