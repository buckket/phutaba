from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.http import Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.template import RequestContext
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.urlresolvers import reverse
import datetime, os, socket
from phutaba.settings import APP_URL, MEDIA_ROOT, VALID_IMAGE_EXTENSIONS, VALID_IMAGE_MIME, VALID_FILE_EXTENSIONS, VALID_FILE_MIME
from dateutil import relativedelta
from phutaba.cms.models import *
import re
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template.defaultfilters import slugify
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

def static_view(request, template, **args):	
	return render_to_response(template, locals(), context_instance=RequestContext(request))

def dynamic_view(request, page, **args):
	mypage = get_object_or_404(Page, url=page)
	return render_to_response("cms/%s" % mypage.base_template, locals(), context_instance=RequestContext(request))