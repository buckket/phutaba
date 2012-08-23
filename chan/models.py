from django.db import models
from django.contrib.auth.models import User
import datetime
from django.db.models import Q, Count, Sum
from django.db.models.fields import IntegerField

class BigIntegerField(IntegerField):
	empty_strings_allowed=False
	def get_internal_type(self):
		return "BigIntegerField"
	def db_type(self):
		return 'bigint' # Note this won't work with Oracle.


class UserProfile(models.Model):
	user = models.ForeignKey(User, unique=True)
	level = models.PositiveSmallIntegerField(default=1)
	
	def __unicode__(self):
		return "UserProfile of %s" % self.user.username

class UserACL(models.Model):
	user = models.ForeignKey(User)
	board = models.ForeignKey('Board')
	perm_view_post_data = models.BooleanField(default=False)
	perm_post_as_mod = models.BooleanField(default=False)
	perm_no_captchas = models.BooleanField(default=False)
	perm_delete = models.BooleanField(default=False)
	perm_sticky = models.BooleanField(default=False)
	perm_close = models.BooleanField(default=False)
	perm_ban = models.BooleanField(default=False)
	perm_evade_ban = models.BooleanField(default=False)
	
	def __unicode__(self):
		return "UserACL for %s on %s" % (self.user.username, self.board)

class BoardCategory(models.Model):
	name = models.CharField(max_length=255)
	nsfw = models.BooleanField()
	order = models.SmallIntegerField() # high = up

	def __unicode__(self):
		return "%s%s" % (self.name, ('',' (NSFW)')[self.nsfw])

	class Meta:
		ordering = ['-order','id']

class Board(models.Model):
	identifier = models.CharField(max_length=10, unique=True)
	category = models.ForeignKey(BoardCategory)
	title = models.CharField(max_length=255)
	subtitle = models.CharField(max_length=255)
	allow_uploads = models.BooleanField(default=True)
	pages = models.PositiveSmallIntegerField(default=10)
	force_nick = models.BooleanField(default=False)
	default_nick = models.CharField(max_length=50)
	sage_limit = models.PositiveIntegerField(default=50)
	sage_string = models.CharField(max_length=30, default="SAGE!")
	autosage_string = models.CharField(max_length=30, default="AUTOSAGE")
	ban_string = models.CharField(max_length=255, default="USER WAS BANNED FOR THIS POST")
	mod_string = models.CharField(max_length=30, default="STAFF")
	
	def __unicode__(self):
		return "/%s/ - %s" % (self.identifier, self.title)
	
	class Meta:
		ordering = ["category", "identifier"]

class Thread(models.Model):
	board = models.ForeignKey(Board)
	time_created = models.DateTimeField(null=False, blank=False)
	is_locked = models.BooleanField(default=False)
	is_sticky = models.BooleanField(default=False)
	flag_autosage = models.BooleanField(default=False)
	cached_last_post = models.DateTimeField(null=False, blank=False)
	
	@property
	def first_post(self):
		try:
			p = Post.objects.filter(thread=self).order_by('time','localpk')[0]
			return p
		except:
			return False
	
	@property
	def last_post(self):
		try:
			p = Post.objects.filter(thread=self).order_by('-time','-localpk')[0]
			return p
		except:
			return False
	
	@property
	def sagecount(self):
		try:
			p = Post.objects.filter(thread=self, flag_sage=True).count()
			return p
		except:
			return 0
	
	def save(self): # update cached_last_post automatically
		if self.last_post and not self.flag_autosage:
			self.cached_last_post = self.last_post.time 
		super(Thread, self).save()
	
	def delete(self):
		for p in self.post_set.all():
			try:
				p.delete()
			except:
				pass
		super(Thread, self).delete()
		
	class Meta:
		ordering = ['-is_sticky', '-cached_last_post']

class Post(models.Model):
#	board = models.ForeignKey(Board)
	thread = models.ForeignKey(Thread)
	localpk = models.PositiveIntegerField(null=False, blank=False)
	time = models.DateTimeField(null=False, blank=False)
	title = models.CharField(max_length=255, null=True, blank=True)
	nick = models.CharField(max_length=255, null=True, blank=True)
	ip = models.IPAddressField(null=False, blank=False)
	host = models.CharField(max_length=255, null=True, blank=True)
	location = models.CharField(max_length=255, null=True, blank=True)
	useragent = models.CharField(max_length=255, null=True, blank=True)
	content = models.TextField(max_length=5000)
	content_HTML = models.TextField(max_length=7000)
	password = models.CharField(max_length=50, null=True, blank=True)
	flag_sage = models.BooleanField(default=False)
	flag_op = models.BooleanField(default=False)
	flag_banned = models.BooleanField(default=False)
	flag_hidden = models.BooleanField(default=False)
	flag_reported = models.BooleanField(default=False)
	flag_verified = models.BooleanField(default=False)
	custom_banned = models.CharField(max_length=255, null=True, blank=True)
	user = models.ForeignKey(User, blank=True, null=True)
	rank = models.CharField(max_length=255, null=True, blank=True)
	#files = models.ManyToManyField('File')
	
	def delete(self): # update cached_last_post automatically
		for f in self.postfile_set.all():
			try:
				f.delete()
			except:
				pass
		super(Post, self).delete()
		self.thread.save()
	
	def save(self): # update cached_last_post automatically
		super(Post, self).save()
		if self.flag_sage and not self.thread.flag_autosage:
			if Post.objects.filter(thread=self.thread).count() >= self.thread.board.sage_limit:
				self.thread.flag_autosage = True
				self.thread.save()
				return True
		if not self.flag_sage and not self.thread.flag_autosage:
			self.thread.save()
	class Meta:
		ordering = ['localpk','time']
	
class PostFile(models.Model):
	post = models.ForeignKey(Post)
	filetype = models.CharField(max_length=100) # (data|image)
	original_name = models.CharField(max_length=255)
	fileid = BigIntegerField()
	filesize = models.CharField(max_length=100, null=True, blank=True)
	data = models.FileField(upload_to="uploads/files/", null=True, blank=True) #XXX
	image = models.ImageField(upload_to="uploads/images/", null=True, blank=True) #XXX
	imagethumb = models.ImageField(upload_to="uploads/images/thumbs/", null=True, blank=True)
	imagedimensions = models.CharField(max_length=255, null=True, blank=True)
 
class Wordfilter(models.Model):
	boards = models.ManyToManyField(Board)
	filter = models.CharField(max_length=255)
	value = models.TextField()

	def __unicode__(self):
		return "%s => %s" % (self.filter, self.value[:100])
 
class Ban(models.Model):
	ip = models.CharField(max_length=255) # IPAddressFields are not ipv6 ready yet.
	netmask = models.PositiveSmallIntegerField(default=32)
	admin = models.ForeignKey(User)
	boards = models.ManyToManyField(Board, null=True) # if null, it's a global ban
	time_set = models.DateTimeField(null=False, blank=False)
	time_expiration = models.DateTimeField(null=True, blank=True)
	reason = models.CharField(max_length=255)
	appeal = models.CharField(max_length=1000, null=True, blank=True)
	appeal_allow = models.BooleanField(default=False)
	appeal_void = models.BooleanField(default=False)
	
	def __unicode__(self):
		return "%s/%d" % (self.ip, self.netmask)

class Whitelist(models.Model):
	ip = models.CharField(max_length=255)
	code = models.CharField(max_length=255)
	time_set = models.DateTimeField(null=False, blank=False)
	time_expiration = models.DateTimeField(null=True, blank=True)
	issuer = models.ForeignKey(User)

	def __unicode__(self):
		return "%s (%s)" % (self.code, self.ip)

