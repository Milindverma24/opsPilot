package com.urbanthread.opspilot.rag;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Main Entry Point for OpsPilot Spring Boot RAG Microservice.
 * Provides production-grade knowledge ingestion, vector retrieval with pgvector, and grounded generation.
 */
@SpringBootApplication
public class OpsPilotRagApplication {

    public static void main(String[] args) {
        SpringApplication.run(OpsPilotRagApplication.class, args);
    }
}
