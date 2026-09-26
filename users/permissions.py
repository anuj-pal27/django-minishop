from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    message = "Only staff can change this."                 # error text for 403

    def has_permission(self, request, view):                # runs for EVERY request to the view
        if request.method in permissions.SAFE_METHODS:      # GET, HEAD, OPTIONS = only reading
            return True                                     # anyone may read
        return bool(request.user and request.user.is_staff) # writing: staff only


class IsOwnerOrStaff(permissions.BasePermission):
    message = "You can only access your own orders."

    def has_object_permission(self, request, view, obj):   # runs for ONE object (detail pages)
        return request.user.is_staff or obj.user_id == request.user.id  # staff, or the order's owner


class IsSelfOrStaff(permissions.BasePermission):            # 1C-2 exercise
    message = "You can only view your own profile."

    def has_object_permission(self, request, view, obj):   # obj = the User being viewed
        return request.user.is_staff or obj == request.user  # staff, or it's me
