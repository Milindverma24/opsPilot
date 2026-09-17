package com.urbanthread.opspilot.rag.service;

import com.urbanthread.opspilot.rag.domain.entity.DocumentChunkEntity;
import com.urbanthread.opspilot.rag.domain.entity.DocumentEntity;
import com.urbanthread.opspilot.rag.domain.enums.DocumentType;
import com.urbanthread.opspilot.rag.domain.enums.IngestionStatus;
import com.urbanthread.opspilot.rag.dto.request.IngestDocumentRequest;
import com.urbanthread.opspilot.rag.dto.request.IngestWebsiteRequest;
import com.urbanthread.opspilot.rag.dto.response.DocumentUploadResponse;
import com.urbanthread.opspilot.rag.exception.RagException;
import com.urbanthread.opspilot.rag.repository.DocumentChunkRepository;
import com.urbanthread.opspilot.rag.repository.DocumentRepository;
import com.urbanthread.opspilot.rag.service.chunking.ChunkingService;
import com.urbanthread.opspilot.rag.service.embedding.EmbeddingService;
import com.urbanthread.opspilot.rag.service.loader.DocumentLoader;
import com.urbanthread.opspilot.rag.service.loader.DocumentLoaderFactory;
import com.urbanthread.opspilot.rag.service.loader.WebDocumentLoader;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.security.MessageDigest;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class IngestionService {

    private final DocumentRepository documentRepository;
    private final DocumentChunkRepository chunkRepository;
    private final DocumentLoaderFactory loaderFactory;
    private final ChunkingService chunkingService;
    private final EmbeddingService embeddingService;
    private final WebDocumentLoader webDocumentLoader;

    @Transactional
    public DocumentUploadResponse ingestDocument(IngestDocumentRequest request) {
        log.info("Ingesting document text: '{}' ({})", request.getTitle(), request.getDocumentType());
        String docId = UUID.randomUUID().toString();
        String checksum = computeChecksum(request.getContent().getBytes());

        DocumentEntity document = DocumentEntity.builder()
                .id(docId)
                .organizationId(request.getOrganizationId() != null ? request.getOrganizationId() : "urbanthread")
                .title(request.getTitle())
                .category(request.getCategory() != null ? request.getCategory() : "GENERAL_SOP")
                .documentType(request.getDocumentType())
                .sourceUrl(request.getSourceUrl())
                .fileSizeBytes((long) request.getContent().length())
                .checksum(checksum)
                .status(IngestionStatus.PROCESSING)
                .createdAt(OffsetDateTime.now())
                .updatedAt(OffsetDateTime.now())
                .build();

        document = documentRepository.save(document);

        // Chunk and Embed
        List<String> textChunks = chunkingService.chunkText(request.getContent());
        List<DocumentChunkEntity> chunkEntities = new ArrayList<>();

        for (int i = 0; i < textChunks.size(); i++) {
            String chunkContent = textChunks.get(i);
            float[] embedding = embeddingService.computeEmbedding(chunkContent);

            DocumentChunkEntity chunkEntity = DocumentChunkEntity.builder()
                    .id(UUID.randomUUID().toString())
                    .document(document)
                    .organizationId(document.getOrganizationId())
                    .chunkIndex(i)
                    .content(chunkContent)
                    .tokenCount(chunkContent.split("\\s+").length)
                    .embeddingVector(embeddingService.vectorToString(embedding))
                    .createdAt(OffsetDateTime.now())
                    .build();

            chunkEntities.add(chunkEntity);
        }

        chunkRepository.saveAll(chunkEntities);

        document.setStatus(IngestionStatus.INDEXED);
        documentRepository.save(document);

        log.info("Successfully ingested and indexed document '{}' with {} vector chunks", document.getTitle(), chunkEntities.size());

        return DocumentUploadResponse.builder()
                .documentId(document.getId())
                .title(document.getTitle())
                .category(document.getCategory())
                .documentType(document.getDocumentType())
                .status(document.getStatus())
                .chunksCreated(chunkEntities.size())
                .fileSizeBytes(document.getFileSizeBytes())
                .checksum(document.getChecksum())
                .indexedAt(document.getUpdatedAt())
                .message("Document parsed, chunked, and vector indexed successfully.")
                .build();
    }

    @Transactional
    public DocumentUploadResponse ingestFile(MultipartFile file, String category, String organizationId) {
        if (file.isEmpty()) {
            throw new RagException("Uploaded file is empty");
        }

        String filename = file.getOriginalFilename() != null ? file.getOriginalFilename() : "uploaded_document";
        DocumentType docType = loaderFactory.detectTypeFromFilename(filename);
        DocumentLoader loader = loaderFactory.getLoader(docType);

        String extractedText = loader.extractText(file);
        if (extractedText == null || extractedText.trim().isEmpty()) {
            throw new RagException("Failed to extract any text content from uploaded file: " + filename);
        }

        IngestDocumentRequest req = IngestDocumentRequest.builder()
                .title(filename)
                .category(category != null ? category : "COMPANY_POLICY")
                .documentType(docType)
                .content(extractedText)
                .organizationId(organizationId != null ? organizationId : "urbanthread")
                .build();

        return ingestDocument(req);
    }

    @Transactional
    public DocumentUploadResponse ingestWebsite(IngestWebsiteRequest request) {
        log.info("Ingesting website URL: {}", request.getUrl());
        String extractedText = webDocumentLoader.fetchAndExtractFromUrl(request.getUrl());

        String title = request.getTitle() != null && !request.getTitle().isBlank()
                ? request.getTitle()
                : "UrbanThread Web: " + request.getUrl();

        IngestDocumentRequest docReq = IngestDocumentRequest.builder()
                .title(title)
                .category(request.getCategory() != null ? request.getCategory() : "WEBSITE_PAGE")
                .documentType(DocumentType.WEBSITE)
                .content(extractedText)
                .sourceUrl(request.getUrl())
                .organizationId(request.getOrganizationId() != null ? request.getOrganizationId() : "urbanthread")
                .build();

        return ingestDocument(docReq);
    }

    private String computeChecksum(byte[] data) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(data);
            StringBuilder hexString = new StringBuilder();
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (Exception e) {
            return UUID.randomUUID().toString();
        }
    }
}
