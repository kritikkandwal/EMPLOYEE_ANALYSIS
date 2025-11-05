#!/usr/bin/env python3
"""
Test script to verify database connectivity and basic operations
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.user import User, db

def test_database():
    """Test database connectivity and basic operations"""
    try:
        # Create app and push context
        app = create_app()
        
        with app.app_context():
            # Test database connection
            print("✓ Testing database connection...")
            
            # Count users
            user_count = User.query.count()
            print(f"✓ Current users in database: {user_count}")
            
            # Test creating a user
            test_user = User(
                username='test_user',
                email='test@example.com',
                department='Testing',
                position='Tester'
            )
            test_user.set_password('test123')
            
            db.session.add(test_user)
            db.session.commit()
            print("✓ Successfully created test user")
            
            # Verify user was created
            verified_user = User.query.filter_by(email='test@example.com').first()
            if verified_user and verified_user.check_password('test123'):
                print("✓ User verification successful")
            else:
                print("✗ User verification failed")
            
            # Clean up
            db.session.delete(verified_user)
            db.session.commit()
            print("✓ Cleanup completed")
            
            return True
            
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

if __name__ == '__main__':
    print("Starting database test...")
    if test_database():
        print("🎉 All tests passed! Database is working correctly.")
    else:
        print("❌ Database test failed. Please check the configuration.")