#!/bin/bash
# CRO Trilemma Environment Setup Script
# Configures the experimental environment for reproducible evaluation

set -e  # Exit on error

echo "================================================"
echo "CRO Trilemma Environment Setup"
echo "================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Python version
    if ! python3 --version | grep -E "3\.(10|11|12)" > /dev/null; then
        print_error "Python 3.10+ required"
        exit 1
    fi
    
    # Check available memory
    available_mem=$(free -g | awk '/^Mem:/{print $7}')
    if [ "$available_mem" -lt 8 ]; then
        print_warning "Less than 8GB RAM available. Large experiments may fail."
    fi
    
    # Check CPU cores
    cpu_cores=$(nproc)
    if [ "$cpu_cores" -lt 4 ]; then
        print_warning "Less than 4 CPU cores detected. Parallel execution will be limited."
    fi
    
    print_status "System requirements check complete"
}

# Create virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Skipping creation."
    else
        python3 -m venv venv
        print_status "Virtual environment created"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip wheel setuptools
    print_status "Virtual environment ready"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Core dependencies
    pip install numpy==1.23.5
    pip install scipy==1.9.3
    pip install pandas==1.5.2
    pip install matplotlib==3.6.2
    pip install seaborn==0.12.2
    
    # Cryptographic libraries
    pip install cryptography==39.0.0
    pip install pycryptodome==3.17.0
    
    # Machine learning dependencies
    pip install scikit-learn==1.1.3
    pip install torch==1.13.0 --index-url https://download.pytorch.org/whl/cpu
    
    # Additional utilities
    pip install pyyaml==6.0
    pip install tqdm==4.64.1
    pip install joblib==1.2.0
    
    print_status "Python dependencies installed"
}

# Install system dependencies
install_system_deps() {
    print_status "Checking system dependencies..."
    
    # Check if running with sudo privileges
    if [ "$EUID" -ne 0 ]; then
        print_warning "Not running as root. Some system dependencies may require manual installation."
        return
    fi
    
    # Detect OS
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        apt-get update
        apt-get install -y \
            build-essential \
            libgmp-dev \
            libssl-dev \
            libffi-dev \
            git \
            cmake
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS/Fedora
        yum install -y \
            gcc \
            gcc-c++ \
            gmp-devel \
            openssl-devel \
            libffi-devel \
            git \
            cmake
    else
        print_warning "Unknown OS. Please install dependencies manually."
    fi
    
    print_status "System dependencies checked"
}

# Clone and build cryptographic libraries
setup_crypto_libs() {
    print_status "Setting up cryptographic libraries..."
    
    # Create libs directory
    mkdir -p libs
    cd libs
    
    # Clone libsnark for Groth16
    if [ ! -d "libsnark" ]; then
        git clone https://github.com/scipr-lab/libsnark.git
        cd libsnark
        git checkout a477c9b
        git submodule update --init --recursive
        mkdir -p build && cd build
        cmake ..
        make -j$(nproc)
        cd ../..
        print_status "libsnark built successfully"
    else
        print_warning "libsnark already exists"
    fi
    
    # Clone PQClean for Dilithium
    if [ ! -d "PQClean" ]; then
        git clone https://github.com/PQClean/PQClean.git
        cd PQClean
        git checkout v0.7.3
        make -C crypto_sign/dilithium3/clean
        cd ..
        print_status "PQClean built successfully"
    else
        print_warning "PQClean already exists"
    fi
    
    cd ..
}

# Setup data directories
setup_directories() {
    print_status "Creating project directories..."
    
    directories=(
        "data/contexts"
        "data/proofs"
        "results/figures"
        "results/logs"
        "cache"
        "models"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        print_status "Created $dir"
    done
}

# Download pre-trained models (if available)
download_models() {
    print_status "Checking for pre-trained models..."
    
    # Download ML adversary models
    model_url="https://github.com/cro-trilemma/models/releases/download/v1.0/"
    models=(
        "cnn_adversary.pth"
        "transformer_adversary.pth"
    )
    
    for model in "${models[@]}"; do
        if [ ! -f "models/$model" ]; then
            print_status "Downloading $model..."
            wget -q "$model_url$model" -O "models/$model" || {
                print_warning "Failed to download $model. Training from scratch will be required."
            }
        fi
    done
}

# Configure Git for reproducibility
setup_git() {
    print_status "Configuring Git for reproducibility..."
    
    # Initialize git if not already initialized
    if [ ! -d ".git" ]; then
        git init
        git add .
        git commit -m "Initial commit for CRO Trilemma evaluation"
    fi
    
    # Create .gitignore
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Data and results
data/proofs/
results/
cache/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF
    
    print_status "Git configured"
}

# Verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    # Test Python imports
    python3 -c "
import numpy
import scipy
import pandas
import torch
print('All Python imports successful')
    " || {
        print_error "Python package imports failed"
        exit 1
    }
    
    # Test main script
    if python3 evaluate_protocol.py --help > /dev/null 2>&1; then
        print_status "Main evaluation script verified"
    else
        print_error "Main evaluation script not working"
        exit 1
    fi
    
    print_status "Installation verified successfully"
}

# Main setup flow
main() {
    echo "Starting environment setup..."
    echo "This may take several minutes."
    echo ""
    
    check_requirements
    setup_venv
    install_python_deps
    install_system_deps
    setup_crypto_libs
    setup_directories
    download_models
    setup_git
    verify_installation
    
    echo ""
    echo "================================================"
    echo -e "${GREEN}Environment setup complete!${NC}"
    echo "================================================"
    echo ""
    echo "To activate the environment, run:"
    echo "  source venv/bin/activate"
    echo ""
    echo "To run a basic test:"
    echo "  python evaluate_protocol.py --protocol groth16 --trials 100"
    echo ""
    echo "To reproduce all paper results:"
    echo "  python run_all_experiments.py"
    echo ""
}

# Run main function
main