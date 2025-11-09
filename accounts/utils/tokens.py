from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
import six
import jwt


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk)
            + six.text_type(timestamp)
            + six.text_type(user.is_active)
        )
    
def generate_activation_token(user):
    payload = {
            'user_id': user.id,
            'email': user.email,
            'username': user.username,
        }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')



account_activation_token = AccountActivationTokenGenerator()