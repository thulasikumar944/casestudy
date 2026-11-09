# Multi-Agent Orchestrator for Chemical Disclosure RAG

## 1. Project Overview

This project implements a multi-agent RAG system that answers questions using the California Safe Cosmetics Program chemical disclosure dataset.

The system combines structured SQL retrieval and semantic search to identify relevant chemical, product, brand, and company information. It uses an orchestrator to determine the appropriate retrieval strategy and generates answers grounded in retrieved records.

## 2. Technology Stack

- Python
- LangGraph – agent orchestration and workflow management
- SQLite – structured data storage and SQL queries
- ChromaDB – vector storage and semantic retrieval
- Sentence Transformers – text embeddings
- LLM – entity extraction, SQL generation, and answer synthesis
- FastAPI – API interface

## 3. Implemented Capabilities

### Multi-Agent Workflow
- Entity extraction from natural-language questions.
- Entity validation against the available dataset.
- Orchestrator-based routing.
- Structured SQL retrieval.
- Semantic retrieval for unresolved chemical and product names.
- Answer synthesis using retrieved records.

### Structured Retrieval
- SQL query generation based on extracted entities and filters.
- SQL validation to restrict execution to safe SELECT queries.
- SQLite query execution.
- Support for filtering and retrieving product, chemical, brand, and company information.

### Semantic Retrieval
- ChromaDB collections for chemical and product names.
- Embedding-based similarity search.
- Fuzzy matching for spelling variations.
- Canonical entity resolution before structured SQL retrieval.

### Explainability and Logging
- Query plan and routing reason.
- Generated SQL logging.
- Semantic matching results.
- Agent execution logs and error handling.

### API
- FastAPI application.
- Health-check endpoint.
- Question-answering endpoint.

## 4. Workflow

1. User submits a natural-language question.
2. Entity extractor identifies intent, entities, and filters.
3. Entity validation checks extracted entities against the dataset.
4. Orchestrator selects the retrieval strategy.
5. Semantic retrieval resolves eligible unresolved entities when required.
6. SQL agent retrieves matching records from SQLite.
7. Answer synthesizer generates a response based on retrieved data.
8. The API returns the answer.

## 5. Current Limitations

The current implementation demonstrates the core architecture and retrieval workflow. Some capabilities require additional testing and refinement:

- Broader testing across all supported intents.
- Improved handling of ambiguous and incomplete questions.
- Calibration of semantic similarity and fuzzy-matching thresholds.
- Verification of row-level citations and evidence completeness.
- Improved handling of large result sets and complex comparisons.
- More comprehensive evaluation of generated answers and SQL queries.

## 6. Enhancements Required



- Add a golden evaluation dataset with expected answers and SQL queries.
- Evaluate retrieval quality, answer faithfulness, and citation correctness.
- Improve entity resolution using chemical synonyms and domain-specific dictionaries.
- Add advanced multi-step planning for complex questions.



## 7. Running the Application

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --reload
```

Open Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /health
```

Question endpoint:

```text
POST /ask
```

Example request:

```json
{
  "question": "Find products containing Titanium dioxide"
}
```

