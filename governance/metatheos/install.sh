#!/bin/bash
# Aequitas Meta Engine - Installation Script

set -e

echo "🔧 Aequitas Meta Engine - Installation"
echo "========================================"
echo ""

# Check for Rust
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust is not installed."
    echo "📥 Install Rust from: https://rustup.rs/"
    echo "   Or run: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

echo "✓ Rust found: $(rustc --version)"
echo ""

# Build release binary
echo "🔨 Building Meta Engine..."
cargo build --release

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✓ Build successful"
echo ""

# Get absolute path to binary
BIN_PATH="$(pwd)/target/release/meta-cli"
GOVERNANCE_PATH="$(realpath ../governance 2>/dev/null || echo "./governance")"

echo "📍 Binary location: $BIN_PATH"
echo "📂 Governance folder: $GOVERNANCE_PATH"
echo ""

# Offer to create alias
echo "🔗 Installation options:"
echo "  1. Add alias to ~/.bashrc (recommended)"
echo "  2. Add alias to ~/.zshrc"
echo "  3. Create symlink to /usr/local/bin/meta (requires sudo)"
echo "  4. Manual setup (show instructions)"
echo ""

read -p "Choose option (1-4): " choice

case $choice in
    1)
        ALIAS_CMD="alias meta='$BIN_PATH --root $GOVERNANCE_PATH'"
        if ! grep -q "alias meta=" ~/.bashrc 2>/dev/null; then
            echo "" >> ~/.bashrc
            echo "# Aequitas Meta Engine" >> ~/.bashrc
            echo "$ALIAS_CMD" >> ~/.bashrc
            echo "✓ Added alias to ~/.bashrc"
            echo "⚠ Run: source ~/.bashrc (or restart terminal)"
        else
            echo "⚠ Alias already exists in ~/.bashrc"
        fi
        ;;
    2)
        ALIAS_CMD="alias meta='$BIN_PATH --root $GOVERNANCE_PATH'"
        if ! grep -q "alias meta=" ~/.zshrc 2>/dev/null; then
            echo "" >> ~/.zshrc
            echo "# Aequitas Meta Engine" >> ~/.zshrc
            echo "$ALIAS_CMD" >> ~/.zshrc
            echo "✓ Added alias to ~/.zshrc"
            echo "⚠ Run: source ~/.zshrc (or restart terminal)"
        else
            echo "⚠ Alias already exists in ~/.zshrc"
        fi
        ;;
    3)
        sudo ln -sf "$BIN_PATH" /usr/local/bin/meta
        echo "✓ Created symlink: /usr/local/bin/meta"
        echo "⚠ Note: You'll need to pass --root flag when using 'meta' command"
        ;;
    4)
        echo ""
        echo "📋 Manual setup instructions:"
        echo ""
        echo "Add this to your shell config (~/.bashrc or ~/.zshrc):"
        echo ""
        echo "  alias meta='$BIN_PATH --root $GOVERNANCE_PATH'"
        echo ""
        echo "Or create a symlink:"
        echo ""
        echo "  sudo ln -s $BIN_PATH /usr/local/bin/meta"
        echo ""
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "✅ Installation complete!"
echo ""
echo "📚 Quick start:"
echo "  meta audit              # Validate governance"
echo "  meta goals --status active  # List active goals"
echo "  meta today              # Open today's daily note"
echo "  meta phase current      # Show current phase"
echo ""
echo "📖 Full documentation: README.md"
