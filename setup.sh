#!/bin/bash

###########################################
# DBT MCP Server - Complete Setup Script
# This script sets up everything needed to run the DBT MCP Server
###########################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Banner
echo ""
echo "=========================================="
echo "  DBT MCP Server - Setup Script"
echo "=========================================="
echo ""

###########################################
# 1. Check Prerequisites
###########################################
log_info "Checking prerequisites..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed. Please install Python 3.10 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
log_success "Python version: $(python3 --version)"

# Check/Install uv
if ! command -v uv &> /dev/null; then
    log_warning "uv is not installed. Installing now..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    log_success "uv installed successfully"
else
    log_success "uv is already installed ($(uv --version))"
fi

# Check uvx
if ! command -v uvx &> /dev/null; then
    log_error "uvx is not available. Please restart your shell and run this script again."
    exit 1
else
    log_success "uvx is available"
fi

# Check dbt
if command -v dbt &> /dev/null; then
    log_success "dbt is installed ($(dbt --version | head -n1))"
    DBT_PATH=$(which dbt)
else
    log_warning "dbt is not found in PATH. You'll need to configure DBT_PATH in .env manually."
    DBT_PATH="/usr/local/bin/dbt"
fi

###########################################
# 2. Setup Virtual Environment
###########################################
log_info "Setting up Python virtual environment..."

# Remove old venv if exists
if [ -d ".venv" ]; then
    log_warning "Removing existing virtual environment..."
    rm -rf .venv
fi

# Create new venv
uv venv
log_success "Virtual environment created"

# Activate virtual environment
log_info "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi
log_success "Virtual environment activated"

###########################################
# 3. Install Python Dependencies
###########################################
log_info "Installing Python dependencies..."
uv pip install -r requirements.txt
log_success "Python dependencies installed"

###########################################
# 4. Configure Environment
###########################################
log_info "Configuring environment..."

# Get current project directory
CURRENT_DIR=$(pwd)

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    log_info "Creating .env file from template..."
    cp .env.example .env

    # Try to auto-configure .env
    if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Update DBT_PROJECT_DIR
        sed -i.bak "s|DBT_PROJECT_DIR=/Users/yuchencao/C/Git-Repo/DBT-MCP/DBT-MCP-Server|DBT_PROJECT_DIR=$CURRENT_DIR|g" .env
        # Update DBT_PATH if found
        if [ -n "$DBT_PATH" ]; then
            sed -i.bak "s|DBT_PATH=/path/to/your/dbt/executable|DBT_PATH=$DBT_PATH|g" .env
        fi
        rm -f .env.bak
    fi

    log_success ".env file created"
else
    log_success ".env file already exists"
fi

###########################################
# 5. Verify dbt-mcp availability
###########################################
log_info "Verifying dbt-mcp availability via uvx..."
if uvx --help &> /dev/null; then
    log_success "uvx is working correctly"
    log_info "dbt-mcp will be auto-installed on first run via: uvx --env-file .env dbt-mcp"
else
    log_error "uvx is not working properly"
    exit 1
fi

###########################################
# 6. Check OpenAI API Key
###########################################
if [ -z "$OPENAI_API_KEY" ]; then
    log_warning "OPENAI_API_KEY is not set in environment"
    log_info "You need to set it before running the MCP agent:"
    echo "    export OPENAI_API_KEY='your-api-key-here'"
else
    log_success "OPENAI_API_KEY is set"
fi

###########################################
# 7. Test Installation
###########################################
log_info "Testing Python imports..."
python3 -c "import pydantic_ai; import openai; print('All imports successful')" && log_success "Python packages working" || log_error "Import test failed"

###########################################
# Setup Complete
###########################################
echo ""
echo "=========================================="
log_success "Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Configuration Summary:"
echo "   - Python: $(python3 --version)"
echo "   - Virtual Environment: .venv/"
echo "   - DBT Project: $CURRENT_DIR"
echo "   - Config File: .env"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Review and edit .env file if needed:"
echo "   ${BLUE}nano .env${NC} or ${BLUE}vim .env${NC}"
echo ""
echo "2. Set your OpenAI API key (if not already set):"
echo "   ${BLUE}export OPENAI_API_KEY='your-api-key-here'${NC}"
echo ""
echo "3. Activate the virtual environment:"
echo "   ${BLUE}source .venv/bin/activate${NC}"
echo ""
echo "4. Run the MCP agent:"
echo "   ${BLUE}python agents/mcp_cli.py${NC}"
echo ""
echo "📝 Notes:"
echo "   - dbt-mcp will auto-install via uvx on first run"
echo "   - The agent runs in read-only mode (safe exploration)"
echo "   - Type /exit or Ctrl+C to quit the agent"
echo ""
