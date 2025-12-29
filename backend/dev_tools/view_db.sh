#!/bin/bash
# Quick script to view MongoDB database

echo "=== Historical Figures Database ==="
echo ""

# Count documents
COUNT=$(mongosh talkwith --quiet --eval "db.historical_figures.countDocuments({})")
echo "Total figures: $COUNT"
echo ""

# List all figures
mongosh talkwith --quiet --eval "
db.historical_figures.find().forEach(function(doc) {
    print('Person: ' + doc.person_name);
    print('ID: ' + doc._id);
    print('Questions answered: ' + Object.keys(doc.answers || {}).length);
    print('---');
})
"

echo ""
echo "To view full details, use: mongosh talkwith"
echo "Then run: db.historical_figures.find().pretty()"

