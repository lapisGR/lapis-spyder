web: uvicorn src.main:app --host 0.0.0.0 --port $PORT
worker: celery -A src.celery worker --loglevel=info
beat: celery -A src.celery beat --loglevel=info