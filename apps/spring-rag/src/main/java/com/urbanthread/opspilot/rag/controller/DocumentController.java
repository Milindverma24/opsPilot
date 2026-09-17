package com.urbanthread.opspilot.rag.controller;

import com.urbanthread.opspilot.rag.domain.entity.DocumentEntity;
import com.urbanthread.opspilot.rag.repository.DocumentRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Tag(name = "Document Management API", description = "Query and manage indexed enterprise documents in the RAG store")
@RestController
@RequestMapping("/documents")
@RequiredArgsConstructor
public class DocumentController {

    private final DocumentRepository documentRepository;

    @Operation(summary = "List all indexed documents", description = "Retrieves all indexed documents for the organization.")
    @GetMapping
    public ResponseEntity<List<DocumentEntity>> listDocuments(
            @RequestParam(value = "organization_id", defaultValue = "urbanthread") String organizationId) {
        List<DocumentEntity> docs = documentRepository.findByOrganizationId(organizationId);
        return ResponseEntity.ok(docs);
    }

    @Operation(summary = "Get document by ID", description = "Retrieves document metadata.")
    @GetMapping("/{id}")
    public ResponseEntity<DocumentEntity> getDocument(@PathVariable String id) {
        return documentRepository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @Operation(summary = "Delete indexed document", description = "Removes document and all associated vector chunks.")
    @DeleteMapping("/{id}")
    public ResponseEntity<Map<String, String>> deleteDocument(@PathVariable String id) {
        if (!documentRepository.existsById(id)) {
            return ResponseEntity.notFound().build();
        }
        documentRepository.deleteById(id);
        return ResponseEntity.ok(Map.of("message", "Document and associated chunks deleted successfully", "id", id));
    }
}
