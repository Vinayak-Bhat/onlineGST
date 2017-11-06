from django.conf.urls import url
from . import views
from django.conf import settings

urlpatterns = [
  url(r'^{}$'.format(settings.COURSE_ID_PATTERN), views.index, name='index'),
]

urlpatterns += [
  url(r'^join/(?P<value>\d+)/$', views.join, name='join'),
]