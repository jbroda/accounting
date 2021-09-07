from haystack import indexes
from .models import Account, Owner, Tenant, Vehicle

##############################################################################
class AccountIndex(indexes.SearchIndex,indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    rendered = indexes.CharField(use_template=True, indexed=False)

    def get_model(self):
        return Account

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        qs = self.get_model().objects.all()
        return qs

##############################################################################
class OwnerIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    rendered = indexes.CharField(use_template=True, indexed=False)

    def get_model(self):
        return Owner

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        qs = self.get_model().objects.all()
        return qs

##############################################################################
class TenantIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    rendered = indexes.CharField(use_template=True, indexed=False)

    def get_model(self):
        return Tenant 

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        qs = self.get_model().objects.all()
        return qs


##############################################################################
class VehicleIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    rendered = indexes.CharField(use_template=True, indexed=False)

    def get_model(self):
        return Vehicle

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        qs = self.get_model().objects.all()
        return qs
