import os
from django.core.management.base import BaseCommand
from subprocess import run
from artgen.models import Article
from pathlib import Path

class Command(BaseCommand):
    help = 'Commit and push changes inside Git submodules'

    def handle(self, *args, **kwargs):
        # Replace 'submodule1', 'submodule2', etc. with the actual submodule folder names
        submodules = list(Article.objects.values_list('website__hugo_dir', flat=True))

        commit_message = "Updating site content to git"

        for submodule in submodules:
            submodule_path = Path(submodule)
            self.stdout.write(self.style.SUCCESS(f'Pushing for module {submodule_path}'))
            # Navigate to the submodule folder
            os.chdir(submodule_path)

            # Stage and commit changes
            run('git add .', shell=True)
            run(f'git commit -m "{commit_message}"', shell=True)

            # Push the changes to the remote repository
            run('git push origin master', shell=True)

        self.stdout.write(self.style.SUCCESS('Successfully committed and pushed changes in all submodules.'))
