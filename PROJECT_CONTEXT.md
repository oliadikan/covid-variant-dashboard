# Project Context: COVID-19 Variant Analysis Dashboard

This document serves as a comprehensive context hand-off for the next AI instance to continue development. It captures the current state, architectural decisions, and the full roadmap for completion.

## 1. Current Work & Status
The project is a bioinformatics portfolio showcase. We have successfully moved from a skeleton structure to a functional microservices environment. The infrastructure is fully containerized, and the core application skeletons are in place.

### Completed Milestones:
- **Infrastructure**: Docker Compose setup for Redis, Backend (FastAPI), Worker (Celery), and Dashboard (Dash).
- **Environment**: `.env` and `.env.example` configured for local and containerized development.
- **Backend**: FastAPI entry point (`backend/app/main.py`) with endpoints for FASTA upload, task polling, and aggregate data serving.
- **Worker**: Celery application (`worker/celery_app.py`) and analysis task skeleton (`worker/tasks/analysis.py`) using BioPython.
- **Dashboard**: Dash UI (`dashboard/app.py`) with a Bootstrap layout, upload component, and polling logic.
- **Data Foundation**: SQLite schema defined and initialization script created (`data_pipeline/init_database.py`).
- **Developer Experience**: Combined `requirements-dev.txt` and `INSTALL.md` for easy local setup.

## 2. Key Technical Concepts
- **Architecture**: Microservices (FastAPI + Celery + Redis + Dash + SQLite).
- **Bioinformatics**: K-mer matching and sequence alignment (BioPython, scikit-bio).
- **Async Flow**: Dash (Frontend) -> FastAPI (Orchestrator) -> Celery (Worker) -> Redis (Broker) -> SQLite (Results).
- **Data Source**: NCBI GenBank (SARS-CoV-2 reference NC_045512.2).

## 3. Relevant Files & Code Sections
- `docker-compose.yml`: Defines the service orchestration and volume mounts for hot-reloading.
- `backend/app/main.py`: Handles file saving to `UPLOAD_DIR` and dispatches tasks via `celery_client.send_task`.
- `worker/tasks/analysis.py`: Contains the `analyze_sequence` task. Currently uses mock logic but is wired for BioPython parsing.
- `data_pipeline/init_database.py`: Contains the `DatabaseInitializer` class with the full SQL schema for variants, mutations, and k-mer indexes.
- `dashboard/app.py`: Uses `dcc.Interval` for polling the backend and `dcc.Store` for managing task IDs.

## 4. Problem Solving & Decisions
- **Task Dispatching**: Used `celery_client.send_task` by name in the backend to avoid importing worker code, maintaining strict service separation.
- **Shared Storage**: Implemented a shared `./data` volume in Docker to allow all services to access the SQLite DB and uploaded FASTA files.
- **Local Dev**: Created `requirements-dev.txt` to solve the issue of managing three separate requirements files during local (non-Docker) development.

## 5. Full Project Roadmap

### **Phase 1: Data Foundation & ETL**
- [x] **Step 1.1: Finalize SQLite Schema**: Implemented in `data_pipeline/init_database.py`.
- [ ] **Step 1.2: Populate Reference Data**: Refine `data_pipeline/download_reference.py` to fetch the SARS-CoV-2 reference genome and ~1,000 representative variant sequences.
- [ ] **Step 1.3: Implement Aggregation Logic**: Create a script to generate the `aggregates/` files (Parquet/JSON) for the global timeline and heatmap visualizations.

### **Phase 2: Bioinformatics Engine**
- [ ] **Step 2.1: K-mer Indexing**: Implement a k-mer based similarity search in `worker/bioinformatics/` to quickly identify the closest matching variant in the database.
- [ ] **Step 2.2: Mutation Detection**: Implement a simplified alignment logic (using `BioPython` or `scikit-bio`) to compare the uploaded sequence against the reference and identify specific mutations.
- [ ] **Step 2.3: Rule-Based Classification**: Build the logic to check identified mutations against the "concerning mutations" rules (e.g., flagging E484K or N501Y).
- [ ] **Step 2.4: Phylogenetic Tree Generation**: Implement "on-the-fly" tree generation using `Bio.Phylo` to show the uploaded sequence's position relative to the top N matches.

### **Phase 3: Backend & Worker Integration**
- [ ] **Step 3.1: Real Task Implementation**: Replace the mock logic in `worker/tasks/analysis.py` with calls to the Bioinformatics Engine.
- [ ] **Step 3.2: Database Integration**: Update the worker to query the SQLite database for variant metadata and rules during analysis.
- [x] **Step 3.3: FASTA Validation**: Basic extension validation implemented in `backend/app/main.py`.

### **Phase 4: Dashboard & Visualization**
- [x] **Step 4.1: Real Data Polling**: Polling structure implemented in `dashboard/app.py`.
- [ ] **Step 4.2: Interactive Visualizations**:
    - Implement the **Variant Timeline** using Plotly.
    - Implement the **Mutation Heatmap** using Plotly.
    - Render the **Phylogenetic Tree** (both the global static one and the dynamic result one).
- [x] **Step 4.3: UI/UX Refinement**: Basic Bootstrap layout and upload interface are functional.

### **Phase 5: Automation & DevOps**
- [ ] **Step 5.1: GitHub Actions**: Create a workflow to periodically run the data pipeline, update the SQLite DB, and push updated aggregates.
- [ ] **Step 5.2: Testing**: Write unit tests for the bioinformatics logic and integration tests for the FastAPI/Celery flow.
- [x] **Step 5.3: Production Hardening**: `docker-compose.yml` and `.env` are fully configured.

## 6. Instructions for the AI
"Pick up from Phase 1.2 or 1.3. Use the existing `DatabaseInitializer` in `data_pipeline/init_database.py` as a reference for the data structure. Ensure that any new bioinformatics logic is placed in the `worker/bioinformatics/` directory and called via the Celery tasks."
