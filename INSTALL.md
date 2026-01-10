# Local Development Installation Guide

This guide provides instructions for setting up a local development environment for the COVID-19 Variant Analysis Dashboard.

## Prerequisites

- **Python 3.11+**
- **Redis** (Required for Celery task queue)
- **Git**

## Setup Instructions

Follow these steps to set up the project on your local machine:

### 1. Clone the Repository
```bash
git clone https://github.com/oliadikan/covid-variant-dashboard.git
cd covid-variant-dashboard
```

### 2. Create a Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies.
```bash
python -m venv venv
```

### 3. Activate the Virtual Environment
- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

### 4. Install Dependencies
Install all required Python modules using the combined development requirements file:
```bash
pip install -r requirements-dev.txt
```

### 5. Configure Environment Variables
Copy the example environment file and adjust the values if necessary:
```bash
cp .env.example .env
```

### 6. Initialize the Database
Run the database initialization script to create the schema and populate reference data:
```bash
python data_pipeline/init_database.py --force
```

## Running the Services Locally

To run the project without Docker, you will need to start each service in a separate terminal:

1.  **Start Redis:**
    Ensure your local Redis server is running (usually `redis-server`).

2.  **Start the Backend API:**
    ```bash
    cd backend
    uvicorn app.main:app --reload
    ```

3.  **Start the Celery Worker:**
    ```bash
    cd worker
    celery -A celery_app worker --loglevel=info
    ```

4.  **Start the Dashboard:**
    ```bash
    cd dashboard
    python app.py
    ```

## Troubleshooting

- **scikit-bio installation:** If you encounter issues installing `scikit-bio`, ensure you have the necessary build tools (`gcc`, `g++`) installed on your system.
- **Redis connection:** Verify that the `REDIS_URL` in your `.env` file matches your local Redis configuration.
