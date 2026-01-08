"""
Utility script to query and inspect the database.
"""

import sqlite3
import json
from pathlib import Path
from tabulate import tabulate


def query_database(db_path: str = "./data/variants.db"):
    """Interactive database query tool."""
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("COVID-19 Variant Database Inspector")
    print("="*60)
    
    # Show reference genome info
    cursor.execute("SELECT * FROM reference_genome")
    ref = cursor.fetchone()
    if ref:
        print(f"\n📋 Reference Genome:")
        print(f"  Accession: {ref['accession_id']}")
        print(f"  Length: {ref['sequence_length']:,} bp")
        
        annotation = json.loads(ref['annotation'])
        print(f"  Genes: {len(annotation['genes'])}")
    
    # Show mutation rules
    cursor.execute("SELECT COUNT(*) as count FROM mutation_rules")
    rules_count = cursor.fetchone()['count']
    print(f"\n🔬 Mutation Rules: {rules_count}")
    
    cursor.execute("SELECT rule_name, severity FROM mutation_rules")
    rules = cursor.fetchall()
    if rules:
        print(tabulate(
            [(r['rule_name'], r['severity']) for r in rules],
            headers=['Rule Name', 'Severity'],
            tablefmt='simple'
        ))
    
    # Show variants count
    cursor.execute("SELECT COUNT(*) as count FROM variants")
    variants_count = cursor.fetchone()['count']
    print(f"\n🦠 Variants: {variants_count}")
    
    if variants_count > 0:
        cursor.execute("""
            SELECT lineage, who_label, collection_date, country
            FROM variants
            ORDER BY collection_date DESC
            LIMIT 10
        """)
        variants = cursor.fetchall()
        print("\nMost Recent Variants:")
        print(tabulate(
            [(v['lineage'], v['who_label'], v['collection_date'], v['country']) 
             for v in variants],
            headers=['Lineage', 'WHO Label', 'Date', 'Country'],
            tablefmt='simple'
        ))
    
    # Show database size
    cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
    size = cursor.fetchone()['size']
    print(f"\n💾 Database Size: {size / 1024 / 1024:.2f} MB")
    
    conn.close()
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="./data/variants.db")
    
    args = parser.parse_args()
    
    try:
        query_database(args.db)
    except Exception as e:
        print(f"Error: {e}")
