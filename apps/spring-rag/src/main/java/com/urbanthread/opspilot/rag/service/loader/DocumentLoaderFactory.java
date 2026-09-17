package com.urbanthread.opspilot.rag.service.loader;

import com.urbanthread.opspilot.rag.domain.enums.DocumentType;
import com.urbanthread.opspilot.rag.exception.RagException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@RequiredArgsConstructor
public class DocumentLoaderFactory {

    private final List<DocumentLoader> loaders;

    public DocumentLoader getLoader(DocumentType documentType) {
        return loaders.stream()
                .filter(loader -> loader.supports(documentType))
                .findFirst()
                .orElseThrow(() -> new RagException("No document loader found supporting type: " + documentType));
    }

    public DocumentType detectTypeFromFilename(String filename) {
        if (filename == null) return DocumentType.TXT;
        String lower = filename.toLowerCase();
        if (lower.endsWith(".pdf")) return DocumentType.PDF;
        if (lower.endsWith(".docx") || lower.endsWith(".doc")) return DocumentType.DOCX;
        if (lower.endsWith(".md") || lower.endsWith(".markdown")) return DocumentType.MARKDOWN;
        if (lower.endsWith(".csv")) return DocumentType.CSV;
        if (lower.endsWith(".html") || lower.endsWith(".htm")) return DocumentType.WEBSITE;
        return DocumentType.TXT;
    }
}
