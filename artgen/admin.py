# admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .forms import ArticleForm

class ArticleAdmin(admin.AdminSite):
    site_header = 'Article Admin'
    site_title = 'Article Admin'

    def get_urls(self):
        from django.urls import path
        from .views import create_article_view

        urlpatterns = super().get_urls()
        urlpatterns += [
            path('create_article/', self.admin_view(create_article_view), name='create_article'),
        ]
        return urlpatterns

    def create_article_link(self):
        url = reverse('admin:create_article')
        return format_html('<a href="{}">Create Article</a>', url)

    index_title = create_article_link

admin_site = ArticleAdmin(name='articleadmin')
