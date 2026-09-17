package com.urbanthread.opspilot.rag.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RagResponse {
    private String query;
    private String answer;
    private Boolean isGrounded;
    private Double confidenceScore;
    private Integer chunksRetrieved;
    private Long latencyMs;
    private List<CitationDto> citations;
    private String modelUsed;
    private Boolean promptInjectionDetected;
}
