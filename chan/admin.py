from phutaba.chan.models import *
from django.contrib import admin

admin.site.register(UserProfile)
admin.site.register(UserACL)
admin.site.register(Board)
admin.site.register(BoardCategory)
admin.site.register(Thread)
admin.site.register(Post)
admin.site.register(PostFile)
admin.site.register(Ban)
admin.site.register(Wordfilter)