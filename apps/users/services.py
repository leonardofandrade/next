"""
Services for users app
"""
from typing import Dict, Any, Optional
from django.db.models import QuerySet
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from apps.core.services.base import BaseService, ValidationServiceException, PermissionServiceException
from apps.users.models import UserProfile


class UserProfileService(BaseService):
    """Service for UserProfile business logic"""
    
    model_class = UserProfile
    
    def get_or_create_profile(self, user: User) -> UserProfile:
        """Get or create user profile"""
        profile, created = UserProfile.objects.get_or_create(user=user)
        return profile
    
    def get_profile_by_user(self, user: User) -> Optional[UserProfile]:
        """Get user profile by user"""
        try:
            return UserProfile.objects.get(user=user, deleted_at__isnull=True)
        except UserProfile.DoesNotExist:
            return None
    
    def update_profile(self, profile: UserProfile, data: Dict[str, Any], user_data: Optional[Dict[str, Any]] = None) -> UserProfile:
        """
        Update user profile and optionally user data
        
        Args:
            profile: UserProfile instance
            data: Profile data
            user_data: Optional User model data (first_name, last_name, email)
        """
        # Update profile fields
        for field, value in data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        
        # Update user fields if provided
        if user_data and profile.user:
            if 'first_name' in user_data:
                profile.user.first_name = user_data['first_name']
            if 'last_name' in user_data:
                profile.user.last_name = user_data['last_name']
            if 'email' in user_data:
                profile.user.email = user_data['email']
            profile.user.save()
        
        # Validate and save
        profile.full_clean()
        profile.updated_by = self.user
        profile.save()
        
        return profile
    
    def update_profile_image(self, profile: UserProfile, image_data: Optional[bytes], remove: bool = False) -> UserProfile:
        """Update profile image"""
        if remove:
            profile.profile_image = None
        elif image_data:
            profile.profile_image = image_data
        
        profile.updated_by = self.user
        profile.save()
        return profile
    
    def change_password(self, user: User, current_password: str, new_password: str) -> User:
        """Change user password"""
        if not user.check_password(current_password):
            raise ValidationServiceException("Senha atual incorreta")
        
        user.set_password(new_password)
        user.save()
        return user
    
    def validate_permissions(self, action: str, obj: Optional[UserProfile] = None) -> bool:
        """
        Validate user permissions for actions on user profiles.
        Users can only edit their own profile.
        """
        if not self.user:
            return False
        
        # For list/create, any authenticated user can access
        if action in ['list', 'create']:
            return True
        
        # For update/delete, user must own the profile
        if action in ['update', 'delete'] and obj:
            return obj.user == self.user
        
        # For view, user can view their own profile
        if action == 'view' and obj:
            return obj.user == self.user
        
        return False

