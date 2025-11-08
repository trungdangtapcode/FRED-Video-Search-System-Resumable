#!/bin/bash

# Bash script to install Docker Engine on Ubuntu/Debian
# Tested on Ubuntu 20.04, 22.04, 24.04

set -e  # Exit on error

echo "🔍 Updating package index..."
sudo apt update -y

echo "📦 Installing required dependencies..."
sudo apt install -y ca-certificates curl gnupg lsb-release apt-transport-https software-properties-common

echo "🧩 Adding Docker’s official GPG key..."
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo "💾 Setting up the Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "🔄 Updating package index again..."
sudo apt update -y

echo "🐳 Installing Docker Engine, CLI, and containerd..."
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "⚙️ Enabling and starting Docker service..."
sudo systemctl enable docker
sudo systemctl start docker

echo "👤 Adding current user ($USER) to the docker group..."
sudo usermod -aG docker $USER

echo "✅ Verifying Docker installation..."
docker --version
docker compose version || true

echo "🎉 Docker installed successfully!"
echo "ℹ️ You may need to log out and back in for 'docker' group changes to take effect."
