"""
Enhanced initialization that uses the real reference genome.
"""

import sqlite3
import json
import logging
from pathlib import Path
from Bio import SeqIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_with_fasta(
    db_path: str = "./data/variants.db",
    fasta_path: str = "./data/reference_genome.fasta"
):
    """Initialize database with real FASTA sequence."""
    
    fasta_file = Path(fasta_path)
    if not fasta_file.exists():
        logger.error(f"Reference genome file not found: {fasta_path}")
        logger.info("Run: python data_pipeline/download_reference.py --email your@email.com")
        return False
    
    # Read FASTA
    logger.info(f"Reading reference genome from {fasta_path}...")
    record = SeqIO.read(fasta_path, "fasta")
    sequence = str(record.seq)
    
    logger.info(f"✓ Loaded sequence: {len(sequence)} bp")
    
    # Update database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE reference_genome 
        SET sequence = ?, sequence_length = ?
        WHERE id = 1
    """, (sequence, len(sequence)))
    
    conn.commit()
    conn.close()
    
    logger.info("✓ Database updated with full reference sequence")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="./data/variants.db")
    parser.add_argument("--fasta", default="./data/reference_genome.fasta")
    
    args = parser.parse_args()
    
    init_with_fasta(args.db, args.fasta)
