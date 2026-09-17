# OpsPilot Spring RAG Microservice — UrbanThread Production Pipeline

> **Final-Year Project Technical Documentation & Viva Defense Guide**  
> **System**: OpsPilot — AI-Powered Autonomous Business Operations System  
> **Subsystem**: Production-Style Enterprise RAG Pipeline (Spring Boot 3 + Spring AI + PostgreSQL pgvector)  
> **Fictional Enterprise**: UrbanThread (Direct-to-Consumer Apparel & Lifestyle)

---

## 1. Executive Summary: Why RAG and NOT Fine-Tuning?

A central tenet of the OpsPilot architecture is that **Retrieval-Augmented Generation (RAG) is strictly separated from model fine-tuning**:
* **The LLM remains completely pretrained and frozen** (e.g., OpenAI `gpt-4o`, Anthropic Claude, or local Ollama `llama3`).
* **Why not fine-tune?**
  1. **Knowledge Freshness**: E-commerce policies (e.g., Diwali sale return windows, monsoon shipping delays, flash coupon thresholds) change weekly. Retraining or fine-tuning weights costs thousands of dollars and hours of compute. In RAG, updating a policy takes **<100 milliseconds** by re-indexing chunks in PostgreSQL.
  2. **Hallucination Prevention**: Fine-tuned models still hallucinate plausible-sounding numbers. With RAG, the model is strictly conditioned on retrieved context with the system instruction: *"Answer using ONLY the provided verified context chunks."*
  3. **Verifiable Grounded Citations**: Every sentence can be traced back to an exact document ID, chunk index, and policy snippet with a quantifiable confidence score.
  4. **Multi-Tenant Security**: Tenant A cannot see Tenant B's data because PostgreSQL queries filter on `organization_id = 'urbanthread'` at retrieval time—something fine-tuned weights cannot enforce.

---

## 2. End-to-End Architectural Pipeline

```
UrbanThread Documents & Website
(PDF, DOCX, TXT, MD, CSV, Web URLs)
               │
               ▼
   [1. Text Extraction Layer]
   (Apache Tika, POI, PDFBox, Jsoup, Commons CSV)
               │
               ▼
   [2. Text Normalization & Cleaning]
   (Strip boilerplate, normalize whitespace, sanitize control chars)
               │
               ▼
   [3. Recursive Sliding-Window Chunking]
   (500 chars/chunk, 80 chars overlap, boundary-aware splitting)
               │
               ▼
   [4. Dense Vector Embedding]
   (1536-dim vectors via Spring AI OpenAI / Zero-Cloud Deterministic Fallback)
               │
               ▼
   [5. PostgreSQL 15+ & pgvector Storage]
   (HNSW vector index m=16, ef=64 + TSVector English Lexical GIN index)
               │
               ▼
   [6. Query-Time Hybrid Retrieval & RRF Reranking]
   (Dense Cosine Top-K + Sparse Full-Text Top-K -> Reciprocal Rank Fusion)
               │
               ▼
   [7. Grounded Context Synthesis & Citations]
   (Context assembly -> Security Gate -> LLM / Grounded Extractor -> Aria Response)
```

---

## 3. Ingestion & Document Loaders

The ingestion engine supports 6 document types via [`DocumentLoaderFactory`](file:///Users/milindverma/Desktop/opsPilot/apps/spring-rag/src/main/java/com/urbanthread/opspilot/rag/service/loader/DocumentLoaderFactory.java):

| Format | Loader Implementation | Extraction Technology | Handling Details |
|---|---|---|---|
| **PDF** | `PdfDocumentLoader` | Apache PDFBox / Tika | Strips page headers/footers, extracts multi-page text cleanly |
| **DOCX** | `DocxDocumentLoader` | Apache POI (`XWPFDocument`) | Extracts structured paragraphs and table content |
| **Markdown** | `MarkdownDocumentLoader` | Regex & Header Parser | Preserves headings, converts markdown tables to readable text |
| **Text** | `TextDocumentLoader` | Standard UTF-8 Scanner | Cleans raw text files and policy manuals |
| **CSV** | `CsvDocumentLoader` | Apache Commons CSV | Converts tabular rows into semantic sentences (`Product X has size Y, price Z`) |
| **Web** | `WebDocumentLoader` | Jsoup HTML Parser | Connects via HTTP, strips `<script>`, `<style>`, `<nav>`, extracts main article |

---

## 4. Chunking Strategy

Implemented in [`ChunkingService`](file:///Users/milindverma/Desktop/opsPilot/apps/spring-rag/src/main/java/com/urbanthread/opspilot/rag/service/chunking/ChunkingService.java):
* **Chunk Size**: `500` characters (~100 to 125 tokens).
* **Chunk Overlap**: `80` characters.
* **Why Overlap?** Overlap prevents boundary cutoff where a crucial sentence (e.g., *"Refunds above ₹2,000 require manager approval"*) is split across two chunks and loses its semantic coherence.
* **Recursive Splitting**: Splits first on paragraph breaks (`\n\n`), then sentence periods (`. `), then space boundaries to ensure natural linguistic units.

---

## 5. PostgreSQL + pgvector Storage & Indexing

The schema in [`schema.sql`](file:///Users/milindverma/Desktop/opsPilot/apps/spring-rag/src/main/resources/schema.sql) defines two production tables:

```sql
-- Chunks table with 1536-dimensional vector and TSVector
CREATE TABLE rag_document_chunks (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
    organization_id VARCHAR(64) NOT NULL DEFAULT 'urbanthread',
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    token_count INT NOT NULL,
    tsv_content tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Fast Approximate Nearest Neighbor (ANN) Index
CREATE INDEX idx_rag_chunks_embedding_hnsw 
    ON rag_document_chunks USING hnsw (embedding vector_cosine_ops) 
    WITH (m = 16, ef_construction = 64);

-- Full-Text Lexical Search Index
CREATE INDEX idx_rag_chunks_tsv ON rag_document_chunks USING GIN(tsv_content);
```

### Why HNSW over IVFFlat?
* **IVFFlat (Inverted File Flat)** divides vectors into Voronoi cells. It requires an upfront training step on existing vectors. As new UrbanThread documents are added, quality degrades unless the index is rebuilt.
* **HNSW (Hierarchical Navigable Small World)** builds a multi-layer graph. It provides:
  1. **Sub-millisecond query time** ($O(\log N)$ graph traversal).
  2. **True incremental indexing** without retraining.
  3. **High recall (>98%)** even under continuous document insertions.

---

## 6. Hybrid Search & Reciprocal Rank Fusion (RRF)

Dense vector search is great at semantic understanding (e.g., *"give me my cash back"* matches *"Refund Policy"*), but can struggle with exact acronyms or SKUs (e.g., *"COD"*, *"UT-TSHIRT-001"*).

OpsPilot uses **Hybrid Search** combining:
1. **Dense Vector Search**: Cosine similarity $\frac{u \cdot v}{\|u\| \|v\|}$ against 1536-dimensional embeddings.
2. **Sparse Lexical Search**: PostgreSQL `tsquery` / BM25-style keyword matching.

### Reciprocal Rank Fusion Formula
Rather than normalizing disparate vector cosine scores and BM25 scores, OpsPilot applies **Reciprocal Rank Fusion (RRF)**:

$$RRF(d) = \sum_{m \in M} \frac{w_m}{k + r_m(d)}$$

Where:
* $M = \{\text{dense}, \text{lexical}\}$
* $w_{\text{dense}} = 0.70$, $w_{\text{lexical}} = 0.30$
* $k = 60$ (standard Cormack et al. constant smoothing factor)
* $r_m(d)$ is the rank (1-indexed) of document chunk $d$ in system $m$.

Chunks appearing in top ranks across **both** dense and lexical searches receive the highest consensus score.

---

## 7. Security: Prompt Injection Gate

Before any query hits the retrieval or LLM pipeline, it passes through the deterministic security gate in [`RagService`](file:///Users/milindverma/Desktop/opsPilot/apps/spring-rag/src/main/java/com/urbanthread/opspilot/rag/service/rag/RagService.java):
* Blocks instruction override attempts: `ignore all previous instructions`, `disregard`, `system prompt`, `reveal instructions`, `database password`.
* Immediately returns safe fallback response with `prompt_injection_detected = true` and zero chunks exposed.

---

## 8. API Specifications & cURL Testing

### 1. Health Check
```bash
curl -X GET http://localhost:8081/api/v1/rag/health
```

### 2. Ingest UrbanThread Policy Document
```bash
curl -X POST http://localhost:8081/api/v1/ingest/document \
  -H "Content-Type: application/json" \
  -d '{
    "title": "UrbanThread 30-Day Return & Exchange SOP",
    "category": "RETURN_POLICY",
    "documentType": "TXT",
    "content": "UrbanThread allows returns within 30 days of delivery. Items must have tags attached and remain unworn. High-value refunds exceeding ₹2,000 require store manager review. Standard refunds take 48 hours to process back to the original payment method.",
    "organizationId": "urbanthread"
  }'
```

### 3. Query RAG System
```bash
curl -X POST http://localhost:8081/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many days do I have to return an unworn jacket, and what is the approval limit?",
    "organizationId": "urbanthread",
    "topK": 3,
    "minSimilarity": 0.15
  }'
```

**Sample JSON Response**:
```json
{
  "query": "How many days do I have to return an unworn jacket, and what is the approval limit?",
  "answer": "According to UrbanThread 30-Day Return & Exchange SOP: Customers have 30 days from delivery to return unworn items with original tags. Refunds exceeding ₹2,000 require store manager review.",
  "is_grounded": true,
  "confidence_score": 0.94,
  "chunks_retrieved": 1,
  "latency_ms": 38,
  "model_used": "gpt-4o",
  "prompt_injection_detected": false,
  "citations": [
    {
      "document_id": "7b2e8f1c-4392-4d10-8b1e-39fae7c91823",
      "document_title": "UrbanThread 30-Day Return & Exchange SOP",
      "category": "RETURN_POLICY",
      "chunk_index": 0,
      "snippet": "UrbanThread allows returns within 30 days of delivery. Items must have tags attached and remain unworn. High-value refunds exceeding ₹2,000 require store manager review...",
      "confidence": 0.94
    }
  ]
}
```

---

## 9. Final-Year Viva Defense Q&A Sheet

### Q1: What makes your RAG system "Production-Style"?
> **Answer**: "Unlike toy RAG implementations that keep in-memory embeddings in Python arrays, OpsPilot uses:
> 1. Multi-format ingestion with document deduplication and SHA-256 checksums.
> 2. PostgreSQL with the `pgvector` extension and HNSW indexing for logarithmic ANN search.
> 3. Hybrid Search combining dense vector cosine similarity with sparse TSVector lexical search, fused using Reciprocal Rank Fusion (RRF).
> 4. Metadata filtering and multi-tenant partitioning (`organization_id`).
> 5. Deterministic prompt injection scanning at the ingress layer.
> 6. Grounded citations with confidence scores returned to the user."

### Q2: Why did you choose Reciprocal Rank Fusion (RRF)?
> **Answer**: "Vector similarity scores (cosine distance from 0 to 1) and full-text search scores (BM25 or TSVector ranking from 0 to $\infty$) operate on completely different statistical scales. Trying to linearly combine them with ad-hoc weights often skews results. RRF solves this by only considering the ordinal ranking ($r(d)$) from each retrieval algorithm, making it mathematically robust and resistant to outlier score scales."

### Q3: How do you handle security and malicious user prompts?
> **Answer**: "We employ a defense-in-depth model:
> 1. **Scanner Gate**: Queries matching instruction overrides or privilege escalation are blocked before vector lookup.
> 2. **Context Sandboxing**: Retrieved chunks are injected inside explicit XML/delimiter blocks (`--- VERIFIED KNOWLEDGE CHUNKS ---`), instructing the LLM to treat them strictly as reference data, never as executable commands.
> 3. **Tenant Scoping**: All database queries enforce `WHERE organization_id = ?` at the SQL level, preventing multi-tenant data leakage."
