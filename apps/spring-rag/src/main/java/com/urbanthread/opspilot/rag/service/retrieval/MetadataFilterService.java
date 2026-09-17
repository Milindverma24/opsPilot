package com.urbanthread.opspilot.rag.service.retrieval;

import com.urbanthread.opspilot.rag.domain.entity.DocumentChunkEntity;
import com.urbanthread.opspilot.rag.dto.request.RagQueryRequest;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

/**
 * Enforces strict multi-tenant isolation and metadata constraints on retrieved chunks.
 */
@Service
public class MetadataFilterService {

    public List<DocumentChunkEntity> filter(List<DocumentChunkEntity> chunks, RagQueryRequest request) {
        if (chunks == null || chunks.isEmpty()) {
            return List.of();
        }

        return chunks.stream()
                // 1. Strict Tenant Boundary Isolation
                .filter(chunk -> {
                    String org = request.getOrganizationId() != null ? request.getOrganizationId() : "urbanthread";
                    return org.equalsIgnoreCase(chunk.getOrganizationId());
                })
                // 2. Category Filter (Optional)
                .filter(chunk -> {
                    if (request.getCategoryFilter() == null || request.getCategoryFilter().isBlank()) {
                        return true;
                    }
                    return chunk.getDocument() != null &&
                            request.getCategoryFilter().equalsIgnoreCase(chunk.getDocument().getCategory());
                })
                // 3. Document Type Filter (Optional)
                .filter(chunk -> {
                    if (request.getDocumentTypes() == null || request.getDocumentTypes().isEmpty()) {
                        return true;
                    }
                    if (chunk.getDocument() == null || chunk.getDocument().getDocumentType() == null) {
                        return false;
                    }
                    return request.getDocumentTypes().contains(chunk.getDocument().getDocumentType().name());
                })
                .collect(Collectors.toList());
    }
}
