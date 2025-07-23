#!/usr/bin/env python3
import pymongo
import urllib.parse
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError

def test_connection_methods():
    password = "P@ssw0rd!1"
    
    # Method 1: Using quote_plus (current approach)
    encoded_password1 = urllib.parse.quote_plus(password)
    uri1 = f"mongodb+srv://darknesscrawler:{encoded_password1}@marketing.agcqpdr.mongodb.net/?retryWrites=true&w=majority&appName=Marketing"
    
    # Method 2: Using quote with safe characters
    encoded_password2 = urllib.parse.quote(password, safe='')
    uri2 = f"mongodb+srv://darknesscrawler:{encoded_password2}@marketing.agcqpdr.mongodb.net/?retryWrites=true&w=majority&appName=Marketing"
    
    # Method 3: Manual encoding
    manual_encoded = password.replace('@', '%40').replace('!', '%21')
    uri3 = f"mongodb+srv://darknesscrawler:{manual_encoded}@marketing.agcqpdr.mongodb.net/?retryWrites=true&w=majority&appName=Marketing"
    
    # Method 4: Try without appName parameter
    uri4 = f"mongodb+srv://darknesscrawler:{encoded_password1}@marketing.agcqpdr.mongodb.net/?retryWrites=true&w=majority"
    
    methods = [
        ("quote_plus", uri1),
        ("quote with safe=''", uri2),
        ("manual encoding", uri3),
        ("without appName", uri4)
    ]
    
    for method_name, uri in methods:
        print(f"\nTrying method: {method_name}")
        print(f"Encoded password: {uri.split(':')[2].split('@')[0]}")
        
        try:
            client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
            # Test the connection
            client.admin.command('ping')
            print(f"✅ SUCCESS with {method_name}")
            
            # Try to access the database
            db = client.marketing
            collections = db.list_collection_names()
            print(f"Available collections: {collections}")
            
            client.close()
            return uri
            
        except OperationFailure as e:
            print(f"❌ Operation failed with {method_name}: {e}")
        except ServerSelectionTimeoutError as e:
            print(f"❌ Server selection timeout with {method_name}: {e}")
        except Exception as e:
            print(f"❌ Connection failed with {method_name}: {e}")
    
    return None

if __name__ == "__main__":
    print("Testing different MongoDB connection methods...")
    print("Original password: P@ssw0rd!1")
    
    successful_uri = test_connection_methods()
    
    if successful_uri:
        print(f"\n🎉 Successful connection string: {successful_uri}")
    else:
        print("\n❌ All connection methods failed.")
        print("\nPlease verify:")
        print("1. Username: darknesscrawler")
        print("2. Password: P@ssw0rd!1")
        print("3. Cluster name: marketing.agcqpdr.mongodb.net")
        print("4. IP whitelist includes your current IP or 0.0.0.0/0")
        print("5. User has proper database permissions")