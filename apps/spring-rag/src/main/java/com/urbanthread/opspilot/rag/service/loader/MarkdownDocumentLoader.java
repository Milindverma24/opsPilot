package com.urbanthread.opspilot.rag.service.loader;

import com.urbanthread.opspilot.rag.domain.enums.DocumentType;
import com.urbanthread.opspilot.rag.exception.RagException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.stream.Collectors;

@Slf4j
@Component
public class MarkdownDocumentLoader implements DocumentLoader {

    @Override
    public boolean supports(DocumentType documentType) {
        return documentType == DocumentType.MARKDOWN;
    }

    @Override
    public String extractText(InputStream inputStream, String filename) {
        log.info("Extracting text from Markdown document: {}", filename);
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream, StandardCharsets.UTF_8))) {
            return reader.lines().collect(Collectors.joining("\n")).trim();
        } catch (Exception e) {
            log.error("Failed to parse Markdown {}: {}", filename, e.getMessage());
            throw new RagException("Error reading Markdown file: " + filename, e);
        }
    }
}
