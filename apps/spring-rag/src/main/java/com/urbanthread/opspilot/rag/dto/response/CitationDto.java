package com.urbanthread.opspilot.rag.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Verifiable source attribution returned alongside grounded LLM responses.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CitationDto {
    private String documentId;
    private String documentTitle;
    private String category;
    private Integer chunkIndex;
    private String snippet;
    private Double confidence;
    private String sourceUrl;
}
