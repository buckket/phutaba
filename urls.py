from django.conf.urls.defaults import *
from django.contrib import auth
from django.conf import settings
from phutaba.chan.models import BoardCategory
from phutaba.cms.models import News
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('django.contrib.auth.views',
	url(r'^accounts/login/$', 'login', {'template_name': 'core/login.html'}, name="login"),
	url(r'^accounts/logout/$', 'logout', {'template_name': 'core/logout.html'}, name="logout"),
	url(r'^accounts/pwchange/$', 'password_change', {'template_name': 'core/pwchange.html','post_change_redirect': '/accounts/pwchange/done/',}, name="pwchange"),
	url(r'^accounts/pwchange/done/$', 'password_change_done', {'template_name': 'core/pwchange_done.html'}, name="pwchange-done"),
	url(r'^accounts/pwreset/$', 'password_reset', {'template_name': 'core/pwreset.html','post_reset_redirect': '/accounts/pwreset/done/',}, name="pwreset"),
	url(r'^accounts/pwreset/done/$', 'password_reset_done', {'template_name': 'core/pwreset_done.html'}, name="pwreset-done"),
	url(r'^accounts/pwreset/confirm/(?P<token>(.+))/(?P<uidb36>(.+))/$', 'password_reset_confirm', {'template_name': 'core/pwreset_confirm.html'}, name="pwreset-confirm"),
	url(r'^accounts/pwreset/complete/$', 'password_reset_complete', {'template_name': 'core/pwreset_complete.html'}, name="pwreset-complete"),
)

urlpatterns += patterns('phutaba.cms.views',

	url(r'^$', 'static_view', {'template': 'cms/index.html', 'boardcategory_items': BoardCategory.objects.all(), 'news_items': News.objects.filter(published=True)[:5]}, name='start'),

	url(r'^rules/$', 'static_view', {'template': 'rules.html',}, name='rules'),
	url(r'^faq/$', 'static_view', {'template': 'faq.html',}, name='faq'),
	url(r'^irc/$', 'static_view', {'template': 'irc.html',}, name='irc'),

	url(r'^cms/(?P<page>(.*))/$', 'dynamic_view', name='dynamic'),
	
	url(r'^robots.txt$', 'static_view', {'template': 'robots.txt',}, name='robots'),
)

urlpatterns += patterns('phutaba.chan.views',
		
	url(r'^(?P<board>(\w{1,4}))/$', 'board_view', name='board'),
	url(r'^(?P<board>(\w{1,4}))/post/$', 'post_view', name='board-post'),
	url(r'^(?P<board>(\w{1,4}))/(?P<thread_id>(\d+))/$', 'thread_view', name='thread'),
	url(r'^(?P<board>(\w{1,4}))/(?P<thread_id>(\d+))/post/$', 'post_view', name='thread-post'),
#	url(r'^(?P<board>(\w{1,4}))/(?P<thread_id>(\d+))/(?P<file>(\w+\.\w{3,4}))/$', 'thread_file_view', name='thread-file'),
	
	url(r'^_ajax/postinfo/(?P<post_id>(\d+))/$', 'ajax_postinfo_view', name='ajax-postinfo'),
	url(r'^_ajax/postaction/(?P<post_id>(\d+))/$', 'ajax_postaction_view', name='ajax-postaction'),
	
	url(r'^(?P<board>(\w{1,4}))/(?P<thread_id>(\d+))/lock/$', 'thread_lock_view', name='thread-lock'),
	url(r'^(?P<board>(\w{1,4}))/(?P<thread_id>(\d+))/sticky/$', 'thread_sticky_view', name='thread-sticky'),
	url(r'^(?P<board>(\w{1,4}))/(?P<thread_id>(\d+))/autosage/$', 'thread_autosage_view', name='thread-autosage'),
	url(r'^(?P<board>(\w{1,4}))/(?P<thread_id>(\d+))/(?P<post_id>(\d+))/delete/$', 'post_delete_view', name='post-delete'),

)

urlpatterns += patterns('',
	(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': False }),
	(r'^admin/', include(admin.site.urls)),
)