#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🔍 Updating package index..."
sudo apt update -y

echo "📦 Installing prerequisites..."
sudo apt install -y curl software-properties-common ca-certificates gnupg

echo "🌐 Fetching NodeSource setup script for the latest Node.js..."
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -

echo "⬇️ Installing Node.js..."
sudo apt install -y nodejs

echo "🧩 Installing build tools (optional but recommended)..."
sudo apt install -y build-essential

echo "✅ Node.js installation complete!"
echo "-----------------------------------"
node -v
npm -v
echo "-----------------------------------"
echo "🚀 Node.js and npm are ready to use."
