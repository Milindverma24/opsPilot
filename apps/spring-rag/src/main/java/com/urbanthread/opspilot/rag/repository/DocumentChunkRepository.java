package com.urbanthread.opspilot.rag.repository;

import com.urbanthread.opspilot.rag.domain.entity.DocumentChunkEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface DocumentChunkRepository extends JpaRepository<DocumentChunkEntity, String> {

    List<DocumentChunkEntity> findByDocumentIdOrderByChunkIndexAsc(String documentId);

    List<DocumentChunkEntity> findByOrganizationId(String organizationId);

    void deleteByDocumentId(String documentId);

    /**
     * Lexical keyword search using LIKE fallback across chunk text.
     */
    @Query("SELECT c FROM DocumentChunkEntity c WHERE c.organizationId = :orgId AND LOWER(c.content) LIKE LOWER(CONCAT('%', :keyword, '%'))")
    List<DocumentChunkEntity> searchLexicalFallback(@Param("orgId") String orgId, @Param("keyword") String keyword);
}
