from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.views.generic import TemplateView, FormView
from django.db.models import Q
from braces.views import LoginRequiredMixin
from accounting.models import Entry, Account
from haystack.views import SearchView
from haystack.query import SearchQuerySet
import re
import logging
import sys

##############################################################################
logger = logging.getLogger(__name__)

##############################################################################
def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example:
        
        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
    
    '''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)] 

##############################################################################
def get_query(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.
    
    '''
    query = None # Query to search for every search term        
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query

###############################################################################
class SimpleSearch(LoginRequiredMixin, TemplateView):
    template_name = 'search_results.html'

    def get_context_data(self, **kwargs):
        context = super(SimpleSearch, self).get_context_data(**kwargs)
        query_string = self.request.GET.get('q')

        if query_string:
            entry_query = get_query(query_string, ['unit_address',])
            found_entries = Account.objects.filter(entry_query)
            context['query_string'] = query_string
            context['found_entries'] = found_entries

        return context

###############################################################################
class SearchResults(LoginRequiredMixin, SearchView):
    def __init__(self, *args, **kwargs):
        super(SearchResults, self).__init__(*args, **kwargs)
        self.load_all = False

    def create_response(self):
        if len(self.results) == 1:
            # Redirect to the object's URL if only one found.
            try:
                obj = self.results[0].object
                response = HttpResponseRedirect(obj.get_absolute_url())
            except Exception, e:
                logger.exception(e)
                response = super(SearchResults, self).create_response()
        else:
            response = super(SearchResults, self).create_response()
        return response