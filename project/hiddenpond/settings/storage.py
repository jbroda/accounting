########## django-dropbox CONFIGURATION
from django_dropbox.storage import DropboxStorage

StaticRootDropboxStorage = lambda: DropboxStorage(location='/Public/static')
MediaRootDropboxStorage = lambda: DropboxStorage(location='/Accounting/media')
########## END django-dropbox CONFIGURATION

########## s3-storage CONFIGURATION
#from storages.backends.s3boto import S3BotoStorage

#StaticRootS3BotoStorage = lambda: S3BotoStorage(location='static')
#MediaRootS3BotoStorage  = lambda: S3BotoStorage(location='media')
########## END s3-storage CONFIGURATION

