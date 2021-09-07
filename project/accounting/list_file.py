from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import multiprocessing
import logging

##############################################################################
logger = logging.getLogger(__name__)

###############################################################################
LIST_FILE = ".list.txt"

##############################################################################
LIST_FILE_LOCK = multiprocessing.Lock()

##############################################################################
def does_list_file_exist(dir_path):
    file_path = os.path.join(dir_path, LIST_FILE).replace('\\','/')
    is_list_file = default_storage.exists(file_path)
    return is_list_file

##############################################################################
def update_list_file(increment, report_dir):
    # Update the list file.
    try:
        LIST_FILE_LOCK.acquire()

        list_file = report_dir + LIST_FILE

        logger.info("LIST FILE: {0}".format(list_file))

        if not default_storage.exists(list_file):
            if increment:
                default_storage.save(list_file, ContentFile("1"))
        else:
            # Read the number of files from the list file.
            f = default_storage.open(list_file, mode='r')
            num_files = int(f.read())
            f.close()
            
            # Adjust the number of files.
            if increment:
                num_files += 1
            else:
                num_files -= 1
                
            default_storage.delete(list_file)                
            
            # Store the number of files.
            if num_files > 0:
                logger.info("Writing number of files: {0}".format(num_files))
                f = default_storage.open(list_file, mode='w')
                f.write(str(num_files))
                f.close()

        LIST_FILE_LOCK.release()

    except Exception, e:
        logger.exception(e)
        LIST_FILE_LOCK.release()

