from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Website

@receiver(post_save, sender=Website)
def create_github_repo(sender, instance, created, **kwargs):
    if created:
        instance.create_github_repo()
