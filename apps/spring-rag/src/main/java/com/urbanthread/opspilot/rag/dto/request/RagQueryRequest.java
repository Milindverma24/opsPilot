package com.urbanthread.opspilot.rag.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RagQueryRequest {

    @NotBlank(message = "Query question cannot be blank")
    private String query;

    @Builder.Default
    private String organizationId = "urbanthread";

    private String categoryFilter;

    private List<String> documentTypes;

    @Builder.Default
    private Integer topK = 3;

    @Builder.Default
    private Double minSimilarity = 0.15;

    @Builder.Default
    private Boolean enableReranking = true;
}
