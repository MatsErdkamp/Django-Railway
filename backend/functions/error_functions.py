import sys
import traceback
from django.core import mail
from django.views.debug import ExceptionReporter

def send_manual_exception_email(e):
    exc_info = sys.exc_info()

    mail.mail_admins('ERROR (MANUAL)', e, fail_silently=True,)