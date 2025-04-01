#!/bin/bash
set -e  # Exit immediately if any command fails

# Download a pre-built wheel for dlib (Python 3.11 compatible)
# Note: You may need to find the correct wheel URL for your Python version
DLIB_WHEEL_URL="https://files.pythonhosted.org/packages/0e/ce/f8a3cff33ac03a8219768f0694c5d703c8e037e6aba2e865f9bae22ed63c/dlib-19.24.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"

# Create a temporary directory for the wheel
TMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TMP_DIR"

# Download the wheel
echo "Downloading dlib wheel..."
wget -q $DLIB_WHEEL_URL -O "$TMP_DIR/dlib.whl"

# Install dlib from the wheel
echo "Installing dlib..."
pip install --no-cache-dir "$TMP_DIR/dlib.whl"

# Clean up
rm -rf "$TMP_DIR"
echo "Cleaned up temporary files"

# Now install the rest of the requirements
echo "Installing other requirements..."
pip install -r requirements.txt

echo "Installation completed successfully!"