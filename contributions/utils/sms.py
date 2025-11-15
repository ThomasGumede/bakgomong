import requests
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
import logging
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from contributions.models import MemberContribution

logger = logging.getLogger('emails')


def send_sms_via_smsportal(to, message):
    """
    SMSPortal API (South Africa)
    """
    url = "https://rest.smsportal.com/v1/bulkmessages"
    payload = {
        "messages": [
            {
                "content": message,
                "destination": to
            }
        ]
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {settings.SMSPORTAL_AUTH}"  # Base64(clientID:secret)
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()


def send_sms_via_twilio(to, message):
    """
    Twilio WhatsApp OR SMS
    """
    client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)

    return client.messages.create(
        from_=settings.TWILIO_FROM,  # "whatsapp:+14155238886" or "+123456789"
        to=to,
        body=message
    )


def send_email_notification(site_url, mc: MemberContribution):
    """
    Sends an HTML email when a new MemberContribution is created.
    """

    try:
        subject = "BAKGOMONG | New Contribution Assigned"

        # Prepare email HTML
        message = render_to_string(
            "emails/new-contribution-notification.html",
            {
                "mc": mc,
                "site_url": site_url,
            }
        )

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[mc.account.email],
        )
        email.content_subtype = "html"

        email.send()
        logger.info(f"[EMAIL SENT] New contribution email sent to {mc.account.email}")

        return True

    except Exception as err:
        logger.error(
            f"[EMAIL FAILED] Could not send contribution email to {mc.account.email}. Error: {err}"
        )
        return False
