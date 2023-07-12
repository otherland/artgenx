
import os

from celery import Celery
from celery import signals

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'artgen.settings')

app = Celery(
    'artgen',
    include=['artgen.tasks']
)



# 'django.conf:settings' - means we should use the only one django
# configuration file
# - namespace='CELERY' means all celery-realted configuration keys
#   should have a `CELERY_` prefix
app.config_from_object('django.conf:settings', namespace='CELERY')


import logging
@signals.setup_logging.connect
def on_celery_setup_logging(**kwargs):
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s %(process)d/%(thread)d %(name)s ~~~~%(funcName)s %(lineno)s %(levelname)s %(message)s',
                'datefmt': "%Y/%m/%d %H:%M:%S"
            }
        },
        'handlers': {
            'celery': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': './logs/celery.log',
                'formatter': 'default'
            },
            'default': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'default'
            }
        },
        'loggers': {
            'celery': {
                'handlers': ['celery'],
                'level': 'INFO',
                'propagate': False
            },
        },
        'root': {
            'handlers': ['default'],
            'level': 'DEBUG'
        },
    }

    logging.config.dictConfig(config)


app.autodiscover_tasks()  # load tasks from all registered Django apps


# app.task is being used when there is no concern for reusable apps
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


if __name__ == '__main__':
    app.start()

