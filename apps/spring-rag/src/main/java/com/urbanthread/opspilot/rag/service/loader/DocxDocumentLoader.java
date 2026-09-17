package com.urbanthread.opspilot.rag.service.loader;

import com.urbanthread.opspilot.rag.domain.enums.DocumentType;
import com.urbanthread.opspilot.rag.exception.RagException;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.xwpf.extractor.XWPFWordExtractor;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.springframework.stereotype.Component;

import java.io.InputStream;

@Slf4j
@Component
public class DocxDocumentLoader implements DocumentLoader {

    @Override
    public boolean supports(DocumentType documentType) {
        return documentType == DocumentType.DOCX;
    }

    @Override
    public String extractText(InputStream inputStream, String filename) {
        log.info("Extracting text from DOCX document: {}", filename);
        try (XWPFDocument doc = new XWPFDocument(inputStream);
             XWPFWordExtractor extractor = new XWPFWordExtractor(doc)) {
            String text = extractor.getText();
            return text != null ? text.trim() : "";
        } catch (Exception e) {
            log.error("Failed to parse DOCX {}: {}", filename, e.getMessage());
            throw new RagException("Error parsing DOCX file: " + filename, e);
        }
    }
}
