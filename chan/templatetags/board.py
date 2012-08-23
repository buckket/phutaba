from django.template import Library, Node, TemplateSyntaxError, Variable, resolve_variable
from django.conf import settings
from django.utils.encoding import smart_str, force_unicode
from django.utils.safestring import mark_safe
from phutaba.settings import MEDIA_URL
from phutaba.chan.models import Board
from phutaba.chan.views import check_user_perm
from phutaba.decorators import basictag
from django.template.defaultfilters import stringfilter
import re
register = Library()

@register.inclusion_tag('board_thread_overview.html')
def thread_overview(thread, request):
	posts = thread.post_set.all()
	omit = 0
	if len(posts) > 4:
		# more than 4 posts, only show the first and last 3.
		omit = len(posts) - 4
		posts = [posts[0], posts[len(posts)-3], posts[len(posts)-2], posts[len(posts)-1]]
	return {'posts': posts, 'thread': thread, 'board': thread.board, 'omit': omit, 'view': 'board', 'MEDIA_URL': MEDIA_URL, 'user': request.user}

@register.inclusion_tag('core/board_nav.html')
def board_overview():
	boards = Board.objects.all()
	return {'boards': boards}

@register.inclusion_tag('board_thread_overview.html')
def thread(thread, request):
	posts = thread.post_set.all().order_by('localpk')
	return {'posts': posts, 'thread': thread, 'board': thread.board, 'omit': 0, 'view': 'thread', 'MEDIA_URL': MEDIA_URL, 'user': request.user}

@register.tag
@basictag(takes_context=True)
def check_perm(context, user, board, perm, retvar):
	if settings.DEBUG:
		print "checkperm called with %s/%s/%s" % (user, board, perm)
	#if context[retvar]:
	#	raise "I won't change existing context variables, fuck off, lazy template dev!"
	context[retvar] = check_user_perm(user, board, perm)
	return "" # else this will echo "None" into our template

@register.filter
@stringfilter
def nopath(string):
	return string.split("/")[-1]
