from django.template import Library, Node, TemplateSyntaxError, Variable, resolve_variable
from django.conf import settings
from django.utils.encoding import smart_str, force_unicode
from django.utils.safestring import mark_safe
from phutaba.settings import MEDIA_URL
from phutaba.chan.models import Board
from phutaba.chan.views import check_user_perm
from phutaba.decorators import basictag
register = Library()

@register.inclusion_tag('core/cms/boards.html')
def board_overview():
	boards = Board.objects.all()
	return {'boards': boards}

