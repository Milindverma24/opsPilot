package com.urbanthread.opspilot.rag.domain.entity;

import com.urbanthread.opspilot.rag.domain.enums.DocumentType;
import com.urbanthread.opspilot.rag.domain.enums.IngestionStatus;
import jakarta.persistence.*;
import lombok.*;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Entity representing an ingested enterprise document (Policy SOP, sizing guide, website page).
 */
@Entity
@Table(name = "rag_documents")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DocumentEntity {

    @Id
    @Column(name = "id", length = 36, nullable = false)
    private String id;

    @Column(name = "organization_id", length = 64, nullable = false)
    @Builder.Default
    private String organizationId = "urbanthread";

    @Column(name = "title", nullable = false)
    private String title;

    @Column(name = "category", length = 64, nullable = false)
    @Builder.Default
    private String category = "GENERAL_SOP";

    @Enumerated(EnumType.STRING)
    @Column(name = "document_type", length = 32, nullable = false)
    private DocumentType documentType;

    @Column(name = "source_url", columnDefinition = "TEXT")
    private String sourceUrl;

    @Column(name = "file_size_bytes")
    private Long fileSizeBytes;

    @Column(name = "checksum", length = 64)
    private String checksum;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", length = 32, nullable = false)
    @Builder.Default
    private IngestionStatus status = IngestionStatus.INDEXED;

    @Column(name = "metadata", columnDefinition = "TEXT")
    private String metadata;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

    @OneToMany(mappedBy = "document", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    @Builder.Default
    private List<DocumentChunkEntity> chunks = new ArrayList<>();

    @PrePersist
    public void onPrePersist() {
        if (this.createdAt == null) {
            this.createdAt = OffsetDateTime.now();
        }
        if (this.updatedAt == null) {
            this.updatedAt = OffsetDateTime.now();
        }
    }

    @PreUpdate
    public void onPreUpdate() {
        this.updatedAt = OffsetDateTime.now();
    }
}
