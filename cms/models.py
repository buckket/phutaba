from django.db import models
from django.contrib.auth.models import User

class Page(models.Model):
	url = models.CharField(max_length=255)
	name = models.CharField(max_length=255)
	base_template = models.CharField(max_length=255)

	@property
	def content(self):
		try:
			return self.pagerevision_set.filter(published=True)[:1][0]
		except:
			raise # XXX
	
	def __unicode__(self):
		return "%s/ (%s)" % (self.url, self.name)

class PageRevision(models.Model):
	page = models.ForeignKey(Page)
	user = models.ForeignKey(User)
	time = models.DateTimeField(null=False, blank=False)
	content_HTML = models.TextField()
	published = models.BooleanField(default=False)

	def __unicode__(self):
		return "%s r%d (by %s, %s)" % (self.page, self.pk, self.user.username, self.time)

	class Meta:
		ordering = ['-time']

class News(models.Model):
	user = models.ForeignKey(User)
	time = models.DateTimeField(null=False, blank=False)
	title = models.CharField(max_length=255, null=True, blank=True)
	content = models.TextField(max_length=5000)
	content_HTML = models.TextField(max_length=7000)
	published = models.BooleanField(default=False)

	def __unicode__(self):
		return "\"%s\" by %s, %s" % (self.title, self.user.username, self.time)
	class Meta:
		ordering = ['-time']