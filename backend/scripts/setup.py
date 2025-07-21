#!/usr/bin/env python3
"""
Setup script for the Global Protest Tracker
Gets everything installed and ready to go
"""

import os
import sys
import subprocess
import platform


def run_command(command, description):
    """Run a command and let the user know if it worked or not."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False


def check_python_version():
    """Make sure we have a recent enough Python version."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def check_mongodb():
    """See if MongoDB is installed and running."""
    print("🍃 Checking MongoDB availability...")
    
    # Try to connect to MongoDB
    try:
        import pymongo
        client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        client.server_info()  # Will raise an exception if can't connect
        print("✅ MongoDB is running and accessible")
        client.close()
        return True
    except Exception as e:
        print("⚠️  MongoDB not accessible. Please ensure MongoDB is installed and running.")
        print("   Installation instructions:")
        
        system = platform.system().lower()
        if system == "darwin":  # macOS
            print("   macOS: brew install mongodb-community")
            print("   Then: brew services start mongodb-community")
        elif system == "linux":
            print("   Ubuntu/Debian: sudo apt-get install mongodb")
            print("   CentOS/RHEL: sudo yum install mongodb-org")
            print("   Then: sudo systemctl start mongod")
        elif system == "windows":
            print("   Windows: Download from https://www.mongodb.com/try/download/community")
        
        print("   Or use MongoDB Atlas (cloud): https://www.mongodb.com/atlas")
        return False


def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Not in a virtual environment. Consider creating one:")
        print("   python -m venv venv")
        print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        print("   Then run this setup script again.")
        
        response = input("Continue anyway? (y/N): ").lower()
        if response != 'y':
            return False
    
    # Install requirements
    requirements_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'requirements.txt')
    return run_command(f"pip install -r {requirements_path}", "Installing dependencies")


def create_env_file():
    """Create a .env file with default configuration."""
    print("⚙️  Creating environment configuration...")
    
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    if os.path.exists(env_path):
        print("✅ .env file already exists")
        return True
    
    env_content = """# Global Protest Tracker Configuration
# Copy this file to .env and modify as needed

# Flask Configuration
FLASK_CONFIG=development
SECRET_KEY=dev-secret-key-change-in-production

# Database Configuration
MONGODB_URI=mongodb://localhost:27017/protest_tracker
USE_TEST_DATA=false

# API Configuration
API_RATE_LIMIT=100 per hour
CORS_ORIGINS=http://localhost:3000,http://localhost:5000

# Optional: External API Keys (for future features)
# GDELT_API_KEY=your-gdelt-api-key
# NEWS_API_KEY=your-news-api-key
# GEONAMES_USERNAME=your-geonames-username

# Email Configuration (for alerts - future feature)
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USE_TLS=true
# MAIL_USERNAME=your-email@gmail.com
# MAIL_PASSWORD=your-app-password
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"✅ Created .env file at {env_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("🌍 GLOBAL PROTEST TRACKER - SETUP")
    print("=" * 60)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install dependencies
    if success and not install_dependencies():
        success = False
    
    # Check MongoDB
    if success:
        mongodb_available = check_mongodb()
        if not mongodb_available:
            print("⚠️  MongoDB not available. You can still continue setup,")
            print("   but you'll need to install and start MongoDB before running the app.")
    
    # Create environment file
    if success and not create_env_file():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("1. Ensure MongoDB is running")
        print("2. Initialize the database: python scripts/init_database.py")
        print("3. Start the Flask app: python app.py")
        print("4. Test the API at http://localhost:5000/health")
        print("\n🔧 Optional:")
        print("- Edit .env file to customize configuration")
        print("- Set up the frontend (see frontend/README.md)")
    else:
        print("❌ SETUP FAILED!")
        print("=" * 60)
        print("Please resolve the issues above and run setup again.")
    
    print("\n📚 Documentation:")
    print("- API Documentation: Check the blueprints/ folder")
    print("- Database Models: Check the models/ folder")
    print("- Configuration: Check config.py and .env file")


if __name__ == "__main__":
    main()
