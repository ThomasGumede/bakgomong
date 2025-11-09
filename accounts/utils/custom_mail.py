import logging, base64
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from accounts.utils.tokens import account_activation_token, generate_activation_token
from django.utils.http import urlsafe_base64_encode
from django.core.mail import EmailMessage
from django.conf import settings

logger = logging.getLogger("emails")

def send_html_email(subject, to_email, template_name, context):
    try:
        
        html_content = render_to_string(template_name, context)

        # Create the email message
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email='BAKGOMONG Community <noreply@BAKGOMONG.co.za>',
            to=[to_email],
        )
        email.content_subtype = 'html' 

        # Send the email
        email.send()
        logger.info(f"Email sent to {to_email} without attachment.")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}. Error: {e}")  

def send_email_confirmation_email(user, new_email, request):
    try:
        mail_subject = "BAKGOMONG | New Email Confirmation"
        message = render_to_string("emails/account/email_activation.html",
                {
                    "user": user.get_full_name(),
                    "email": new_email,
                    "uid": generate_activation_token(user),
                    "token": account_activation_token.make_token(user),
                }, request
            )

        email = EmailMessage(
                subject=mail_subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
        email.content_subtype = 'html' 

            # Send the email
        email.send()
        logger.info(f"Email sent to {user.email} without attachment.")
            
        return True
    except Exception as err:
        logger.error(f"Failed to send send_email_confirmation_email to {user.email}. Error: {err}")
        return False
    
def send_verification_email(user, request):
        
        try:
            mail_subject = "BAKGOMONG | Activate Account"
            message = render_to_string("emails/account/account_activate_email.html",
                {
                    "user": user.get_full_name(),
                    "uid": generate_activation_token(user),
                    "token": account_activation_token.make_token(user),
                }, request
            )
            
            # sent = custom_send_email(user.email, mail_subject, message)

            # if not sent:
            #     logger.error("User did not receive email")
            #     return False

            email = EmailMessage(
                subject=mail_subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.content_subtype = 'html' 

            # Send the email
            email.send()
            logger.info(f"Email sent to {user.email} without attachment.")
            
            return True
        except Exception as err:
             logger.error(f"Failed to send send_verification_email to {user.email}. Error: {err}")
             return False

def send_password_reset_email(user, request):
    try:
        mail_subject = "BAKGOMONG | Password Reset request"
        message = render_to_string("emails/password/reset_password_email.html", {
            'user': user.get_full_name(),     
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        }, request)
            
            
        # sent = custom_send_email(user.email, subject, message)
        # if not sent:
        #     return False
           
        email = EmailMessage(
                subject=mail_subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
        email.content_subtype = 'html' 

            # Send the email
        email.send()
        logger.info(f"Email sent to {user.email} without attachment.")
            
        return True
    except Exception as err:
        logger.error(f"Failed to send send_password_reset_email to {user.email}. Error: {err}")
        return False

def send_html_email_with_attachments(to_email: str, subject: str, html_content: str, from_email: str, attachments: list = None) -> bool:
    try:
        email = EmailMessage(subject=subject, body=html_content, from_email=from_email, to=[to_email])
        email.content_subtype = 'html'

        # Attach files if provided
        if attachments:
            for attachment in attachments:
                email.attach(attachment['filename'], base64.b64decode(attachment['file_content']), 'application/pdf')

        email.send()
        logger.info(f"Email sent to {to_email} with attachments.")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}. Error: {e}")
        return False

 

