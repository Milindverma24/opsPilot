package com.urbanthread.opspilot.rag.service.loader;

import com.urbanthread.opspilot.rag.domain.enums.DocumentType;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;

/**
 * Interface defining extraction contract for UrbanThread multi-format documents.
 */
public interface DocumentLoader {

    boolean supports(DocumentType documentType);

    String extractText(InputStream inputStream, String filename);

    default String extractText(MultipartFile file) {
        try (InputStream is = file.getInputStream()) {
            return extractText(is, file.getOriginalFilename());
        } catch (Exception e) {
            throw new RuntimeException("Failed to read file: " + file.getOriginalFilename(), e);
        }
    }
}
