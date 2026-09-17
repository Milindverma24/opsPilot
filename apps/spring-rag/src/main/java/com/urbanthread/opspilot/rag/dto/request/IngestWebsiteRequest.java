package com.urbanthread.opspilot.rag.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.validator.constraints.URL;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class IngestWebsiteRequest {

    @NotBlank(message = "Website URL is required")
    @URL(message = "Must be a valid URL")
    private String url;

    private String title;

    @Builder.Default
    private String category = "WEBSITE_PAGE";

    @Builder.Default
    private String organizationId = "urbanthread";
}
