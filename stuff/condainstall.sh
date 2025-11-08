#!/usr/bin/env bash
set -e  # Exit on error

# === CONFIG ===
CONDA_DIR="$HOME/miniconda3"
CONDA_INSTALLER="Miniconda3-latest-Linux-x86_64.sh"
CONDA_URL="https://repo.anaconda.com/miniconda/$CONDA_INSTALLER"

# === INSTALL ===
echo "Downloading Miniconda installer..."
wget -q $CONDA_URL -O /tmp/$CONDA_INSTALLER

echo "Running Miniconda installer..."
bash /tmp/$CONDA_INSTALLER -b -p "$CONDA_DIR"

echo "Initializing Conda..."
source "$CONDA_DIR/bin/activate"
conda init bash

echo "Cleaning up..."
rm /tmp/$CONDA_INSTALLER

echo "✅ Conda installed successfully at $CONDA_DIR"
echo "To start using Conda, run: source ~/.bashrc"
