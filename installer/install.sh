#!/bin/bash

################################################################################
# WavesAI Installer Script
# Version: 3.0
# Description: Installs WavesAI system-wide with wavesctl command
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Installation directories
INSTALL_DIR="$HOME/.wavesai"
BIN_DIR="/usr/local/bin"
MODELS_DIR="$INSTALL_DIR/models"
CONFIG_DIR="$INSTALL_DIR/config"
MODULES_DIR="$INSTALL_DIR/modules"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║              WavesAI Installation Script                ║"
    echo "║              JARVIS-like AI Assistant                    ║"
    echo "║              Version 3.0                                 ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${CYAN}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

################################################################################
# Check Requirements
################################################################################

check_requirements() {
    print_step "Checking system requirements..."
    
    # Check if running on Linux
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_error "This installer only supports Linux systems"
        exit 1
    fi
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        echo "Please install Python 3.8 or higher"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    REQUIRED_VERSION="3.8"
    
    if (( $(echo "$PYTHON_VERSION < $REQUIRED_VERSION" | bc -l) )); then
        print_error "Python version $PYTHON_VERSION is too old"
        echo "Please install Python 3.8 or higher"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION detected"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_warning "pip3 is not installed. Installing..."
        sudo pacman -S --noconfirm python-pip || {
            print_error "Failed to install pip3"
            exit 1
        }
    fi
    
    print_success "All requirements met"
}

################################################################################
# Create Virtual Environment
################################################################################

create_venv() {
    print_step "Creating Python virtual environment..."
    
    VENV_DIR="$INSTALL_DIR/venv"
    
    # Check if venv module is available
    if ! python3 -m venv --help &> /dev/null; then
        print_warning "python3-venv not installed. Installing..."
        sudo pacman -S --noconfirm python-virtualenv || {
            print_error "Failed to install python-virtualenv"
            exit 1
        }
    fi
    
    # Create virtual environment
    python3 -m venv "$VENV_DIR" || {
        print_error "Failed to create virtual environment"
        exit 1
    }
    
    print_success "Virtual environment created at $VENV_DIR"
}

################################################################################
# Install Python Dependencies
################################################################################

install_dependencies() {
    print_step "Installing Python dependencies in virtual environment..."
    
    VENV_DIR="$INSTALL_DIR/venv"
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate" || {
        print_error "Failed to activate virtual environment"
        exit 1
    }
    
    print_success "Virtual environment activated"
    
    # Upgrade pip
    print_step "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    # Required packages
    PACKAGES=(
        "llama-cpp-python"
        "psutil"
        "requests"
        "beautifulsoup4"
        "wikipedia"
    )
    
    for package in "${PACKAGES[@]}"; do
        print_step "Installing $package..."
        pip install "$package" --quiet || {
            print_error "Failed to install $package"
            deactivate
            exit 1
        }
    done
    
    print_success "All dependencies installed in virtual environment"
    
    # Deactivate virtual environment
    deactivate
}

################################################################################
# Create Directory Structure
################################################################################

create_directories() {
    print_step "Creating directory structure..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$MODELS_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$CONFIG_DIR/logs"
    mkdir -p "$MODULES_DIR"
    
    print_success "Directory structure created"
}

################################################################################
# Copy Files
################################################################################

copy_files() {
    print_step "Copying WavesAI files..."
    
    # Get the script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    SOURCE_DIR="$(dirname "$SCRIPT_DIR")"
    
    # Copy main files
    if [ -f "$SOURCE_DIR/wavesai.py" ]; then
        cp "$SOURCE_DIR/wavesai.py" "$INSTALL_DIR/"
        print_success "Copied wavesai.py"
    else
        print_error "wavesai.py not found in $SOURCE_DIR"
        exit 1
    fi
    
    # Copy system prompt
    if [ -f "$SOURCE_DIR/system_prompt.txt" ]; then
        cp "$SOURCE_DIR/system_prompt.txt" "$INSTALL_DIR/"
        print_success "Copied system_prompt.txt"
    else
        print_warning "system_prompt.txt not found, will be created on first run"
    fi
    
    # Copy config
    if [ -f "$SOURCE_DIR/config/config.json" ]; then
        cp "$SOURCE_DIR/config/config.json" "$CONFIG_DIR/"
        print_success "Copied config.json"
    else
        print_warning "config.json not found, will be created on first run"
    fi
    
    # Copy modules
    if [ -d "$SOURCE_DIR/modules" ]; then
        cp -r "$SOURCE_DIR/modules/"* "$MODULES_DIR/" 2>/dev/null || true
        print_success "Copied modules"
    else
        print_warning "modules directory not found"
    fi
    
    # Copy documentation
    for doc in README.md ADVANCED_FEATURES_ADDED.md CONFIRMATION_SYSTEM.md CONVERSATIONAL_ERROR_HANDLING.md INTELLIGENT_ERROR_HANDLING.md SUDO_ACCESS_MANAGEMENT.md; do
        if [ -f "$SOURCE_DIR/$doc" ]; then
            cp "$SOURCE_DIR/$doc" "$INSTALL_DIR/"
        fi
    done
    
    print_success "All files copied"
}

################################################################################
# Download Model (Optional)
################################################################################

download_model() {
    print_step "Checking for AI model..."
    
    MODEL_FILE="$MODELS_DIR/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    
    if [ -f "$MODEL_FILE" ]; then
        print_success "Model already exists"
        return
    fi
    
    print_warning "AI model not found"
    echo -e "${YELLOW}Would you like to download the AI model now? (Recommended)${NC}"
    echo "Model: Llama 3.2 3B Instruct (Quantized)"
    echo "Size: ~2GB"
    read -p "Download now? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "Downloading model... (this may take a while)"
        
        # Download from Hugging Face
        MODEL_URL="https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
        
        wget -O "$MODEL_FILE" "$MODEL_URL" --progress=bar:force 2>&1 || {
            print_error "Failed to download model"
            print_warning "You can download it manually later and place it in: $MODELS_DIR"
            return
        }
        
        print_success "Model downloaded successfully"
    else
        print_warning "Skipping model download"
        print_warning "You'll need to download the model manually and place it in: $MODELS_DIR"
    fi
}

################################################################################
# Setup wavesctl Command
################################################################################

create_wavesctl() {
    print_step "Setting up wavesctl command..."
    
    # wavesctl.py should already be copied, just make it executable
    WAVESCTL_SCRIPT="$INSTALL_DIR/wavesctl.py"
    
    if [ ! -f "$WAVESCTL_SCRIPT" ]; then
        print_error "wavesctl.py not found in $INSTALL_DIR"
        exit 1
    fi
    
    # Make it executable
    chmod +x "$WAVESCTL_SCRIPT"
    print_success "wavesctl.py is now executable"
    
    # Create symlink in /usr/local/bin
    print_step "Creating global command..."
    
    if [ -w "$BIN_DIR" ]; then
        ln -sf "$WAVESCTL_SCRIPT" "$BIN_DIR/wavesctl"
        print_success "wavesctl is now globally available"
    else
        print_step "Need sudo access to create global command..."
        sudo ln -sf "$WAVESCTL_SCRIPT" "$BIN_DIR/wavesctl" || {
            print_error "Failed to create global command"
            print_warning "You can run WavesAI with: $WAVESCTL_SCRIPT"
            return
        }
        print_success "wavesctl is now globally available"
    fi
}

# Old bash script creation (keeping for reference, but not used)
create_wavesctl_bash_old() {
    print_step "Creating wavesctl bash script..."
    
    # Create wavesctl script
    WAVESCTL_SCRIPT="$INSTALL_DIR/wavesctl_bash"
    
    cat > "$WAVESCTL_SCRIPT" << 'EOF'
#!/bin/bash

################################################################################
# wavesctl - WavesAI Control Script
# Global command to interact with WavesAI
################################################################################

INSTALL_DIR="$HOME/.wavesai"
WAVESAI_SCRIPT="$INSTALL_DIR/wavesai.py"
VENV_DIR="$INSTALL_DIR/venv"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check if WavesAI is installed
if [ ! -f "$WAVESAI_SCRIPT" ]; then
    echo -e "${RED}Error: WavesAI is not installed${NC}"
    echo "Please run the installer first"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}Error: Virtual environment not found${NC}"
    echo "Please reinstall WavesAI"
    exit 1
fi

# Function to show help
show_help() {
    echo -e "${PURPLE}WavesAI Control (wavesctl)${NC}"
    echo ""
    echo "Usage: wavesctl [command]"
    echo ""
    echo "Commands:"
    echo "  start, run          Start WavesAI interactive mode"
    echo "  status              Show system status"
    echo "  version             Show version information"
    echo "  update              Update WavesAI"
    echo "  config              Edit configuration"
    echo "  logs                View logs"
    echo "  help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  wavesctl start      # Start WavesAI"
    echo "  wavesctl status     # Show system status"
    echo ""
}

# Function to show version
show_version() {
    echo -e "${PURPLE}WavesAI Version 3.0${NC}"
    echo "JARVIS-like AI Assistant for Linux"
    echo "Installation: $INSTALL_DIR"
}

# Function to show status
show_status() {
    echo -e "${CYAN}WavesAI Status:${NC}"
    echo ""
    
    # Check if virtual environment exists
    if [ -d "$VENV_DIR" ]; then
        echo -e "${GREEN}✓${NC} Virtual Environment: Present"
    else
        echo -e "${YELLOW}✗${NC} Virtual Environment: Missing"
    fi
    
    # Check if model exists
    if [ -f "$INSTALL_DIR/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf" ]; then
        echo -e "${GREEN}✓${NC} AI Model: Installed"
    else
        echo -e "${YELLOW}✗${NC} AI Model: Not found"
    fi
    
    # Check if config exists
    if [ -f "$INSTALL_DIR/config/config.json" ]; then
        echo -e "${GREEN}✓${NC} Configuration: Present"
    else
        echo -e "${YELLOW}✗${NC} Configuration: Missing"
    fi
    
    # Check Python dependencies in venv
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
        if python -c "import llama_cpp" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} Dependencies: Installed"
        else
            echo -e "${YELLOW}✗${NC} Dependencies: Missing"
        fi
        deactivate
    else
        echo -e "${YELLOW}✗${NC} Dependencies: Cannot check (venv missing)"
    fi
    
    echo ""
}

# Function to edit config
edit_config() {
    CONFIG_FILE="$INSTALL_DIR/config/config.json"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${YELLOW}Config file not found. Creating default...${NC}"
        mkdir -p "$INSTALL_DIR/config"
        echo '{}' > "$CONFIG_FILE"
    fi
    
    ${EDITOR:-nano} "$CONFIG_FILE"
}

# Function to view logs
view_logs() {
    LOG_FILE="$INSTALL_DIR/config/logs/wavesai.log"
    
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${YELLOW}No logs found${NC}"
        exit 0
    fi
    
    tail -f "$LOG_FILE"
}

# Main command handler
case "${1:-start}" in
    start|run)
        cd "$INSTALL_DIR"
        # Activate virtual environment and run WavesAI
        source "$VENV_DIR/bin/activate"
        python "$WAVESAI_SCRIPT"
        deactivate
        ;;
    status)
        show_status
        ;;
    version)
        show_version
        ;;
    config)
        edit_config
        ;;
    logs)
        view_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${YELLOW}Unknown command: $1${NC}"
        echo "Use 'wavesctl help' for usage information"
        exit 1
        ;;
esac
EOF
    
    chmod +x "$WAVESCTL_SCRIPT"
    print_success "wavesctl script created"
    
    # Create symlink in /usr/local/bin
    print_step "Creating global command..."
    
    if [ -w "$BIN_DIR" ]; then
        ln -sf "$WAVESCTL_SCRIPT" "$BIN_DIR/wavesctl"
        print_success "wavesctl is now globally available"
    else
        print_step "Need sudo access to create global command..."
        sudo ln -sf "$WAVESCTL_SCRIPT" "$BIN_DIR/wavesctl" || {
            print_error "Failed to create global command"
            print_warning "You can run WavesAI with: $WAVESCTL_SCRIPT"
            return
        }
        print_success "wavesctl is now globally available"
    fi
}

################################################################################
# Set Permissions
################################################################################

set_permissions() {
    print_step "Setting permissions..."
    
    chmod +x "$INSTALL_DIR/wavesai.py"
    chmod -R 755 "$INSTALL_DIR"
    
    print_success "Permissions set"
}

################################################################################
# Create Desktop Entry (Optional)
################################################################################

create_desktop_entry() {
    print_step "Creating desktop entry..."
    
    DESKTOP_DIR="$HOME/.local/share/applications"
    mkdir -p "$DESKTOP_DIR"
    
    cat > "$DESKTOP_DIR/wavesai.desktop" << EOF
[Desktop Entry]
Version=3.0
Type=Application
Name=WavesAI
Comment=JARVIS-like AI Assistant
Exec=wavesctl start
Icon=utilities-terminal
Terminal=true
Categories=Utility;System;
Keywords=AI;Assistant;JARVIS;
EOF
    
    print_success "Desktop entry created"
}

################################################################################
# Main Installation
################################################################################

main() {
    print_header
    
    echo "This script will install WavesAI on your system."
    echo "Installation directory: $INSTALL_DIR"
    echo "Global command: wavesctl"
    echo ""
    read -p "Continue with installation? (y/n): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Installation cancelled"
        exit 0
    fi
    
    echo ""
    
    # Run installation steps
    check_requirements
    create_directories
    create_venv
    install_dependencies
    copy_files
    download_model
    create_wavesctl
    set_permissions
    create_desktop_entry
    
    echo ""
    print_success "Installation completed successfully!"
    echo ""
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║              WavesAI is now installed!                   ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Quick Start:${NC}"
    echo "  wavesctl start      # Start WavesAI"
    echo "  wavesctl status     # Check status"
    echo "  wavesctl help       # Show all commands"
    echo ""
    echo -e "${CYAN}Features:${NC}"
    echo "  ✓ JARVIS-like conversational AI"
    echo "  ✓ System monitoring and control"
    echo "  ✓ Command execution with sudo management"
    echo "  ✓ Intelligent error handling"
    echo "  ✓ 170+ advanced system commands"
    echo "  ✓ Dangerous operation protection"
    echo ""
    echo -e "${GREEN}Ready to assist, sir!${NC}"
    echo ""
}

# Run main installation
main
