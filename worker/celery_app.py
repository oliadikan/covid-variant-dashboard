import os
from celery import Celery

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Initialize Celery
app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks.analysis"]  # Include the tasks module
)

# Optional configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
)

if __name__ == "__main__":
    app.start()
