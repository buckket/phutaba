from django.template import Library, Node, TemplateSyntaxError, Variable, resolve_variable
from django.conf import settings
from django.utils.encoding import smart_str, force_unicode
from django.utils.safestring import mark_safe
from phutaba.settings import MEDIA_URL, MEDIA_ROOT
from phutaba.chan.models import Board
from phutaba.chan.views import check_user_perm
import pygeoip
register = Library()

try:
	gi = pygeoip.GeoIP(MEDIA_ROOT+"GeoIPCity.dat")#, GeoIP.GEOIP_STANDARD)
except:
	pass

@register.inclusion_tag('ajax/postinfo_geoip.html')
def geoip_info(post, request):
	try:
		gi
	except:
		try:
			gi = pygeoip.GeoIP(MEDIA_ROOT+"GeoIPCity.dat")
		except:
			return {'fail': True}
	try:
		ginfo = gi.record_by_addr(post.ip)
		if not ginfo:
			raise
	except:
		return {'fail': True}
	for key in ginfo:
		if type(ginfo[key]).__name__ == "str":
			ginfo[key] = ginfo[key].decode('ISO-8859-1') # GEOIP TROLLING WITH ISO SHIT
	return {'ginfo': ginfo, 'post': post, 'MEDIA_URL': MEDIA_URL, 'user': request.user}