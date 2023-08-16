import toml
import os

import markdown
from github import Github, GithubException

from django.conf import settings
from django.db import models
from django.contrib import admin
from .tasks import process_article_task
from generate.cloudflare_deploy import deploy_project
import shutil


class Website(models.Model):
    topic = models.CharField(max_length=100, unique=True)
    hugo_dir = models.CharField(max_length=1024, blank=True)
    data_dir = models.CharField(max_length=1024, blank=True)
    
    title = models.CharField(max_length=1024, blank=True)
    description = models.CharField(max_length=1024, blank=True)
    author_name = models.CharField(max_length=1024, blank=True)
    google_analytics = models.CharField(max_length=1024, blank=True)

    setup_github = models.BooleanField(default=True)
    github_repo_url = models.CharField(max_length=1024, blank=True)

    api_key = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.topic

    def save(self, *args, **kwargs):
        # Set the required fields if they are empty
        if not self.hugo_dir:
            self.hugo_dir = os.path.join(settings.BASE_DIR, "sites", f"{self.topic.lower().replace(' ', '-')}-website", "site")

        if not self.data_dir:
            self.data_dir = os.path.join(settings.BASE_DIR, "sites", f"{self.topic.lower().replace(' ', '-')}-website", "data")

        super().save(*args, **kwargs)

    def create_github_repo(self):
        if not self.setup_github:
            return
        # Create a GitHub repository
        try:
            github_token = settings.GITHUB_ACCESS_TOKEN  # Get the token from Django settings
            g = Github(github_token)
            user = g.get_user()
            repo_name = f"{self.topic.lower().replace(' ', '-')}-website"
            repo_description = f"A Hugo website for {self.topic}"
            repo = user.create_repo(repo_name, description=repo_description)
        except GithubException as e:
            if e.status == 422 and e.data and 'errors' in e.data:
                error_message = e.data['errors'][0]['message']
                raise ValueError(f"GitHub Repository creation failed: {error_message}")

            raise  # Re-raise the exception if it's not a 422 error

        # Duplicate Hugo website and initialize Git repository
        source_hugo_dir = os.path.join(settings.BASE_DIR, "sites", "template", "site")

        # Create the target directory for the new website
        os.makedirs(self.hugo_dir)

        # Copy all files from the source directory to the target directory
        for root, dirs, files in os.walk(source_hugo_dir):
            for file in files:
                source_file_path = os.path.join(root, file)
                target_file_path = os.path.join(self.hugo_dir, os.path.relpath(source_file_path, source_hugo_dir))
                os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                shutil.copy2(source_file_path, target_file_path)

        # Initialize Git repository in the target directory
        repo_path = os.path.abspath(self.hugo_dir)

        # Path to the hugo.toml file
        hugo_toml_path = os.path.join(repo_path, 'hugo.toml')

        # Read the existing hugo.toml file
        with open(hugo_toml_path, 'r') as toml_file:
            config = toml.load(toml_file)

        # Modify the values if not blank or empty
        if self.description:
            config['Params']['description'] = self.description

        if self.author_name:
            config['Params']['copyright'] = self.author_name
            config['Author']['name'] = self.author_name

        if self.title:
            config['title'] = self.title

        if self.google_analytics:
            config['googleAnalytics'] = self.google_analytics

        # Write back the modified values to the hugo.toml file
        with open(hugo_toml_path, 'w') as toml_file:
            toml.dump(config, toml_file)


        os.chdir(repo_path)
        os.system("git init")
        os.system("git add .")
        os.system("git commit -m 'Initial commit'")
        os.system(f"git remote add origin {repo.ssh_url}")
        os.system("git push -u origin master")

        # Update the Website object with the GitHub repository URL
        self.github_repo_url = repo.html_url
        self.save()

        print('Deploying project to Cloudflare...')

        deploy_project(project_name=repo_name)



class Article(models.Model):
    query = models.CharField(max_length=100)
    website = models.ForeignKey(Website, on_delete=models.CASCADE)
    markdown_file = models.FileField(upload_to='markdown_files/', blank=True)
    failed_flag = models.BooleanField(default=False)

    class Meta:
        # Define unique_together to make articles unique by website and query
        unique_together = ('website', 'query')

    def get_site_data(self):
        post_dir = os.path.join(self.website.hugo_dir, 'content', 'posts')
        data_dir = self.website.data_dir
        image_dir = os.path.join(self.website.hugo_dir, 'static', 'images')
        return (post_dir, data_dir, image_dir, self.website.topic)

    def __str__(self):
        return self.query


class Competitor(models.Model):
    domain_name = models.CharField(max_length=255)

class Keyword(models.Model):
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=255)
    position = models.PositiveIntegerField()
    previous_position = models.PositiveIntegerField()
    search_volume = models.PositiveIntegerField()
    keyword_difficulty = models.PositiveIntegerField()
    cpc = models.DecimalField(max_digits=10, decimal_places=2)
    url = models.URLField()
    traffic = models.PositiveIntegerField()
    traffic_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    traffic_cost = models.DecimalField(max_digits=10, decimal_places=2)
    competition = models.DecimalField(max_digits=5, decimal_places=2)
    num_results = models.PositiveIntegerField()
    trends = models.JSONField()  # Store the list of trends
    timestamp = models.DateTimeField()
    serp_features = models.TextField()  # Store the list of SERP features
    keyword_intents = models.CharField(max_length=255)
    position_type = models.CharField(max_length=255)

    class Meta:
        unique_together = ('competitor', 'keyword', 'timestamp')

    def __str__(self):
        return f"{self.keyword} - {self.competitor.domain_name}"