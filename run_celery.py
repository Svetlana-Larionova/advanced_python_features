"""
Запуск Celery worker
"""
from background_tasks import celery_app

if __name__ == "__main__":
    celery_app.start()