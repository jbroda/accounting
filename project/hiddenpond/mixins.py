from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from dirtyfields import DirtyFieldsMixin
from reversion.revisions import revision_context_manager
from cuser.middleware import CuserMiddleware
import logging
import reversion

##############################################################################
logger = logging.getLogger(__name__)

##############################################################################
class ChangeHistoryMixin(DirtyFieldsMixin, object):
    def save(self, *args, **kwargs):
        try:
            # Check if a new object.
            is_new = self.pk is None

            # Get the current user.
            user = CuserMiddleware.get_user()

            # Get fields that were changed in the object.
            changed_fields = self.get_dirty_fields()

            # Create a change comment.
            comment = "'{0}' id {1}: ".format(self._meta.model_name, self.id)
            for key,value in changed_fields.iteritems():
                comment += "changed '{0}' from '{1}' to '{2}', ".format(key, value, self.__dict__[key])

            if is_new or not user or user.is_anonymous():
                # Save the new object.
                super(ChangeHistoryMixin, self).save(*args, **kwargs)
            else:
                # Create a new revision for a changed object.
                with transaction.atomic(), reversion.create_revision():
                    reversion.set_user(user)
                    reversion.set_comment(comment)

                    # Save the changed object.
                    super(ChangeHistoryMixin, self).save(*args, **kwargs)

            if user and not user.is_anonymous():
                # Log the change in the Recent Actions.
                LogEntry.objects.log_action(user_id=CuserMiddleware.get_user().id,
                                            content_type_id=ContentType.objects.get_for_model(self).pk,
                                            object_id=self.id,
                                            object_repr=unicode(self),
                                            action_flag=ADDITION if is_new else CHANGE,
                                            change_message=unicode(comment))
                logger.debug(comment)

        except Exception, e:
            logger.exception(e)
