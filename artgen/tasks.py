import os
import csv
from celery import shared_task
from generate.generate import generate
from subprocess import run
from artgen.models import Competitor, Keyword
from generate.semrush_reports import run_semrush_automation
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import make_aware  # Import the make_aware function
from datetime import datetime  # Import the datetime module


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def process_article_task(self, id):
    from artgen.models import Article
    try:
        article = Article.objects.get(pk=id)
        post_dir, data_dir, image_dir, subject = article.get_site_data()

        article.markdown_file = generate(article.query, subject, post_dir, data_dir, image_dir)
        article.save()

    except Exception as exc:
        if self.request.retries >= self.retry_kwargs['max_retries']:
            # If the task still fails after max retries, set the flag
            try:
                article.failed_flag = True
                article.save()
            except UnboundLocalError:
                pass
        else:
            # If the task failed but is still retrying, re-raise the exception for retry
            self.retry(exc=exc, countdown=2 ** self.request.retries)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def queue_articles(self):
    from artgen.models import Article
    articles_to_process = Article.objects.filter(markdown_file='')

    # send unwritten articles for writing
    for article in articles_to_process:
        current_app.send_task('artgen.tasks.process_article_task', kwargs={'id': article.id})

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def update_site_repos(self):
    from artgen.models import Article
    # update git repos for all sites
    submodules = list(Article.objects.values_list('website__hugo_dir', flat=True))

    commit_message = "Updating site content to git"

    for submodule in submodules:
        self.stdout.write(self.style.SUCCESS(f'Pushing for module {submodule}'))
        # Navigate to the submodule folder
        run(f'cd {submodule}', shell=True)

        # Stage and commit changes
        run('git add .', shell=True)
        run(f'git commit -m "{commit_message}"', shell=True)

        # Push the changes to the remote repository
        run('git push origin master', shell=True)

    self.stdout.write(self.style.SUCCESS('Successfully committed and pushed changes in all submodules.'))


@shared_task
def run_sem_rush_for_missing_keywords():
    # Find competitors without related keywords
    competitors_without_keywords = Competitor.objects.annotate(keyword_count=Count('keyword')).filter(keyword_count=0)
    
    # Get the domain names of competitors without keywords
    domain_names = competitors_without_keywords.values_list('domain_name', flat=True)
    
    # Chunk the domain names into groups of 10
    domain_chunks = [domain_names[i:i + 10] for i in range(0, len(domain_names), 10)]
    
    reported_domains = run_semrush_automation(domain_chunks)

@shared_task
def process_csv_files():
    download_directory = os.path.join(settings.BASE_DIR, 'generate', 'semrush_reports')
    
    for file_name in os.listdir(download_directory):
        if file_name.endswith('.csv'):
            file_path = os.path.join(download_directory, file_name)
            domain_name = file_name.split('-')[0]
            try:
                competitor = Competitor.objects.get(domain_name=domain_name)
            except Competitor.DoesNotExist:
                continue
            
            with open(file_path, 'r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    timestamp_naive = datetime.strptime(row['Timestamp'], '%Y-%m-%d')
                    timestamp_aware = make_aware(timestamp_naive)
                    # Use get_or_create to prevent duplicates
                    try:
                        Keyword.objects.get_or_create(
                            competitor=competitor,
                            keyword=row['Keyword'],
                            defaults={
                                'position': int(row['Position']),
                                'previous_position': int(row['Previous position']),
                                'search_volume': int(row['Search Volume']),
                                'keyword_difficulty': int(row['Keyword Difficulty']),
                                'cpc': float(row['CPC']),
                                'url': row['URL'],
                                'traffic': int(row['Traffic']),
                                'traffic_percentage': float(row['Traffic (%)']),
                                'traffic_cost': float(row['Traffic Cost']),
                                'competition': float(row['Competition']),
                                'num_results': int(row['Number of Results']),
                                'trends': row['Trends'],  # This field might need further processing
                                'timestamp': timestamp_aware,  # You might need to parse this into a datetime object
                                'serp_features': row['SERP Features by Keyword'],
                                'keyword_intents': row['Keyword Intents'],
                                'position_type': row['Position Type'],
                            }
                        )
                    except Exception as e:
                        print(e)
                        print(f"Error creating keyword: {row['Keyword']}")
                    finally:
                        # Move or delete the CSV file after successful processing
                        # os.remove(file_path)
                        pass

