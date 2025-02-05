import os
from pinecone import Pinecone
from langchain_community.embeddings import OpenAIEmbeddings
import logging
import asyncio
import json
from collections import Counter
from typing import Dict, List, Set

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Set up API keys
PINECONE_API_KEY = '946c3781-26d7-4e46-a778-5262d54403f8'
OPENAI_API_KEY = "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"
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "vegento-tagged-data-md"
index = pc.Index(index_name)

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)


# Test Query and Validate Metadata Enhancement
async def verify_metadata_tagging():
    """Verify that metadata tagging is working correctly."""
    logger.info("Starting metadata verification...")

    # Initialize Pinecone client
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index("vegento-tagged-data-md")

    # Get index statistics
    stats = index.describe_index_stats()
    logger.info(f"Total vectors in index: {stats['total_vector_count']}")


    # Test queries that should match different metadata categories
    test_queries = [
        {
            "query": "soybean aphid management",
            "expected_categories": ["pests", "crops", "management_practices"]
        },
        {
            "query": "soil fertility in Wisconsin corn fields",
            "expected_categories": ["soil_management", "regions", "crops"]
        }
    ]

    for test in test_queries:
        logger.info(f"\nTesting query: {test['query']}")

        # Generate query embedding
        query_embedding = embeddings.embed_query(test['query'])

        # Query index
        results = index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True,
            namespace="vegento-data"
        )

        # Analyze results
        for i, match in enumerate(results.matches):
            logger.info(f"\nResult {i + 1}:")
            logger.info(f"Score: {match.score}")

            # Check metadata presence
            if not match.metadata:
                logger.warning("No metadata found!")
                continue

            # Check for expected categories
            found_categories = set()
            for category in test['expected_categories']:
                if category in match.metadata and match.metadata[category]:
                    found_categories.add(category)
                    logger.info(f"{category}: {match.metadata[category]}")

            # Report missing categories
            missing_categories = set(test['expected_categories']) - found_categories
            if missing_categories:
                logger.warning(f"Missing expected categories: {missing_categories}")

            # Print text preview
            text = match.metadata.get('text', '')
            if text:
                logger.info(f"Text preview: {text[:200]}...")


class MetadataDiagnostic:
    def __init__(self, pinecone_api_key: str, openai_api_key: str, index_name: str = "vegento-tagged-data-md"):
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index = self.pc.Index(index_name)
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    def analyze_index_metadata(self) -> Dict:
        """Analyze metadata distribution in the index."""
        stats = self.index.describe_index_stats()
        logger.info(f"Total vectors in index: {stats['total_vector_count']}")

        # Sample some vectors to analyze metadata structure
        sample_query = self.embeddings.embed_query("sample query for metadata analysis")
        results = self.index.query(
            vector=sample_query,
            top_k=100,  # Get a good sample size
            include_metadata=True
        )

        metadata_stats = {
            "category_distribution": Counter(),
            "empty_metadata": 0,
            "metadata_examples": {},
            "missing_text": 0
        }

        for match in results.matches:
            if not match.metadata:
                metadata_stats["empty_metadata"] += 1
                continue

            if 'text' not in match.metadata:
                metadata_stats["missing_text"] += 1

            for category in ['pests', 'crops', 'management_practices', 'regions', 'soil_management', 'crop_health']:
                if category in match.metadata and match.metadata[category]:
                    metadata_stats["category_distribution"][category] += 1
                    if category not in metadata_stats["metadata_examples"]:
                        metadata_stats["metadata_examples"][category] = match.metadata[category]

        return metadata_stats

    def test_specific_queries(self) -> None:
        """Test specific queries and analyze their metadata matching."""
        test_queries = [
            {
                "query": "soil fertility in Wisconsin corn fields",
                "text_must_contain": ["soil", "fertility", "wisconsin", "corn"],
                "expected_categories": {"soil_management", "regions", "crops"}
            },
            {
                "query": "soybean aphid management practices",
                "text_must_contain": ["soybean", "aphid", "management"],
                "expected_categories": {"crops", "pests", "management_practices"}
            }
        ]

        for test in test_queries:
            logger.info(f"\nTesting query: {test['query']}")
            query_embedding = self.embeddings.embed_query(test["query"])

            results = self.index.query(
                vector=query_embedding,
                top_k=5,
                include_metadata=True
            )

            for i, match in enumerate(results.matches):
                logger.info(f"\nResult {i + 1} (Score: {match.score:.3f}):")

                # Check text content
                if match.metadata.get('text'):
                    text = match.metadata['text'].lower()
                    contained_words = [word for word in test['text_must_contain']
                                       if word.lower() in text]
                    logger.info(f"Text preview: {text[:200]}...")
                    logger.info(f"Contains {len(contained_words)}/{len(test['text_must_contain'])} "
                                f"expected words: {contained_words}")
                else:
                    logger.warning("No text field in metadata!")

                # Check metadata categories
                found_categories = {cat for cat in test['expected_categories']
                                    if cat in match.metadata and match.metadata[cat]}

                for category in found_categories:
                    logger.info(f"{category}: {match.metadata[category]}")

                missing = test['expected_categories'] - found_categories
                if missing:
                    logger.warning(f"Missing expected categories: {missing}")


def main():
    diagnostic = MetadataDiagnostic(
        pinecone_api_key=PINECONE_API_KEY,
        openai_api_key=OPENAI_API_KEY
    )

    # Analyze overall metadata distribution
    logger.info("\n=== Analyzing Index Metadata ===")
    stats = diagnostic.analyze_index_metadata()
    logger.info("\nMetadata Statistics:")
    logger.info(f"Category Distribution: {dict(stats['category_distribution'])}")
    logger.info(f"Records with Empty Metadata: {stats['empty_metadata']}")
    logger.info(f"Records Missing Text Field: {stats['missing_text']}")
    logger.info("\nExample Metadata Values:")
    for category, examples in stats['metadata_examples'].items():
        logger.info(f"{category}: {examples}")

    # Test specific queries
    logger.info("\n=== Testing Specific Queries ===")
    diagnostic.test_specific_queries()


if __name__ == "__main__":
    main()

# if __name__ == "__main__":
#     asyncio.run(verify_metadata_tagging())
