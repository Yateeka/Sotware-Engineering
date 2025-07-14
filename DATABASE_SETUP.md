# MongoDB Database Setup for Global Protest Tracker

Hey! This guide will help you get the MongoDB database up and running for our protest tracker app. Don't worry if you're new to MongoDB - I'll walk you through everything step by step.

## What's in the Database?

We've got 5 main collections (think of them like tables in SQL):

**protests** - Where all the protest data lives
- Stores location info so we can search by area
- Full text search so people can find protests by keywords
- Organized by status and categories for easy filtering

**users** - Everyone who uses the app
- Each person gets a unique email and username
- Passwords are properly encrypted (using bcrypt)
- Three types: regular users, verified activists, and admins

**alerts** - User notifications
- People can subscribe to get notified about protests
- Works with keywords, locations, and categories
- Can be set to immediate, daily, or weekly

**user_content** - Stuff users post
- Photos, reports, videos, updates about protests
- Has a moderation system (pending → approved/rejected)
- Tracks likes and reports

**admin_actions** - Keeps track of what admins do
- Every admin action gets logged here
- Useful for auditing and debugging

There are also a few smaller collections for user permissions and content interactions.

## Quick Start (The Easy Way)

You'll need:
- Python 3.8 or newer
- MongoDB (we'll help you install it)
- A virtual environment (trust me, it's worth it)

Here's what to do:

1. **Get to the right folder:**
   ```bash
   cd Protest/backend
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows folks: venv\Scripts\activate
   ```

3. **Run our setup script (it does most of the work):**
   ```bash
   python scripts/setup.py
   ```

4. **Initialize the database:**
   ```bash
   python scripts/init_database.py
   ```

5. **Fire up the app:**
   ```bash
   python app.py
   ```

That's it! If everything worked, you should see the app running at http://localhost:5000

## Manual Setup (If Scripts Don't Work)

Sometimes the automated scripts have issues. Here's how to do it manually:

**Step 1: Install Python packages**
```bash
pip install -r requirements.txt
```

**Step 2: Get MongoDB running**

*On Mac (with Homebrew):*
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

*On Ubuntu/Debian:*
```bash
sudo apt-get update
sudo apt-get install -y mongodb
sudo systemctl start mongod
```

*On Windows:*
Download from [MongoDB's website](https://www.mongodb.com/try/download/community) and follow their installer.

*Using Docker (if you're into that):*
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**Step 3: Create your config file**

Make a `.env` file in the backend folder:

```env
FLASK_CONFIG=development
SECRET_KEY=change-this-in-production
MONGODB_URI=mongodb://localhost:27017/protest_tracker
USE_TEST_DATA=false
API_RATE_LIMIT=100 per hour
CORS_ORIGINS=http://localhost:3000,http://localhost:5000
```

**Step 4: Set up the database**

```bash
python scripts/init_database.py
```

This script will:
- Create all the necessary database indexes
- Set up user permission types
- Create an admin user (admin@protesttracker.com / admin123)
- Add some sample protest data to play with

## Configuration Options

**MongoDB Connection Strings:**
- Local: `mongodb://localhost:27017/protest_tracker`
- MongoDB Atlas (cloud): `mongodb+srv://username:password@cluster.mongodb.net/protest_tracker`
- Docker: `mongodb://mongo:27017/protest_tracker`

**Environment Variables:**
- `MONGODB_URI` - Where your MongoDB is running
- `USE_TEST_DATA` - Set to `false` to use MongoDB (not the JSON test data)
- `SECRET_KEY` - Flask needs this for security stuff
- `FLASK_CONFIG` - Usually `development` or `production`

## Testing Everything Works

**Quick health check:**
```bash
curl http://localhost:5000/health
```

**Try some API calls:**
```bash
# See all protests
curl http://localhost:5000/api/protests

# Search for climate protests
curl http://localhost:5000/api/search/protests?q=climate

# Get a specific protest
curl http://localhost:5000/api/protests/1
```

**Check the database directly:**
```bash
mongo protest_tracker
> show collections
> db.protests.count()
> db.users.count()
```

## Admin Login Info

The setup creates an admin account for you:
- **Email:** admin@protesttracker.com
- **Password:** admin123

**Please change this password before going live!**

## Sample Data

We've included some test data to get you started:
- 3 example protests (climate march, workers rally, education protest)
- A test user account
- An example alert subscription
- All the user permission types set up

## Troubleshooting

**"Can't connect to MongoDB"**
- Make sure MongoDB is actually running: `sudo systemctl status mongod`
- Double-check your connection string in the `.env` file
- Sometimes it's a firewall issue

**"Import errors" or "Module not found"**
- Are you in the `backend/` folder?
- Did you activate your virtual environment?
- Try running `pip install -r requirements.txt` again

**"Permission denied"**
- Make the scripts executable: `chmod +x scripts/*.py`
- Check if MongoDB has the right permissions on its data folder

**"Port already in use"**
- MongoDB uses port 27017, Flask uses 5000
- If something else is using these ports, you can change them in the config

**Need to start over?**
```bash
mongo protest_tracker
> db.dropDatabase()
> exit
python scripts/init_database.py
```

## Moving Data Around

If you need to backup or move data:

**Backup:**
```bash
mongodump --db protest_tracker --out backup/
```

**Restore:**
```bash
mongorestore --db protest_tracker backup/protest_tracker/
```

## Performance Notes

The database is set up with indexes to make things fast:
- Location searches use a geospatial index
- Text searches are indexed on titles and descriptions
- Date queries are optimized
- User lookups are super fast with unique indexes
- Alert matching is efficient

## Security Stuff

Before going live:
- Change that default admin password!
- Use environment variables for secrets
- Turn on MongoDB authentication
- Use SSL for database connections
- Set up rate limiting on the API
- Keep dependencies updated

## Need Help?

If you're stuck:
1. Check the troubleshooting section above
2. Look at the app logs for error messages
3. Check MongoDB logs (usually in `/var/log/mongodb/mongod.log`)
4. Ask the team or check GitHub issues

## Useful Links

- [MongoDB docs](https://docs.mongodb.com/) - if you want to dive deeper
- [PyMongo docs](https://pymongo.readthedocs.io/) - Python MongoDB driver
- [Flask docs](https://flask.palletsprojects.com/) - our web framework
