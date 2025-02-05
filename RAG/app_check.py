from flask import Flask, jsonify, session, render_template, request, redirect, url_for
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from config import SQLALCHEMY_DATABASE_URI, FLASK_SECRET_KEY
from models.database import db, QueryLog
from services.evaluation import EvaluationService
from services.llm import LLMService
from services.search import SearchService
import logging
import asyncio
import os

# Initialize Flask app
app = Flask(__name__, template_folder="templates")
app.config["SECRET_KEY"] = FLASK_SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

# Initialize database
db.init_app(app)
admin = Admin(app, name="MyAdmin", template_mode="bootstrap3")
admin.add_view(ModelView(QueryLog, db.session))

# API Keys and Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")
MCP_SERVER_COMMAND = os.getenv("MCP_SERVER_COMMAND")
MCP_SERVER_SCRIPT = os.getenv("MCP_SERVER_SCRIPT")
OPEN_AI_EMBEDDING_API_KEY = os.getenv("OPEN_AI_EMBEDDING_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Initialize Services
llm_service = LLMService(
    openai_api_key="OPENAI_API_KEY",
    mcp_params={MCP_SERVER_COMMAND,MCP_SERVER_SCRIPT}
)
search_service = SearchService(
    pinecone_api_key=PINECONE_API_KEY,
    openai_embedding_key=OPEN_AI_EMBEDDING_API_KEY
)
evaluation_service = EvaluationService(llm_service, search_service)

# Routes
@app.route("/", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        session["user_id"] = os.urandom(24).hex()
        return redirect(url_for("chat_page"))
    return render_template("login.html", user_id=session.get("user_id"))


@app.route("/chat", methods=["POST"])
async def chat_page():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "User not logged in"}), 403

    user_query = request.json.get("query", "")
    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    # Generate responses using LLM and search services
    responses = await llm_service.generate_all_responses(user_query)
    return jsonify(responses)


@app.route("/health", methods=["GET"])
def health_check():
    return "App is running!"


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)
