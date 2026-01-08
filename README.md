# COVID-19 Variant Analysis Dashboard

A bioinformatics web application for analyzing SARS-CoV-2 genomic sequences and identifying variants through BLAST-like sequence alignment.

## 🎯 Project Overview

This portfolio project demonstrates full-stack development skills combined with bioinformatics expertise:

- **Async Processing**: FastAPI + Celery for responsive sequence analysis
- **Interactive Dashboard**: Dash-based visualization interface
- **Bioinformatics Pipeline**: K-mer indexing and sequence alignment
- **Data Engineering**: Automated ETL from NCBI GenBank
- **Containerization**: Complete Docker Compose deployment

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- 4GB RAM minimum

### Running with Docker
```bash
# Clone the repository
git clone https://github.com/oliadikan/covid-variant-dashboard
cd covid-variant-dashboard

# Copy environment variables
cp .env.example .env

# Build and start all services
docker-compose up --build

# Access the dashboard
# Dashboard: http://localhost:8050
# API Docs: http://localhost:8000/docs
```

### Local Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies for each component
pip install -r backend/requirements.txt
pip install -r worker/requirements.txt
pip install -r dashboard/requirements.txt

# Initialize database
python data_pipeline/process_variants.py --init

# Start services individually (in separate terminals)
# Terminal 1: Redis
redis-server

# Terminal 2: Backend API
cd backend && uvicorn app.main:app --reload

# Terminal 3: Celery Worker
cd worker && celery -A celery_app worker --loglevel=info

# Terminal 4: Dashboard
cd dashboard && python app.py
```

## 📊 Features

### User-Facing Features
- Upload FASTA sequences for variant identification
- Real-time analysis progress tracking
- Mutation detection and annotation
- Concerning mutation alerts (immune escape, ACE2 binding)
- Interactive phylogenetic tree visualization
- Global variant prevalence timeline
- Mutation frequency heatmap

### Technical Features
- Asynchronous job processing with Celery
- K-mer based sequence similarity search
- Rule-based mutation classification
- Automated data pipeline from NCBI GenBank
- RESTful API with FastAPI
- Containerized microservices architecture

## 🏗️ Architecture
```
User → Dash Dashboard → FastAPI → Celery Worker → SQLite DB
                           ↓            ↓
                        Redis ← ─ ─ ─ ─ ┘
```

See [docs/architecture.md](docs/architecture.md) for detailed component descriptions.

## 📁 Project Structure
```
covid-variant-dashboard/
├── backend/          # FastAPI application
├── worker/           # Celery tasks & bioinformatics engine
├── dashboard/        # Dash visualization interface
├── data_pipeline/    # ETL scripts for NCBI data
├── data/            # SQLite DB & generated files
└── docs/            # Documentation
```

## 🧬 Data Sources

Sequence data is sourced from **NCBI GenBank** (https://www.ncbi.nlm.nih.gov/genbank/).

**Disclaimer**: This tool is for educational and research purposes only. It is not a substitute for clinical diagnosis or public health surveillance systems.

## 🧪 Testing
```bash
# Run backend tests
cd backend && pytest

# Run worker tests
cd worker && pytest

# Run all tests with coverage
pytest --cov=. --cov-report=html
```

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details

## Status
🚧 In Development

## 🤝 Contributing

This is a portfolio project, but suggestions and feedback are welcome! Please open an issue to discuss proposed changes.

## 📧 Contact

Your Name - olia.dikan@gmail.com

Project Link: [https://github.com/oliadikan/covid-variant-dashboard](https://github.com/oliadikan/covid-variant-dashboard)