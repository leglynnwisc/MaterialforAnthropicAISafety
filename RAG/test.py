import sys
import asyncio
import json
from neo4j import GraphDatabase
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone as PineconeVectorStore
import logging
import os
from dotenv import load_dotenv
from services.search import SearchService, EnhancedSearchService
import logging


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
#
#
#
# async def test_connections():
#     # Load environment variables
#     dotenv_path = os.path.join(os.path.dirname(__file__), "keys2.env")
#     load_dotenv(dotenv_path)
#
#     PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
#
#     try:
#         # Initialize Pinecone
#         logger.info("Initializing Pinecone connection...")
#         pc = Pinecone(api_key=PINECONE_API_KEY)
#
#         # List indexes to verify connection
#         indexes = pc.list_indexes()
#         logger.info(f"Available Pinecone indexes: {indexes}")
#
#         # Try to get specific index
#         index_name = "vegento-pdfs"  # Or whatever your index name is
#         index = pc.Index(index_name)
#
#         # Get index stats
#         stats = index.describe_index_stats()
#         logger.info(f"Index stats: {stats}")
#
#         # Try a simple query to verify data
#         query_response = index.query(
#             vector=[0.1] * 1536,  # Example vector - adjust dimension based on your embeddings
#             top_k=1,
#             include_metadata=True
#         )
#         logger.info(f"Sample query response: {query_response}")
#
#         return True
#
#     except Exception as e:
#         logger.error(f"Error testing connections: {e}")
#         return False
#
#
# async def test_vector_store():
#     search_service = SearchService(PINECONE_API_KEY, OPEN_AI_EMBEDDING_API_KEY)
#
#     # Try a basic similarity search first
#     basic_results = search_service.vectorstore.similarity_search(
#         "soybean",
#         k=5
#     )
#     print("\nBasic similarity search results:")
#     for doc in basic_results:
#         print(f"Content: {doc.page_content[:200]}...")
#
#     # Try the hybrid search with minimal filters
#     hybrid_results = search_service.advanced_hybrid_search(
#         "soybean",
#         filters={"should": {"crop_type": ["soybean"]}},
#         top_k=5
#     )
#
#     print("\nHybrid search results:")
#     for result in hybrid_results:
#         print(f"\nRelevance Score: {result.relevance_score}")
#         print(f"Text: {result.text[:200]}...")
#
#
# async def debug_search():
#     # Load environment variables
#     dotenv_path = os.path.join(os.path.dirname(__file__), "keys2.env")
#     load_dotenv(dotenv_path)
#
#     PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
#     OPEN_AI_EMBEDDING_API_KEY = os.getenv("OPEN_AI_EMBEDDING_API_KEY")
#
#     # Initialize services
#     pc = Pinecone(api_key=PINECONE_API_KEY)
#     embeddings = OpenAIEmbeddings(
#         model="text-embedding-3-small",
#         openai_api_key=OPEN_AI_EMBEDDING_API_KEY
#     )
#
#     # Test both indexes
#     indexes = ["vegento-tagged-data", "vegento-pdfs"]
#
#     for index_name in indexes:
#         logger.info(f"\nTesting index: {index_name}")
#
#         try:
#             # Get index
#             index = pc.Index(index_name)
#
#             # Get stats
#             stats = index.describe_index_stats()
#             logger.info(f"Index stats: {stats}")
#
#             # For vegento-tagged-data, use the vegento-data namespace
#             namespace = "vegento-data" if index_name == "vegento-tagged-data" else ""
#             logger.info(f"Using namespace: {namespace}")
#
#             # Initialize vector store
#             vectorstore = PineconeVectorStore(
#                 index=index,
#                 embedding=embeddings,
#                 text_key="text",
#                 namespace=namespace
#             )
#
#             # Test queries
#             test_queries = [
#                 "soybean pests",
#                 "soybean insects",
#                 "insects during soybean blooming",
#                 "wisconsin soybean management"
#             ]
#
#             for query in test_queries:
#                 logger.info(f"\nTesting query: {query}")
#
#                 try:
#                     # Try basic similarity search
#                     results = vectorstore.similarity_search(
#                         query,
#                         k=3
#                     )
#
#                     logger.info(f"Found {len(results)} results:")
#                     for i, doc in enumerate(results, 1):
#                         logger.info(f"\nResult {i}:")
#                         logger.info(f"Content: {doc.page_content[:200]}...")
#                         if hasattr(doc, 'metadata'):
#                             logger.info(f"Metadata: {doc.metadata}")
#
#                 except Exception as e:
#                     logger.error(f"Error performing search for query '{query}': {str(e)}")
#
#         except Exception as e:
#             logger.error(f"Error processing index {index_name}: {str(e)}")
#             continue
#
#
#
#
# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
#
# async def test_pipeline():
#     # Load environment variables
#     dotenv_path = os.path.join(os.path.dirname(__file__), "keys2.env")
#     load_dotenv(dotenv_path)
#
#     # Initialize service
#     search_service = EnhancedSearchService(
#         pinecone_api_key=os.getenv("PINECONE_API_KEY"),
#         openai_api_key=os.getenv("OPEN_AI_EMBEDDING_API_KEY"),
#         neo4j_uri=os.getenv("NEO4J_URI"),
#         neo4j_user=os.getenv("NEO4J_USERNAME"),
#         neo4j_password=os.getenv("NEO4J_PASSWORD")
#     )
#
#     # Test queries
#     test_queries = [
#         "soybean pests in wisconsin",
#         "insects during soybean blooming",
#         "wisconsin soybean management"
#     ]
#
#     for query in test_queries:
#         logger.info(f"\n{'=' * 50}")
#         logger.info(f"Testing query: {query}")
#
#         # Run debug search
#         results = search_service.debug_search(query)
#
#         # Analyze results
#         if results:
#             logger.info("\nTop enhanced results:")
#             for i, result in enumerate(results[:3]):
#                 logger.info(f"\nResult {i + 1}:")
#                 logger.info(f"Content: {result['content'][:200]}...")
#                 logger.info(f"Vector Score: {result['vector_score']}")
#                 logger.info(f"Graph Relationships: {len(result['relationships'])}")
#
#                 # Log relationship details
#                 for rel in result['relationships'][:3]:
#                     logger.info(f"Related: {rel}")
#         else:
#             logger.warning("No results found")
#
#
# def test_neo4j_connection():
#     # Load environment variables
#     dotenv_path = os.path.join(os.path.dirname(__file__), "keys2.env")
#     load_dotenv(dotenv_path)
#
#     # Neo4j Aura connection details
#     URI = "neo4j+s://baa455f5.databases.neo4j.io"
#     AUTH = (os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD"))
#
#     logger.info("Neo4j Aura Connection Details:")
#     logger.info(f"URI: {URI}")
#     logger.info(f"Username: {AUTH[0]}")
#     logger.info(f"Password set: {'Yes' if AUTH[1] else 'No'}")
#
#     try:
#         logger.info("Attempting to connect to Neo4j Aura...")
#         with GraphDatabase.driver(URI, auth=AUTH) as driver:
#             # Verify connectivity
#             driver.verify_connectivity()
#             logger.info("Successfully verified connectivity!")
#
#             # Test with a simple query
#             with driver.session() as session:
#                 # Get node count
#                 result = session.run("MATCH (n) RETURN count(n) as count")
#                 count = result.single()["count"]
#                 logger.info(f"Found {count} nodes in database")
#
#                 # Get node labels
#                 result = session.run("""
#                     MATCH (n)
#                     WITH DISTINCT labels(n) as labels
#                     RETURN labels
#                 """)
#                 logger.info("\nNode types in database:")
#                 for record in result:
#                     logger.info(f"- {record['labels']}")
#
#             return True
#
#     except Exception as e:
#         logger.error(f"Failed to connect to Neo4j Aura: {str(e)}")
#         if "unauthorized" in str(e).lower():
#             logger.error("\nAuthentication Error: Please check your username and password")
#         return False
#
#
#
#
#
# def inspect_tags():
#     # Load environment variables
#     dotenv_path = os.path.join(os.path.dirname(__file__), "keys2.env")
#     load_dotenv(dotenv_path)
#     logger = logging.getLogger(__name__)
#     logging.basicConfig(level=logging.INFO)
#
#     URI = "neo4j+s://baa455f5.databases.neo4j.io"
#     AUTH = (os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD"))
#
#     with GraphDatabase.driver(URI, auth=AUTH) as driver:
#         with driver.session() as session:
#             # Get sample tags with their properties
#
#             result = session.run("""
#                 MATCH (t:Tag)
#                 RETURN t, COUNT { (t)--() } as connections
#             """)
#
#             logger.info("\nTop 5 most connected tags:")
#             for record in result:
#                 tag = record["t"]
#                 connections = record["connections"]
#                 logger.info(f"\nTag Properties: {dict(tag)}")
#                 logger.info(f"Number of connections: {connections}")

from services.search import EnhancedSearchService  # Adjust the import to your file structure
# import os
# from dotenv import load_dotenv
# import logging
#
# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
# def test_specific_query():
#     """
#     Test the hybrid RAG pipeline with a specific query about insects and blooming soybeans in Wisconsin.
#     """
#     # Load environment variables
#     dotenv_path = os.path.join(os.path.dirname(__file__), "keys2.env")
#     load_dotenv(dotenv_path)
#
#     # Initialize EnhancedSearchService
#     search_service = EnhancedSearchService(
#         pinecone_api_key=os.getenv("PINECONE_API_KEY"),
#         openai_api_key=os.getenv("OPEN_AI_EMBEDDING_API_KEY"),
#         neo4j_username=os.getenv("NEO4J_USERNAME"),
#         neo4j_password=os.getenv("NEO4J_PASSWORD")
#     )
#
#     # Define the query and filters
#     query = "What insects are a problem in blooming soybeans in Wisconsin?"
#     filters = {
#         "must": {
#             "regions": ["wisconsin", "midwest"],
#             "crops": ["soybeans"]
#         },
#         "should": {
#             "pests": ["aphids", "japanese beetle", "Stink Bugs", "insects"],
#             "crop_health": ["pest resistance", "plant health"],
#             "management_practices": ["integrated pest management", "IPM", "monitoring"]
#         }
#     }
#
#     logger.info(f"\n{'=' * 50}")
#     logger.info(f"Testing query: {query}")
#
#     try:
#         # Perform the hybrid search
#         results = search_service.advanced_hybrid_search_with_context(query, filters)
#
#         # Analyze and log the results
#         if results:
#             logger.info("\nTop results:")
#             for i, result in enumerate(results[:5], 1):  # Limit to top 5 results
#                 logger.info(f"\nResult {i}:")
#                 logger.info(f"ID: {result.id}")
#                 logger.info(f"Relevance Score: {result.relevance_score}")
#                 logger.info(f"Text: {result.text[:200]}...")  # Display first 200 characters
#                 logger.info(f"Tags: {result.categories_matched}")
#                 logger.info("=" * 50)
#         else:
#             logger.warning("No results found for the query.")
#
#     except Exception as e:
#         logger.error(f"Error during query test: {e}")


async def debug_pinecone_index():
    # Load environment variables
    dotenv_path = os.path.join(os.path.dirname(__file__), "keys2.env")
    load_dotenv(dotenv_path)

    OPEN_AI_EMBEDDING_API_KEY = os.getenv("OPEN_AI_EMBEDDING_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    print("\nDebugging Pinecone Index...")

    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index("vegento-tagged-data")

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



# Add to your main test
if __name__ == "__main__":
    asyncio.run(debug_pinecone_index())
    asyncio.run(test_soybean_queries())


# if __name__ == "__main__":
#     # Test specific query
#     test_specific_query()

#
# if __name__ == "__main__":

#
#     if test_neo4j_connection():
#         logger.info("Neo4j Aura connection test successful!")
#     else:
#         logger.error("Neo4j Aura connection test failed!")
#
#     inspect_tags()




#     asyncio.run(test_connections())
#     asyncio.run(debug_search())
#     asyncio.run(test_pipeline())