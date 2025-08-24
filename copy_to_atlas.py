#!/usr/bin/env python3
"""
Script to copy local MongoDB data to MongoDB Atlas cluster
"""

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import sys
from datetime import datetime

def connect_to_local_mongodb():
    """Connect to local MongoDB"""
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ Connected to local MongoDB")
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ Failed to connect to local MongoDB: {e}")
        return None

def connect_to_atlas_mongodb(atlas_uri):
    """Connect to MongoDB Atlas"""
    try:
        client = MongoClient(atlas_uri, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas")
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ Failed to connect to MongoDB Atlas: {e}")
        return None

def copy_database(local_client, atlas_client, local_db_name, atlas_db_name):
    """Copy all collections from local to Atlas"""
    local_db = local_client[local_db_name]
    atlas_db = atlas_client[atlas_db_name]
    
    # Get all collections from local database
    collections = local_db.list_collection_names()
    
    if not collections:
        print(f"⚠️  No collections found in local database '{local_db_name}'")
        return
    
    print(f"\n📋 Found {len(collections)} collections in local database:")
    for coll in collections:
        count = local_db[coll].count_documents({})
        print(f"  - {coll}: {count} documents")
    
    print(f"\n🚀 Starting copy to Atlas database '{atlas_db_name}'...")
    
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
            
            # Clear existing collection in Atlas (optional)
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
    print(f"Collections in Atlas database '{atlas_db_name}':")
    for coll in atlas_collections:
        count = atlas_db[coll].count_documents({})
        print(f"  - {coll}: {count} documents")

def main():
    print("🔄 MongoDB Local to Atlas Copy Tool")
    print("=" * 50)
    
    # Get Atlas connection string
    atlas_uri = input("\n🔗 Enter your MongoDB Atlas connection string: ").strip()
    if not atlas_uri:
        print("❌ Atlas connection string is required!")
        return
    
    # Get database names
    local_db_name = input("📁 Enter local database name (default: EcommerceSU2): ").strip() or "EcommerceSU2"
    atlas_db_name = input("☁️  Enter Atlas database name (default: EcommerceSU2): ").strip() or "EcommerceSU2"
    
    print(f"\n📋 Configuration:")
    print(f"  Local DB: {local_db_name}")
    print(f"  Atlas DB: {atlas_db_name}")
    
    # Connect to local MongoDB
    local_client = connect_to_local_mongodb()
    if not local_client:
        return
    
    # Connect to Atlas MongoDB
    atlas_client = connect_to_atlas_mongodb(atlas_uri)
    if not atlas_client:
        local_client.close()
        return
    
    try:
        # Copy the database
        copy_database(local_client, atlas_client, local_db_name, atlas_db_name)
        
        print(f"\n✅ Database copy completed successfully!")
        print(f"Your data is now available in MongoDB Atlas database: {atlas_db_name}")
        
    except Exception as e:
        print(f"\n❌ Error during copy process: {e}")
    
    finally:
        # Close connections
        local_client.close()
        atlas_client.close()
        print("\n🔌 Connections closed")

if __name__ == "__main__":
    main()
