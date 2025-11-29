from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from apps.users.models import UserProfile
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Log apenas tentativa de autenticação (sem username para segurança)
            logger.info("Authentication attempt")

            # First try to find the user by email
            if '@' in username:
                logger.debug("Attempting email authentication")
                user = User.objects.get(email=username)
                logger.debug(f"User found by email")
            else:
                # If not an email, try to find by employee_id
                try:
                    # First try exact username match
                    logger.debug("Attempting username authentication")
                    user = User.objects.get(username=username)
                    logger.debug(f"User found by username")
                except User.DoesNotExist:
                    # If not found, try employee_id
                    logger.debug("Attempting employee_id authentication")
                    profile = UserProfile.objects.get(employee_id=username)
                    user = profile.user
                    logger.debug(f"User found by employee_id")

            # Check the password
            if user.check_password(password):
                logger.info(f"Authentication successful for user: {user.username}")
                return user
            logger.warning("Authentication failed - invalid credentials")
            return None

        except User.DoesNotExist:
            logger.warning("Authentication failed - user not found")
            return None
        except UserProfile.DoesNotExist:
            logger.warning("Authentication failed - user profile not found")
            return None
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
