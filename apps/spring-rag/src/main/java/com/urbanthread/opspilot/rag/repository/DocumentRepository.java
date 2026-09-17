package com.urbanthread.opspilot.rag.repository;

import com.urbanthread.opspilot.rag.domain.entity.DocumentEntity;
import com.urbanthread.opspilot.rag.domain.enums.DocumentType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface DocumentRepository extends JpaRepository<DocumentEntity, String> {

    List<DocumentEntity> findByOrganizationId(String organizationId);

    List<DocumentEntity> findByOrganizationIdAndCategory(String organizationId, String category);

    List<DocumentEntity> findByOrganizationIdAndDocumentType(String organizationId, DocumentType documentType);

    Optional<DocumentEntity> findByOrganizationIdAndChecksum(String organizationId, String checksum);

    Optional<DocumentEntity> findByOrganizationIdAndSourceUrl(String organizationId, String sourceUrl);
}
