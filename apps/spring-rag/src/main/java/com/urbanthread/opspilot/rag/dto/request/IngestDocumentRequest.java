package com.urbanthread.opspilot.rag.dto.request;

import com.urbanthread.opspilot.rag.domain.enums.DocumentType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class IngestDocumentRequest {

    @NotBlank(message = "Document title is required")
    private String title;

    @Builder.Default
    private String category = "GENERAL_SOP";

    @NotNull(message = "Document type is required")
    private DocumentType documentType;

    @NotBlank(message = "Content cannot be empty")
    private String content;

    private String sourceUrl;
    
    @Builder.Default
    private String organizationId = "urbanthread";
}
