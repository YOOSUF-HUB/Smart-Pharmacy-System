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
        
        # Check for role-specific paths and ensure user has correct role
        if request.user.is_authenticated:
            if '/admin-dashboard/' in path and request.user.role != 'admin':
                from django.shortcuts import redirect
                return redirect('redirect_dashboard')
                
            if '/med-inventory-dash/' in path and request.user.role != 'pharmacist':
                from django.shortcuts import redirect
                return redirect('redirect_dashboard')
                
            if '/cashier-dashboard/' in path and request.user.role != 'cashier':
                from django.shortcuts import redirect
                return redirect('redirect_dashboard')
                
            if '/customer-dashboard/' in path and request.user.role != 'customer':
                from django.shortcuts import redirect
                return redirect('redirect_dashboard')
        
        response = self.get_response(request)
        return response