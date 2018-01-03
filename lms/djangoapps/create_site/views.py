from django.shortcuts import render_to_response
from django.template import RequestContext

from django.contrib.sites.models import Site 
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

from collections import OrderedDict
from jsonfield import JSONField

import route53

def index(request):    
	if request.method == 'POST':
          	name =	request.POST.get("name", "")
		display_name = request.POST.get("display-name", "")
		new_site = Site.objects.create(domain=name +'.cuelms.com',name=display_name)
                conn = route53.connect(
                            aws_access_key_id='AKIAJTLSMH2QGPOY2EKQ',
                            aws_secret_access_key='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',
                                )
                zone = conn.get_hosted_zone_by_id('Z3OCP561F3DA1M')
                new_record, change_info = zone.create_a_record(
                            # Notice that this is a full-qualified name.
                                name= name + '.cuelms.com.',
                                    # A list of IP address entries, in the case fo an A record.
                                        values=['172.104.191.17'],
                                        )


		if new_site.id:
			print new_site.id
			new_site_config = SiteConfiguration.objects.create(site=new_site,enabled=True,values={
			 "PLATFORM_NAME":display_name,
			 "email_from_address":"support@cuelms.com",
			 "payment_support_email":"support@cuelms.com",
			 "SITE_NAME":display_name,
			 "site_domain":name+  ".cuelms.com",
			 "SESSION_COOKIE_DOMAIN": name +".cuelms.com",
			 "course_org_filter":"CueDemo",
			 "FEATURES":{
					           "ENABLE_SPECIAL_EXAMS":True,
						   "ENABLE_MKTG_SITE":True,
						   "ENABLE_OAUTH2_PROVIDER":True,
						   "ALLOW_AUTOMATED_SIGNUPS":True,
						   "ENABLE_THIRD_PARTY_AUTH":True,
						   "ENABLE_COMBINED_LOGIN_REGISTRATION":True
				     },
			 "MKTG_URLS":{
						     "ROOT":"http://cuelms.com",
						         "COURSES":"/courses"
			   	   },
			 "COURSE_CATALOG_VISIBILITY_PERMISSION":"see_in_catalog",
			 "COURSE_ABOUT_VISIBILITY_PERMISSION":"see_about_page",
			 "ENABLE_COMBINED_LOGIN_REGISTRATION":True,
			 "ENABLE_PAID_COURSE_REGISTRATION":True,
			 "ENABLE_SHOPPING_CART":True,
			 "DEFAULT_FROM_EMAIL":"support@cavarsity.com"
							})
                        print new_site_config.id
		context = {
				'name' : name,
				'display_name':display_name

				}
		return render_to_response("create_site/success.html", context)
        c = RequestContext(request, {
		    'foo': 'bar',
		    })
        return render_to_response("create_site/create_site.html", c)
