#!/bin/bash

################################################################################
# WavesAI Uninstaller Script
# Version: 3.0
# Description: Removes WavesAI from the system
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
DESKTOP_DIR="$HOME/.local/share/applications"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║            WavesAI Uninstaller Script                   ║"
    echo "║            Version 3.0                                   ║"
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
# Backup Configuration
################################################################################

backup_config() {
    print_step "Backing up configuration..."
    
    if [ -d "$INSTALL_DIR/config" ]; then
        BACKUP_DIR="$HOME/wavesai_backup_$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        cp -r "$INSTALL_DIR/config" "$BACKUP_DIR/" 2>/dev/null || true
        cp "$INSTALL_DIR/system_prompt.txt" "$BACKUP_DIR/" 2>/dev/null || true
        
        print_success "Configuration backed up to: $BACKUP_DIR"
    else
        print_warning "No configuration to backup"
    fi
}

################################################################################
# Remove Files
################################################################################

remove_files() {
    print_step "Removing WavesAI files..."
    
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        print_success "Removed $INSTALL_DIR"
    else
        print_warning "Installation directory not found"
    fi
}

################################################################################
# Remove Global Command
################################################################################

remove_global_command() {
    print_step "Removing global command..."
    
    if [ -L "$BIN_DIR/wavesctl" ] || [ -f "$BIN_DIR/wavesctl" ]; then
        if [ -w "$BIN_DIR" ]; then
            rm -f "$BIN_DIR/wavesctl"
            print_success "Removed wavesctl command"
        else
            print_step "Need sudo access to remove global command..."
            sudo rm -f "$BIN_DIR/wavesctl" || {
                print_error "Failed to remove global command"
                return
            }
            print_success "Removed wavesctl command"
        fi
    else
        print_warning "wavesctl command not found"
    fi
}

################################################################################
# Remove Desktop Entry
################################################################################

remove_desktop_entry() {
    print_step "Removing desktop entry..."
    
    if [ -f "$DESKTOP_DIR/wavesai.desktop" ]; then
        rm -f "$DESKTOP_DIR/wavesai.desktop"
        print_success "Removed desktop entry"
    else
        print_warning "Desktop entry not found"
    fi
}

################################################################################
# Remove Python Dependencies (Optional)
################################################################################

remove_dependencies() {
    echo ""
    echo -e "${YELLOW}Would you like to remove Python dependencies?${NC}"
    echo "This will remove: llama-cpp-python, psutil, requests, beautifulsoup4, wikipedia"
    echo "Note: These packages might be used by other applications"
    read -p "Remove dependencies? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "Removing Python dependencies..."
        
        PACKAGES=(
            "llama-cpp-python"
            "psutil"
            "requests"
            "beautifulsoup4"
            "wikipedia"
        )
        
        for package in "${PACKAGES[@]}"; do
            pip3 uninstall -y "$package" 2>/dev/null || true
        done
        
        print_success "Dependencies removed"
    else
        print_warning "Skipping dependency removal"
    fi
}

################################################################################
# Main Uninstallation
################################################################################

main() {
    print_header
    
    echo -e "${RED}WARNING: This will remove WavesAI from your system${NC}"
    echo ""
    echo "The following will be removed:"
    echo "  - Installation directory: $INSTALL_DIR"
    echo "  - Global command: wavesctl"
    echo "  - Desktop entry"
    echo ""
    echo "Your configuration will be backed up before removal."
    echo ""
    read -p "Continue with uninstallation? (y/n): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Uninstallation cancelled"
        exit 0
    fi
    
    echo ""
    
    # Run uninstallation steps
    backup_config
    remove_global_command
    remove_desktop_entry
    remove_files
    remove_dependencies
    
    echo ""
    print_success "WavesAI has been uninstalled"
    echo ""
    echo -e "${CYAN}Thank you for using WavesAI!${NC}"
    echo ""
}

# Run main uninstallation
main
