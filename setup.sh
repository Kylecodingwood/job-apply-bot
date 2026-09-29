#!/bin/bash

# Job Apply Bot - Setup Script
# This script helps you create your profile.json from the template

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$SCRIPT_DIR/profile.template.json"
PROFILE="$SCRIPT_DIR/profile.json"

echo ""
echo "========================================"
echo "  Job Apply Bot - Profile Setup"
echo "========================================"
echo ""

if [ -f "$PROFILE" ]; then
  read -p "profile.json already exists. Overwrite? (y/N): " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
fi

echo "Copy template and open for editing..."
cp "$TEMPLATE" "$PROFILE"

# Try to open in a sensible editor
if [ -n "$VISUAL" ]; then
  $VISUAL "$PROFILE"
elif [ -n "$EDITOR" ]; then
  $EDITOR "$PROFILE"
elif command -v code &>/dev/null; then
  code "$PROFILE"
elif command -v nano &>/dev/null; then
  nano "$PROFILE"
else
  echo "Please edit profile.json manually: $PROFILE"
fi

echo ""
echo "========================================"
echo "  Next Steps"
echo "========================================"
echo ""
echo "1. Make sure Playwright MCP is set up:"
echo "   claude mcp add playwright npx @playwright/mcp@latest"
echo ""
echo "2. Add your CV path to profile.json:"
echo "   \"cv_path\": \"/path/to/your/CV.pdf\""
echo ""
echo "3. Start Claude in this directory:"
echo "   cd $(dirname "$PROFILE") && claude"
echo ""
echo "4. Paste a job application URL and Claude will fill it for you!"
echo ""
