from django import forms
from django.contrib import admin
from .models import Article, Website, Competitor, Keyword
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


class WebsiteAdmin(admin.ModelAdmin):
    list_display = ('topic', 'hugo_dir', 'data_dir', 'title', 'author_name', 'google_analytics', 'setup_github', 'github_repo_url', 'api_key')

admin.site.register(Website, WebsiteAdmin)    
admin.site.register(Article, ArticleAdmin)
admin.site.register(Competitor,)
admin.site.register(Keyword,)