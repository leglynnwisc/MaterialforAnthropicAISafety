import os
from dotenv import load_dotenv

# Add debug print to check the path
dotenv_path = os.path.join(os.path.dirname(__file__), "keys2.env")
print(f"Looking for .env file at: {dotenv_path}")
print(f"File exists: {os.path.exists(dotenv_path)}")

# Load environment variables
load_dotenv(dotenv_path)

# API Keys and Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MCP_SERVER_COMMAND = os.getenv("MCP_SERVER_COMMAND")
MCP_SERVER_SCRIPT = os.getenv("MCP_SERVER_SCRIPT")
OPEN_AI_EMBEDDING_API_KEY = os.getenv("OPEN_AI_EMBEDDING_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Flask Configuration
FLASK_SECRET_KEY = "my super secretive key"
SQLALCHEMY_DATABASE_URI = 'sqlite:///extension_query_log.db'