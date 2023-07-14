from django.contrib import admin
from .models import Article, Site

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('query', 'site', 'content')
    readonly_fields = ('content',)
    
admin.site.register(Site,)
admin.site.register(Article, ArticleAdmin)