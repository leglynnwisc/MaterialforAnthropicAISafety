from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.exc import OperationalError
from sqlalchemy import text, inspect
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
import asyncio
import uuid
from bert_score import score
from rouge_score import rouge_scorer
from nltk.translate import meteor_score
from mcp.client.stdio import StdioServerParameters

# Import our services
from services.search import SearchService
from services.llm import LLMService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///extension_query_log.db'
app.config['SECRET_KEY'] = "my super secretive key"
db = SQLAlchemy(app)

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), 'keys.env')
load_dotenv(dotenv_path)

# Initialize services
mcp_params = StdioServerParameters(
    command=os.getenv("MCP_SERVER_COMMAND"),
    args=[os.getenv("MCP_SERVER_SCRIPT")],
    env=None
)

search_service = SearchService(
    pinecone_api_key=os.getenv("PINECONE_API_KEY"),
    openai_embedding_key=os.getenv("OPEN_AI_EMBEDDING_API_KEY")
)

llm_service = LLMService(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    mcp_params=mcp_params
)

# Initialize admin
admin = Admin(app, name='MyAdmin', template_mode='bootstrap3')


class QueryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    query = db.Column(db.String(500), nullable=False)
    preference = db.Column(db.String(10), nullable=False, default='default_value')
    updated_preference = db.Column(db.String(10))
    openai_response = db.Column(db.String(1000), nullable=False)
    augment_response = db.Column(db.String(2000), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    relevance_score = db.Column(db.Float)  # Added to track search relevance


admin.add_view(ModelView(QueryLog, db.session))


def calculate_scores(generated_output: str, reference: str):
    """Calculate various evaluation metrics"""
    # BERT score
    P, R, F1 = score([generated_output], [reference], lang="en", rescale_with_baseline=True)
    bert_scores = {
        "precision": P.item(),
        "recall": R.item(),
        "f1": F1.item()
    }

    # ROUGE score
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    rouge_scores = scorer.score(generated_output, reference)

    # METEOR score
    meteor = meteor_score.meteor_score([reference.split()], generated_output.split())

    return {
        "bert": bert_scores,
        "rouge": {
            "rouge1": rouge_scores['rouge1'].fmeasure,
            "rouge2": rouge_scores['rouge2'].fmeasure,
            "rougeL": rouge_scores['rougeL'].fmeasure
        },
        "meteor": meteor
    }


@app.route("/", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        session['user_id'] = str(uuid.uuid4())
        return redirect(url_for('chat_page'))
    return render_template('joint_template_2.html', user_id=session.get('user_id'))


@app.route("/chat", methods=["POST"])
async def chat_page():
    try:
        user_input = request.json.get('query', '')

        # Get search results first
        search_results = search_service.advanced_hybrid_search(
            query=user_input,
            filters={
                "must": {"regions": ["wisconsin", "midwest"]},
                "should": {
                    "crops": ["soybean", "soybeans"],
                    "pests": ["insects", "aphids", "beetles"]
                }
            }
        )

        # Generate responses using search results
        responses = await llm_service.generate_all_responses(
            query=user_input,
            search_results=[{
                'text': r.text,
                'relevance_score': r.relevance_score,
                'categories_matched': r.categories_matched
            } for r in search_results] if search_results else None
        )

        if not search_results:
            logger.warning(f"No relevant search results found for query: {user_input}")

        # Generate all responses
        responses = await llm_service.generate_all_responses(
            user_input,
            [result.text for result in search_results] if search_results else None
        )

        # Calculate scores if reference text is available
        reference_text = """For reference text comparison"""  # Replace with actual reference
        scores = {
            "openai": calculate_scores(responses["OpenAI Response"], reference_text),
            "rag": calculate_scores(responses["RAG-Augmented Response"], reference_text)
        }

        # Log interaction
        query_log = QueryLog(
            user_id=user_id,
            query=user_input,
            openai_response=responses["OpenAI Response"],
            augment_response=responses["RAG-Augmented Response"],
            relevance_score=search_results[0].relevance_score if search_results else 0.0
        )
        db.session.add(query_log)
        db.session.commit()

        # Prepare response
        response_data = {
            "openai_response": responses["OpenAI Response"],
            "augment_response": responses["RAG-Augmented Response"],
            "mcp_response": responses.get("Claude MCP Response", "MCP response not available"),
            "search_metadata": [
                {
                    "relevance_score": result.relevance_score,
                    "categories_matched": result.categories_matched
                } for result in search_results
            ] if search_results else [],
            "evaluation_scores": scores
        }

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        db.session.rollback()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route("/submit_preference", methods=["POST"])
def submit_preference():
    preference = request.json.get('preference')
    query = request.json.get('query')
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "User ID not found in session"}), 403

    try:
        interaction = QueryLog.query.filter_by(
            user_id=user_id,
            query=query
        ).order_by(QueryLog.timestamp.desc()).first()

        if interaction:
            interaction.preference = preference
            db.session.commit()
            return jsonify({"success": True})
        else:
            return jsonify({"error": "No matching interaction found"}), 404

    except Exception as e:
        logger.error(f"Error submitting preference: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/health')
def health():
    return "OK"


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True)