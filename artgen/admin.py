from django import forms
from django.contrib import admin
from .models import Article, Website
from markdownx.models import MarkdownxField  # Import MarkdownxField
from markdownx.widgets import MarkdownxWidget  # Import MarkdownxWidget

class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = '__all__'
        widgets = {
            'markdown_file': MarkdownxWidget,
        }

class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    list_display = ('query', 'site',)

    
admin.site.register(Website,)
admin.site.register(Article, ArticleAdmin)