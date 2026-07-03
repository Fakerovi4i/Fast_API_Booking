#!/bin/sh
if [ "$1" = "celery" ]; then
    celery -A app.tasks.celery_app:celery worker --loglevel=info --pool=threads
elif [ "$1" = "flower" ]; then
    celery -A app.tasks.celery_app:celery flower --pool=threads
else
    echo "Usage: $0 {celery|flower}"
    exit 1
fi
