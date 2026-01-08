"""
Downloads the complete SARS-CoV-2 reference genome from NCBI.
"""

from Bio import Entrez, SeqIO
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_reference_genome(
    accession: str = "NC_045512.2",
    output_file: str = "./data/reference_genome.fasta",
    email: str = "your.email@example.com"
):
    """
    Download reference genome from NCBI GenBank.
    
    Args:
        accession: GenBank accession ID
        output_file: Output FASTA file path
        email: Your email (required by NCBI)
    """
    # Set email for NCBI (required)
    Entrez.email = email
    
    logger.info(f"Downloading {accession} from NCBI...")
    
    try:
        # Fetch the sequence
        handle = Entrez.efetch(
            db="nucleotide",
            id=accession,
            rettype="fasta",
            retmode="text"
        )
        
        # Parse and save
        record = SeqIO.read(handle, "fasta")
        handle.close()
        
        # Create output directory
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        SeqIO.write(record, output_file, "fasta")
        
        logger.info(f"✓ Downloaded {len(record.seq)} bp")
        logger.info(f"✓ Saved to: {output_file}")
        
        return str(record.seq)
        
    except Exception as e:
        logger.error(f"Error downloading reference: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True, help="Your email address")
    parser.add_argument("--output", default="./data/reference_genome.fasta")
    
    args = parser.parse_args()
    
    download_reference_genome(email=args.email, output_file=args.output)