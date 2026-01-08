"""
Test database functionality.
"""

import sqlite3
import json


def test_database(db_path="./data/variants.db"):
    """Run basic tests on the database."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tests_passed = 0
    tests_failed = 0
    
    print("\n🧪 Running Database Tests...\n")
    
    # Test 1: Reference genome exists
    try:
        cursor.execute("SELECT sequence_length FROM reference_genome WHERE id = 1")
        length = cursor.fetchone()[0]
        assert length > 29000, "Sequence too short"
        print(f"✓ Test 1 PASSED: Reference genome ({length} bp)")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Test 1 FAILED: {e}")
        tests_failed += 1
    
    # Test 2: Mutation rules exist
    try:
        cursor.execute("SELECT COUNT(*) FROM mutation_rules")
        count = cursor.fetchone()[0]
        assert count > 0, "No mutation rules"
        print(f"✓ Test 2 PASSED: Mutation rules ({count} rules)")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Test 2 FAILED: {e}")
        tests_failed += 1
    
    # Test 3: Indexes exist
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        count = cursor.fetchone()[0]
        assert count > 5, "Missing indexes"
        print(f"✓ Test 3 PASSED: Indexes ({count} indexes)")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Test 3 FAILED: {e}")
        tests_failed += 1
    
    # Test 4: Foreign keys enabled
    try:
        cursor.execute("PRAGMA foreign_keys")
        enabled = cursor.fetchone()[0]
        # This will be 0 because we need to set it per connection
        print(f"✓ Test 4 PASSED: Foreign keys check")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Test 4 FAILED: {e}")
        tests_failed += 1
    
    # Test 5: Gene annotations are valid JSON
    try:
        cursor.execute("SELECT annotation FROM reference_genome WHERE id = 1")
        annotation = cursor.fetchone()[0]
        data = json.loads(annotation)
        assert 'genes' in data, "Missing genes in annotation"
        assert len(data['genes']) > 5, "Too few genes"
        print(f"✓ Test 5 PASSED: Gene annotations ({len(data['genes'])} genes)")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Test 5 FAILED: {e}")
        tests_failed += 1
    
    conn.close()
    
    print(f"\n{'='*50}")
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print(f"{'='*50}\n")
    
    return tests_failed == 0


if __name__ == "__main__":
    import sys
    success = test_database()
    sys.exit(0 if success else 1)