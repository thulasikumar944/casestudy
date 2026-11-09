import chromadb
import hashlib
import logging

from functools import lru_cache
from rapidfuzz import fuzz, process
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer

from app.core import settings
from app.core.sql_helper import get_db_connection

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Embedding Model
# --------------------------------------------------

@lru_cache(maxsize=1)
def get_embedding_model():

    logger.info("Loading Sentence Transformer model")

    return SentenceTransformer(settings.EMBEDDING_MODEL)


@lru_cache(maxsize=4)
def get_entity_names(collection_name, entity_field):

    collection = get_collection(collection_name)

    results = collection.get(include=["metadatas"])

    return tuple(
        metadata[entity_field]
        for metadata in results["metadatas"]
    )

# --------------------------------------------------
# ChromaDB Client
# --------------------------------------------------

@lru_cache(maxsize=1)
def get_chroma_client():

    return chromadb.PersistentClient(
        path=settings.CHROMA_DB_PATH
    )


def get_collection(collection_name: str):

    client = get_chroma_client()

    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )


# --------------------------------------------------
# Create Collections
# --------------------------------------------------

def create_collections():

    collections = [
        "chemical_names",
        "product_names"
    ]

    client = get_chroma_client()

    for collection_name in collections:

        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        logger.info(
            "Collection ready | Name: %s | Count: %s",
            collection_name,
            collection.count()
        )


# --------------------------------------------------
# Common Entity Ingestion
# --------------------------------------------------

def ingest_entity_names(
    column_name: str,
    collection_name: str,
    entity_field: str
):

    allowed_columns = {
        "ChemicalName",
        "ProductName"
    }

    if column_name not in allowed_columns:
        raise ValueError(f"Unsupported column: {column_name}")

    conn = get_db_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT DISTINCT TRIM({column_name})
            FROM cosmetics
            WHERE {column_name} IS NOT NULL
              AND TRIM({column_name}) != ''
        """)

        raw_names = [row[0] for row in cursor.fetchall()]

    finally:
        conn.close()

    # Normalize and deduplicate case-insensitively.
    unique_names = {}

    for name in raw_names:

        if not name:
            continue

        normalized_name = " ".join(name.split())

        if normalized_name:
            unique_names.setdefault(
                normalized_name.casefold(),
                normalized_name
            )

    entity_names = list(unique_names.values())

    if not entity_names:
        logger.warning("No entity names found for %s", column_name)
        return

    logger.info(
        "Starting ingestion | Collection: %s | Unique names: %s",
        collection_name,
        len(entity_names)
    )

    collection = get_collection(collection_name)
    embedding_model = get_embedding_model()

    batch_size = 100

    for start in range(0, len(entity_names), batch_size):

        batch = entity_names[start:start + batch_size]

        # Generate embeddings locally.
        embeddings = embedding_model.encode(
            batch,
            convert_to_numpy=True,
            normalize_embeddings=True
        ).tolist()

        # Stable IDs based on normalized entity names.
        ids = [
            hashlib.sha256(
                " ".join(name.split()).casefold().encode("utf-8")
            ).hexdigest()
            for name in batch
        ]

        # Safety check before ChromaDB upsert.
        if len(ids) != len(set(ids)):
            raise ValueError(
                f"Duplicate IDs detected in {collection_name} batch"
            )

        metadatas = [
            {entity_field: name}
            for name in batch
        ]

        collection.upsert(
            ids=ids,
            documents=batch,
            embeddings=embeddings,
            metadatas=metadatas
        )

        logger.info(
            "Ingestion progress | Collection: %s | Processed: %s/%s",
            collection_name,
            min(start + len(batch), len(entity_names)),
            len(entity_names)
        )

    logger.info(
        "Ingestion completed | Collection: %s | Count: %s",
        collection_name,
        collection.count()
    )


# --------------------------------------------------
# Common Entity Semantic Search
# --------------------------------------------------

def search_entity_name(
    query: str,
    collection_name: str,
    entity_field: str,
    top_k: int = 3
) -> list[dict]:

    collection = get_collection(collection_name)

    total_records = collection.count()

    if total_records == 0:
        logger.warning(
            "Collection is empty: %s",
            collection_name
        )
        return []

    embedding_model = get_embedding_model()

    query_embedding = embedding_model.encode(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, total_records),
        include=["documents", "metadatas", "distances"]
    )

    candidates = []

    for metadata, distance in zip(
        results["metadatas"][0],
        results["distances"][0]
    ):

        candidates.append({
            entity_field: metadata[entity_field],
            "distance": distance
        })

    return candidates


# --------------------------------------------------
# Delete Collections
# --------------------------------------------------

def delete_entity_collections():

    client = get_chroma_client()

    for collection_name in [
        "chemical_names",
        "product_names"
    ]:

        try:

            client.delete_collection(collection_name)

            logger.info(
                "Deleted collection: %s",
                collection_name
            )

        except Exception as exc:

            logger.warning(
                "Could not delete collection %s: %s",
                collection_name,
                exc
            )
def fuzzy_search_entity(
    query,
    collection_name,
    entity_field,
    top_k=3
):

    entity_names = get_entity_names(
        collection_name,
        entity_field
    )

    matches = process.extract(
        query,
        entity_names,
        scorer=fuzz.WRatio,
        limit=top_k
    )

    return [
        {
            entity_field: name,
            "fuzzy_score": score
        }
        for name, score, _ in matches
    ]

# --------------------------------------------------
# Main Execution
# --------------------------------------------------

if __name__ == "__main__":

    """# Run delete_entity_collections() only when
    # rebuilding collections or changing embedding models.

    # delete_entity_collections()

    # Step 1: Create collections
    create_collections()

    # Step 2: Ingest chemical names
    ingest_entity_names(
        column_name="ChemicalName",
        collection_name="chemical_names",
        entity_field="chemical_name"
    )

    # Step 3: Ingest product names
    ingest_entity_names(
        column_name="ProductName",
        collection_name="product_names",
        entity_field="product_name"
    )

    print("Vector database initialization completed.")"""

    results = fuzzy_search_entity(
    query="titanium dioxside",
    collection_name="chemical_names",
    entity_field="chemical_name"
    )

    print(results)
