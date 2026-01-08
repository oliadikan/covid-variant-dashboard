.PHONY: init-db clean-db query-db download-ref help

help:
	@echo "COVID-19 Variant Dashboard - Database Management"
	@echo ""
	@echo "Available commands:"
	@echo "  make init-db        - Initialize database with schema"
	@echo "  make download-ref   - Download reference genome from NCBI"
	@echo "  make query-db       - Query and inspect database"
	@echo "  make clean-db       - Delete database (use with caution!)"
	@echo "  make full-init      - Complete initialization (init + download)"

init-db:
	python data_pipeline/init_database.py

download-ref:
	@read -p "Enter your email for NCBI: " email; \
	python data_pipeline/download_reference.py --email $$email

update-ref:
	python data_pipeline/init_with_real_sequence.py

query-db:
	python data_pipeline/query_db.py

clean-db:
	@read -p "Are you sure you want to delete the database? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		rm -f data/variants.db data/variants.db-shm data/variants.db-wal; \
		echo "✓ Database deleted"; \
	else \
		echo "Cancelled"; \
	fi

full-init: init-db download-ref update-ref query-db
	@echo "✓ Full initialization complete!"