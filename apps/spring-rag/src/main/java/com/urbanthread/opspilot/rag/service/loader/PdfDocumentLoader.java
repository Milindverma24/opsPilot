package com.urbanthread.opspilot.rag.service.loader;

import com.urbanthread.opspilot.rag.domain.enums.DocumentType;
import com.urbanthread.opspilot.rag.exception.RagException;
import lombok.extern.slf4j.Slf4j;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.springframework.stereotype.Component;

import java.io.InputStream;

@Slf4j
@Component
public class PdfDocumentLoader implements DocumentLoader {

    @Override
    public boolean supports(DocumentType documentType) {
        return documentType == DocumentType.PDF;
    }

    @Override
    public String extractText(InputStream inputStream, String filename) {
        log.info("Extracting text from PDF document: {}", filename);
        try {
            byte[] bytes = inputStream.readAllBytes();
            try (PDDocument document = Loader.loadPDF(bytes)) {
                PDFTextStripper stripper = new PDFTextStripper();
                stripper.setSortByPosition(true);
                String text = stripper.getText(document);
                if (text == null || text.trim().isEmpty()) {
                    log.warn("Extracted empty text from PDF: {}", filename);
                    return "";
                }
                return text.replaceAll("\\r\\n", "\n").replaceAll("[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F]", "").trim();
            }
        } catch (Exception e) {
            log.error("Failed to parse PDF {}: {}", filename, e.getMessage());
            throw new RagException("Error parsing PDF file: " + filename, e);
        }
    }
}
