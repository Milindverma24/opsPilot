package com.urbanthread.opspilot.rag.domain.enums;

/**
 * Processing status for documents ingested into the RAG pipeline.
 */
public enum IngestionStatus {
    PENDING,
    PROCESSING,
    INDEXED,
    FAILED
}
