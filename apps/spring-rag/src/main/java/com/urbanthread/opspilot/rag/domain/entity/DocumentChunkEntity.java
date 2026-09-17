package com.urbanthread.opspilot.rag.domain.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.OffsetDateTime;

/**
 * Entity representing an individual semantic segment (chunk) of an ingested document.
 * Contains text segment, token length, metadata, and dense vector embedding.
 */
@Entity
@Table(name = "rag_document_chunks")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DocumentChunkEntity {

    @Id
    @Column(name = "id", length = 36, nullable = false)
    private String id;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "document_id", nullable = false)
    private DocumentEntity document;

    @Column(name = "organization_id", length = 64, nullable = false)
    @Builder.Default
    private String organizationId = "urbanthread";

    @Column(name = "chunk_index", nullable = false)
    private Integer chunkIndex;

    @Column(name = "content", nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(name = "token_count", nullable = false)
    private Integer tokenCount;

    /**
     * Stored as a serialized float array or vector string representation for cross-database resilience.
     */
    @Column(name = "embedding_vector", columnDefinition = "TEXT")
    private String embeddingVector;

    @Column(name = "metadata", columnDefinition = "TEXT")
    private String metadata;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;

    @Transient
    private Double score;

    @PrePersist
    public void onPrePersist() {
        if (this.createdAt == null) {
            this.createdAt = OffsetDateTime.now();
        }
    }
}
