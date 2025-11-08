#!/bin/bash

# Bash script to install GNU Screen

set -e  # Exit immediately on error

echo "🔍 Updating package lists..."
sudo apt update -y

echo "📦 Installing GNU Screen..."
sudo apt install -y screen

echo "✅ Verifying installation..."
if command -v screen &> /dev/null; then
    screen --version
    echo "🎉 GNU Screen installed successfully!"
else
    echo "❌ Installation failed. Please check your system configuration."
fi