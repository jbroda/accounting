from django.core.management.base import BaseCommand, CommandError
from accounting.tasks import backup_db
import logging

###############################################################################
logger = logging.getLogger(__name__)

###############################################################################
class Command(BaseCommand):
    args = None
    help = 'Backup the database ...'

    def handle(self, *args, **options):
        try:
            logger.info('Backing up the database ...')
            backup_db()
            logger.info('FINISHED backup up the database!')
        except Exception, e:
            logger.exception(e)
            self.stderr.write("ERROR: " + str(e))