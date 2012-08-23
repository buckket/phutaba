#!/usr/bin/env python

from django.core.management import setup_environ
import settings, datetime
setup_environ(settings)

from phutaba.chan.models import *
from phutaba.cms.models import *

def date(pd):
	return datetime.datetime.strptime(pd, "%Y-%m-%dT%H:%M:%SZ")

bc = BoardCategory(name="Random",nsfw=True,order=10)
bc.save()

b = Board(
	identifier = "dev",
	category = bc,
	title = "Entwicklung",
	subtitle = "Pareto-Prinzip: 20% Produktivit&auml;t, 80% Weissbier",
	allow_uploads = True,
	pages = 10,
	force_nick = False,
	default_nick = "Faulfrosch",
	sage_string = "META",
	autosage_string = "SYSTEMKONTRA",
	ban_string = "BANANE KAM REIN",
	mod_string = "GESCH&Auml;FTSF&Uuml;HRER"
)
b.save()

w = Wordfilter(filter="weissbier", value="faulbier")
w.save()
w.boards.add(b)

news = News(
	user = User.objects.get(pk=1),
	time = datetime.datetime.now(),
	title = "Es wird wieder gearbeitet!",
	content = "Huesel Duesel Hurr Durr",
	content_HTML = "<b>Huesel Duesel</b> <u>Hurr Durr</u>",
	published = True
)
news.save()

acl = UserACL(
	user = User.objects.get(pk=1),
	board = b,
	perm_view_post_data = True,
	perm_post_as_mod = True,
	perm_no_captchas = True,
	perm_delete = True,
	perm_sticky = True,
	perm_close = True,
	perm_ban = True,
	perm_evade_ban = True
)
acl.save()

print "Okay."