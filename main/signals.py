from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.conf import settings
from HealthNet import customLog

@receiver(user_logged_in)
def sig_user_logged_in(sender, user, request, **kwargs):
    customLog.add_log("User logged in: %s at %s" % (user, request.META['REMOTE_ADDR']), 'LOGON')

@receiver(user_logged_out)
def sig_user_logged_out(sender, user, request, **kwargs):
    customLog.add_log("User logged out: %s at %s" % (user, request.META['REMOTE_ADDR']), 'LOGOFF')