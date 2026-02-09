# Contentry Database Setup Guide

## Overview
This package contains the MongoDB database export for the Contentry application.

**Database Name:** `contentry`  
**Export Date:** December 15, 2024  

---

## Package Contents

```
database_export/
├── README.md                    # This file
├── import_database.py           # Python import script
├── import_database.sh           # Bash import script (using mongoimport)
├── _summary.json                # Export metadata
├── changelog.json               # Changelog collection
├── content_analyses.json        # Content analysis history
├── documentation_changelog.json # Documentation updates
├── phone_otps.json              # Phone OTP records
├── user_roles.json              # User role definitions
└── users.json                   # User accounts
```

---

## Prerequisites

1. **MongoDB** installed and running (v4.4+ recommended)
2. **Python 3.8+** with `pymongo` or `motor` (for Python import script)

---

## Method 1: Using Python Script (Recommended)

### Step 1: Install dependencies
```bash
pip install pymongo
```

### Step 2: Set your MongoDB connection string
```bash
# Default local MongoDB
export MONGO_URL="mongodb://localhost:27017"
export DB_NAME="contentry"

# Or use your own connection string
export MONGO_URL="mongodb://username:password@host:port"
export DB_NAME="contentry"
```

### Step 3: Run the import script
```bash
python import_database.py
```

---

## Method 2: Using mongoimport (CLI)

### Step 1: Ensure MongoDB tools are installed
```bash
# Ubuntu/Debian
sudo apt-get install mongodb-database-tools

# macOS
brew install mongodb-database-tools

# Or download from: https://www.mongodb.com/try/download/database-tools
```

### Step 2: Run the import script
```bash
# Make the script executable
chmod +x import_database.sh

# Run with default settings (localhost:27017, database: contentry)
./import_database.sh

# Or specify custom connection
./import_database.sh "mongodb://username:password@host:port" "your_database_name"
```

---

## Method 3: Manual Import

If you prefer to import collections individually:

```bash
# Import each collection
mongoimport --uri="mongodb://localhost:27017" --db=contentry --collection=users --file=users.json --jsonArray
mongoimport --uri="mongodb://localhost:27017" --db=contentry --collection=content_analyses --file=content_analyses.json --jsonArray
mongoimport --uri="mongodb://localhost:27017" --db=contentry --collection=documentation_changelog --file=documentation_changelog.json --jsonArray
mongoimport --uri="mongodb://localhost:27017" --db=contentry --collection=changelog --file=changelog.json --jsonArray
mongoimport --uri="mongodb://localhost:27017" --db=contentry --collection=phone_otps --file=phone_otps.json --jsonArray
mongoimport --uri="mongodb://localhost:27017" --db=contentry --collection=user_roles --file=user_roles.json --jsonArray
```

---

## Collection Details

| Collection | Documents | Description |
|------------|-----------|-------------|
| `users` | 1 | User accounts and profiles |
| `content_analyses` | 15 | Content analysis history and results |
| `documentation_changelog` | 1 | Documentation version history |
| `changelog` | 0 | Application changelog |
| `phone_otps` | 0 | Phone verification OTPs |
| `user_roles` | 0 | Role-based access control |

---

## Test Credentials

After importing, you can log in with:

- **Email:** `demo@test.com`
- **Password:** `password123`

---

## Environment Variables

Your application will need these environment variables:

```bash
# Required
MONGO_URL=mongodb://localhost:27017
DB_NAME=contentry

# For the full application, you may also need:
# OPENAI_API_KEY=your_key
# GOOGLE_VISION_API_KEY=your_key
# GOOGLE_CREDENTIALS_BASE64=your_service_account_base64
```

---

## Verification

After import, verify the data was imported correctly:

```bash
# Using mongosh
mongosh contentry --eval "db.getCollectionNames()"
mongosh contentry --eval "db.users.countDocuments({})"

# Or using Python
python -c "from pymongo import MongoClient; db = MongoClient()['contentry']; print(db.list_collection_names())"
```

---

## Troubleshooting

### Connection refused
- Ensure MongoDB is running: `sudo systemctl start mongod`
- Check MongoDB is listening: `netstat -tlnp | grep 27017`

### Authentication failed
- Verify your connection string includes correct username/password
- Check the user has readWrite permissions on the target database

### Import errors
- Ensure JSON files are valid: `python -m json.tool users.json`
- Check file permissions: `ls -la *.json`

---

## Support

If you encounter issues, check:
1. MongoDB logs: `tail -f /var/log/mongodb/mongod.log`
2. Connection string format
3. Database user permissions

