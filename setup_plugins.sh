#!/bin/bash
# Setup script to install external Arelle plugins required for XBRL validation

set -e  # Exit on error

echo "==================================="
echo "XBRL Validator Plugin Setup"
echo "==================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLUGIN_DIR="$SCRIPT_DIR/Arelle/arelle/plugin"

echo "Plugin directory: $PLUGIN_DIR"
echo ""

# Check if Arelle dependencies are installed
echo "Checking Arelle dependencies..."
if ! python3 -c "import regex" 2>/dev/null; then
    echo "Installing Arelle dependencies..."
    pip install -q -r "$SCRIPT_DIR/Arelle/requirements.txt"
    echo "✓ Arelle dependencies installed"
else
    echo "✓ Arelle dependencies already installed"
fi
echo ""

# Clone EDGAR plugin
echo "Installing EDGAR plugin..."
if [ -d "$PLUGIN_DIR/EDGAR" ]; then
    echo "  EDGAR plugin already exists, updating..."
    cd "$PLUGIN_DIR/EDGAR"
    git pull -q
else
    echo "  Cloning EDGAR plugin from GitHub..."
    cd "$PLUGIN_DIR"
    git clone -q --depth 1 https://github.com/Arelle/EDGAR.git
fi
echo "✓ EDGAR plugin installed"
echo ""

# Clone and setup xule plugin
echo "Installing xule plugin..."
if [ -d "$PLUGIN_DIR/xule" ]; then
    echo "✓ xule plugin already installed"
else
    echo "  Cloning xule repository from GitHub..."
    cd "$PLUGIN_DIR"
    
    # Clone the full xule repository temporarily
    git clone -q --depth 1 https://github.com/xbrlus/xule.git xule_temp
    
    # Move the xule engine to the plugin directory
    echo "  Setting up xule engine..."
    mv xule_temp/plugin/xule ./xule
    
    # Clean up temporary directory
    rm -rf xule_temp
fi
echo "✓ xule plugin installed"
echo ""

# Verification
echo "Verifying xule plugin structure..."
if [ ! -d "$PLUGIN_DIR/xule" ]; then
    echo "  ERROR: xule plugin installation failed"
    exit 1
fi
echo "✓ xule plugin structure verified"
echo ""

# Verify installations
echo "==================================="
echo "Verifying plugin installations..."
echo "==================================="
echo ""

cd "$SCRIPT_DIR/Arelle"

# Test EDGAR plugin
echo "Testing EDGAR plugin..."
if python3 arelleCmdLine.py --plugins "EDGAR/render" --help 2>&1 | grep -q "Edgar"; then
    echo "✓ EDGAR plugin is working"
else
    echo "✗ EDGAR plugin test failed"
    exit 1
fi

# Test xule plugin (indirectly through EDGAR)
echo "Testing xule integration..."
if python3 arelleCmdLine.py --plugins "EDGAR/render" --help 2>&1 | grep -q "formulaParam"; then
    echo "✓ xule integration is working"
else
    echo "✗ xule integration test failed"
    exit 1
fi

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "You can now use the validator:"
echo "  python validate_filing.py <filing-url-or-path>"
echo ""
echo "For help:"
echo "  python validate_filing.py --help"
echo ""
