from dotenv import load_dotenv
import os
import asyncio
import json
from langchain.chat_models.openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession
from bert_score import score
from rouge_score import rouge_scorer
from nltk.translate import meteor_score
from services.searchv2 import EnhancedSearchService

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), "keys2.env")
load_dotenv(dotenv_path)

# Access API keys and setup
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPEN_AI_EMBEDDING_API_KEY = os.getenv("OPEN_AI_EMBEDDING_API_KEY")

# Initialize services
chat = ChatOpenAI(model='gpt-3.5-turbo', openai_api_key=OPENAI_API_KEY)
embeddings = OpenAIEmbeddings(model='text-embedding-ada-002', openai_api_key=OPEN_AI_EMBEDDING_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "enhanced-vengento-tagged-data"
index = pc.Index(index_name)
vectorstore = PineconeVectorStore(index, embeddings, "text")

# MCP Parameters
mcp_params = StdioServerParameters(
    command=os.getenv("MCP_SERVER_COMMAND"),
    args=[os.getenv("MCP_SERVER_SCRIPT")],
    env=None
)


class MCPClient:
    def __init__(self, server_params: StdioServerParameters, max_retries: int = 3, timeout: int = 30):
        self.server_params = server_params
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = None
        self._connection_lock = asyncio.Lock()

    async def _connect(self):
        if self.session and not self.session.closed:
            return

        async with self._connection_lock:
            for attempt in range(self.max_retries):
                try:
                    read_stream, write_stream = await asyncio.wait_for(
                        stdio_client(self.server_params),
                        timeout=self.timeout
                    )
                    self.session = await ClientSession(read_stream, write_stream).__aenter__()
                    await asyncio.wait_for(self.session.initialize(), timeout=self.timeout)
                    return
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise ConnectionError(f"Failed to connect after {self.max_retries} attempts: {e}")
                    await asyncio.sleep(1 * (attempt + 1))

    async def query(self, user_query: str) -> str:
        await self._connect()
        try:
            response = await asyncio.wait_for(
                self.session.complete_message(
                    [{"role": "user", "content": user_query}],
                    max_tokens=300
                ),
                timeout=self.timeout
            )
            return response["choices"][0]["text"]
        except Exception as e:
            await self._cleanup()
            raise e

    async def _cleanup(self):
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None



async def debug_document_structure():
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index("vegento-tagged-data")

    # Create a simple query vector
    embeddings = OpenAIEmbeddings(openai_api_key=OPEN_AI_EMBEDDING_API_KEY)
    query_embedding = embeddings.embed_query("soybeans")

    # Query index and examine document structure
    results = index.query(
        vector=query_embedding,
        top_k=3,
        include_metadata=True,
        namespace="vegento-data"
    )

    print("\nExamining document structure:")
    for i, match in enumerate(results.matches):
        print(f"\nDocument {i + 1}:")
        print(f"ID: {match.id}")
        print("Metadata keys:", list(match.metadata.keys()) if match.metadata else "No metadata")
        print("Metadata content:", json.dumps(match.metadata, indent=2) if match.metadata else "Empty")


def augment_rag_prompt_with_neighbors(query: str, search_results) -> str:
    """Generate a RAG prompt with neighbors included."""
    context_blocks = []
    for i, result in enumerate(search_results, 1):
        context_block = f"""Context {i}:
        Relevance Score: {result.get('relevance_score', 0):.2f}
        Text: {result.get('text', '')}
        ---"""
        context_blocks.append(context_block)

    return f"""Using the following contexts, answer the query. Contexts are ordered by relevance and include neighbors:

    {'\n'.join(context_blocks)}

    Query: {query}"""

async def test_soybean_queries():
    """Test soybean-related queries with RAG and neighbors."""
    # Debug index first
    await debug_document_structure()

    # Initialize services
    search_service = EnhancedSearchService(PINECONE_API_KEY, OPEN_AI_EMBEDDING_API_KEY)
    mcp_client = MCPClient(mcp_params)

    # Reference text for evaluation
    reference_text = """Japanese beetles (Treatment should be considered at 30% leaf defoliation pre-bloom and 15-20% defoliation from bloom to pod fill), 
    Potato leafhoppers (six leafhoppers per plant on flowering plants may need control), 
    Soybean aphids (best control between beginning bloom (R1) and beginning seed (R5)), 
    Stink bugs (threshold is 40 bugs/100 sweeps for grain soybean during pod fill)."""

    # Test query
    query = "What insects are a problem in blooming soybeans in Wisconsin?"

    # Search with filters
    filters = {
        "must": {"regions": ["wisconsin", "midwest"], "crops": ["soybean", "soybeans"]},
        "should": {
            "pests": ["aphids", "japanese beetle", "stink bug", "insect", "pest"],
            "management_practices": ["pest management", "IPM", "monitoring"],
            "crop_health": ["plant health", "crop damage"],
        },
    }

    print("\nApplying filters:", json.dumps(filters, indent=2))

    # Perform the search
    hybrid_results = search_service.advanced_hybrid_search_with_neighbors(query, filters=filters, top_k=10)
    rag_prompt = augment_rag_prompt_with_neighbors(query, hybrid_results)

    # Get RAG response
    start_time = asyncio.get_event_loop().time()
    rag_response = chat([HumanMessage(content=rag_prompt)]).content
    rag_time = asyncio.get_event_loop().time() - start_time

    print("\nRAG Response:", rag_response)
    print(f"Response Time: {rag_time:.2f}s")

    # Evaluate Metrics
    print("\nHybrid Search Metrics:")
    for result in hybrid_results[:3]:  # Show top 3 results
        print(f"\nDocument ID: {result.id}")
        print(f"Relevance Score: {result.relevance_score:.3f}")
        print(f"Vector Similarity: {result.score:.3f}")
        print(f"Categories Matched: {result.categories_matched}")

    # MCP Response
    try:
        start_time = asyncio.get_event_loop().time()
        mcp_response = await mcp_client.query(query)
        mcp_time = asyncio.get_event_loop().time() - start_time
        print("\nMCP Response:", mcp_response)
        print(f"Response Time: {mcp_time:.2f}s")
    except Exception as e:
        print(f"\nMCP Error: {str(e)}")
        mcp_response = ""
        mcp_time = 0

    # Compare Metrics
    responses = [
        ("RAG", rag_response, rag_time),
        ("MCP", mcp_response, mcp_time),
    ]

    for response_type, response, response_time in responses:
        if response:
            print(f"\n{response_type} Metrics:")
            print(f"Response Time: {response_time:.2f}s")

            # Calculate BERT Score
            P, R, F1 = score([response], [reference_text], lang="en", rescale_with_baseline=True)
            print(f"BERT Scores: P={P.item():.3f}, R={R.item():.3f}, F1={F1.item():.3f}")

            # Calculate ROUGE Score
            scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
            scores = scorer.score(response, reference_text)
            print(f"ROUGE Scores:")
            print(f"ROUGE-1: {scores['rouge1'].fmeasure:.3f}")
            print(f"ROUGE-2: {scores['rouge2'].fmeasure:.3f}")
            print(f"ROUGE-L: {scores['rougeL'].fmeasure:.3f}")

    await mcp_client._cleanup()

async def debug_pinecone_index():
    # Load environment variables
    dotenv_path = os.path.join(os.path.dirname(__file__), "keys2.env")
    load_dotenv(dotenv_path)

    OPEN_AI_EMBEDDING_API_KEY = os.getenv("OPEN_AI_EMBEDDING_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    print("\nDebugging Pinecone Index...")

    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index("enhanced-vengento-tagged-data")

    # Get index stats
    stats = index.describe_index_stats()
    print("\nIndex Stats:", stats)

    # Try a simple query without filters first
    query_embedding = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=OPEN_AI_EMBEDDING_API_KEY
    ).embed_query("soybean insects")

    print("\nTesting simple query without filters...")
    basic_results = index.query(
        vector=query_embedding,
        top_k=3,
        include_metadata=True,
        namespace="vegento-data"
    )

    print("\nSample metadata structure:")
    if basic_results.matches:
        print(json.dumps(basic_results.matches[0].metadata, indent=2))
    else:
        print("No results found in basic query")

    # Try with minimal filters
    print("\nTesting with minimal filters...")
    test_filters = {
        "regions": {"$in": ["wisconsin", "midwest"]}
    }

    filter_results = index.query(
        vector=query_embedding,
        filter=test_filters,
        top_k=3,
        include_metadata=True,
        namespace="vegento-data"
    )

    if filter_results.matches:
        print("\nFilter query successful")
        print(f"Found {len(filter_results.matches)} results")
    else:
        print("\nNo results with filters")



if __name__ == "__main__":
    # asyncio.run(test_soybean_queries())
    asyncio.run(debug_pinecone_index())