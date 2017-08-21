from edxmako.shortcuts import render_to_string
from shoppingcart.processors.helpers import get_processor_config
from collections import OrderedDict, defaultdict
from shoppingcart.models import Order

from django.shortcuts import render, render_to_response
from django.http import HttpResponse,HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context, Template,RequestContext
import datetime
import hashlib
from random import randint
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.core.context_processors import csrf
import json

import time

def get_purchase_endpoint():
    return get_processor_config().get('PURCHASE_ENDPOINT', '')

def get_signed_purchase_params(cart, **kwargs):
	
    return sign(get_purchase_params(cart))




def sign(params):
    """
    params needs to be an ordered dict, b/c cybersource documentation states that order is important.
    Reverse engineered from PHP version provided by cybersource
    """
    SALT = get_processor_config().get('SECRET', '') # '3sf0jURk'
    hashSequence = "key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5|udf6|udf7|udf8|udf9|udf10"
  
    hash_string=''
    hashVarsSeq=hashSequence.split('|')
    for i in hashVarsSeq:
        try:
            hash_string+=str(params[i])
        except Exception:
            hash_string+=''
        hash_string+='|'
    
    hash_string+=SALT
  
    params['hash'] = hashlib.sha512(hash_string).hexdigest().lower()
 
    params['hash_string'] = hash_string
    params['key'] = get_processor_config().get('KEY', '')
    params['surl'] = get_processor_config().get('SUCCESS_URL', '')
    params['furl'] = get_processor_config().get('FAILURE_URL', '')
    params['phone'] = '9741892299'

    return params



def get_purchase_params(cart):
    productinfo = ''
    for item in cart.orderitem_set.all().select_subclasses("paidcourseregistration"):                   
            productinfo += item.pdf_receipt_display_name 

    total_cost = cart.total_cost
    amount =   "{0:0.2f}".format(total_cost)
    cart_items = cart.orderitem_set.all()    
    key = get_processor_config().get('KEY', '')  
  
    params = OrderedDict()
    params['key'] = key #'C0Dr8m'
    params['txnid'] =     int(time.time() * 1000)      #'12345' 
    params['amount'] = amount # 10
    productinfo = productinfo.replace(" ", "")
    params['productinfo'] = productinfo # 'Shopping'
    params['firstname'] =  cart.user #'Test'
    params['email'] = cart.user.email #'test@test.com' #



    params['udf1'] = "{0:d}".format(cart.id)
    #params['udf2'] = 'abc'
    #params['udf4'] = '15'

    return params


def render_purchase_form_html(cart, **kwargs):
    """
    Renders the HTML of the hidden POST form that must be used to initiate a purchase with CyberSource
    """

    return render_to_string('shoppingcart/cybersource_form.html', {
        'action': get_purchase_endpoint(),
        'params': get_signed_purchase_params(cart),
    })


def process_postpay_callback(params, **kwargs):
    """
    The top level call to this module, basically
    This function is handed the callback request after the customer has entered the CC info and clicked "buy"
    on the external Hosted Order Page.
    It is expected to verify the callback and determine if the payment was successful.
    It returns {'success':bool, 'order':Order, 'error_html':str}
    If successful this function must have the side effect of marking the order purchased and calling the
    purchased_callbacks of the cart items.
    If unsuccessful this function should not have those side effects but should try to figure out why and
    return a helpful-enough error message in error_html.
    """
      
    status=params["status"]
    firstname=params["firstname"]
    amount=params["amount"]
    txnid=params["txnid"]
    posted_hash=params["hash"]
    key=params["key"]
    productinfo=params["productinfo"]
    email=params["email"]
    salt=get_processor_config().get('SECRET', '')
    
    try:
        additionalCharges=params["additionalCharges"]
        retHashSeq=additionalCharges+'|'+salt+'|'+status+'||||||||||' + params['udf1']+ '|'+email+'|'+firstname+'|'+productinfo+'|'+amount+'|'+txnid+'|'+key
    except Exception:
        retHashSeq = salt+'|'+status+'||||||||||'  +  params['udf1']   +'|'+email+'|'+firstname+'|'+productinfo+'|'+amount+'|'+txnid+'|'+key
    hashh=hashlib.sha512(retHashSeq).hexdigest().lower()
    order = Order.objects.get(id=params['udf1'])
    if(hashh !=posted_hash):
        return {'success': False,
                    'order': order,
                    'error_html': 'Transaction failed'}
    else:
        if(status != 'success'):
            return {'success': False,
                    'order': order,
                    'error_html': 'Transaction failed'}

        order.purchase(
        first=params.get('firstname', ''),
        last=params.get('lastName', ''),
        street1=params.get('address1', ''),
        street2=params.get('address2', ''),
        city=params.get('city', ''),
        state=params.get('state', ''),
        country=params.get('country', ''),
        postalcode=params.get('zipcode', ''),
        ccnum='#####',
        cardtype=params.get('mode', ''),
        processor_reply_dump=json.dumps(params)
            )

        return {'success': True,
                    'order': order,
                    'error_html': ''}

    # try:
    #     verify_signatures(params)
    #     result = payment_accepted(params)
    #     if result['accepted']:
    #         # SUCCESS CASE first, rest are some sort of oddity
    #         record_purchase(params, result['order'])
    #         return {'success': True,
    #                 'order': result['order'],
    #                 'error_html': ''}
    #     else:
    #         return {'success': False,
    #                 'order': result['order'],
    #                 'error_html': get_processor_decline_html(params)}
    # except CCProcessorException as error:
    #     return {'success': False,
    #             'order': None,  # due to exception we may not have the order
    #             'error_html': get_processor_exception_html(error)}