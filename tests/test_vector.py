from app.core.vector_helper import (
    get_chroma_client,
    search_entity_name
)

# Check collections
client = get_chroma_client()

for collection in client.list_collections():
    print(
        f"Collection: {collection.name} | "
        f"Records: {collection.count()}"
    )

# Test chemical search
print("\nChemical Search:")

chemical_results = search_entity_name(
    query="titanium dioxside",
    collection_name="chemical_names",
    entity_field="chemical_name",
    top_k=3
)

print(chemical_results)


# Test product search
print("\nProduct Search:")

product_results = search_entity_name(
    query="ultra color rich lipstick",
    collection_name="product_names",
    entity_field="product_name",
    top_k=3
)

print(product_results)