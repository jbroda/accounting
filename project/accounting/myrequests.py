
import os
import time
import signal
import multiprocessing
import logging
import shutil
import pickle
from django.core.files.storage import default_storage
from django.conf import settings

##############################################################################
logger = logging.getLogger(__name__)

###############################################################################
class RequestInfo:
    def __init__(self,pid):
        self.pid = pid        # Process ID of the spawned request
        self.toBeDeleted = () # Files or dirs to be deleted when cancelled.

###############################################################################

# Active requests file.
AR_FILE = os.environ.get('TEMP',settings.SITE_ROOT) + '/requests.bin'

# Synchronize updates of the active requests file with this lock.
GlobalLock = multiprocessing.Lock()

###############################################################################
def get_active_requests():
    activeRequests = dict()
    GlobalLock.acquire()
    try:
        if os.path.exists(AR_FILE):
            with open(AR_FILE,'rb') as f:
                activeRequests = pickle.load(f)
    except Exception, e:
        logger.exception(e)
    GlobalLock.release()
    return activeRequests

###############################################################################
def get_active_request(reqId):
    rqInfo = None
    try:
        activeRequests = get_active_requests()
        if not activeRequests:
            raise Exception('no active requests found!')
        rqInfo = activeRequests.get(reqId)
        if not rqInfo:
            raise Exception("no running processes for reqId %s" % reqId)
    except Exception, e:
        logger.exception(e)
    return rqInfo

###############################################################################
def add_active_request(reqId, rqInfo):
    try:
        activeRequests = get_active_requests()
        GlobalLock.acquire()
        activeRequests[reqId] = rqInfo
        with open(AR_FILE, 'wb') as f:
            pickle.dump(activeRequests, f, pickle.HIGHEST_PROTOCOL)
        GlobalLock.release()
        logger.info("added req '%s' with PID %d" % (reqId, rqInfo.pid))
    except Exception, e:
        logger.exception(e)

###############################################################################
def update_active_request(reqId, toBeDeleted):
    try:
        activeRequests = get_active_requests()
        if reqId not in activeRequests:
            raise Exception("req '%s' not found!" % reqId)
        GlobalLock.acquire()
        rqInfo = activeRequests[reqId]
        rqInfo.toBeDeleted = rqInfo.toBeDeleted + toBeDeleted 
        activeRequests[reqId] = rqInfo
        with open(AR_FILE, 'wb') as f:
            pickle.dump(activeRequests, f, pickle.HIGHEST_PROTOCOL)
        GlobalLock.release()
        logger.info("updated req '%s'" % reqId)
    except Exception, e:
        logger.exception(e)

###############################################################################
def delete_active_request(reqId):
    try:
        activeRequests = get_active_requests()
        if reqId not in activeRequests:
            logger.info("req '%s' not found!" % reqId)
            return
        GlobalLock.acquire()
        del activeRequests[reqId]
        with open(AR_FILE, 'wb') as f:
            pickle.dump(activeRequests, f, pickle.HIGHEST_PROTOCOL)
        GlobalLock.release()
        logger.info("deleted req '%s'" % reqId)
    except Exception, e:
        logger.exception(e)


###############################################################################
def requestProcWrapper(syncEvent,proc,*args):
    # Initialize Django for this process.
    import django
    django.setup()

    logger.info("waiting for the sync event ...")
    syncEvent.wait()
    logger.info("the sync event was signalled!"); 
    proc(*args)

###############################################################################
def spawn_request(reqId, proc, params):
    logger.info('PID: %d, reqId: %s' % (os.getpid(), reqId))

    try:
        # Use this sync event to let us store PID of the spawned process
        # before it proceeds with execution.
        syncEvent = multiprocessing.Event()
        syncEvent.clear()

        # Create a new process with the given parameters.
        p = multiprocessing.Process(target=requestProcWrapper, args=(syncEvent,proc,)+params)

        # This is a background process.
        p.daemon = True

        # Start the process.
        p.start()

        # Save the process ID in the global "Active Request" dictionary.
        add_active_request(reqId, RequestInfo(p.pid))

        # Signal the spawned process to proceed.
        syncEvent.set()

        # Wait for the process to finish.
        p.join()

        # Remove the process from the global dictionary.
        delete_active_request(reqId)
    except Exception, e:
        logger.exception(e)

###############################################################################
def update_request(reqId, toBeDeleted):
    logger.info('PID: %d, reqId: %s' % (os.getpid(), reqId))
    try:
        update_active_request(reqId, toBeDeleted)
    except Exception, e:
        logger.exception(e)

###############################################################################
def cancel_request(reqId):
    try:
        logger.info('PID: %d, reqId: %s' % (os.getpid(), reqId))

        rqInfo = get_active_request(reqId)
        if not rqInfo:
            raise Exception("req '%s' not found!" % reqId)

        logger.info("killing process PID %d" % rqInfo.pid)
        os.kill(rqInfo.pid, signal.SIGTERM)
        time.sleep(1)

        for item in rqInfo.toBeDeleted:
            # Try to delete as a file.
            try:
                if default_storage.exists(item):
                    logger.info("deleting item '%s'" % item)
                    default_storage.delete(item)
                    logger.info("deleted item '%s'" % item)
            except Exception,e:
                pass

            # Try to delete as a directory.
            try:
                if default_storage.exists(item):
                    dirs, files = default_storage.listdir(item)
                    for f in files:
                        file = os.path.join(item, f)
                        logger.info("deleting file '%s'" % file)
                        default_storage.delete(file)
                        logger.info("deleted file '%s'" % file)

                    dir = default_storage.location + "/" + item
                    logger.info("deleting dir '%s'" % dir)
                    if os.path.exists(dir):
                        os.rmdir(dir)

                    if default_storage.exists(item):
                        default_storage.delete(item)
                    logger.info("deleted dir '%s'" % item)
            except Exception,e:
                logger.exception(e)

        delete_active_request(reqId)
    except Exception, e:
        logger.exception(e)
