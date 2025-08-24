#!/usr/bin/env python3
"""
Script to check MongoDB database and hash any unhashed passwords.
This script connects directly to MongoDB and checks all users in the 'users' collection.
"""

import os
import sys
import bcrypt
from pymongo import MongoClient
from datetime import datetime

# MongoDB Configuration
MONGODB_CONFIG = {
    'host': 'localhost',
    'port': 27017,
    'database': 'EcommerceSU2',
    'collection': 'users'
}

def connect_to_mongodb():
    """Connect to MongoDB and return the users collection"""
    try:
        client = MongoClient(
            host=MONGODB_CONFIG['host'],
            port=MONGODB_CONFIG['port']
        )
        db = client[MONGODB_CONFIG['database']]
        users_collection = db[MONGODB_CONFIG['collection']]
        
        # Test connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB")
        return users_collection
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None

def is_password_hashed(password):
    """Check if a password is already hashed with bcrypt"""
    if not password:
        return False
    
    # bcrypt hashed passwords start with '$2b$' and are 60 characters long
    return (isinstance(password, str) and 
            password.startswith('$2b$') and 
            len(password) == 60)

def hash_password(password):
    """Hash a password using bcrypt"""
    if not password:
        return None
    
    # Encode password to bytes
    password_bytes = password.encode('utf-8')
    
    # Hash the password
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    
    # Return as string
    return hashed.decode('utf-8')

def check_and_hash_passwords():
    """Main function to check and hash passwords"""
    print("🔍 Checking MongoDB database for unhashed passwords...")
    print("=" * 60)
    
    # Connect to MongoDB
    users_collection = connect_to_mongodb()
    if not users_collection:
        return
    
    try:
        # Get all users
        users = list(users_collection.find())
        
        if not users:
            print("📭 No users found in the database.")
            return
        
        print(f"📊 Found {len(users)} users in the database")
        print("-" * 60)
        
        unhashed_count = 0
        hashed_count = 0
        updated_count = 0
        
        for user in users:
            username = user.get('username', 'Unknown')
            password = user.get('password', '')
            
            print(f"👤 User: {username}")
            
            if is_password_hashed(password):
                print(f"   ✅ Password is already hashed")
                hashed_count += 1
            else:
                print(f"   ❌ Password is NOT hashed: {password}")
                unhashed_count += 1
                
                # Ask user if they want to hash this password
                response = input(f"   🔐 Hash password '{password}' for user '{username}'? (y/n): ").lower().strip()
                
                if response in ['y', 'yes']:
                    # Hash the password
                    hashed_password = hash_password(password)
                    
                    if hashed_password:
                        # Update the user in MongoDB
                        result = users_collection.update_one(
                            {'_id': user['_id']},
                            {'$set': {'password': hashed_password}}
                        )
                        
                        if result.modified_count > 0:
                            print(f"   ✅ Successfully hashed password for {username}")
                            updated_count += 1
                        else:
                            print(f"   ❌ Failed to update password for {username}")
                    else:
                        print(f"   ❌ Failed to hash password for {username}")
                else:
                    print(f"   ⏭️  Skipped hashing password for {username}")
            
            print()
        
        # Summary
        print("=" * 60)
        print("📈 SUMMARY:")
        print(f"   Total users: {len(users)}")
        print(f"   Already hashed: {hashed_count}")
        print(f"   Unhashed: {unhashed_count}")
        print(f"   Updated: {updated_count}")
        
        if unhashed_count > 0 and updated_count == 0:
            print("\n💡 Tip: You can run this script again to hash remaining passwords.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def hash_all_passwords_to_123():
    """Hash all passwords to '123'"""
    print("🔐 Hashing all passwords to '123'...")
    print("=" * 60)
    
    # Connect to MongoDB
    users_collection = connect_to_mongodb()
    if not users_collection:
        return
    
    try:
        # Hash the password "123"
        hashed_password = hash_password("123")
        
        if not hashed_password:
            print("❌ Failed to hash password '123'")
            return
        
        # Update all users
        result = users_collection.update_many(
            {},  # Update all documents
            {'$set': {'password': hashed_password}}
        )
        
        print(f"✅ Successfully updated {result.modified_count} users")
        print(f"📊 Total users in database: {result.matched_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("🔧 MongoDB Password Checker & Hasher")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'hash-all':
            # Hash all passwords to "123"
            hash_all_passwords_to_123()
        elif command == 'check':
            # Check and hash passwords interactively
            check_and_hash_passwords()
        else:
            print("❌ Unknown command. Use 'check' or 'hash-all'")
    else:
        # Default: check and hash passwords interactively
        check_and_hash_passwords()

if __name__ == "__main__":
    main()





