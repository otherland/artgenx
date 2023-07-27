from django import forms
from django.contrib import admin
from .models import Article, Website
from markdownx.models import MarkdownxField  # Import MarkdownxField
from markdownx.widgets import MarkdownxWidget  # Import MarkdownxWidget

class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ('query', 'website', 'markdown_file', 'failed_flag')
        widgets = {
            'markdown_file': MarkdownxWidget,
        }

class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    list_display = ('query', 'website')

    
admin.site.register(Website,)
admin.site.register(Article, ArticleAdmin)