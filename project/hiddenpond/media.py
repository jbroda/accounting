from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.storage import default_storage
from django.http import StreamingHttpResponse, HttpResponse, HttpResponseRedirect
from django.views.static import serve
from accounting.list_file import *
import logging
import os

##############################################################################
logger = logging.getLogger(__name__)

##############################################################################
@user_passes_test(lambda u: u.is_superuser)
def serve_log(request):
    response = 'None'
    try:
        f = open(settings.ERROR_LOG, "r")
        response = StreamingHttpResponse(streaming_content=f, 
                                         content_type='text/plain')
    except Exception, e:
        logger.exception(e)
    return response

##############################################################################
@login_required
def serve_media(request, mediaType, subType, filename, fileExtension):
    disk_file = os.path.normpath(default_storage.location + "/" + 
                                 mediaType + "/" +
                                 subType + "/" +
                                 filename + "." + fileExtension)
    logger.info("file '%s'" % disk_file)
    return serve(request, os.path.basename(disk_file), os.path.dirname(disk_file))

##############################################################################
@login_required
def delete_media(request, mediaType, subType, filename, fileExtension):
    response = HttpResponse(("Failed to delete '%s.%s'!" % (filename,fileExtension)), 
                            content_type='text/plain')
    try:
        disk_file = os.path.normpath(default_storage.location + "/" + 
                                     mediaType + "/" +
                                     subType + "/" +
                                     filename + "." + fileExtension)
        redirect_url = request.POST.get('redirect_url')
        logger.info("redirect URL:" + str(redirect_url))
        if default_storage.exists(disk_file):
            logger.info("DELETING '%s'" % disk_file)
            default_storage.delete(disk_file)
            logger.info("DELETED '%s'" % disk_file)

            # Decrement  the number of files in the list file.
            update_list_file(False, mediaType + "/" + subType + "/")
            response = HttpResponseRedirect(redirect_url)
    except Exception, e:
        logger.exception(e)

    return response
