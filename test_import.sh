#!/bin/bash
# Test photo import with valid payload

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Testing Photo Import ===${NC}\n"

# Step 1: Login and get token
echo -e "${YELLOW}Step 1: Logging in...${NC}"
echo "Enter username:"
read USERNAME
echo "Enter password:"
read -s PASSWORD

LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Login failed!${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Login successful${NC}"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Step 2: Import photo
echo -e "${YELLOW}Step 2: Importing photo...${NC}"
IMPORT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/photos/new-photo" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @test_import_payload.json)

# Check if successful
if echo "$IMPORT_RESPONSE" | jq -e '.photo_hothash' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Import successful!${NC}"
    echo ""
    echo "Response:"
    echo "$IMPORT_RESPONSE" | jq .
else
    echo -e "${RED}❌ Import failed!${NC}"
    echo ""
    echo "Response:"
    echo "$IMPORT_RESPONSE" | jq .
    exit 1
fi
