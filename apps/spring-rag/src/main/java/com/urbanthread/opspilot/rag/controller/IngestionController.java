package com.urbanthread.opspilot.rag.controller;

import com.urbanthread.opspilot.rag.dto.request.IngestDocumentRequest;
import com.urbanthread.opspilot.rag.dto.request.IngestWebsiteRequest;
import com.urbanthread.opspilot.rag.dto.response.DocumentUploadResponse;
import com.urbanthread.opspilot.rag.service.IngestionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@Tag(name = "Data Ingestion API", description = "Multi-format document parsing and vector ingestion endpoints")
@RestController
@RequestMapping("/ingestion")
@RequiredArgsConstructor
public class IngestionController {

    private final IngestionService ingestionService;

    @Operation(summary = "Upload and parse file", description = "Upload PDF, DOCX, TXT, Markdown, or CSV. Automatically extracts, chunks, and indexes vectors.")
    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<DocumentUploadResponse> uploadFile(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "category", defaultValue = "COMPANY_POLICY") String category,
            @RequestParam(value = "organization_id", defaultValue = "urbanthread") String organizationId) {

        DocumentUploadResponse response = ingestionService.ingestFile(file, category, organizationId);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Ingest raw document text", description = "Directly ingests text content under a specified category and document type.")
    @PostMapping("/text")
    public ResponseEntity<DocumentUploadResponse> ingestText(@Valid @RequestBody IngestDocumentRequest request) {
        DocumentUploadResponse response = ingestionService.ingestDocument(request);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Crawl and ingest website URL", description = "Fetches an external or local website URL, extracts semantic body text, and indexes chunks.")
    @PostMapping("/website")
    public ResponseEntity<DocumentUploadResponse> ingestWebsite(@Valid @RequestBody IngestWebsiteRequest request) {
        DocumentUploadResponse response = ingestionService.ingestWebsite(request);
        return ResponseEntity.ok(response);
    }
}
