from courseware.courses import get_course_overview_with_access
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
import time
from sys import argv
from base64 import b64encode
from Crypto.Hash import SHA, HMAC
import urllib, urllib2
import socket
import traceback
import datetime
import httplib
import logging
import xml.dom.minidom
from xml.dom.minidom import parse
from hashlib import sha1
import hmac
from collections import OrderedDict
from django.http import HttpResponseRedirect
import shelve
from django.contrib.auth.models import User
from xml.etree.ElementTree import tostring
import xml.etree.ElementTree as etree
import sys

log = logging.getLogger("edx.student")


def CDATA(text=None):
    element = etree.Element('![CDATA[')
    element.text = text
    return element

etree._original_serialize_xml = etree._serialize_xml
def _serialize_xml(write, elem, encoding, qnames, namespaces):
    if elem.tag == '![CDATA[':
        write("<%s%s]]>" % (
                elem.tag, elem.text))
        return
    return etree._original_serialize_xml(
        write, elem,encoding, qnames, namespaces)
etree._serialize_xml = etree._serialize['xml'] = _serialize_xml

def create_signature(secret_key, string):
    """ Create the signed message from api_key and string_to_sign """
    secret_key = secret_key.encode('utf-8')
    string_to_sign = string.encode('utf-8')    
    hashed = hmac.new(secret_key, string, sha1)
    return hashed.digest().encode("base64").rstrip('\n')

def http_call(url, data):   
    timeout = 10    
    req = urllib2.Request(url, data)
    socket.setdefaulttimeout(timeout)
    try:        
        req = urllib2.urlopen(req)       
        dom = parse(req)
        presenter_url = dom.getElementsByTagName('presenter_url')
        class_id = dom.getElementsByTagName('class_id')
        wiziq_meeting_details = {
          'presenter_url' : presenter_url[0].firstChild.nodeValue,
          'class_id' : class_id[0].firstChild.nodeValue
        }            

        return  wiziq_meeting_details#'https://backend.wiziq.com/landing/session/v1/363670?auth_via=wiziq-anon&id=46786&u=5756e0c284166050100a2d2553b29ed9427b60d6c4ce7a1b6caf67db29a6790f9b4c09e84e2e8e58f1cbc2192ac605696348dd48088c497d445125edbd7ccd85a0223cb1dfe6cd7729fb02fe65aaec199799bf8d74b26192f905913e3c5a1efe&flag=true#'
    except urllib2.HTTPError, e:
        log.error(
            u'Big blue api error =`%s`',
            str(e.reason)
        )
    except urllib2.URLError, e:
        log.error(
            u'Big blue api error =`%s`',
            str(e.reason)
        )
    except httplib.HTTPException, e:
        log.error(
            u'Big blue api error =`%s`',
            str(e.reason)
        )
    except Exception:
        import traceback
        log.error(
            u'Big blue api error =`%s`',
            traceback.format_exc()
        )

def get_all_course_learners(course_key):
    enrolled_students = User.objects.filter(
        courseenrollment__course_id=course_key,
        courseenrollment__is_active=1
    )
    attendee_list = etree.Element('attendee_list')
    count = 0
    for student in enrolled_students:
      if count == 3:
        break      
      if not student.is_staff:
       count = count + 1 
       attendee = etree.Element('attendee')  
       attendee_id = etree.Element('attendee_id') 
       screen_name = etree.Element('screen_name')
       locale = etree.Element('language_culture_name')   
       cdata = CDATA(str(student.id))
       cdata2 = CDATA(student.username)
       cdata3 = CDATA('en-us') 
       attendee_id.append(cdata)
       screen_name.append(cdata2)
       locale.append(cdata3)
       attendee.append(attendee_id)
       attendee.append(screen_name)
       attendee.append(locale)
       attendee_list.append(attendee)
    et = etree.ElementTree(attendee_list)   
    et.write("wiziq_students.txt", "utf-8")
    
def join(request,value):
  shelf = shelve.open("wiziq.txt", writeback = True)        
  url = shelf[str(value)]
  return HttpResponseRedirect(url)

@login_required
@ensure_csrf_cookie
def index(request,course_id):
    user = request.user
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_overview_with_access(user, 'load', course_key)
    get_all_course_learners(course_key)
    
    unix_time =  int(time.time())
    now = datetime.datetime.utcnow()
    start_time = now + datetime.timedelta(minutes = 2)
    signature_digest = create_signature(urllib.quote_plus('ZWmElA9AePI/28tK+HypXw=='),'access_key=aOpoCYQh198=&timestamp='+str(unix_time)+'&method=create')
    
    if request.user.is_staff:
        url_create = 'http://classapi.wiziqxt.com/apimanager.ashx?method=create'    
        parameters = OrderedDict([
                      ('access_key', 'aOpoCYQh198='),
                      ('timestamp', str(unix_time)),
                      ('signature', signature_digest),
                      ('title' , course.display_name ),  
                      ('start_time' , start_time.strftime("%Y-%m-%d %H:%M")) ,
                      ('presenter_email' , 'winayakg@gmail.com'),
                      ('duration', '05')                                   
                      ])    
        parameters = urllib.urlencode(parameters)        
        wiziq_meeting_details = http_call(url_create,parameters)
        shelf = shelve.open("wiziq.txt", writeback = True)        
        shelf[course_id.encode('ascii','ignore')] = wiziq_meeting_details
        shelf.sync()

        url_add = 'http://classapi.wiziqxt.com/apimanager.ashx?method=add_attendees' 
        unix_time =  int(time.time())   
        signature_digest = create_signature(urllib.quote_plus('ZWmElA9AePI/28tK+HypXw=='),'access_key=aOpoCYQh198=&timestamp='+str(unix_time)+'&method=add_attendees')
        data = ''
        with open('wiziq_students.txt', 'r') as myfile:
            data=myfile.read().replace('\n', '')

            
        parameters = OrderedDict([
                      ('access_key', 'aOpoCYQh198='),
                      ('timestamp', str(unix_time)),
                      ('signature', signature_digest),
                      ('class_id',  wiziq_meeting_details['class_id']) ,
                      ('attendee_list',  data)# '<attendee_list><attendee><attendee_id><![CDATA[101]]></attendee_id><screen_name><![CDATA[Attendee1]]></screen_name><language_culture_name><![CDATA[en-us]]></language_culture_name></attendee><attendee><attendee_id><![CDATA[102]]></attendee_id><screen_name><![CDATA[Attendee2]]></screen_name><language_culture_name><![CDATA[en-us]]></language_culture_name></attendee></attendee_list>')
                       ])    
        parameters = urllib.urlencode(parameters) 
        req = urllib2.Request(url_add, parameters)
        req = urllib2.urlopen(req)   
        dom = parse(req)
        attendees = dom.getElementsByTagName('attendee')
        for attendee in attendees:
          attendee_id = attendee.getElementsByTagName('attendee_id')
          student_id = attendee_id[0].firstChild.nodeValue
          attendee_url = attendee.getElementsByTagName('attendee_url')
          url = attendee_url[0].firstChild.nodeValue
          shelf[student_id.encode('ascii','ignore')] = url
        shelf.sync()  
        return HttpResponseRedirect(wiziq_meeting_details['presenter_url']) 
    else:
       shelf = shelve.open("wiziq.txt", writeback = True)
       return HttpResponseRedirect(shelf[str(user.id)])
        
       
      
   