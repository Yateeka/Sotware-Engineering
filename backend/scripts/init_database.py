#!/usr/bin/env python3
"""
Database setup script for the Global Protest Tracker
Sets up the database and adds some sample data to get started
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    DatabaseConnection, 
    protest_model, 
    user_model, 
    alert_model, 
    user_content_model, 
    admin_action_model
)


def init_database():
    """Set up the database with all the indexes and basic structure."""
    print("🚀 Initializing Global Protest Tracker Database...")
    
    try:
        # Test database connection
        db_connection = DatabaseConnection()
        db = db_connection.db
        print(f"✅ Connected to database: {db.name}")
        
        # The indexes are automatically created when models are initialized
        print("✅ Database indexes created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False


def seed_sample_data():
    """Add some example data so you have something to work with."""
    print("\n📊 Seeding database with sample data...")
    
    try:
        # Load test data
        test_data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'test',
            'test_data.json'
        )
        
        with open(test_data_path, 'r') as f:
            test_data = json.load(f)
        
        # Seed protests
        print("  📍 Seeding protests...")
        for protest_data in test_data.get('protests', []):
            try:
                # Convert test data format to MongoDB format
                protest_doc = {
                    'title': protest_data['title'],
                    'description': protest_data['description'],
                    'location': {
                        'city': protest_data['city'],
                        'country': protest_data['country'],
                        'coordinates': [protest_data['longitude'], protest_data['latitude']]
                    },
                    'categories': protest_data['categories'],
                    'start_date': protest_data['start_date'],
                    'participant_count': protest_data['participant_count'],
                    'status': protest_data['status'],
                    'verified': True,
                    'source': 'seed_data'
                }
                
                result = protest_model.create(protest_doc)
                print(f"    ✅ Created protest: {protest_data['title']}")
                
            except Exception as e:
                print(f"    ⚠️  Error creating protest {protest_data['title']}: {e}")
        
        # Seed users
        print("  👥 Seeding users...")
        for user_data in test_data.get('users', []):
            try:
                # Add a default password for test users
                user_doc = {
                    'username': user_data['username'],
                    'email': user_data['email'],
                    'password': 'testpassword123',  # Default test password
                    'user_type_id': user_data.get('user_type_id', 'regular'),
                    'verified': user_data.get('verified', False)
                }
                
                result = user_model.create(user_doc)
                print(f"    ✅ Created user: {user_data['username']}")
                
            except Exception as e:
                print(f"    ⚠️  Error creating user {user_data['username']}: {e}")
        
        # Seed alerts
        print("  🔔 Seeding alerts...")
        for alert_data in test_data.get('alerts', []):
            try:
                alert_doc = {
                    'user_id': alert_data['user_id'],
                    'keywords': alert_data['keywords'],
                    'location_filter': alert_data.get('location_filter', ''),
                    'frequency': 'immediate'
                }
                
                result = alert_model.create(alert_doc)
                print(f"    ✅ Created alert for user: {alert_data['user_id']}")
                
            except Exception as e:
                print(f"    ⚠️  Error creating alert for {alert_data['user_id']}: {e}")
        
        print("✅ Sample data seeded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error seeding sample data: {e}")
        return False


def create_admin_user():
    """Create an admin account so you can manage the app."""
    print("\n👑 Creating default admin user...")
    
    try:
        admin_data = {
            'username': 'admin',
            'email': 'admin@protesttracker.com',
            'password': 'admin123',  # Change this in production!
            'user_type_id': 'admin',
            'verified': True
        }
        
        # Check if admin already exists
        existing_admin = user_model.find_by_email(admin_data['email'])
        if existing_admin:
            print("  ⚠️  Admin user already exists")
            return True
        
        result = user_model.create(admin_data)
        print(f"  ✅ Created admin user: {admin_data['username']}")
        print(f"  📧 Email: {admin_data['email']}")
        print(f"  🔑 Password: {admin_data['password']} (CHANGE THIS IN PRODUCTION!)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False


def verify_setup():
    """Verify that the database setup was successful."""
    print("\n🔍 Verifying database setup...")
    
    try:
        # Check collections exist and have data
        db_connection = DatabaseConnection()
        db = db_connection.db
        
        collections = {
            'protests': db.protests.count_documents({}),
            'users': db.users.count_documents({}),
            'alerts': db.alerts.count_documents({}),
            'user_types': db.user_types.count_documents({})
        }
        
        print("  📊 Collection counts:")
        for collection, count in collections.items():
            print(f"    {collection}: {count} documents")
        
        # Test a basic query
        sample_protest = protest_model.find_with_filters()
        if sample_protest:
            print(f"  ✅ Sample protest query successful: Found {len(sample_protest)} protests")
        
        # Test user authentication
        admin_user = user_model.find_by_email('admin@protesttracker.com')
        if admin_user:
            print("  ✅ Admin user found")
        
        print("✅ Database verification completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying database setup: {e}")
        return False


def main():
    """Main function to run the database initialization."""
    print("=" * 60)
    print("🌍 GLOBAL PROTEST TRACKER - DATABASE INITIALIZATION")
    print("=" * 60)
    
    # Step 1: Initialize database
    if not init_database():
        print("❌ Database initialization failed. Exiting.")
        sys.exit(1)
    
    # Step 2: Create admin user
    if not create_admin_user():
        print("❌ Admin user creation failed. Exiting.")
        sys.exit(1)
    
    # Step 3: Seed sample data
    if not seed_sample_data():
        print("⚠️  Sample data seeding failed, but continuing...")
    
    # Step 4: Verify setup
    if not verify_setup():
        print("⚠️  Database verification failed, but setup may still be functional")
    
    print("\n" + "=" * 60)
    print("🎉 DATABASE INITIALIZATION COMPLETED!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Start your Flask application: python app.py")
    print("2. Test the API endpoints")
    print("3. Change the default admin password!")
    print("4. Configure environment variables for production")
    print("\n🔗 Default Admin Credentials:")
    print("   Email: admin@protesttracker.com")
    print("   Password: admin123")
    print("\n⚠️  IMPORTANT: Change the admin password in production!")


if __name__ == "__main__":
    main()
