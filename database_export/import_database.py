#!/usr/bin/env python3
"""
Contentry Database Import Script
Imports JSON files into MongoDB

Usage:
    python import_database.py

Environment Variables:
    MONGO_URL - MongoDB connection string (default: mongodb://localhost:27017)
    DB_NAME   - Target database name (default: contentry)
"""

import os
import json
import glob
from pymongo import MongoClient
from datetime import datetime

def import_database():
    # Configuration
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'contentry')
    
    print("=" * 60)
    print("CONTENTRY DATABASE IMPORT")
    print("=" * 60)
    print(f"\nConnecting to: {mongo_url}")
    print(f"Database: {db_name}")
    print("-" * 60)
    
    try:
        # Connect to MongoDB
        client = MongoClient(mongo_url)
        db = client[db_name]
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!\n")
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("\nPlease check:")
        print("  1. MongoDB is running")
        print("  2. MONGO_URL environment variable is correct")
        return False
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all JSON files (except _summary.json)
    json_files = glob.glob(os.path.join(script_dir, "*.json"))
    json_files = [f for f in json_files if not f.endswith('_summary.json')]
    
    if not json_files:
        print("❌ No JSON files found in the current directory")
        return False
    
    print(f"Found {len(json_files)} collection files to import:\n")
    
    total_imported = 0
    
    for json_file in sorted(json_files):
        collection_name = os.path.basename(json_file).replace('.json', '')
        
        try:
            with open(json_file, 'r') as f:
                documents = json.load(f)
            
            if not documents:
                print(f"  ⏭️  {collection_name}: (empty - skipped)")
                continue
            
            # Drop existing collection and insert new data
            db[collection_name].drop()
            
            if isinstance(documents, list) and len(documents) > 0:
                result = db[collection_name].insert_many(documents)
                count = len(result.inserted_ids)
                total_imported += count
                print(f"  ✅ {collection_name}: {count} documents imported")
            else:
                print(f"  ⏭️  {collection_name}: (no valid documents)")
                
        except json.JSONDecodeError as e:
            print(f"  ❌ {collection_name}: Invalid JSON - {e}")
        except Exception as e:
            print(f"  ❌ {collection_name}: Error - {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ IMPORT COMPLETE!")
    print(f"   Total documents imported: {total_imported}")
    print(f"   Database: {db_name}")
    print("=" * 60)
    
    # Verify import
    print("\n📊 Verification:")
    print("-" * 40)
    for col_name in db.list_collection_names():
        count = db[col_name].count_documents({})
        print(f"  • {col_name}: {count} documents")
    
    client.close()
    return True

if __name__ == "__main__":
    import_database()
