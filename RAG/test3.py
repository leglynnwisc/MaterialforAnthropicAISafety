import logging
from typing import re

from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
import json
import os
from dotenv import load_dotenv
import re as regex  # Renamed to avoid confusion
from tqdm.auto import tqdm
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), "keys2.env")
load_dotenv(dotenv_path)


# def verify_index_update():
#     """Comprehensive verification of Pinecone index content"""
#
#     # Initialize connections
#     pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
#     embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
#     index = pc.Index("vegento-tagged-data")
#
#     # 1. Check index statistics
#     stats = index.describe_index_stats()
#     logger.info("\nIndex Statistics:")
#     logger.info(f"Total vectors: {stats.total_vector_count}")
#     logger.info(f"Dimension: {stats.dimension}")
#     for namespace, ns_stats in stats.namespaces.items():
#         logger.info(f"Namespace '{namespace}': {ns_stats.vector_count} vectors")
#
#     # 2. Test queries for known content
#     test_queries = [
#         "soybean pests in wisconsin",
#         "alfalfa management practices",
#         "wheat crop diseases"
#     ]
#
#     logger.info("\nTesting queries for content verification:")
#     for query in test_queries:
#         logger.info(f"\nQuery: {query}")
#
#         # Generate embedding
#         query_vector = embeddings.embed_query(query)
#
#         # Search with metadata
#         results = index.query(
#             vector=query_vector,
#             top_k=3,
#             include_metadata=True,
#             namespace="vegento-data"
#         )
#
#         if results.matches:
#             logger.info(f"Found {len(results.matches)} matches")
#             for i, match in enumerate(results.matches, 1):
#                 logger.info(f"\nMatch {i}:")
#                 logger.info(f"Score: {match.score:.3f}")
#                 logger.info("Metadata fields: " + ", ".join(match.metadata.keys()))
#                 # Check if text is present
#                 if "text" in match.metadata:
#                     logger.info(f"Text preview: {match.metadata['text'][:100]}...")
#                 # Check for tags
#                 for tag_type in ["crops", "pests", "regions", "management_practices"]:
#                     if tag_type in match.metadata:
#                         logger.info(f"{tag_type}: {match.metadata[tag_type]}")
#         else:
#             logger.warning("No matches found for query")
#
#     # 3. Verify metadata structure
#     logger.info("\nVerifying metadata structure:")
#     sample_query = index.query(
#         vector=[0.1] * 1536,  # dummy vector
#         top_k=1,
#         include_metadata=True
#     )
#
#     if sample_query.matches:
#         metadata = sample_query.matches[0].metadata
#         logger.info("Metadata fields present:")
#         for field, value in metadata.items():
#             logger.info(f"{field}: {type(value).__name__}")
#             if isinstance(value, list):
#                 logger.info(f"  Sample values: {value[:3]}")
#     else:
#         logger.warning("Could not retrieve sample for metadata verification")
#
#
# import logging
# from collections import defaultdict
# from pinecone import Pinecone
# import json
#
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
#
# def analyze_metadata(index, namespace="vegento-data", sample_size=100):
#     """Detailed analysis of metadata structure and content"""
#
#     # Get random sample of vectors
#     query_vector = [0.1] * 1536  # dummy vector
#     results = index.query(
#         vector=query_vector,
#         top_k=sample_size,
#         include_metadata=True,
#         namespace=namespace
#     )
#
#     # Initialize counters
#     metadata_stats = {
#         'total_docs': 0,
#         'has_text': 0,
#         'field_counts': defaultdict(int),
#         'empty_fields': defaultdict(int),
#         'tag_examples': defaultdict(set)
#     }
#
#     if results.matches:
#         metadata_stats['total_docs'] = len(results.matches)
#
#         for match in results.matches:
#             metadata = match.metadata
#
#             # Check text field
#             if 'text' in metadata:
#                 metadata_stats['has_text'] += 1
#
#             # Analyze each field
#             for field, value in metadata.items():
#                 metadata_stats['field_counts'][field] += 1
#
#                 if isinstance(value, list):
#                     if not value:
#                         metadata_stats['empty_fields'][field] += 1
#                     else:
#                         # Collect some examples of non-empty tags
#                         metadata_stats['tag_examples'][field].update(value[:3])
#
#         # Print analysis
#         logger.info(f"\nAnalyzed {metadata_stats['total_docs']} documents:")
#         logger.info(f"Documents with text field: {metadata_stats['has_text']}")
#
#         logger.info("\nField Statistics:")
#         for field in metadata_stats['field_counts']:
#             present = metadata_stats['field_counts'][field]
#             empty = metadata_stats['empty_fields'].get(field, 0)
#             logger.info(f"\n{field}:")
#             logger.info(f"  Present in {present}/{metadata_stats['total_docs']} documents")
#             logger.info(f"  Empty in {empty}/{present} documents")
#             if field in metadata_stats['tag_examples']:
#                 logger.info(f"  Sample tags: {list(metadata_stats['tag_examples'][field])[:5]}")
#
#     return metadata_stats
#
#
# def test_specific_content(index, text_sample="soybean aphid"):
#     """Find and analyze documents containing specific text"""
#     logger.info(f"\nSearching for documents containing: '{text_sample}'")
#
#     # Use dummy vector but large k to get a good sample
#     results = index.query(
#         vector=[0.1] * 1536,
#         top_k=100,
#         include_metadata=True
#     )
#
#     found_docs = []
#     for match in results.matches:
#         if text_sample.lower() in match.metadata.get('text', '').lower():
#             found_docs.append(match)
#
#     if found_docs:
#         logger.info(f"\nFound {len(found_docs)} matching documents")
#         for i, doc in enumerate(found_docs[:3], 1):
#             logger.info(f"\nDocument {i}:")
#             logger.info(f"Text preview: {doc.metadata.get('text', '')[:200]}...")
#             logger.info("Tags:")
#             for field in ['crops', 'pests', 'regions', 'management_practices']:
#                 logger.info(f"  {field}: {doc.metadata.get(field, [])}")
#     else:
#         logger.warning("No matching documents found")
#
#
# if __name__ == "__main__":
#     pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
#     index = pc.Index("vegento-tagged-data")
#
#     # Run analysis
#     stats = analyze_metadata(index)
#
#     # Test specific content
#     test_specific_content(index, "soybean aphid")
#     test_specific_content(index, "wisconsin alfalfa")
#
# if __name__ == "__main__":
#     # verify_index_update()
#     pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
#     index = pc.Index("vegento-tagged-data")
#
#     # Run analysis
#     stats = analyze_metadata(index)
#
#     # Test specific content
#     test_specific_content(index, "soybean aphid")
#     test_specific_content(index, "wisconsin alfalfa")

import os
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# def check_index_content():
#     # Initialize connections
#     pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
#     embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
#     index = pc.Index("vegento-tagged-data-md")
#
#     # Get index statistics
#     stats = index.describe_index_stats()
#     logger.info("\nIndex Statistics:")
#     logger.info(f"Total vectors: {stats.total_vector_count}")
#
#     # Check metadata structure
#     logger.info("\nChecking metadata structure...")
#     sample_vector = [0.1] * 1536  # dummy vector for sampling
#     results = index.query(
#         vector=sample_vector,
#         top_k=5,
#         include_metadata=True
#     )
#
#     if results.matches:
#         logger.info(f"\nFound {len(results.matches)} sample documents")
#         for i, match in enumerate(results.matches):
#             logger.info(f"\nDocument {i + 1}:")
#             logger.info(f"ID: {match.id}")
#             metadata = match.metadata
#             logger.info("Metadata fields present:")
#             for field, value in metadata.items():
#                 if isinstance(value, list):
#                     logger.info(f"{field}: {value}")
#                 else:
#                     logger.info(f"{field}: {value[:100]}..." if field == 'text' else f"{field}: {value}")
#
#     # Test specific queries for the volunteer wheat content
#     test_queries = [
#         "What are the effects of volunteer wheat in Wisconsin alfalfa fields?",
#         "How does volunteer wheat impact alfalfa establishment?",
#         "What are the management practices for volunteer wheat in alfalfa?"
#     ]
#
#     logger.info("\nTesting specific queries...")
#     for query in test_queries:
#         logger.info(f"\nQuery: {query}")
#         vector = embeddings.embed_query(query)
#
#         results = index.query(
#             vector=vector,
#             top_k=2,
#             include_metadata=True
#         )
#
#         if results.matches:
#             for i, match in enumerate(results.matches):
#                 logger.info(f"\nMatch {i + 1} (Score: {match.score:.3f})")
#                 logger.info(f"Text: {match.metadata.get('text', '')[:200]}...")
#                 for field in ['crops', 'pests', 'regions', 'management_practices']:
#                     if match.metadata.get(field):
#                         logger.info(f"{field}: {match.metadata[field]}")
#         else:
#             logger.warning("No matches found")
#
#
# if __name__ == "__main__":
#     check_index_content()


class MetadataEnhancer:
    def __init__(self):
        # Region patterns
        self.region_patterns = {
            'wisconsin': r'wisconsin|wisc\.|wi\b',
            'midwest': r'midwest|mid-west|midwestern|upper midwest',
            'illinois': r'illinois|il\b',
            'iowa': r'iowa|ia\b',
            'minnesota': r'minnesota|mn\b',
            'michigan': r'michigan|mi\b'
        }

        # Management practice patterns
        self.management_patterns = {
            'chemical control': r'roundup|poast plus|raptor|herbicide|chemical|spray',
            'application timing': r'timing|application|applied|treatment',
            'monitoring': r'monitor|scout|observe|inspect',
            'ipm': r'ipm|integrated pest management',
            'cultural control': r'rotation|planting date|seeding rate',
            'mechanical control': r'tillage|cultivation|mechanical',
            'biological control': r'natural enemies|predators|parasites'
        }

        # Common agricultural terms
        self.practice_indicators = {
            'rate': r'rate|\d+\s*(oz|lb|pt|gal)/acre',
            'timing': r'stage|growth stage|early|late|before|after',
            'method': r'broadcast|foliar|soil applied|incorporation'
        }

    def find_pattern_matches(self, text: str, patterns: Dict[str, str]) -> List[str]:
        """Find matches using regex patterns"""
        matches = []
        text_lower = text.lower()

        for name, pattern in patterns.items():
            try:
                if regex.search(pattern, text_lower, regex.IGNORECASE):
                    matches.append(name)
            except Exception as e:
                logger.error(f"Error matching pattern '{pattern}': {str(e)}")
                continue

        return matches

    def enhance_metadata(self, text: str, current_metadata: dict) -> dict:
        """Enhance metadata with better tag extraction"""
        if not text:
            return current_metadata

        enhanced_metadata = current_metadata.copy()
        text_lower = text.lower()

        try:
            # Extract regions
            regions = self.find_pattern_matches(text, self.region_patterns)
            if regions:
                current_regions = enhanced_metadata.get('regions', [])
                enhanced_metadata['regions'] = list(set(current_regions + regions))

            # Extract management practices
            practices = self.find_pattern_matches(text, self.management_patterns)
            practice_indicators = self.find_pattern_matches(text, self.practice_indicators)

            if practices or practice_indicators:
                all_practices = practices + [f"{p}_management" for p in practice_indicators]
                current_practices = enhanced_metadata.get('management_practices', [])
                enhanced_metadata['management_practices'] = list(set(current_practices + all_practices))

            # Add context-based tags
            context_words = {
                'crop_health': ['yield', 'growth', 'development', 'stress'],
                'soil_management': ['soil', 'tillage', 'organic matter', 'fertility'],
                'pests': ['pest', 'disease', 'insect', 'weed']
            }

            for category, words in context_words.items():
                if any(word in text_lower for word in words):
                    current_tags = enhanced_metadata.get(category, [])
                    if category == 'crop_health':
                        current_tags.append('crop performance')
                    elif category == 'soil_management':
                        current_tags.append('soil condition')
                    elif category == 'pests' and 'pest' not in current_tags:
                        current_tags.append('pest')
                    enhanced_metadata[category] = list(set(current_tags))

        except Exception as e:
            logger.error(f"Error enhancing metadata: {str(e)}")
            return current_metadata

        return enhanced_metadata


def enhance_index_metadata(index_name: str = "vegento-tagged-data-md", batch_size: int = 50):
    """Enhance metadata for all documents in the index"""
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(index_name)
    enhancer = MetadataEnhancer()

    processed = 0
    enhanced = 0

    logger.info("Starting metadata enhancement process...")

    try:
        # Get initial batch
        results = index.query(
            vector=[0.1] * 1536,
            top_k=batch_size,
            include_metadata=True
        )

        while results.matches:
            updates = []

            for match in tqdm(results.matches, desc="Processing documents"):
                processed += 1

                try:
                    current_metadata = match.metadata
                    text = current_metadata.get('text', '')

                    if not text:
                        continue

                    enhanced_metadata = enhancer.enhance_metadata(text, current_metadata)

                    # Check for changes
                    changed = False
                    for key in enhanced_metadata:
                        if isinstance(enhanced_metadata[key], list):
                            if set(enhanced_metadata[key]) != set(current_metadata.get(key, [])):
                                changed = True
                                break

                    if changed:
                        updates.append({
                            "id": match.id,
                            "values": match.values,
                            "metadata": enhanced_metadata
                        })
                        enhanced += 1

                        # Log first few changes
                        if enhanced <= 3:
                            logger.info(f"\nEnhanced document {match.id}:")
                            for key in enhanced_metadata:
                                if isinstance(enhanced_metadata[key], list):
                                    old_tags = set(current_metadata.get(key, []))
                                    new_tags = set(enhanced_metadata[key])
                                    added_tags = new_tags - old_tags
                                    if added_tags:
                                        logger.info(f"Added {key}: {added_tags}")

                except Exception as e:
                    logger.error(f"Error processing document {match.id}: {str(e)}")
                    continue

            # Update batch if needed
            if updates:
                try:
                    index.upsert(vectors=updates)
                    logger.info(f"Updated batch of {len(updates)} documents")
                except Exception as e:
                    logger.error(f"Error updating documents: {e}")

            # Get next batch
            if len(results.matches) == batch_size:
                results = index.query(
                    vector=[0.1] * 1536,
                    top_k=batch_size,
                    include_metadata=True
                )
            else:
                break

        logger.info(f"\nProcessing complete:")
        logger.info(f"Total documents processed: {processed}")
        logger.info(f"Documents enhanced: {enhanced}")

    except Exception as e:
        logger.error(f"Error during batch processing: {str(e)}")


import os
from pinecone import Pinecone
from langchain_community.embeddings import OpenAIEmbeddings
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Pinecone and OpenAI API keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Pinecone and connect to the index
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "vegento-tagged-data-md"
index = pc.Index(index_name)

# Define the batch size
BATCH_SIZE = 100  # Number of documents to process per batch

# Initialize Metadata Enhancer
enhancer = MetadataEnhancer()


def process_and_update_index(index, batch_size=100):
    """Process all documents in the index and update metadata."""
    logger.info("Starting metadata enhancement for the entire index...")

    # Get total number of documents in the index
    stats = index.describe_index_stats()
    total_vectors = stats.total_vector_count
    logger.info(f"Total vectors in the index: {total_vectors}")

    # Initialize progress tracker
    processed_count = 0
    successful_updates = 0

    # Process the index in batches
    while processed_count < total_vectors:
        logger.info(f"Processing batch {processed_count // batch_size + 1}...")

        # Query the next batch of vectors
        results = index.query(
            vector=[0.1] * 1536,  # Dummy vector
            top_k=batch_size,
            include_metadata=True,
            include_values=True
        )

        if not results.matches:
            logger.info("No more vectors to process.")
            break

        updates = []
        for match in results.matches:
            try:
                # Extract current metadata and text
                current_metadata = match.metadata
                text_fragments = current_metadata.get('text', '').split('. ')  # Split text into fragments

                # Apply metadata enhancement
                metadata_batch = enhance_metadata_for_fragments(text_fragments, enhancer, current_metadata)
                metadata_ngrams = enhance_metadata_with_ngrams(text_fragments, enhancer, current_metadata)
                metadata_window = enhance_metadata_with_sliding_window(text_fragments, enhancer, current_metadata)

                # Aggregate enhanced metadata
                enhanced_metadata = metadata_batch.copy()
                for key in metadata_ngrams:
                    enhanced_metadata[key] = list(set(enhanced_metadata.get(key, []) + metadata_ngrams[key]))
                for key in metadata_window:
                    enhanced_metadata[key] = list(set(enhanced_metadata.get(key, []) + metadata_window[key]))

                # Prepare the update object
                update = {
                    "id": match.id,
                    "values": match.values,  # Retain the original embedding
                    "metadata": enhanced_metadata
                }
                updates.append(update)

            except Exception as e:
                logger.error(f"Error processing document {match.id}: {e}")

        # Upload the updated batch to the index
        if updates:
            try:
                index.upsert(vectors=updates)
                successful_updates += len(updates)
                logger.info(f"Successfully updated {len(updates)} vectors in this batch.")
            except Exception as e:
                logger.error(f"Error updating batch: {e}")

        # Update the processed count
        processed_count += len(results.matches)

    logger.info(f"Metadata enhancement complete. Total updates: {successful_updates}/{total_vectors}")


# Run the full update
if __name__ == "__main__":
    process_and_update_index(index, BATCH_SIZE)

