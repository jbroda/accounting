from django.conf import settings
from django.views.generic.edit import FormView
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta
import logging
import jwt
import time
from .forms import SetupForm

##############################################################################
#SELLER_ID = "00867737661238792029"
#SELLER_SECRET = "SKSrGYCd99ASf-Z8KSZoRQ"

# Sandbox
SELLER_ID = "11618333245639580495"
SELLER_SECRET = "SSv7p2yIL4u4j5rH1nkm3A"

# Production
#SELLER_ID = "11618333245639580495"
#SELLER_SECRET = "y5A4hmEpQTOvlCPy2j2ozg"

##############################################################################
logger = logging.getLogger(__name__)

###############################################################################
class SetupView(FormView):
    template_name = 'payment/setup.html'
    form_class = SetupForm
    success_url = '/payment/'

    def form_valid(self, form):
        return super(SetupView, self).form_valid(form)

##############################################################################
def seconds_until_first_of_next_month():
    now = timezone.now()
    first_of_next_month = now + relativedelta(months=1)
    first_of_next_month = first_of_next_month.replace(day=1)
    delta = first_of_next_month - now
    seconds_delta = delta.total_seconds()
    logger.info("seconds: %d" % seconds_delta)
    return seconds_delta

###############################################################################
def generate_jwt(request):
    token = ""
    try:
        amount = float(request.POST.get('amount'))
        scheduling = int(request.POST.get('scheduling'))
        description = request.POST.get('description')
        logger.info("amount: %.2f, scheduling: %d, desc: %s" % (amount, scheduling, description))

        # Add Google fee to the amount:
        # the most favorable of 5% or 1.9% + 30c (USD) per transaction
        new1 = round((amount + 0.30)/(1 - 0.019), 2)
        new2 = round(amount / (1 - 0.05), 2)
        amount = min(new1, new1)

        curr_time = int(time.time())
        exp_time = curr_time + 3600

        if scheduling == 1:
            #
            # One time payment
            #
            request_info = {'currencyCode': 'USD',
                            'sellerData' : 'Custom Data',
                            'name' : 'One Time Payment',
                            'description' : 'Payment to Hidden Pond Condominium Association, Inc.',
                            'price' : '%.2f' % amount}

            jwt_info = {'iss': SELLER_ID,
                        'aud': 'Google',
                        'typ': 'google/payments/inapp/item/v1',
                        'iat': curr_time,
                        'exp': exp_time,
                        'request': request_info}

            # create JWT for one time payment
            token = jwt.encode(jwt_info, SELLER_SECRET)

        elif scheduling == 2:
            #
            # Recurring payment.
            #

            # initial payment data
            initial_payment_info = {'price': '%.2f' % amount,
                                    'currencyCode': 'USD',
                                    'paymentType': 'prorated'}
            
            # subscription recurrence data
            recurrence_info = {'price': '%.2f' % amount,
                               'currencyCode': 'USD',
                               'startTime': curr_time + seconds_until_first_of_next_month(),
                               'frequency': 'monthly'}
                               #'numRecurrences': '24'}
                                    
            # subscription request object info                
            request_info = {'sellerData': 'Custom Data',
                            'name' : 'Recurring Monthly Payment',
                            'description': 'Monthly payment to Hidden Pond Condominium Association, Inc.',
                            #'initialPayment': initial_payment_info,
                            'recurrence': recurrence_info}
            
            # common JWT 
            jwt_info = {'iss': SELLER_ID,
                        'aud': 'Google',
                        'typ': 'google/payments/inapp/subscription/v1',
                        'iat': curr_time,
                        'exp': exp_time,
                        'request': request_info}

            # create JWT for recurring payment
            token = jwt.encode(jwt_info, SELLER_SECRET)

        else:
            raise Exception("Unknown scheduling: %d" % scheduling)
            
    except Exception, e:
        logger.exception(e)

    response = HttpResponse(token,
                            content_type='text/plain')
    return response

###############################################################################
@csrf_exempt
def postback(request):
    orderId = "None"
    try:
        #
        # validate the payment request and respond back to Google.
        #

        encoded_jwt = request.POST.get('jwt')

        if encoded_jwt is None:
            raise Exception('encoded_jwt is None')

        decoded_jwt = jwt.decode(str(encoded_jwt), 
                                 SELLER_SECRET)

        if (decoded_jwt['iss'] != 'Google' or
            decoded_jwt['aud'] != SELLER_ID):
            raise Exception('Invalid iss "{1}" or aud "{2}"'.
                            format(decoded_jwt['iss'], decoded_jwt['aud']))

        if ('response' not in decoded_jwt or
            'orderId' not in decoded_jwt['response']):
            raise Exception('No response or request or orderId: {1}'.
                            string(decoded_jwt))

        order_id = decoded_jwt['response']['orderId']

        if ('request' in decoded_jwt):

            request_info = decoded_jwt['request']

            if ('name' not in request_info or
                'sellerData' not in request_info):
                raise Exception('No name or sellerData in request: {1}'.
                                string(request_info))
                                
            if 'recurrence' in request_info:
                recurrence_info = decoded_jwt['request']['recurrence']

                if ('currencyCode' not in recurrence_info or
                    'price' not in recurrence_info):
                    raise Exception('No currencyCode or price in recurrence: {1}'.
                                    str(recurrence_info))
                orderId = order_id

            elif ('currencyCode' not in request_info or
                  'price' not in request_info):
                raise Exception('No currencyCode or price in request: {1}'. 
                                str(request_info))
            orderId = order_id

        elif ('statusCode' in decoded_jwt['response'] and
              'SUBSCRIPTION_CANCELED' in decoded_jwt['response']['statusCode']):
            orderId = order_id

    except Exception,e:
        logger.exception(e)

    response = HttpResponse(status=200,
                            content=orderId,
                            content_type='text/plain')
    return response
