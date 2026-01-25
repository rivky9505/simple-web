#!/bin/bash

# SSH connection script for Linux/Mac
# Usage: ./connect-vm.sh /path/to/keyfile

set -e

# Default values
USERNAME="azureuser"
IP_ADDRESS="108.143.33.48"

# Check if key file is provided
if [ -z "$1" ]; then
    echo "Error: Key file path is required"
    echo "Usage: $0 /path/to/keyfile"
    exit 1
fi

KEY_FILE="$1"

# Check if key file exists
if [ ! -f "$KEY_FILE" ]; then
    echo "Error: Key file not found: $KEY_FILE"
    exit 1
fi

# Set correct permissions on key file
chmod 600 "$KEY_FILE"
echo "Set key file permissions to 600"

# Check if SSH is available
if ! command -v ssh &> /dev/null; then
    echo "Error: SSH client not found"
    exit 1
fi

echo "Connecting to Azure VM..."
echo "IP Address: $IP_ADDRESS"
echo "Username: $USERNAME"
echo "Key File: $KEY_FILE"
echo ""

# Connect via SSH
ssh -i "$KEY_FILE" "$USERNAME@$IP_ADDRESS"
