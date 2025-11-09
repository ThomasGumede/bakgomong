import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

LOGGING_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGGING_DIR):
    os.makedirs(LOGGING_DIR)

LOGGING_LEVEL = 'ERROR'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'custom': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        }
    },
    'handlers': {
        'file': {
            'level': LOGGING_LEVEL,
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'errors.log'),
            'formatter': 'custom'
        },
        'campaign_file': {
            'level': LOGGING_LEVEL,
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'campaigns.log'),
            'formatter': 'custom'
        },
        'event_file': {
            'level': LOGGING_LEVEL,
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'events.log'),
            'formatter': 'custom'
        },
        'account_file': {
            'level': LOGGING_LEVEL,
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'accounts.log'),
            'formatter': 'custom'
        },
        'payment_file': {
            'level': LOGGING_LEVEL,
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'payments.log'),
            'formatter': 'custom'
        },
        'task_file': {
            'level': LOGGING_LEVEL,
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'tasks.log'),
            'formatter': 'custom'
        },
        'email_file': {
            'level': LOGGING_LEVEL,
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'emails.log'),
            'formatter': 'custom'
        },
        'util_file': {
            'level': LOGGING_LEVEL,
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'utils.log'),
            'formatter': 'custom'
        },
        'listing_file': {
            'level': LOGGING_LEVEL,
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'listings.log'),
            'formatter': 'custom'
        },
        'smtp_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'smtp.log'),
            'formatter': 'custom'
        },
        'info_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'infos.log'),
            'formatter': 'custom'
        },
        
    },
    'loggers': {
        'django': {
            'level': LOGGING_LEVEL,
            'handlers': ['file'],
            'propagate': True,
        },
        'campaigns': {
            'level': LOGGING_LEVEL,
            'handlers': ['campaign_file'],
            'propagate': True,
        },
        'events': {
            'level': LOGGING_LEVEL,
            'handlers': ['event_file'],
            'propagate': True,
        },
        'accounts': {
            'level': LOGGING_LEVEL,
            'handlers': ['account_file'],
            'propagate': True,
        },
        'payments': {
            'level': LOGGING_LEVEL,
            'handlers': ['payment_file'],
            'propagate': True,
        },
        'tasks': {
            'level': LOGGING_LEVEL,
            'handlers': ['task_file'],
            'propagate': True,
        },
        'emails': {
            'level': LOGGING_LEVEL,
            'handlers': ['email_file'],
            'propagate': True,
        },
        'utils': {
            'level': LOGGING_LEVEL,
            'handlers': ['util_file'],
            'propagate': True,
        },
        'listings': {
            'level': LOGGING_LEVEL,
            'handlers': ['listing_file'],
            'propagate': True,
        },
        'smtplib': {
            'handlers': ['smtp_file'],
            'level': 'DEBUG',
        },
        'infos': {
            'handlers': ['info_file'],
            'level': 'DEBUG',
        },
        
    },
}

