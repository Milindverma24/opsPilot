package com.urbanthread.opspilot.rag.dto.response;

import com.urbanthread.opspilot.rag.domain.enums.DocumentType;
import com.urbanthread.opspilot.rag.domain.enums.IngestionStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.OffsetDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DocumentUploadResponse {
    private String documentId;
    private String title;
    private String category;
    private DocumentType documentType;
    private IngestionStatus status;
    private Integer chunksCreated;
    private Long fileSizeBytes;
    private String checksum;
    private OffsetDateTime indexedAt;
    private String message;
}
