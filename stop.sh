#!/bin/bash

echo "================================================"
echo "  Fashion Recommendation System - Shutdown"
echo "================================================"
echo ""

echo "Stopping services..."
echo ""

# Stop backend
if pkill -f "uvicorn app.main:app" 2>/dev/null; then
  echo "✓ Backend stopped"
else
  echo "⚠ No backend process found"
fi

# Stop frontend
if pkill -f "node.*vite" 2>/dev/null; then
  echo "✓ Frontend stopped"
else
  echo "⚠ No frontend process found"
fi

sleep 2

# Verify
echo ""
echo "Verification:"

if pgrep -f "uvicorn app.main:app" > /dev/null; then
  echo "✗ Backend still running"
else
  echo "✓ Backend stopped"
fi

if pgrep -f "node.*vite" > /dev/null; then
  echo "✗ Frontend still running"
else
  echo "✓ Frontend stopped"
fi

echo ""
echo "Shutdown complete!"
echo ""

