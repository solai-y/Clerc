#!/bin/bash

echo "=== Testing processed_documents creation ==="

# Step 1: Create raw document
echo -e "\n=== Step 1: Creating raw document ==="
RAW_DOC_RESPONSE=$(curl -s -X POST http://localhost/documents \
  -H "Content-Type: application/json" \
  -d '{
    "document_name": "test-upload-'$(date +%s)'.pdf",
    "document_type": "PDF",
    "link": "https://example.com/test.pdf",
    "file_size": 2048,
    "status": "uploaded"
  }')

echo "Raw document response:"
echo "$RAW_DOC_RESPONSE"

# Extract document_id using grep and sed (no jq needed)
DOC_ID=$(echo "$RAW_DOC_RESPONSE" | grep -o '"document_id":[0-9]*' | grep -o '[0-9]*')
echo -e "\n✅ Created document_id: $DOC_ID"

if [ -z "$DOC_ID" ]; then
  echo "❌ ERROR: Failed to extract document_id"
  exit 1
fi

# Step 2: Create processed document
echo -e "\n=== Step 2: Creating processed document ==="
PROCESSED_RESPONSE=$(curl -s -X POST http://localhost/documents/processed \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": '$DOC_ID',
    "suggested_tags": [{"tag": "Test", "score": 0.9}],
    "threshold_pct": 80,
    "ocr_used": false,
    "processing_ms": 1000
  }')

echo "Processed document response:"
echo "$PROCESSED_RESPONSE"

# Check if it was successful
if echo "$PROCESSED_RESPONSE" | grep -q '"status":"success"'; then
  PROCESS_ID=$(echo "$PROCESSED_RESPONSE" | grep -o '"process_id":[0-9]*' | grep -o '[0-9]*')
  echo -e "\n✅ Created process_id: $PROCESS_ID"
else
  echo -e "\n❌ ERROR: Failed to create processed document"
  echo "Response indicates: $(echo "$PROCESSED_RESPONSE" | grep -o '"message":"[^"]*"')"
  exit 1
fi

# Step 3: Verify it was created
echo -e "\n=== Step 3: Fetching document to verify ==="
VERIFY_RESPONSE=$(curl -s http://localhost/documents/$DOC_ID)
echo "$VERIFY_RESPONSE"

echo -e "\n=== Test Complete ==="
if [ -n "$PROCESS_ID" ]; then
  echo "✅ SUCCESS: Document created with process_id $PROCESS_ID"
else
  echo "⚠️  WARNING: Could not verify process_id"
fi
