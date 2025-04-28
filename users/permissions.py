from rest_framework.permissions import BasePermission
from vendors.models import Vendor


class IsAdminOrSuperuser(BasePermission):
    """
    Custom permission to allow access only to admin or superuser users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)

    
class IsVendor(BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.user, Vendor) and request.user.is_authenticated


class IsSuperUserOrAdmin(BasePermission):
    def has_permission(self, request, view):
        print(f"User authenticated: {request.user.is_authenticated}, Is superuser: {request.user.is_superuser}")

        return request.user and (request.user.is_superuser or request.user.is_staff)


class IsAdminOrVendor(BasePermission):
    """
    - Admins can create and manage all coupons.
    - Vendors can create and manage only their own coupons.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated  # Only authenticated users

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:  # Admin can access all
            return True
        try:
            vendor = Vendor.objects.get(user=request.user)  # Check if user is a vendor
            return obj.vendor == vendor  # Vendor can access only their own coupons
        except Vendor.DoesNotExist:
            return False