
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from .forms import ArticleForm
from .tasks import create_article_task

@staff_member_required
def create_article_view(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            site = form.cleaned_data['site']
            topic = form.cleaned_data['topic']
            # Run your Celery task with the site and topic parameters
            create_article_task.delay(site, topic)
            return HttpResponseRedirect('/admin/')  # Redirect to admin homepage after submission
    else:
        form = ArticleForm()
    return render(request, 'admin/create_article.html', {'form': form})