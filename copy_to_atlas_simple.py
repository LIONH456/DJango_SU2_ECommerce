#!/usr/bin/env python3
"""
Simple script to copy local MongoDB data to MongoDB Atlas cluster
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import sys

# Configuration - UPDATE THESE VALUES
ATLAS_CONNECTION_STRING = "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
LOCAL_DB_NAME = "EcommerceSU2"
ATLAS_DB_NAME = "EcommerceSU2"

def main():
    print("🔄 MongoDB Local to Atlas Copy Tool")
    print("=" * 50)
    
    # Connect to local MongoDB
    print("🔌 Connecting to local MongoDB...")
    try:
        local_client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        local_client.admin.command('ping')
        print("✅ Connected to local MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect to local MongoDB: {e}")
        return
    
    # Connect to Atlas MongoDB
    print("🔌 Connecting to MongoDB Atlas...")
    try:
        atlas_client = MongoClient(ATLAS_CONNECTION_STRING, serverSelectionTimeoutMS=10000)
        atlas_client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas: {e}")
        local_client.close()
        return
    
    # Get database references
    local_db = local_client[LOCAL_DB_NAME]
    atlas_db = atlas_client[ATLAS_DB_NAME]
    
    # Get all collections from local database
    collections = local_db.list_collection_names()
    
    if not collections:
        print(f"⚠️  No collections found in local database '{LOCAL_DB_NAME}'")
        local_client.close()
        atlas_client.close()
        return
    
    print(f"\n📋 Found {len(collections)} collections in local database:")
    for coll in collections:
        count = local_db[coll].count_documents({})
        print(f"  - {coll}: {count} documents")
    
    print(f"\n🚀 Starting copy to Atlas database '{ATLAS_DB_NAME}'...")
    
    total_documents = 0
    successful_collections = 0
    
    for collection_name in collections:
        try:
            print(f"\n📦 Copying collection: {collection_name}")
            
            # Get all documents from local collection
            documents = list(local_db[collection_name].find({}))
            
            if not documents:
                print(f"  ⚠️  Collection '{collection_name}' is empty, skipping...")
                continue
            
            # Clear existing collection in Atlas
            atlas_db[collection_name].drop()
            
            # Insert documents into Atlas
            if documents:
                result = atlas_db[collection_name].insert_many(documents)
                inserted_count = len(result.inserted_ids)
                total_documents += inserted_count
                successful_collections += 1
                print(f"  ✅ Successfully copied {inserted_count} documents")
            
        except Exception as e:
            print(f"  ❌ Error copying collection '{collection_name}': {e}")
    
    print(f"\n🎉 Copy completed!")
    print(f"  - Collections copied: {successful_collections}/{len(collections)}")
    print(f"  - Total documents copied: {total_documents}")
    
    # Verify the copy
    print(f"\n🔍 Verifying copy...")
    atlas_collections = atlas_db.list_collection_names()
    print(f"Collections in Atlas database '{ATLAS_DB_NAME}':")
    for coll in atlas_collections:
        count = atlas_db[coll].count_documents({})
        print(f"  - {coll}: {count} documents")
    
    # Close connections
    local_client.close()
    atlas_client.close()
    print("\n🔌 Connections closed")
    print(f"\n✅ Database copy completed successfully!")
    print(f"Your data is now available in MongoDB Atlas database: {ATLAS_DB_NAME}")

if __name__ == "__main__":
    main()
