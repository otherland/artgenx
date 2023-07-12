from django.contrib import admin
from .forms import ArticleForm

class ArticleAdmin(admin.AdminSite):
    def get_urls(self):
        from django.urls import path
        from .views import create_article_view

        urlpatterns = super().get_urls()
        urlpatterns += [
            path('create_article/', self.admin_view(create_article_view), name='create_article'),
        ]
        return urlpatterns

admin_site = ArticleAdmin(name='articleadmin')