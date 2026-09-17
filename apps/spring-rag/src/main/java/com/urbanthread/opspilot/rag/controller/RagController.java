package com.urbanthread.opspilot.rag.controller;

import com.urbanthread.opspilot.rag.dto.request.RagQueryRequest;
import com.urbanthread.opspilot.rag.dto.response.RagResponse;
import com.urbanthread.opspilot.rag.service.rag.RagService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@Tag(name = "RAG Query API", description = "Retrieval-Augmented Generation endpoints with hybrid search and grounded citations")
@RestController
@RequestMapping("/rag")
@RequiredArgsConstructor
public class RagController {

    private final RagService ragService;

    @Operation(summary = "Query RAG knowledge base", description = "Performs hybrid retrieval (vector cosine + BM25), metadata filtering, RRF reranking, and generates a grounded response with source citations.")
    @PostMapping("/query")
    public ResponseEntity<RagResponse> query(@Valid @RequestBody RagQueryRequest request) {
        RagResponse response = ragService.answerQuery(request);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "RAG microservice health check")
    @GetMapping("/health")
    public ResponseEntity<java.util.Map<String, Object>> health() {
        return ResponseEntity.ok(java.util.Map.of(
                "status", "UP",
                "subsystem", "OpsPilot Spring RAG Microservice",
                "organization", "urbanthread",
                "vector_dimensions", 1536
        ));
    }
}
