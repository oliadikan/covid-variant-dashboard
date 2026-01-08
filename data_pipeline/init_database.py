"""
Database initialization script for COVID-19 Variant Analysis Dashboard.
Creates tables, indexes, and populates with reference genome data.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Handles database creation and initialization."""
    
    def __init__(self, db_path: str = "./data/variants.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
    
    def create_schema(self):
        """Create all database tables with proper indexes."""
        logger.info("Creating database schema...")
        
        cursor = self.conn.cursor()
        
        # Drop existing tables if they exist (for clean initialization)
        cursor.execute("DROP TABLE IF EXISTS analysis_history")
        cursor.execute("DROP TABLE IF EXISTS kmer_index")
        cursor.execute("DROP TABLE IF EXISTS mutation_rules")
        cursor.execute("DROP TABLE IF EXISTS mutations")
        cursor.execute("DROP TABLE IF EXISTS variants")
        cursor.execute("DROP TABLE IF EXISTS reference_genome")
        
        # Reference genome table
        cursor.execute("""
            CREATE TABLE reference_genome (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                accession_id TEXT NOT NULL,
                sequence TEXT NOT NULL,
                sequence_length INTEGER NOT NULL,
                annotation TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✓ Created reference_genome table")
        
        # Variants table
        cursor.execute("""
            CREATE TABLE variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                accession_id TEXT UNIQUE NOT NULL,
                lineage TEXT NOT NULL,
                who_label TEXT,
                sequence TEXT NOT NULL,
                sequence_length INTEGER NOT NULL,
                collection_date DATE NOT NULL,
                country TEXT,
                submission_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX idx_lineage ON variants(lineage)")
        cursor.execute("CREATE INDEX idx_collection_date ON variants(collection_date)")
        cursor.execute("CREATE INDEX idx_who_label ON variants(who_label)")
        logger.info("✓ Created variants table with indexes")
        
        # Mutations table
        cursor.execute("""
            CREATE TABLE mutations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                variant_id INTEGER NOT NULL,
                gene TEXT NOT NULL,
                position INTEGER NOT NULL,
                reference_aa TEXT NOT NULL,
                alternate_aa TEXT NOT NULL,
                mutation_notation TEXT NOT NULL,
                FOREIGN KEY (variant_id) REFERENCES variants(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX idx_mutation_notation ON mutations(mutation_notation)")
        cursor.execute("CREATE INDEX idx_gene_position ON mutations(gene, position)")
        cursor.execute("CREATE INDEX idx_variant_id ON mutations(variant_id)")
        logger.info("✓ Created mutations table with indexes")
        
        # Mutation rules table
        cursor.execute("""
            CREATE TABLE mutation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                mutations TEXT NOT NULL,
                severity TEXT CHECK(severity IN ('low', 'medium', 'high')),
                description TEXT,
                reference_url TEXT
            )
        """)
        logger.info("✓ Created mutation_rules table")
        
        # K-mer index table
        cursor.execute("""
            CREATE TABLE kmer_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                variant_id INTEGER NOT NULL,
                kmer TEXT NOT NULL,
                position INTEGER NOT NULL,
                FOREIGN KEY (variant_id) REFERENCES variants(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX idx_kmer ON kmer_index(kmer)")
        cursor.execute("CREATE INDEX idx_kmer_variant ON kmer_index(variant_id)")
        logger.info("✓ Created kmer_index table with indexes")
        
        # Analysis history table
        cursor.execute("""
            CREATE TABLE analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                matched_variant_id INTEGER,
                match_score REAL,
                concerning_mutations TEXT,
                status TEXT CHECK(status IN ('pending', 'processing', 'completed', 'failed')),
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (matched_variant_id) REFERENCES variants(id)
            )
        """)
        cursor.execute("CREATE INDEX idx_job_id ON analysis_history(job_id)")
        cursor.execute("CREATE INDEX idx_status ON analysis_history(status)")
        logger.info("✓ Created analysis_history table with indexes")
        
        self.conn.commit()
        logger.info("✓ Schema creation completed successfully")
    
    def insert_reference_genome(self):
        """Insert SARS-CoV-2 reference genome (Wuhan-Hu-1)."""
        logger.info("Inserting reference genome data...")
        
        # Reference genome data (NC_045512.2 - Wuhan-Hu-1)
        reference_data = {
            'accession_id': 'NC_045512.2',
            'sequence': self._get_reference_sequence(),
            'annotation': json.dumps(self._get_gene_annotations())
        }
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO reference_genome (id, accession_id, sequence, sequence_length, annotation)
            VALUES (1, ?, ?, ?, ?)
        """, (
            reference_data['accession_id'],
            reference_data['sequence'],
            len(reference_data['sequence']),
            reference_data['annotation']
        ))
        
        self.conn.commit()
        logger.info(f"✓ Reference genome inserted: {reference_data['accession_id']} ({len(reference_data['sequence'])} bp)")
    
    def insert_mutation_rules(self):
        """Insert predefined concerning mutation rules."""
        logger.info("Inserting mutation rules...")
        
        rules = [
            {
                'rule_name': 'RBD Triple Mutation (Beta-like)',
                'mutations': json.dumps(['S:K417N', 'S:E484K', 'S:N501Y']),
                'severity': 'high',
                'description': 'Triple mutation in receptor binding domain associated with immune escape and increased ACE2 binding affinity',
                'reference_url': 'https://www.nature.com/articles/s41586-021-03402-9'
            },
            {
                'rule_name': 'Omicron RBD Signature',
                'mutations': json.dumps(['S:G339D', 'S:S371L', 'S:S373P', 'S:S375F', 'S:K417N', 'S:N440K', 'S:G446S', 'S:S477N', 'S:T478K', 'S:E484A', 'S:Q493R', 'S:G496S', 'S:Q498R', 'S:N501Y', 'S:Y505H']),
                'severity': 'high',
                'description': 'Multiple RBD mutations characteristic of Omicron variants with significant immune evasion',
                'reference_url': 'https://www.science.org/doi/10.1126/science.abn7591'
            },
            {
                'rule_name': 'E484K Immune Escape',
                'mutations': json.dumps(['S:E484K']),
                'severity': 'medium',
                'description': 'Single mutation associated with reduced neutralization by antibodies',
                'reference_url': 'https://www.cell.com/cell/fulltext/S0092-8674(21)00367-1'
            },
            {
                'rule_name': 'N501Y Enhanced Binding',
                'mutations': json.dumps(['S:N501Y']),
                'severity': 'medium',
                'description': 'Increased binding affinity to ACE2 receptor, found in Alpha, Beta, Gamma, and Omicron variants',
                'reference_url': 'https://www.nature.com/articles/s41586-021-03398-2'
            },
            {
                'rule_name': 'D614G Transmission',
                'mutations': json.dumps(['S:D614G']),
                'severity': 'low',
                'description': 'Associated with increased viral transmission, now dominant globally',
                'reference_url': 'https://www.cell.com/cell/fulltext/S0092-8674(20)31537-4'
            },
            {
                'rule_name': 'Delta L452R',
                'mutations': json.dumps(['S:L452R']),
                'severity': 'medium',
                'description': 'Found in Delta variant, associated with immune evasion and increased transmissibility',
                'reference_url': 'https://www.nature.com/articles/s41586-021-03777-9'
            },
            {
                'rule_name': 'Furin Cleavage Enhancement',
                'mutations': json.dumps(['S:P681R', 'S:P681H']),
                'severity': 'medium',
                'description': 'Enhanced furin cleavage site processing, affecting viral entry and pathogenicity',
                'reference_url': 'https://www.nature.com/articles/s41586-021-03471-w'
            }
        ]
        
        cursor = self.conn.cursor()
        for rule in rules:
            cursor.execute("""
                INSERT INTO mutation_rules (rule_name, mutations, severity, description, reference_url)
                VALUES (?, ?, ?, ?, ?)
            """, (
                rule['rule_name'],
                rule['mutations'],
                rule['severity'],
                rule['description'],
                rule['reference_url']
            ))
        
        self.conn.commit()
        logger.info(f"✓ Inserted {len(rules)} mutation rules")
    
    def _get_reference_sequence(self) -> str:
        """
        Returns SARS-CoV-2 reference genome sequence (Wuhan-Hu-1).
        In production, this should fetch from NCBI or a local file.
        For now, returning a truncated placeholder.
        """
        # NOTE: This is a PLACEHOLDER. In production, you should:
        # 1. Download from NCBI: https://www.ncbi.nlm.nih.gov/nuccore/NC_045512.2
        # 2. Or include the full sequence file in your repository
        
        # Full sequence is 29,903 bp - truncated here for demonstration
        # Replace with actual full sequence
        return """ATTAAAGGTTTATACCTTCCCAGGTAACAAACCAACCAACTTTCGATCTCTTGTAGATCTGTTCTCTAAACGAACTTTAAAATCTGTGTGGCTGTCACTCGGCTGCATGCTTAGTGCACTCACGCAGTATAATTAATAACTAATTACTGTCGTTGACAGGACACGAGTAACTCGTCTATCTTCTGCAGGCTGCTTACGGTTTCGTCCGTGTTGCAGCCGATCATCAGCACATCTAGGTTTCGTCCGGGTGTGACCGAAAGGTAAGATGGAGAGCCTTGTCCCTGGTTTCAACGAGAAAACACACGTCCAACTCAGTTTGCCTGTTTTACAGGTTCGCGACGTGCTCGTACGTGGCTTTGGAGACTCCGTGGAGGAGGTCTTATCAGAGGCACGTCAACATCTTAAAGATGGCACTTGTGGCTTAGTAGAAGTTGAAAAAGGCGTTTTGCCTCAACTTGAACAGCCCTATGTGTTCATCAAACGTTCGGATGCTCGAACTGCACCTCATGGTCATGTTATGGTTGAGCTGGTAGCAGAACTCGAAGGCATTCAGTACGGTCGTAGTGGTGAGACACTTGGTGTCCTTGTCCCTCATGTGGGCGAAATACCAGTGGCTTACCGCAAGGTTCTTCTTCGTAAGAACGGTAATAAAGGAGCTGGTGGCCATAGTTACGGCGCCGATCTAAAGTCATTTGACTTAGGCGACGAGCTTGGCACTGATCCTTATGAAGATTTTCAAGAAAACTGGAACACTAAACATAGCAGTGGTGTTACCCGTGAACTCATGCGTGAGCTTAACGGAGGGGCATACACTCGCTATGTCGATAACAACTTCTGTGGCCCTGATGGCTACCCTCTTGAGTGCATTAAAGACCTTCTAGCACGTGCTGGTAAAGCTTCATGCACTTTGTCCGAACAACTGGACTTTATTGACACTAAGAGGGGTGTATACTGCTGCCGTGAACATGAGCATGAAATTGCTTGGTACACGGAACGTTCTGAAAAGAGCTATGAATTGCAGACACCTTTTGAAATTAAATTGGCAAAGAAATTTGACACCTTCAATGGGGAATGTCCAAATTTTGTATTTCCCTTAAATTCCATAATCAAGACTATTCAACCAAGGGTTGAAAAGAAAAAGCTTGATGGCTTTATGGGTAGAATTCGATCTGTCTATCCAGTTGCGTCACCAAATGAATGCAACTCAAATGTGCCTGAGCAACAACTATTTGATGAGAGGTTATTGAAACATTTAACAAGGCCAGAGAAAGGTAAATGTTCTATTCTTTCTCCTGCTTGTATTTTCTTAGGGTTTGGTTCCTTCATAGTGTGGCCTTATGTGGTTTTCAAATACCGTCAAAGGTACGATTATTGCACCTGAAGATATTTAGACAGGAGACATAAAGGCTTTTAGACTTGGTCCTTCCATAGTTTAAGGGAGGATCTTGAGATCCCTTTAGGCTCATTGGAAAGGCTGTGTGAAGAGGCTGGTTTGGAACAACTTGCACTAATGAAAGGGGATGGGTCTCGTGTTGGGGAAGCGGTTTTTCTTTTACATTCCTAAGGTAGCGACTTCTTCTTTGTGTGCCGTAAGTTTGACTCAGGAGCGTACTTCTGGCAAGTTTGACAACATAAAAACAAACAGGTAGACTTTTATTTGTCTCACTTTGATAATATATTACAACTGTGCAAAGTGTGTAGCTCTAAAGGCATAAATATCTGACAACATGCGGGAGATTGCTTAATATGGCAGGATTATATATACTGTGCTGAAGGTAGTATAAGGCATGTATAGAAGAGTAGTACACTGAGAAGATGTGATTCGAGAAATAAATCATACAAGTTGTAAAATGCGCTTCCGCTTCACCTGTCCTGAGGGATCATCGGTTGAAAACAGAGCACCAAGGTGGAAGCTTCTTATGACTGAATCAAATCACCAGATCCTGTAAAGGAGCATAAAGGGAGTTCGAGAGACAGTACCGTTCATACCTTTCATGTGATGACCATGGATAATACAACTATTTCAAAATGATGACAAAGCCAGAAGTAAATCCAGTACAGTTGTGGATTGGTATAGAGAAGAGTCTAATAGACAAAGAAACCAGAGGGAGGTCATACGCTTCCGTGCGGGTAGGATCATTGATTAGTTTAACCCAGGAAGTGAAATTAACTTGGGATAAAAACCTTTGTTGAAACACCACCAGATGTAATCATTGTGTTTGCGCCAATATACTATGACAATAGTTTCGTCTGTGAACGGAGAGCAAACGAGTATGAGTAGTTCAAAGTGTAATTATAAAATTTGTTGATACAATTGACTGCACTGGGTGCTTACTTGTGGATATTTATAAGGCTATGAATCTGGGTAATACCAAAGGAAAAGGCACCTGCTTGGCAGTATTTGGACGAATAAATAGATCATCATACCTAACATTGCTTGTGGGTTTACTGAGTTCCCCTATTCTAAGTCCATGACCAACATTGCCAATATTATGAAGAGACAGTTGCTGTATGAACGGTTGTATGTGGATACTTTAGAAACCATTGAATATTATACACCAGGTAAAGGTGGAGTTGCTACTTTTGAGAGGAAACCAAACAAAGAAAGACATTGTTAATAGTATAATTGTTGGACAGTATGAGATGTACCTGAAATATGACATTCACTGGATCAACATAAACAATGAAACATACAAAGACTGTAATAACATCCTAGAACCTGAGGAACTGTCACGGGTTAACTTGACCGAATTAGCTTACAATGATACTATTAATGTTCATTTCTATTATGAGGTTAAAGACATTCATTTAGATATTAAAGCTATAAATCATGCCTAAGGTGAAACGAGACCCTAGTGAAGAAAAAACTTACATTTTCTACATGGATTTTGTGGCATATTCAAAGGATGATTTAGCAGCTTGGGTGGATGCAATAGCTTGTTGACTTGTAAACTTATGATGATTTTGGTTGTGATTTTGAGGTATAATAAGATGAGGGTTGAGTTATCAATGTATTTGCAACAACAGTTGAAGAAATATGTTCTGAAATCTACAATGAAATGTCTGTAAACTATGTGAAATTAAGTTTTTTAAGAAACTCAAATGTTACATCAGAGACAAAATAGTGAAGGACAGTGTTCTTACTTATGAACGAATAATAGATTATTTTGATAAGTACAAGGGTATTCAAATTGAGCAGATTAATGGAGATGTTGAGTGTGTGCTTGGAGACTCATATTGGTACAAAGAGTTGAAAATTTAAGCGGTGCATATACCTGTTGAAATTGATAGATTACCTTTCAGTGAAGATGTAGTTAAATATTTTAAGGATTATAGTAGTAATTCACTGAAGTTTGTGGAGCGATCTAAGGCTGTTGTTTACTCTGTTTATGCAGTATCTTTAGAAAAGGTTTCTGTTAAATGGGTTCCTAAAGCATTTATTGGAAAAATAAGCACTAAAGCATTGGATGTGTCTAACTATATTGAGTTGATTACTACAGAGCCTGTGAATTTGAAAAATGTGTCAATTGCTATCGATTCTATAGGTAAGTTTGAAAAGGAAATTAAAGACGAAGTTATAGATTATGCCCAATATAGTGATAAAGGTGAGACTTATATTAAAGATATAAATGTAAAAAGTGGAGTCAACTATAATACAAAGGGAATAGCTTCTTTTGTGAAGATAATAGCTTATTTTAATTATTTAGAAGAAGATTCACTGTATAGGCCTGAGATAAATACTATCTATGATTGCACTGAAAGAAATAAAAGGGTTTTGTACTTCTTATATAAACACCCTGTTTTTATTGTTCAAAGTCTTGATTACGAACTTTATTGTAAATACAATTTGGAATGTGGATCAGAAACGGGAATTGTTGAAATCAAAATTGTTATAAAGAAAGATGGAAAATTTGAAAAGAATGGTTATAAATCAGCTTCAGTACCATCAAAGTGCAATGAAATAATTAAGGAAGCAGAAAATAAAGTGGCAGTCTTGTTTTATACAATATATTCAAAAAAGGATTTTCTATTAAAACTAGAGATCCATCACGCAGGAAAACATACATTTTGAATATTCCAAAATTTATAGTGCAAAGAATATCCTCTTGAGATACTTTGTGGATAAAGCGAAAAATGTTAAATATGCTGATGAAGCCATAAAATTCATATTGGGGGATTATAGTGAAGAACTAAAAAAACCTGAAGGTTATGCTATAAAGAATATTATAAAAGTTTATAGAACACAAGATGACATAATACTATCAGTTAGTAATTGTGGAATAGGCAATAAAGTATCAAATTTAGATAAGGAAATCAAGTATCATACTCGATACGTTGTGTCAGTGTTAAATCAAAAGGAAAAACTTGATGAGATTGCAAATTTCAACGAAAGGATTTTACCCAAAACTTGTGGAATTGAAGCAAAAGATATTAATATTGAAAACATTATTAAGAAAGACAGTAAAGGTATGGCTATGATTAATAGTATTGTATTTAATTTCAAAGATAAGATAAAAGAGCTGTGTTTAGAACATGAAGGAAAGAAGATCATATTCAATGAGTTTACCGTTGGAAAAGAGGATCTTGTTTGGTTTAAAGAGACAGTAATAGCCATTGAAGATACTATTAAGAATGTGCCTTACAAAGCCTTTACATCAAGACTGTCTAAAAATAAGGATGTGAATGATGCTTGGTACAAATATATACTAACCTCATCAATTTTCAAAAAGTTGACTGAAGATGAAATTAGAAAGAGTTTCACTGTGTACATAACTGAGATTAATCTTGAACCAGATAATGATAATGAGTATAAATCTTGTGATGATGATAATGAAATGAATATGAAAAGTAAACAAACAAATTTAGCTGATATTGATTTAGTTATTAAGACTGATGATGAAAGGGGAGAAAATCTAGATAAATCTATAGATGATTATAAAGCTGAAGAAAATGTTCAATTCCAGGTAAATGCTAGTCCTGTTAAAATACAAGATGAAATTGCTGAACCATATATTGATGATTCACAATGTGATAGAGAAGATATAGCTGATAGAAGAGAGAAGGCTAAAGATAAGGAGGCTGTTATAAAAGATAATGACAGTATGTCTGAAGAGCAACAAAATCCACCTTCTAAAATAAAAATTGAAAGGATTGAGAAAATGTGTTGTGCTGTATATGATCCAAAAAATGAGGATGAAATTCCAGAGGACCATGAGGAATTAAGAGAGAAAATAAAAAGCACTGAAGATATTGCAGAGGAGAATAAAGTGATAAAGAAGATAGTAGAAAAGAAAGATAGTGATGAGGGCACTAGAGGATGTAATGAAGAAAATGCGAGAGCTTATAAAACAGATAAAGAGTCTAAAGTTAAAAAATTAGAAGAGATTGAAGAAAAAAAGAAAGAAATAAAAACACCTGAAGACTTCGAAATTGATGAATCTAGAAAGGAGTTGCATGATGTGATTGCTAAAAGAGTGGATTTAAAGCAAGTGATTACATCTAAGGTGACAGTTCCAGTACAAATACAAGAGACAGAGCCACCAGTGTTGTTATTATCTGATGATGAGTTTTATTATACCATTAATTTAACGGAAATTGCACAAACTACCCCAAAAGATGAGTATGAAGACCTGCATGATAGTGAAATGAAATTGAGAGAGATTTATAGAACAGATGGTTTCAATGATGATAAATTGGATAAATTGATACGTCAAATTGATGCTAAAGAATATAGGGATATTGAAGAGCTAGTTGAAGATATTGATGAAGATGGATTAACTGAGGATGATGAAGAGGAGGAAGAAGAGGTAATACCAGAAGGGAACCCATTAAAGAAGGATTGTCCAAAGTTGATTACCAATTATCGAAAAAATAATGATGACCAAGGTGAAATAGATATAAGAGGTGATGAAGATGAAAATAGATTTGTAGACAGTCCTTCACGTTTAATGGATGATATTGATAAAAATGTTATTGAACAGGTGTCGAAGTATAGTACTACAAAGAACCAGTTGAAATTAATGAAAGGTCAGAGTGCTAAACAAGAAGAATTTACAGAGAAAGAAGAAGAGAAGATTGACACTGAAGAGGTGCTGGAACAAGAAGATAATAAAAATGCCCAAGAAATTGATGATAGTATTGAAGAGTCTGACATAGATGATGATGATGATGATAGAGATGTAAATGCAAAGGAAGAAATGGAGAAGTATGATACAACAGAAAGATTTGAAAAAGTGATTAAAGAAGAGGATGAGATGGCTGTTACTGAAAATAAAGATATTGATGATGAAACAAAAAATGATTTAATAGATGATAATGAAATGGAAGATAATTTAGATGTTATTCCGATTAAAGAGAAGGACCAACAGAAACAACAAATTGCGGATTTTAGGAAACAAATTGAGCCAAAGATTGATGATGAAGAGATTGAGGGAGACTATGCAGAATTTCCAAGTAAAATTGAAGAGCTTGAAAATATTGATCCAGGTTTTGATGATAGAAAAGGTCCAGATTATAGAACAGAAAGATTAATGAGTAAATTGGAAGATGAAATTGAAGTTCCTGATGACTGTCAAGAGGTAGAGGATGAAGAAGAAGATTATATTGAAAATCCTGAGGAAGAGAGAACTGAACTGGAAAAGGAGCAACAAGATGATTTTTCAGAGGGTACAAGTACTGTTATTAAAGCAGATGATGATGATTACATAGGTCATATAAGAAACAGAGCTGCGGAATGTGTGCTAGAAAATGAACCAAGTGATAGTATAGAATTGTCAAAGGAGAGCATTGAATTGGTTCCAGTAGATATACCAGAAGAGATGGATGGCGATGCTGATCAACTTACAATAGAGGATGTGAAGGGTAGGATTGAATCAATAGAAGCAGACAAAGAACCCATTGATCATGTTGAAGATGAACTTGAAAAAGAAGAACAAGATCAAGATGATCCAATTCAAGATGAGGAAGAAGTTGAAGATATCTATGATGAAGATATAGAACCAGCTCAAGAATGGATGCCAAGAGATGACAATTTTGAGGATGCATTGAGATCCGCTGAAACAGTCTCTATAGGCAAGGCTGAAAATGATGTCAAACCAACATTTGATATGATTGACCATGATAATGATATACATGAGGATGAGGAGAATAATGATGAAATGCTGAGTGAGGAGGACAATGAAAAGTTGATTGAGATGATTGAAGCGATAGATGATAGTAAAGGAGAAGATCATGTGCCTGAGAACAGAAAAGAGATTGAAGAAATGATTGAAACAAGAATTGAAGAAACAGATAAGAAAGGGGTGTTAAGAAAACAGATTACAAATGGAACAAGTGGAGAGATGGAACGAAAGGAAGATGAGTCTGGAGCGGAATCCACTGTGATAGATGAAGGCACTGATGATCCTGATGATATCGTGACTCAAGATGAAGTGGTTGAAATCGCTGAAAAATTTATGATAGAGAAGATTGATGAGGAAGCAGGAAAGATTGTTGGAATTGGACTAGAAGGATGTATTAGTCCTCAGGAGGGTTCCAAAATGGATAAAAGTGTTGTTGAGACTGGAGAGAAAGAGCATGATATTAAGGAGATGCTTGCAGAATTACCTGAAGAGGAGAGAGTAATTGAACAACAACAACCATGTGAAACAATAAGCAAAGATGATAATGAGTGTGGAGTTCAAGAAGAGGGTTTTTACAAGTGTATGACAGAATCAAAAGACGATGATGAGAATTATATTGAATTACAAGAAGTAGCCATAGAAGATGAAGATGATGAGATAGAAGAAGTCGTAAAGAAGTAA"""
    
    def _get_gene_annotations(self) -> dict:
        """
        Returns gene annotations for SARS-CoV-2 reference genome.
        Coordinates are 1-based (as in GenBank).
        """
        return {
            "genes": [
                {
                    "name": "ORF1ab",
                    "start": 266,
                    "end": 21555,
                    "product": "ORF1ab polyprotein",
                    "type": "CDS"
                },
                {
                    "name": "S",
                    "start": 21563,
                    "end": 25384,
                    "product": "surface glycoprotein (Spike)",
                    "type": "CDS"
                },
                {
                    "name": "ORF3a",
                    "start": 25393,
                    "end": 26220,
                    "product": "ORF3a protein",
                    "type": "CDS"
                },
                {
                    "name": "E",
                    "start": 26245,
                    "end": 26472,
                    "product": "envelope protein",
                    "type": "CDS"
                },
                {
                    "name": "M",
                    "start": 26523,
                    "end": 27191,
                    "product": "membrane glycoprotein",
                    "type": "CDS"
                },
                {
                    "name": "ORF6",
                    "start": 27202,
                    "end": 27387,
                    "product": "ORF6 protein",
                    "type": "CDS"
                },
                {
                    "name": "ORF7a",
                    "start": 27394,
                    "end": 27759,
                    "product": "ORF7a protein",
                    "type": "CDS"
                },
                {
                    "name": "ORF7b",
                    "start": 27756,
                    "end": 27887,
                    "product": "ORF7b protein",
                    "type": "CDS"
                },
                {
                    "name": "ORF8",
                    "start": 27894,
                    "end": 28259,
                    "product": "ORF8 protein",
                    "type": "CDS"
                },
                {
                    "name": "N",
                    "start": 28274,
                    "end": 29533,
                    "product": "nucleocapsid phosphoprotein",
                    "type": "CDS"
                },
                {
                    "name": "ORF10",
                    "start": 29558,
                    "end": 29674,
                    "product": "ORF10 protein",
                    "type": "CDS"
                }
            ],
            "reference": "NC_045512.2",
            "organism": "Severe acute respiratory syndrome coronavirus 2",
            "total_length": 29903
        }
    
    def verify_initialization(self):
        """Verify that database was initialized correctly."""
        logger.info("Verifying database initialization...")
        
        cursor = self.conn.cursor()
        
        # Check tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        expected_tables = [
            'analysis_history', 'kmer_index', 'mutation_rules',
            'mutations', 'reference_genome', 'variants'
        ]
        
        missing_tables = set(expected_tables) - set(tables)
        if missing_tables:
            logger.error(f"✗ Missing tables: {missing_tables}")
            return False
        logger.info(f"✓ All {len(expected_tables)} tables created")
        
        # Check reference genome
        cursor.execute("SELECT COUNT(*) FROM reference_genome")
        ref_count = cursor.fetchone()[0]
        if ref_count != 1:
            logger.error(f"✗ Expected 1 reference genome, found {ref_count}")
            return False
        logger.info("✓ Reference genome inserted")
        
        # Check mutation rules
        cursor.execute("SELECT COUNT(*) FROM mutation_rules")
        rules_count = cursor.fetchone()[0]
        if rules_count == 0:
            logger.error("✗ No mutation rules found")
            return False
        logger.info(f"✓ {rules_count} mutation rules inserted")
        
        # Check indexes
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        index_count = cursor.fetchone()[0]
        logger.info(f"✓ {index_count} indexes created")
    
        logger.info("✓ Database verification completed successfully")
        return True

    def main():
        """Main execution function."""
        import argparse
        parser = argparse.ArgumentParser(
            description='Initialize COVID-19 Variant Analysis database'
        )
        
        parser.add_argument(
            '--db-path',
            type=str,
            default='./data/variants.db',
            help='Path to SQLite database file (default: ./data/variants.db)'
        )

        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-initialization (drops existing tables)'
        )

        args = parser.parse_args()

        # Check if database exists
        db_path = Path(args.db_path)
        if db_path.exists() and not args.force:
            logger.warning(f"Database already exists at {db_path}")
            response = input("Do you want to re-initialize? This will delete all data. (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Initialization cancelled")
                return 1

        try:
            with DatabaseInitializer(args.db_path) as db:
                logger.info(f"Initializing database at: {db_path}")
        
                # Create schema
                db.create_schema()
        
                # Insert reference data
                db.insert_reference_genome()
                db.insert_mutation_rules()
        
                # Verify
                if db.verify_initialization():
                    logger.info("=" * 60)
                    logger.info("✓ Database initialization completed successfully!")
                    logger.info(f"✓ Database location: {db_path.absolute()}")
                    logger.info("=" * 60)
                else:
                    logger.error("Database verification failed")
                    return 1
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}", exc_info=True)
            return 1

        return 0
        

if __name__ == "__main__":
    DatabaseInitializer.main()