from django.contrib import admin
from .models import Article

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('query', 'site', 'content')
    readonly_fields = ('content',)
    
admin.site.register(Article, ArticleAdmin)