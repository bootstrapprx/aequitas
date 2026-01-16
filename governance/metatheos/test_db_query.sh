#!/bin/bash
# Quick diagnostic: What's actually in the phase table?

cd /home/actpm/Documents/workfolder/aequitas/metatheos

# Test 1: Can we query phases from CLI?
echo "=== Test 1: CLI query phases ==="
timeout 3 ./target/debug/metatheos list-phases 2>&1 | head -20 || echo "(CLI command may not exist)"

# Test 2: Check DB file exists
echo -e "\n=== Test 2: DB file check ==="
ls -lh /home/actpm/Documents/workfolder/aequitas/governance/.metatheos.db/ 2>&1 | head -5

# Test 3: What does the Tauri backend log say?
echo -e "\n=== Test 3: Check if store.get_all_phases() works ==="
echo "Launching GUI briefly to test query..."
