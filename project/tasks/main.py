#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Add the library location to the path
import sys
sys.path.insert(0, 'lib')

import os
import webapp2
import logging
import time

from datetime import date, tzinfo, timedelta, datetime

from google.appengine.ext import db
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.appengine import CredentialsProperty
from oauth2client.appengine import StorageByKeyName

from google.appengine.ext.webapp import template
from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler

from webapp2_extras import auth
from webapp2_extras import sessions

from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

import gdata.spreadsheets.client
import gdata.gauth

# Enable info logging by the app (this is separate from appserver's logging).
logging.getLogger().setLevel(logging.INFO)

##############################################################################

TASKS_SS = "0Ak3-IL86c0dqdFpHbm13dlQ5SWNwSnBnVVV3Vm5Bb1E"

##############################################################################

class Credentials(db.Model):
    """Datastore entity for storing OAuth2.0 credentials.

    The CredentialsProperty is provided by the Google API Python Client, and is
    used by the Storage classes to store OAuth 2.0 credentials in the data store."""
    credentials = CredentialsProperty()
      
##############################################################################

class Task():
    id = "id"
    date = "date"    
    creator = "creator"
    description = "desc"
    priority = "none"
    status = "open"
    completed_date = "none"
    hours_spent = "none"
    completed_by = "none"
    comments = "none"

##############################################################################
def user_required(handler):
    """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
    """
    def check_login(self, *args, **kwargs):
        auth = self.auth
        if not auth.get_user_by_session():
            self.redirect(self.uri_for('login'), abort=True)
        else:
            return handler(self, *args, **kwargs)

    return check_login
  
##############################################################################  
class BaseHandler(webapp2.RequestHandler):
    @webapp2.cached_property
    def auth(self):
        """Shortcut to access the auth instance as a property."""
        return auth.get_auth()

    @webapp2.cached_property
    def user_info(self):
        """Shortcut to access a subset of the user attributes that are stored
        in the session.

        The list of attributes to store in the session is specified in
          config['webapp2_extras.auth']['user_attributes'].
        :returns
          A dictionary with most user information
        """
        return self.auth.get_user_by_session()

    @webapp2.cached_property
    def user(self):
        """Shortcut to access the current logged in user.

        Unlike user_info, it fetches information from the persistence layer and
        returns an instance of the underlying model.

        :returns
          The instance of the user model associated to the logged in user.
        """
        u = self.user_info
        return self.user_model.get_by_id(u['user_id']) if u else None

    @webapp2.cached_property
    def user_model(self):
        """Returns the implementation of the user model.

        It is consistent with config['webapp2_extras.auth']['user_model'], if set.
        """    
        return self.auth.store.user_model

    @webapp2.cached_property
    def session(self):
        """Shortcut to access the current session."""
        return self.session_store.get_session(backend="datastore")

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}
        user = self.user_info
        params['user'] = user
        path = os.path.join(os.path.dirname(__file__), 'views', view_filename)
        self.response.out.write(template.render(path, params))

    def display_message(self, message):
        """Utility function to display a template with a simple message."""
        params = {
            'message': message
        }
        self.render_template('message.html', params)

    # this is needed for webapp2 sessions to work
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

##############################################################################
class MainHandler(BaseHandler):
    @user_required
    def get(self):
        self.render_template('home.html')
    
##############################################################################    
class SignupHandler(BaseHandler):
    @user_required
    def get(self):
        self.render_template('signup.html')

    def post(self):
        user_name = self.request.get('username')
        email = self.request.get('email')
        name = self.request.get('name')
        password = self.request.get('password')
        last_name = self.request.get('lastname')

        unique_properties = ['email_address']
        user_data = self.user_model.create_user(user_name,
                                                unique_properties,
                                                email_address=email, 
                                                name=name, 
                                                password_raw=password,
                                                last_name=last_name, 
                                                verified=False)
        if not user_data[0]: #user_data is a tuple
            self.display_message('Unable to create user for email %s because of \
                duplicate keys %s' % (user_name, user_data[1]))
            return
    
        user = user_data[1]
        user_id = user.get_id()

        token = self.user_model.create_signup_token(user_id)

        verification_url = self.uri_for('verification', type='v', user_id=user_id,
                                        signup_token=token, _full=True)

        msg = 'Send an email to user in order to verify their address. \
               They will be able to do so by visiting <a href="{url}">{url}</a>'

        self.display_message(msg.format(url=verification_url))        
  
##############################################################################      
class VerificationHandler(BaseHandler):
    def get(self, *args, **kwargs):
        user = None
        user_id = kwargs['user_id']
        signup_token = kwargs['signup_token']
        verification_type = kwargs['type']

        # it should be something more concise like
        # self.auth.get_user_by_token(user_id, signup_token)
        # unfortunately the auth interface does not (yet) allow to manipulate
        # signup tokens concisely
        user, ts = self.user_model.get_by_auth_token(int(user_id), signup_token,
                                                     'signup')

        if not user:
            logging.info('Could not find any user with id "%s" signup token "%s"',
                         user_id, signup_token)
            self.abort(404)
    
        # store user data in the session
        self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

        if verification_type == 'v':
            # remove signup token, we don't want users to come back with an old link
            self.user_model.delete_signup_token(user.get_id(), signup_token)
    
            if not user.verified:
                user.verified = True
                user.put()
    
            self.display_message('User email address has been verified.')
            return
        elif verification_type == 'p':
            # supply user to the page
            params = {
              'user': user,
              'token': signup_token
            }
            self.render_template('resetpassword.html', params)
        else:
            logging.info('verification type not supported')
            self.abort(404)      
            
##############################################################################            
class SetPasswordHandler(BaseHandler):
  @user_required
  def get(self):
        user = self.auth.get_user_by_session();
        token = user['token']

        # supply user to the page
        params = {
          'user': user,
          'token': token
        }
        self.render_template('resetpassword.html', params)

  def post(self):
    password = self.request.get('password')
    old_token = self.request.get('t')

    if not password or password != self.request.get('confirm_password'):
      self.display_message('passwords do not match')
      return

    user = self.user
    user.set_password(password)
    user.put()

    # remove signup token, we don't want users to come back with an old link
    self.user_model.delete_signup_token(user.get_id(), old_token)
    
    self.display_message('Password updated')

##############################################################################
class LoginHandler(BaseHandler):
  def get(self):
    self._serve_page()

  def post(self):
    username = self.request.get('username')
    password = self.request.get('password')
    try:
      u = self.auth.get_user_by_password(username, password, remember=True,
        save_session=True)
      self.redirect(self.uri_for('home'))
    except (InvalidAuthIdError, InvalidPasswordError) as e:
      logging.info('Login failed for user %s because of %s', username, type(e))
      self._serve_page(True)

  def _serve_page(self, failed=False):
    username = self.request.get('username')
    params = {
      'username': username,
      'failed': failed
    }
    self.render_template('login.html', params)

##############################################################################
class LogoutHandler(BaseHandler):
    def get(self):
        self.auth.unset_session()
        self.redirect(self.uri_for('home'))        
    
##############################################################################        
class ForgotPasswordHandler(BaseHandler):
    def get(self):
        self._serve_page()

    def post(self):
        username = self.request.get('username')

        user = self.user_model.get_by_auth_id(username)
        if not user:
            logging.info('Could not find any user entry for username %s', username)
            self._serve_page(not_found=True)
            return

        user_id = user.get_id()
        token = self.user_model.create_signup_token(user_id)

        verification_url = self.uri_for('verification', type='p', user_id=user_id,
                                        signup_token=token, _full=True)
        
        email = user._values['email_address'].b_val

        mail.send_mail(sender="Hidden Pond Tasks <tasks@XXXXXXXXX.XX>",
                       to=email,
                       subject="Reset password link",
                       body="Reset password by clicking " + verification_url);
                       
        #msg = 'Send an email to user in order to reset their password. \
        #       They will be able to do so by visiting <a href="{url}">{url}</a>'
        #
        #self.display_message(msg.format(url=verification_url))
        
        msg = 'Password reset link sent to ' + email;
        self.display_message(msg);
  
    def _serve_page(self, not_found=False):
        username = self.request.get('username')
        params = {
                  'username': username,
                  'not_found': not_found
                  }
        self.render_template('forgot.html', params)
  
##############################################################################
class AuthenticatedHandler(BaseHandler):
    @user_required
    def get(self):
        self.render_template('authenticated.html')
    
##############################################################################       
    
SCOPES = [ 'https://docs.google.com/feeds',  
          'https://spreadsheets.google.com/feeds']

##############################################################################
class DeleteCreds(BaseHandler):   
    @user_required      
    def get(self):
        StorageByKeyName(Credentials, 'creds', 'credentials').delete()
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Deleted credentials!')
        
##############################################################################
def GetWorksheetFeed(self, spr_client, spr_key):
    # Get stored credentials  
    creds = StorageByKeyName(Credentials, 'creds', 'credentials').get()
            
    if not creds:              
        flow = flow_from_clientsecrets('client_secrets.json', scope='')
        flow.scope = ' '.join(SCOPES)
        #flow.redirect_uri = self.request.url.split('?', 1)[0].rsplit('/', 1)[0]
        flow.redirect_uri = self.request.url.split('?', 1)[0];
    
        code = self.request.get('code')
        if not code:
            logging.info("Starting the OAuth 2.0 flow!") 
            auth_url = flow.step1_get_authorize_url()        
            self.redirect(str(auth_url))   
            return
        else:              
            try:
                #h = httplib2.Http(proxy_info = httplib2.ProxyInfo(httplib2.socks.PROXY_TYPE_HTTP,'Localhost',8118))
                creds = flow.step2_exchange(code)               
            except (FlowExchangeError, Exception), e:
                logging.exception(e)
                
                mail.send_mail(sender="tasks@XXXXXXXXX.XX",
                               to="tasks@XXXXXXXXX.XX",
                               subject="ERROR 2!",
                               body="Exception: " + str(e));
                       
                self.response.headers['Content-Type'] = 'text/plain'
                self.response.out.write('ERROR 2: contact administrator at tasks@XXXXXXXXX.XX!')
                return
                              
            # Store the credentials          
            StorageByKeyName(Credentials, 'creds', 'credentials').put(creds)   
    else:
        logging.info("Got stored credentials!")                      
                        
    # Get the OAuth2 token from the credentials.
    token = gdata.gauth.OAuth2TokenFromCredentials(creds)
    
    # Connect to the Spreadsheet Service.          
    #spr_client = gdata.spreadsheets.client.SpreadsheetsClient()
    token.authorize(spr_client)
    
    #spr_key = TASKS_SS 
    try:                        
        worksheet_feed = spr_client.get_worksheets(spr_key)
    except Exception, e:     
        logging.exception(e)

        mail.send_mail(sender="tasks@XXXXXXXXX.XX",
                       to="tasks@XXXXXXXXX.XX",
                       subject="ERROR 1!",
                       body="Exception: " + str(e));

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('ERROR 1: contact administrator at tasks@XXXXXXXXX.XX!')
        return

    return worksheet_feed

##############################################################################
# A complete implementation of current DST rules for major US time zones.

def first_sunday_on_or_after(dt):
    days_to_go = 6 - dt.weekday()
    if days_to_go:
        dt += timedelta(days_to_go)
    return dt

# US DST Rules
#
# This is a simplified (i.e., wrong for a few cases) set of rules for US
# DST start and end times. For a complete and up-to-date set of DST rules
# and timezone definitions, visit the Olson Database (or try pytz):
# http://www.twinsun.com/tz/tz-link.htm
# http://sourceforge.net/projects/pytz/ (might not be up-to-date)
#
# In the US, since 2007, DST starts at 2am (standard time) on the second
# Sunday in March, which is the first Sunday on or after Mar 8.
DSTSTART_2007 = datetime(1, 3, 8, 2)
# and ends at 2am (DST time; 1am standard time) on the first Sunday of Nov.
DSTEND_2007 = datetime(1, 11, 1, 1)
# From 1987 to 2006, DST used to start at 2am (standard time) on the first
# Sunday in April and to end at 2am (DST time; 1am standard time) on the last
# Sunday of October, which is the first Sunday on or after Oct 25.
DSTSTART_1987_2006 = datetime(1, 4, 1, 2)
DSTEND_1987_2006 = datetime(1, 10, 25, 1)
# From 1967 to 1986, DST used to start at 2am (standard time) on the last
# Sunday in April (the one on or after April 24) and to end at 2am (DST time;
# 1am standard time) on the last Sunday of October, which is the first Sunday
# on or after Oct 25.
DSTSTART_1967_1986 = datetime(1, 4, 24, 2)
DSTEND_1967_1986 = DSTEND_1987_2006
ZERO = timedelta(0)
HOUR = timedelta(hours=1)

class USTimeZone(tzinfo):
    def __init__(self, hours, reprname, stdname, dstname):
        self.stdoffset = timedelta(hours=hours)
        self.reprname = reprname
        self.stdname = stdname
        self.dstname = dstname

    def __repr__(self):
        return self.reprname

    def tzname(self, dt):
        if self.dst(dt):
            return self.dstname
        else:
            return self.stdname

    def utcoffset(self, dt):
        return self.stdoffset + self.dst(dt)

    def dst(self, dt):
        if dt is None or dt.tzinfo is None:
            # An exception may be sensible here, in one or both cases.
            # It depends on how you want to treat them.  The default
            # fromutc() implementation (called by the default astimezone()
            # implementation) passes a datetime with dt.tzinfo is self.
            return ZERO
        assert dt.tzinfo is self

        # Find start and end times for US DST. For years before 1967, return
        # ZERO for no DST.
        if 2006 < dt.year:
            dststart, dstend = DSTSTART_2007, DSTEND_2007
        elif 1986 < dt.year < 2007:
            dststart, dstend = DSTSTART_1987_2006, DSTEND_1987_2006
        elif 1966 < dt.year < 1987:
            dststart, dstend = DSTSTART_1967_1986, DSTEND_1967_1986
        else:
            return ZERO

        start = first_sunday_on_or_after(dststart.replace(year=dt.year))
        end = first_sunday_on_or_after(dstend.replace(year=dt.year))

        # Can't compare naive to aware objects, so strip the timezone from
        # dt first.
        if start <= dt.replace(tzinfo=None) < end:
            return HOUR
        else:
            return ZERO

Eastern  = USTimeZone(-5, "Eastern",  "EST", "EDT")
Central  = USTimeZone(-6, "Central",  "CST", "CDT")
Mountain = USTimeZone(-7, "Mountain", "MST", "MDT")
Pacific  = USTimeZone(-8, "Pacific",  "PST", "PDT")    
                
##############################################################################             
class NextTaskId(ndb.Model):
    nextTaxId = ndb.IntegerProperty()
    
def ndb_key(ndb_name='default_db'):
    return ndb.Key('NextTaskId', ndb_name)

##############################################################################             
class CreateTask(BaseHandler):      
    @user_required   
    def get(self):     
        # Get the stored credentials
        creds = StorageByKeyName(Credentials, 'creds', 'credentials').get()
        if not creds:
            # Start the Oauth 2.0 flow.
            flow = flow_from_clientsecrets('client_secrets.json', scope='')
            flow.scope = ' '.join(SCOPES)
            flow.redirect_uri = self.request.url.split('?', 1)[0];
    
            code = self.request.get('code')
            if not code:
                logging.info("CreateTask - starting the OAuth 2.0 flow!") 
                auth_url = flow.step1_get_authorize_url()        
                self.redirect(str(auth_url))   
                return
            else:
                try:
                    creds = flow.step2_exchange(code)               
                except (FlowExchangeError, Exception), e:
                    logging.exception(e)

                    mail.send_mail(sender="tasks@XXXXXXXXX.XX",
                                   to="tasks@XXXXXXXXX.XX",
                                   subject="ERROR 3!",
                                   body="Exception: " + str(e));
                       
                    self.response.headers['Content-Type'] = 'text/plain'
                    self.response.out.write('ERROR 3: contact administrator at tasks@XXXXXXXXX.XX!')
                    return

                # Store the credentials          
                StorageByKeyName(Credentials, 'creds', 'credentials').put(creds)   
            
        self.render_template('CreateTask.html')           
        
    def post(self):
        username = self.user_info['name'], 
        priority = self.request.get('priority')
        description = self.request.get('description')  
        reply_email = self.user_info['email_address']
        
        added,taskId = AddNewTask(username[0], description, priority, reply_email)

        self.response.headers['Content-Type'] = 'text/html'
        if added == True:                                        
            self.response.out.write("<h2 style='color:green'>Task #" + str(taskId) + " created!</h2>")
        else:
            self.response.out.write("<h3 style='color:red'>Task NOT created!</h2>")
            
##############################################################################
def GetTasksView(self, task_status, start_date=None, end_date=None):          
    # Open the tasks worksheet      
    spr_client = gdata.spreadsheets.client.SpreadsheetsClient()  
    #spr_client = gdata.spreadsheet.service.SpreadsheetsService()
    spr_key = TASKS_SS 
    worksheet_feed = GetWorksheetFeed(self, spr_client, spr_key)
    if not worksheet_feed:
        return;
    
    query = gdata.spreadsheets.client.ListQuery()
    query.order_by = 'position'
    query.reverse = 'false'
    query.sq = 'status == ' + task_status
    
    if start_date and end_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d")
            ed = datetime.strptime(end_date, "%Y-%m-%d")
            ed = ed.replace(hour=23, minute=59, second=59) # till the end of end day

            start_date = str(sd)
            end_date = str(ed)

            logging.info("start date: " + start_date + ", end date: " + end_date)
            query.sq = 'status == ' + task_status + ' && completedon >= ' + start_date + ' && completedon <= ' + end_date

        except Exception, e:     
            logging.exception(e)
    
    worksheet_id = worksheet_feed.entry[0].id.text.rsplit('/',1)[1]                        
    rows = spr_client.GetListFeed(spr_key, worksheet_id,q=query).entry

    #feed = gd_client.GetListFeed(key=spr_key, wksht_id=worksheet_id, query=q)
    
    tasks = list()   
    for row in rows:     
        dictr = row.to_dict()       
        task = Task()                 
        task.id = dictr['id']
        task.date = dictr['timestamp']
        task.creator = dictr['username']
        task.description = dictr['description']
        task.priority = dictr['priority']
        task.status = dictr['status']
        task.completed_date = dictr['completedon']
        task.hours_spent = dictr['hoursspent']
        task.completed_by = dictr['completedby']    
        task.comments = ("", dictr['comments'])[dictr['comments'] != None]
        tasks.append(task)
            
    params = {
        'task_status' : task_status,
        'tasks' : tasks,
        'start_date' : start_date,
        'end_date' : end_date
    
    } 
    self.render_template('tasks.html', params)     
             
##############################################################################             
class OpenTasksView(BaseHandler):      
    @user_required   
    def get(self):       
        GetTasksView(self, "open")   
        
##############################################################################             
class EditDescription(BaseHandler):
    @user_required
    def post(self):
        taskId          = int(self.request.get('taskId'))
        taskDescription = str(self.request.get('taskDescription'))

        # Open the tasks work sheet      
        spr_client = gdata.spreadsheets.client.SpreadsheetsClient()  
        spr_key = TASKS_SS 
        worksheet_feed = GetWorksheetFeed(self, spr_client, spr_key)
        if not worksheet_feed:
            self.response.out.write("Failed to edit task #" + taskId)
            return

        query = gdata.spreadsheets.client.ListQuery()
        query.order_by = 'position'
        query.reverse = 'false'
        query.sq = 'id == ' + str(taskId)

        worksheet_id = worksheet_feed.entry[0].id.text.rsplit('/',1)[1]                        
        rows = spr_client.GetListFeed(spr_key, worksheet_id, q=query).entry

        updated = False 

        try:
            row = rows[0]
            dictr = row.to_dict()    
            dictr['description'] = taskDescription
            row.from_dict(dictr)
            spr_client.update(row)
            updated = True 
        except Exception, e:
            updated = False
            logging.exception(e)

        self.response.headers['Content-Type'] = 'text/plain'
        if updated:
            self.response.out.write(taskDescription)
        else:
            self.response.out.write("Failed to edit task #" + taskId)
    
##############################################################################             
class EditPriority(BaseHandler):
    @user_required
    def post(self):
        taskId       = int(self.request.get('taskId'))
        taskPriority = str(self.request.get('taskPriority'))

        # Open the tasks work sheet      
        spr_client = gdata.spreadsheets.client.SpreadsheetsClient()  
        spr_key = TASKS_SS 
        worksheet_feed = GetWorksheetFeed(self, spr_client, spr_key)
        if not worksheet_feed:
            self.response.out.write("Failed to edit task #" + taskId)
            return

        query = gdata.spreadsheets.client.ListQuery()
        query.order_by = 'position'
        query.reverse = 'false'
        query.sq = 'id == ' + str(taskId)

        worksheet_id = worksheet_feed.entry[0].id.text.rsplit('/',1)[1]                        
        rows = spr_client.GetListFeed(spr_key, worksheet_id, q=query).entry

        updated = False 

        try:
            row = rows[0]
            dictr = row.to_dict()    
            dictr['priority'] = taskPriority 
            row.from_dict(dictr)
            spr_client.update(row)
            updated = True 
        except Exception, e:
            updated = False
            logging.exception(e)

        self.response.headers['Content-Type'] = 'text/plain'
        if updated:
            self.response.out.write(taskPriority)
        else:
            self.response.out.write("Failed to edit task #" + taskId)

##############################################################################             
class MarkComplete(BaseHandler):
    @user_required
    def post(self):
        taskId       = int(self.request.get('taskId'))
        taskHours    = str(self.request.get('taskHours'))
        taskComments = str(self.request.get('taskComments'))
        
        # Open the tasks worksheet      
        spr_client = gdata.spreadsheets.client.SpreadsheetsClient()  
        spr_key = TASKS_SS 
        worksheet_feed = GetWorksheetFeed(self, spr_client, spr_key)
        if not worksheet_feed:
            return
        
        query = gdata.spreadsheets.client.ListQuery()
        query.order_by = 'position'
        query.reverse = 'false'
        query.sq = 'id == ' + str(taskId)
        
        worksheet_id = worksheet_feed.entry[0].id.text.rsplit('/',1)[1]
        rows = spr_client.GetListFeed(spr_key, worksheet_id, q=query).entry                 
        
        marked = False

        try:
            ts = time.time()
            st = datetime.fromtimestamp(ts, Central).strftime('%Y/%m/%d %H:%M:%S')  
            row = rows[0]
            dictr = row.to_dict()    
            dictr['status'] = 'completed'
            dictr['hoursspent'] = taskHours
            dictr['completedby'] = self.user_info['name']
            dictr['completedon'] = st
            dictr['comments'] = taskComments
            row.from_dict(dictr)
            spr_client.update(row)
            marked = True
        except Exception, e:     
            marked = False
            logging.exception(e)

        #ts = time.time()
        #st = datetime.fromtimestamp(ts, Central).strftime('%Y/%m/%d %H:%M:%S')  
        
        #row = gdata.spreadsheets.data.ListEntry()
        #row.from_dict({'timestamp': st, 
        #               'username': self.user_info['name'], 
        #               'description': description,
        #               'priority' : priority,
        #               'status' : 'open'})
        #added = spr_client.add_list_entry(row, spr_key, worksheet_id)
        
        self.response.headers['Content-Type'] = 'text/html'
        if marked:                                        
            self.response.out.write("<h3 style='color:green'>Task #" + str(taskId) + " marked complete (" + taskHours + " hours)!</h2>")
        else:
            self.response.out.write("<h3 style='color:red'>Task #" + str(taskId) + " NOT marked complete!</h2>")

##############################################################################             
class CompletedTasksView(BaseHandler):      
    @user_required   
    def get(self):     
        start_date = self.request.get('start_date')
        end_date = self.request.get('end_date')
        if not start_date and not end_date:
            end_date = date.today() 
            start_date = date.today() - timedelta(days=60)
        GetTasksView(self, "completed", str(start_date), str(end_date)) 
        
    def post(self):
        start_date = self.request.get('start_date')
        end_date = self.request.get('end_date')
        GetTasksView(self, "completed", start_date, end_date)

##############################################################################
def AddNewTask(username, description, priority, reply_email):
    added = False
    taskId = 0

    # Get stored credentials  
    creds = StorageByKeyName(Credentials, 'creds', 'credentials').get()
    if not creds:
        logging.error("AddNewTask - did not get the stored credentials!")
        return added,taskId
    else: 
        logging.info("AddNewTask - got the stored credentials!")

    # Get the OAuth2 token from the credentials.
    token = gdata.gauth.OAuth2TokenFromCredentials(creds)

    try:                        
        # Connect to the Spreadsheet Service.          
        spr_client = gdata.spreadsheets.client.SpreadsheetsClient()  
        token.authorize(spr_client)
        spr_key = TASKS_SS 
        worksheet_feed = spr_client.get_worksheets(spr_key)
    except Exception, e:     
        logging.exception(e)
        return added,taskId

    if not worksheet_feed:
        logging.error("AddNewTask - did not get the work sheet feed!")
        return added,taskId
    
    worksheet_id = worksheet_feed.entry[0].id.text.rsplit('/',1)[1]                        
    
    tq = NextTaskId.query(ancestor=ndb_key())
    taskIdObj = tq.fetch(1)
    if not taskIdObj:
        rows = spr_client.GetListFeed(spr_key, worksheet_id)
        taskId = len(rows.entry) + 1
        taskIdObj = NextTaskId(parent=ndb_key())
        taskIdObj.nextTaxId = taskId + 1
        taskIdObj.put()
    else:
        taskId = taskIdObj[0].nextTaxId
        taskIdObj[0].nextTaxId = taskId + 1
        taskIdObj[0].put()
            
    ts = time.time()
    st = datetime.fromtimestamp(ts, Central).strftime('%Y/%m/%d %H:%M:%S')  
    
    row = gdata.spreadsheets.data.ListEntry()
    row.from_dict({'id' : str(taskId),
                   'timestamp': st, 
                   'username': username,
                   'description': description,
                   'priority' : priority,
                   'status' : 'open'})
    new_task = spr_client.add_list_entry(row, spr_key, worksheet_id)
       
    # Notify about the new task by e-mail
    if new_task:                                        
        added = True
        try:
            new_task_msg = "Task ID: " + str(taskId) + "\nPriority: " + priority + "\nDescription: " + description
            mail.send_mail(sender="Hidden Pond Tasks <tasks@XXXXXXXXX.XX>",
                           to="mihamih@yahoo.com",
                           reply_to=reply_email,
                           subject="New task #" + str(taskId) + " received!",
                           body=new_task_msg);
        except Exception, e:     
            logging.exception(e)
    else:
        logging.error("AddNewTask - did not create a new task!")
        
    return added,taskId

##############################################################################
class LogSenderHandler(InboundMailHandler):
    def receive(self, msg):
        logging.info("Received a message from: " + msg.sender)
        logging.info(" - subject: " + msg.subject)
        
        plaintext_bodies = msg.bodies(content_type='text/plain')
        allBodies = ""; numBodies = 0
        for body in plaintext_bodies:
            allBodies = allBodies + body[1].decode()
            numBodies += 1 
            if isinstance(allBodies, unicode):
                allBodies = allBodies.encode('utf-8')

        logging.info(" - msg: " + allBodies)
                
        if numBodies > 1: logging.warn("recvd mail with %s bodies: %s" % (numBodies, msg))

        html_bodies = msg.bodies('text/html')
        for content_type, body in html_bodies:
            decoded_html = body.decode()
            logging.info("- content_type: " + content_type)
            logging.info("- decoded_html: " + decoded_html)
            
        AddNewTask("website", decoded_html, "2: 24 hours", "hidden.pond.condos@gmail.com")
        
##############################################################################
config = {
  'webapp2_extras.auth': {
    'user_model': 'models.User',
    'user_attributes': ['name','email_address']
  },
  'webapp2_extras.sessions': {
    'secret_key': '12345'
  }
}

##############################################################################
app = webapp2.WSGIApplication([webapp2.Route('/', MainHandler, name='home'),
                               webapp2.Route('/signup', SignupHandler),                                
                               webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
                                             handler=VerificationHandler, name='verification'),                               
                               webapp2.Route('/password', SetPasswordHandler),
                               webapp2.Route('/login', LoginHandler, name='login'),
                               webapp2.Route('/logout', LogoutHandler, name='logout'),
                               webapp2.Route('/forgot', ForgotPasswordHandler, name='forgot'),
                               webapp2.Route('/authenticated', AuthenticatedHandler, name='authenticated'),
                               webapp2.Route('/create_task', CreateTask),  
                               webapp2.Route('/view_open_tasks', OpenTasksView,name="open_tasks"),
                               webapp2.Route('/edit_desc', EditDescription),
                               webapp2.Route('/edit_prio', EditPriority),
                               webapp2.Route('/mark_complete', MarkComplete),
                               webapp2.Route('/view_completed_tasks', CompletedTasksView),
                               webapp2.Route('/del_creds', DeleteCreds),
                               LogSenderHandler.mapping()],
                              debug=True,
                              config=config)
