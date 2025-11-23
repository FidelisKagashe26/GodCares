# content/permissions.py
from rest_framework import permissions

class AdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit content.
    Regular users can only read (GET, HEAD, OPTIONS).
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has a `user` attribute.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return obj.user == request.user

class IsMissionaryOrAdmin(permissions.BasePermission):
    """
    Permission to only allow missionaries or admins to access mission-related data.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        if request.user.is_staff:
            return True
            
        # Check if user is a missionary (has completed scholar stage)
        from .models import DiscipleshipJourney
        try:
            journey = DiscipleshipJourney.objects.get(user=request.user)
            return journey.current_stage == 'missionary' or journey.missionary_completed
        except DiscipleshipJourney.DoesNotExist:
            return False

class IsGroupLeaderOrAdmin(permissions.BasePermission):
    """
    Permission to only allow Bible study group leaders or admins to modify groups.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
            
        return obj.leader == request.user

class CanVerifyMissions(permissions.BasePermission):
    """
    Permission to only allow admins and designated verifiers to verify mission reports.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        if request.user.is_staff:
            return True
            
        # Add logic for designated verifiers if needed
        return hasattr(request.user, 'can_verify_missions') and request.user.can_verify_missions