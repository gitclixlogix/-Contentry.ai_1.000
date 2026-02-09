#!/bin/bash
# Contentry Database Import Script
# Imports JSON files into MongoDB using mongoimport

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MONGO_URL="${1:-mongodb://localhost:27017}"
DB_NAME="${2:-contentry}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================================"
echo "CONTENTRY DATABASE IMPORT (using mongoimport)"
echo "============================================================"
echo ""
echo "MongoDB URL: $MONGO_URL"
echo "Database: $DB_NAME"
echo "Source directory: $SCRIPT_DIR"
echo "------------------------------------------------------------"
echo ""

# Check if mongoimport is available
if ! command -v mongoimport &> /dev/null; then
    echo -e "${RED}❌ mongoimport not found!${NC}"
    echo ""
    echo "Please install MongoDB Database Tools:"
    echo "  Ubuntu/Debian: sudo apt-get install mongodb-database-tools"
    echo "  macOS: brew install mongodb-database-tools"
    echo "  Download: https://www.mongodb.com/try/download/database-tools"
    exit 1
fi

echo -e "${GREEN}✅ mongoimport found${NC}"
echo ""

# Import each collection
COLLECTIONS=(
    "users"
    "content_analyses"
    "documentation_changelog"
    "changelog"
    "phone_otps"
    "user_roles"
)

TOTAL_IMPORTED=0

for collection in "${COLLECTIONS[@]}"; do
    FILE="$SCRIPT_DIR/${collection}.json"
    
    if [ ! -f "$FILE" ]; then
        echo -e "${YELLOW}⏭️  ${collection}: file not found - skipped${NC}"
        continue
    fi
    
    # Check if file is empty array
    if [ "$(cat "$FILE")" = "[]" ]; then
        echo -e "${YELLOW}⏭️  ${collection}: empty collection - skipped${NC}"
        continue
    fi
    
    # Import the collection
    mongoimport \
        --uri="$MONGO_URL" \
        --db="$DB_NAME" \
        --collection="$collection" \
        --file="$FILE" \
        --jsonArray \
        --drop \
        2>/dev/null
    
    if [ $? -eq 0 ]; then
        COUNT=$(grep -o '"id"' "$FILE" 2>/dev/null | wc -l)
        echo -e "${GREEN}✅ ${collection}: imported successfully${NC}"
        ((TOTAL_IMPORTED++))
    else
        echo -e "${RED}❌ ${collection}: import failed${NC}"
    fi
done

echo ""
echo "============================================================"
echo -e "${GREEN}✅ IMPORT COMPLETE!${NC}"
echo "   Collections processed: $TOTAL_IMPORTED"
echo "   Database: $DB_NAME"
echo "============================================================"
echo ""
echo "To verify, run:"
echo "  mongosh $DB_NAME --eval \"db.getCollectionNames()\""
