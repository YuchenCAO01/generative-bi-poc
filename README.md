# GenBI POC - DBT MCP & LangChain Integration

A proof-of-concept (POC) project demonstrating how to integrate DBT MCP Server with LangChain Agent for natural language-based data asset discovery.

## Project Purpose

This POC demonstrates how the Model Context Protocol (MCP) can bridge data tools with AI agents. **This is NOT a DBT project** - it's a showcase of MCP protocol integration with LangChain for intelligent data exploration.

## Key Features

- **Natural Language Queries**: Ask questions about DBT models and tables in plain English
- **Metadata Discovery**: Retrieve table schemas, field types, and descriptions
- **Interactive UI**: User-friendly Streamlit chat interface
- **AI-Powered**: Uses OpenAI GPT-4o-mini as the reasoning engine

## Technology Stack

- **MCP Server**: DBT MCP Server (provides data metadata)
- **MCP Client**: Python MCP SDK (connects to MCP Server)
- **AI Agent**: LangChain + OpenAI
- **UI**: Streamlit

## Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key
- BigQuery access (optional, for DBT data source)

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd DBT-MCP-Server

# Copy environment file
cp .env.example .env

# Edit .env and set your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here

# Start with Docker Compose
docker-compose up -d
```

#### Option 2: Local Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd DBT-MCP-Server

# Run automated setup
chmod +x setup.sh
./setup.sh

# Set OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# Activate virtual environment
source .venv/bin/activate
```

### Running the Application

#### Streamlit Web Interface

```bash
# With Docker
docker-compose run --rm dbt-mcp-server streamlit run app.py

# Local installation
streamlit run app.py
```

#### Command Line Agent

```bash
# With Docker
docker-compose run --rm dbt-mcp-server python agents/mcp_client.py

# Local installation
python agents/mcp_client.py
```

## How It Works

### Agent Workflow

1. User inputs a natural language question
2. LangChain Agent analyzes the intent
3. Agent calls MCP tools to query DBT metadata
4. Results are formatted and returned to the user

### Example Queries

- "What models are available in the staging layer?"
- "Show me the schema of dim_customers table"
- "What are the relationships between customer and order models?"
- "List all fact tables in the project"

## Project Structure

```
DBT-MCP-Server/
├── agents/                  # MCP client and LangChain agent implementations
│   ├── agent.py             # LangChain agent logic
│   ├── mcp_client.py        # MCP client implementation
│   └── README.md            # Agent documentation
├── app.py                   # Streamlit web application
├── credentials/             # Service account credentials (gitignored)
├── models/                  # DBT models (example data)
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── docker-compose.yml       # Docker configuration
├── Dockerfile               # Docker image definition
└── README.md                # This file
```

## Architecture

```
┌─────────────────┐
│  User Interface │
│   (Streamlit)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LangChain Agent │
│  (GPT-4o-mini)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MCP Client    │
│  (Python SDK)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MCP Server    │
│   (dbt-mcp)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  DBT Metadata   │
│   (BigQuery)    │
└─────────────────┘
```

## Important Notes

- **Local Deployment Only**: MCP Server must run in the same environment as the agent (remote deployment not supported)
- **Read-Only Operations**: Current version only supports metadata discovery, no SQL execution
- **Cost Optimization**: Uses GPT-4o-mini to minimize API costs
- **POC Status**: This is a proof-of-concept for demonstration purposes

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# DBT Configuration
DBT_PROJECT_DIR=/path/to/dbt/project
DBT_PATH=/path/to/dbt/executable

# Google Cloud (optional)
GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-credentials.json
GCP_PROJECT=your-project-id
BIGQUERY_DATASET=your_dataset

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key
```

## Development

### Running Tests

```bash
# Test MCP connection
python -m agents.test.test_mcp

# Test agent functionality
python -m agents.test.test_agent

# Test with specific queries
python quick_test_agent.py
```

### Adding New Features

1. Explore the [agents/](agents/) directory for MCP client and agent implementations
2. Check [app.py](app.py) for Streamlit UI customization
3. Refer to [DBT MCP Server documentation](https://github.com/jonnycrunch/dbt-mcp) for available tools

## Troubleshooting

### Common Issues

**MCP Connection Failed**
- Verify `.env` file exists and has correct paths
- Ensure `uvx` is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Check DBT project is valid: `dbt parse`

**OpenAI API Errors**
- Verify `OPENAI_API_KEY` is set in `.env`
- Check API key has sufficient credits

**Import Errors**
- Reinstall dependencies: `uv pip install -r requirements.txt`
- Verify virtual environment is activated

## Contributing

This is a POC project. Contributions and improvement suggestions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Resources

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [DBT MCP Server](https://github.com/jonnycrunch/dbt-mcp)
- [LangChain Documentation](https://python.langchain.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Model Context Protocol team for the MCP specification
- DBT Labs for the dbt framework
- LangChain team for the agent framework
- OpenAI for GPT models
