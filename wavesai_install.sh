#!/bin/bash
# WavesAI Installation Script for Arch Linux
# Optimized for Intel i5 12th Gen + RTX 3050 8GB + 16GB RAM

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║           WavesAI Installation Script                    ║"
echo "║     JARVIS-like AI Assistant for Arch Linux              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running on Arch Linux
if [ ! -f /etc/arch-release ]; then
    echo -e "${RED}Error: This script is designed for Arch Linux only.${NC}"
    exit 1
fi

# Function to print status messages
print_status() {
    echo -e "${BLUE}[*]${NC} $1"
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

# Check for root privileges when needed
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        print_warning "This script requires sudo privileges for some operations."
        sudo -v
    fi
}

# Install system dependencies
install_dependencies() {
    print_status "Installing system dependencies..."
    
    # Essential packages
    PACKAGES=(
        "python"
        "python-pip"
        "base-devel"
        "cmake"
        "git"
        "wget"
        "curl"
        "nvidia-utils"
        "cuda"
        "opencl-nvidia"
        "brightnessctl"
        "openrgb"
        "speedtest-cli"
    )
    
    check_sudo
    
    for pkg in "${PACKAGES[@]}"; do
        if pacman -Qi "$pkg" &> /dev/null; then
            print_success "$pkg is already installed"
        else
            print_status "Installing $pkg..."
            sudo pacman -S --noconfirm "$pkg" || print_warning "Failed to install $pkg"
        fi
    done
    
    # Install yay if not present
    if ! command -v yay &> /dev/null; then
        print_status "Installing yay AUR helper..."
        cd /tmp
        git clone https://aur.archlinux.org/yay.git
        cd yay
        makepkg -si --noconfirm
        cd ~
        print_success "yay installed"
    else
        print_success "yay is already installed"
    fi
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Create virtual environment (optional but recommended)
    VENV_PATH="$HOME/.local/share/wavesai/venv"
    
    if [ ! -d "$VENV_PATH" ]; then
        print_status "Creating virtual environment..."
        mkdir -p "$HOME/.local/share/wavesai"
        python -m venv "$VENV_PATH"
    fi
    
    source "$VENV_PATH/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install llama-cpp-python with CUDA support for RTX 3050
    print_status "Installing llama-cpp-python with CUDA support (this may take a while)..."
    CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
    
    # Install other dependencies
    pip install psutil requests python-dotenv
    
    print_success "Python dependencies installed"
}

# Download Mistral model
download_model() {
    print_status "Setting up Mistral 7B model..."
    
    MODEL_DIR="$HOME/models"
    MODEL_FILE="mistral-7b-instruct-v0.1.Q4_K_M.gguf"
    MODEL_PATH="$MODEL_DIR/$MODEL_FILE"
    
    mkdir -p "$MODEL_DIR"
    
    if [ -f "$MODEL_PATH" ]; then
        print_success "Model already exists at $MODEL_PATH"
    else
        print_status "Downloading Mistral 7B Q4_K_M model (~4.1GB)..."
        print_warning "This will take some time depending on your internet connection..."
        
        wget -O "$MODEL_PATH" \
            "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf" \
            || print_error "Failed to download model. Please download manually from HuggingFace."
        
        if [ -f "$MODEL_PATH" ]; then
            print_success "Model downloaded successfully"
        fi
    fi
}

# Setup WavesAI directories and files
setup_wavesai() {
    print_status "Setting up WavesAI..."
    
    # Create directories
    mkdir -p "$HOME/.config/wavesai"
    mkdir -p "$HOME/.config/wavesai/logs"
    mkdir -p "$HOME/.config/wavesai/modules"
    mkdir -p "$HOME/.local/bin"
    mkdir -p "$HOME/.local/share/wavesai"
    
    # Save the main script
    INSTALL_DIR="$HOME/.local/share/wavesai"
    
    # Copy scripts (assuming they're in the current directory)
    if [ -f "wavesai_core.py" ]; then
        cp wavesai_core.py "$INSTALL_DIR/wavesai.py"
        chmod +x "$INSTALL_DIR/wavesai.py"
    fi
    
    if [ -f "wavesai_modules.py" ]; then
        cp wavesai_modules.py "$INSTALL_DIR/modules.py"
    fi
    
    # Create launcher script
    cat > "$HOME/.local/bin/wavesai" << 'EOF'
#!/bin/bash
source "$HOME/.local/share/wavesai/venv/bin/activate"
python "$HOME/.local/share/wavesai/wavesai.py" "$@"
EOF
    
    chmod +x "$HOME/.local/bin/wavesai"
    
    # Create systemd service for background daemon (optional)
    mkdir -p "$HOME/.config/systemd/user"
    
    cat > "$HOME/.config/systemd/user/wavesai.service" << EOF
[Unit]
Description=WavesAI Background Daemon
After=network.target

[Service]
Type=simple
ExecStart=$HOME/.local/share/wavesai/venv/bin/python $INSTALL_DIR/wavesai.py --daemon
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF
    
    print_success "WavesAI installed to $INSTALL_DIR"
}

# Create configuration file
create_config() {
    print_status "Creating configuration file..."
    
    CONFIG_FILE="$HOME/.config/wavesai/config.json"
    
    cat > "$CONFIG_FILE" << EOF
{
    "model_path": "$HOME/models/mistral-7b-instruct-v0.1.Q4_K_M.gguf",
    "context_length": 4096,
    "gpu_layers": 35,
    "threads": 8,
    "temperature": 0.7,
    "max_tokens": 512,
    "personality": "jarvis",
    "enable_notifications": true,
    "auto_execute_safe_commands": false,
    "search_engine": "duckduckgo",
    "default_location": "auto"
}
EOF
    
    print_success "Configuration file created at $CONFIG_FILE"
}

# Add to PATH
update_path() {
    print_status "Updating PATH..."
    
    SHELL_RC="$HOME/.bashrc"
    if [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    fi
    
    if ! grep -q ".local/bin" "$SHELL_RC"; then
        echo '' >> "$SHELL_RC"
        echo '# WavesAI' >> "$SHELL_RC"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
        print_success "Added ~/.local/bin to PATH in $SHELL_RC"
    else
        print_success "PATH already configured"
    fi
}

# Test CUDA installation
test_cuda() {
    print_status "Testing CUDA installation..."
    
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
        print_success "NVIDIA GPU detected and working"
    else
        print_warning "nvidia-smi not found. GPU acceleration may not work."
    fi
}

# Create desktop entry
create_desktop_entry() {
    print_status "Creating desktop entry..."
    
    mkdir -p "$HOME/.local/share/applications"
    
    cat > "$HOME/.local/share/applications/wavesai.desktop" << EOF
[Desktop Entry]
Name=WavesAI
Comment=JARVIS-like AI Assistant
Exec=$HOME/.local/bin/wavesai
Icon=utilities-terminal
Type=Application
Categories=System;Utility;
Terminal=true
EOF
    
    print_success "Desktop entry created"
}

# Main installation
main() {
    echo ""
    print_status "Starting WavesAI installation..."
    echo ""
    
    install_dependencies
    echo ""
    
    install_python_deps
    echo ""
    
    download_model
    echo ""
    
    setup_wavesai
    echo ""
    
    create_config
    echo ""
    
    update_path
    echo ""
    
    test_cuda
    echo ""
    
    create_desktop_entry
    echo ""
    
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║          WavesAI Installation Complete!                  ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    print_success "Installation successful!"
    echo ""
    echo -e "${BLUE}To start WavesAI, run:${NC}"
    echo -e "${GREEN}  wavesai${NC}"
    echo ""
    echo -e "${BLUE}Or reload your shell first:${NC}"
    echo -e "${GREEN}  source ~/.bashrc${NC}  (or ~/.zshrc)"
    echo ""
    echo -e "${BLUE}To enable background daemon:${NC}"
    echo -e "${GREEN}  systemctl --user enable --now wavesai${NC}"
    echo ""
    print_warning "Note: Make sure the Python scripts (wavesai_core.py and wavesai_modules.py)"
    print_warning "are in the current directory before running this installer."
    echo ""
}

# Run installation
main