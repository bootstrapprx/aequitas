#!/bin/bash
# Database Health Verification Script
# Checks if Metatheos database is properly seeded and healthy

DB_PATH="/home/actpm/Documents/workfolder/aequitas/governance/.metatheos.db"

echo "=== Metatheos Database Health Check ==="
echo ""

# Check if database exists
if [ ! -d "$DB_PATH" ]; then
    echo "❌ Database does not exist at: $DB_PATH"
    echo "   Expected to be created on first startup"
    exit 1
fi

echo "✓ Database exists at: $DB_PATH"
echo ""

# Check database size
DB_SIZE=$(du -sh "$DB_PATH" | cut -f1)
echo "Database size: $DB_SIZE"
echo ""

# Check for manifest and clog directories
if [ -d "$DB_PATH/manifest" ] && [ -d "$DB_PATH/clog" ]; then
    echo "✓ Database structure valid (manifest + clog present)"
else
    echo "❌ Database structure invalid (missing manifest or clog)"
    exit 1
fi

# Count files in database
MANIFEST_FILES=$(find "$DB_PATH/manifest" -type f | wc -l)
CLOG_FILES=$(find "$DB_PATH/clog" -type f | wc -l)

echo "Manifest files: $MANIFEST_FILES"
echo "Changelog files: $CLOG_FILES"
echo ""

if [ $MANIFEST_FILES -eq 0 ] && [ $CLOG_FILES -eq 0 ]; then
    echo "⚠️  Database appears empty (no data files)"
    echo "   This is expected immediately after database creation"
    echo "   Data will be written on first operation"
elif [ $MANIFEST_FILES -gt 0 ] && [ $CLOG_FILES -gt 0 ]; then
    echo "✓ Database contains data"
else
    echo "⚠️  Unusual state: manifest=$MANIFEST_FILES, clog=$CLOG_FILES"
fi

echo ""
echo "=== Health Check Complete ===="
echo ""
echo "To test database functionality:"
echo "  1. Start Metatheos: cd metatheos-gui/src-tauri && cargo run --release"
echo "  2. Check logs for: '✓ Seeded X default phases with goals'"
echo "  3. Check logs for: '✓ Seeded detailed work items based on Aequitas progress'"
echo "  4. Expected: 50 goals, 40 work items"
echo ""
