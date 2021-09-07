from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMessage
from os import environ
import logging

###############################################################################
logger = logging.getLogger(__name__)

###############################################################################
class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            ADMIN_EMAIL= environ.get('ADMIN_EMAIL', 'admin@XXXXXXXXX.XX')
            logger.info('Sending a test email to {0}...'.format(ADMIN_EMAIL))
            from django.core.mail import EmailMessage
            email = EmailMessage('Hello', 'World', ADMIN_EMAIL, to=[ADMIN_EMAIL])
            email.send()
            logger.info('Sent a test email to {0}!'.format(ADMIN_EMAIL))

        except Exception, e:
            logger.exception(e)
            self.stderr.write("ERROR: " + str(e))
