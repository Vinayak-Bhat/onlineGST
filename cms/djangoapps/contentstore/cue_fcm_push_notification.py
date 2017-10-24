"""
Helper methods for push notifications from Studio.
"""

from uuid import uuid4
from django.conf import settings
from logging import exception as log_exception

from contentstore.tasks import push_course_update_task
from contentstore.models import PushNotificationConfig
from xmodule.modulestore.django import modulestore
from parse_rest.installation import Push
from parse_rest.connection import register
from parse_rest.core import ParseError

from pyfcm import FCMNotification
 
push_service = FCMNotification(api_key="AAAAh9Kmjm8:APA91bFFB-UxV00isv9C4LslaTDbvzrfeTZ9-A_3M73N76NozLy4dgOebLXMAv8LhHzaIN7CpTE4fEDPXj-VQO4sBVBXJeRyYzgtj_wB3hNkW71yl2GGGkhfXjwrQ7eg_O_mYGOl6qJS")


def push_notification_enabled():
    """
    Returns whether the push notification feature is enabled.
    """
    return True #PushNotificationConfig.is_enabled()


def enqueue_push_course_update(update, course_key):
    """
    Enqueues a task for push notification for the given update for the given course if
      (1) the feature is enabled and
      (2) push_notification is selected for the update
    """
   # if push_notification_enabled() and update.get("push_notification_selected"):
    course = modulestore().get_course(course_key)
    if course:
        push_course_update_task.delay(
            unicode(course_key),
            course.clean_id(padding_char='_'),
            course.display_name,
            update['content']
            )


def send_push_course_update(course_key_string, course_subscription_id, course_display_name,content):
    """
    Sends a push notification for a course update, given the course's subscription_id and display_name.
    """
    #if settings.PARSE_KEYS:
    try:
        registration_id = "<device registration_id>"
        message_title = course_display_name + " - anouncment"
        message_body = "Hello Students, " + content    
        result = push_service.notify_topic_subscribers(course_subscription_id, message_title=message_title, message_body=message_body)
     
    except ParseError as error:
            log_exception(error.message)
