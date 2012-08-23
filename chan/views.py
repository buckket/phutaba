import datetime
import socket
import re
from PIL import Image
import cStringIO as StringIO

from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.template import RequestContext
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template.defaultfilters import slugify
import markdown2

from phutaba.settings import APP_URL, MEDIA_ROOT, VALID_IMAGE_EXTENSIONS, VALID_IMAGE_MIME, VALID_FILE_EXTENSIONS, VALID_FILE_MIME
from phutaba.chan.models import *

def static_view(request, template, **args):
        return render_to_response(template, locals(), context_instance=RequestContext(request))

def board_view(request, board):
        board = get_object_or_404(Board, identifier=board)
        try:
                thread_list = Thread.objects.filter(board=board)
        except:
                thread_list = []
        paginator = Paginator(thread_list, 10)
        try:
                page = int(request.GET.get("page",1))
        except ValueError:
                page = 1
        try:
                threads = paginator.page(page)
        except (EmptyPage, InvalidPage):
                threads = paginator.page(paginator.num_pages)
        return render_to_response("board.html", locals(), context_instance=RequestContext(request))

def post_view(request, board, thread_id=False):
        request.FILES
        board = get_object_or_404(Board, identifier=board)
        if thread_id:
                thread = get_object_or_404(Thread, pk=thread_id)
                if thread.is_locked and not check_user_perm(request.user, board, "close"):
                        messages.error(request, "Dieser Faden ist dicht.")
                        return HttpResponseRedirect(reverse("thread", args=[board.identifier, thread.pk]))
        else:
                thread = False
        if not request.POST.get("field_comment", False):
                messages.error(request, "Bitte Inhalt pfostieren.")
                return board_view(request, board.identifier)
        fail = False
        if not thread:
                if not request.FILES.get('field_file', False):
                        messages.error(request, "Datei fehlt, du H&auml;sslon.")
                        fail = True
        if request.FILES.get('field_file', False):
                if not fail and request.FILES['field_file'].size > 1024*1024*10:
                        messages.error(request, "10MB, kennste?")
                        fail = True
                if request.FILES['field_file'].name[-4:].lower() in VALID_IMAGE_EXTENSIONS and request.FILES['field_file'].content_type.lower() in VALID_IMAGE_MIME:
                        filetype = "image"
                else: # TODO else if mit normalen dateiformaten
                        User.objects.get(pk=1).email_user("image file upload debug info","name is %s, file type is %s" %(request.FILES['field_file'].name, request.FILES['field_file'].content_type))
                        messages.error(request, "Ge wek mit deinen Mondformaten")
                        fail = True
                if not fail and filetype == "image":
                        try:
                                f = request.FILES['field_file']
                                f.open()
                                imgcontent = f.read()
                                f.close()
                                strimg = Image.open(StringIO.StringIO(imgcontent))
                                src_width, src_height = strimg.size
                                # hier starben 15 zeilen code fuer ein .thumbnail()
                                strimg.thumbnail((300, 200), Image.ANTIALIAS)
                                tmp = StringIO.StringIO()
                                if request.FILES['field_file'].content_type.lower() in ["image/jpeg"]:
                                        strimg.save(tmp, 'JPEG')
                                        imgthumbtype = "jpg"
                                        imgext = "jpg"
                                else:
                                        strimg.save(tmp, 'PNG')
                                        imgthumbtype = "png"
                                        realimgext = re.compile('.*\.(\w+)$')
                                        if realimgext.match(request.FILES['field_file'].name):
                                                imgextt = realimgext.match(request.FILES['field_file'].name)
                                                imgext = imgextt.group(1)
                                        else:
                                                fail = True
                                strimg.seek(0)
                                imgthumbnail = tmp.getvalue()
                                tmp.close()
                                f = PostFile(filetype="image", fileid=9000, imagedimensions="%ix%i" % (src_width, src_height))
                        except:
                                raise
                                messages.error(request, "Bild kapoat")
                                fail = True
        else:
                f = False
        if fail == True:
                print "FAIL"
                try:
                        f.delete()
                except:
                        pass
                return HttpResponseRedirect(reverse("board", args=[board.identifier]))
        try:
                if not thread:
                        t = Thread(board=board, time_created=datetime.datetime.now(), cached_last_post=datetime.datetime.now())
                        t.save()
                else:
                        t = thread
                p = Post(thread=t, localpk=get_free_pk(board), time=datetime.datetime.now(), 
                         title=request.POST.get("field_subject", ''), ip=request.META['REMOTE_ADDR'],
                         host=socket.gethostbyaddr(request.META['REMOTE_ADDR'])[0],
                         useragent=request.META['HTTP_USER_AGENT'], content=request.POST.get("field_comment", ''),
                         content_HTML=markdown2.markdown(request.POST.get("field_comment", '')),
                         password=request.POST.get("field_password", ''))
                if not thread:
                        p.flag_op = True
                if not board.force_nick and request.POST.get("field_nick", False):
                        p.nick = request.POST.get("field_nick", None)
                if request.POST.get("field_sage", False):
                        p.flag_sage = True
                if request.POST.get("field_modpost", False):
                        if check_user_perm(request.user, board, "post_as_mod"):
                                p.rank = board.mod_string
                if request.POST.get("field_adminpost", False):
                        if request.user.is_staff:
                                p.rank = request.POST.get("field_adminpost")
                p.save()
                print "pfost gespeich0rt"
                # TODO file handling
                if f:
                        f.post = p
                        if imgthumbnail:
                                try:
                                        imageid = get_free_fileid()
                                        f.fileid = imageid
                                        f.original_name = request.FILES['field_file'].name
                                        f.filesize = request.FILES['field_file'].size
                                        f.imagethumb.save('%i.%s' % (imageid, imgthumbtype), ContentFile(imgthumbnail), True)
                                        f.image.save('%i.%s' % (imageid, imgext), ContentFile(imgcontent))
                                        f.save()
                                except:
                                        raise
                                        messages.error(request, "Speichern geht nix")
                                        try:
                                                p.delete()
                                        except:
                                                pass
                                        try:
                                                f.delete()
                                        except:
                                                pass
                                        try:
                                                t
                                                if not thread:
                                                        t.delete()
                                        except:
                                                pass
                                        return HttpResponseRedirect(reverse("board", args=[board.identifier]))
                        else:
                                f.delete()
                messages.success(request, "Pfostiert")
                if request.POST.get("gb2","thread") == "thread": #todo set cookie
                        return HttpResponseRedirect(reverse("thread", args=[board.identifier, t.pk]))
                else:
                        return HttpResponseRedirect(reverse("board", args=[board.identifier]))
        except:
                #rollback nicht vergessen:
                try:
                        print "rollback"
                        try:
                                p.delete()
                        except:
                                pass
                        try:
                                f
                        except:
                                pass
                        else:
                                f.delete()
                        try:
                                if not thread:
                                        t.delete()
                        except:
                                raise
                except:
                        pass
                raise
                messages.error(request, "Alles kapoat")
                return board_view(request, board.identifier)

@login_required
def thread_lock_view(request, board, thread_id):
        board = get_object_or_404(Board, identifier=board)
        thread = get_object_or_404(Thread, pk=thread_id)
        if not check_user_perm(request.user, board, "close"):
                raise Http404
        if thread.is_locked:
                thread.is_locked = False
                thread.save()
                messages.success(request, "Faden entsperrt")
        else:
                thread.is_locked = True
                thread.save()
                messages.success(request, "Faden gesperrt")
        return HttpResponseRedirect(reverse("thread", args=[board.identifier, thread.pk]))

@login_required
def thread_sticky_view(request, board, thread_id):
        board = get_object_or_404(Board, identifier=board)
        thread = get_object_or_404(Thread, pk=thread_id)
        if not check_user_perm(request.user, board, "sticky"):
                raise Http404
        if thread.is_sticky:
                thread.is_sticky = False
                thread.save()
                messages.success(request, "Faden befreit")
        else:
                thread.is_sticky = True
                thread.save()
                messages.success(request, "Faden angepinnt")
        return HttpResponseRedirect(reverse("thread", args=[board.identifier, thread.pk]))

@login_required
def thread_autosage_view(request, board, thread_id):
        board = get_object_or_404(Board, identifier=board)
        thread = get_object_or_404(Thread, pk=thread_id)
        if not check_user_perm(request.user, board, "delete"):
                raise Http404
        if thread.flag_autosage:
                thread.flag_autosage = False
                thread.save()
                messages.success(request, "Faden ents&auml;gt; wird bei normalem Limit wieder auftreten")
        else:
                thread.flag_autosage = True
                thread.save()
                messages.success(request, "Faden ges&auml;gt")
        return HttpResponseRedirect(reverse("thread", args=[board.identifier, thread.pk]))

@login_required
def post_delete_view(request, board, thread_id, post_id):
        board = get_object_or_404(Board, identifier=board)
        thread = get_object_or_404(Thread, pk=thread_id)
        post = get_object_or_404(Post, pk=post_id)
        if not check_user_perm(request.user, board, "delete"):
                raise Http404
        if request.GET.get("file",False):
                if request.GET.get("file",False) == "all":
                        for f in post.postfile_set.all():
                                try:
                                        f.delete()
                                except:
                                        pass
                else:
                        try:
                                post.postfile_set.get(pk=request.GET.get("file",False)).delete()
                        except:
                                raise
                messages.success(request, "Datei(en) gel&ouml;scht")
                return HttpResponseRedirect(reverse("thread", args=[board.identifier, thread.pk]))
        delthread = False
        if thread.first_post == post:
                try:
                        thread.delete()
                        delthread = True
                except:
                        messages.error(request, "Faden konnte nicht gel&ouml;scht werden")
                        return HttpResponseRedirect(reverse("thread", args=[board.identifier, thread.pk]))
        try:
                post.delete()
        except:
                messages.error(request, "Pfostierung konnte nicht gel&ouml;scht werden")
        if delthread:
                messages.success(request, "Faden gel&ouml;scht")
                return HttpResponseRedirect(reverse("board", args=[board.identifier]))
        else:
                messages.success(request, "Pfostierung gel&ouml;scht")
                return HttpResponseRedirect(reverse("thread", args=[board.identifier, thread.pk]))
        
        return HttpResponseRedirect(reverse("thread", args=[board.identifier, thread.pk]))

def thread_view(request, board, thread_id):
        board = get_object_or_404(Board, identifier=board)
        thread = get_object_or_404(Thread, pk=thread_id)
        posts = thread.post_set.all()
        return render_to_response("thread.html", locals(), context_instance=RequestContext(request))

# ajax functions
@login_required
def ajax_postinfo_view(request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        if not check_user_perm(request.user, post.thread.board, "view_post_data"):
                raise Http404
        return render_to_response("ajax/postinfo.html", locals(), context_instance=RequestContext(request))

@login_required
def ajax_postaction_view(request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        if not check_user_perm(request.user, post.thread.board, "view_post_data"):
                raise Http404
        return render_to_response("ajax/postaction.html", locals(), context_instance=RequestContext(request))

# helper functions

def check_user_perm(user, board, perm):
        try:
                acl = UserACL.objects.get(user=user, board=board)
        except:
                return False
        # pretty gay setup, but neccessary for templates
        if perm == "mod":
                return True
        if perm == "view_post_data" and acl.perm_view_post_data == True:
                return True
        if perm == "post_as_mod" and acl.perm_post_as_mod == True:
                return True
        if perm == "no_captchas" and acl.perm_no_captchas == True:
                return True
        if perm == "delete" and acl.perm_delete == True:
                return True
        if perm == "sticky" and acl.perm_sticky == True:
                return True
        if perm == "close" and acl.perm_close == True:
                return True
        if perm == "ban" and acl.perm_ban == True:
                return True
        if perm == "evade_ban" and acl.perm_evade_ban == True:
                return True
        return False

def is_moderator(board, user):
        return check_user_perm(user,board,"mod")

def get_free_pk(board):
        try:
                p = Post.objects.filter(thread__board=board).order_by("-localpk")[:1][0]
                return p.localpk+1
        except:
                return 1

def get_free_fileid():
        try:
                f = PostFile.objects.order_by("-fileid")[:1][0]
                return f.fileid+1
        except:
                return 4815162342881
