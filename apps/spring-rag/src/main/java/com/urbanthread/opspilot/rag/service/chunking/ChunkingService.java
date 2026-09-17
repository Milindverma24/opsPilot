package com.urbanthread.opspilot.rag.service.chunking;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

/**
 * Service implementing recursive text chunking with sliding window overlap.
 * Ensures sentence coherence across boundaries.
 */
@Slf4j
@Service
public class ChunkingService {

    @Value("${opspilot.rag.chunking.chunk-size:500}")
    private int chunkSize;

    @Value("${opspilot.rag.chunking.chunk-overlap:80}")
    private int chunkOverlap;

    @Value("${opspilot.rag.chunking.min-chunk-size:100}")
    private int minChunkSize;

    public List<String> chunkText(String rawText) {
        if (rawText == null || rawText.trim().isEmpty()) {
            return List.of();
        }

        String normalized = rawText.replaceAll("\\r\\n", "\n").replaceAll("\\s+", " ").trim();
        if (normalized.length() <= chunkSize) {
            return List.of(normalized);
        }

        List<String> chunks = new ArrayList<>();
        int start = 0;
        int length = normalized.length();

        while (start < length) {
            int end = Math.min(start + chunkSize, length);

            // Attempt to break cleanly at sentence or punctuation boundaries
            if (end < length) {
                int punctuationIndex = findLastPunctuation(normalized, start + minChunkSize, end);
                if (punctuationIndex != -1) {
                    end = punctuationIndex + 1;
                } else {
                    int spaceIndex = normalized.lastIndexOf(' ', end);
                    if (spaceIndex > start + minChunkSize) {
                        end = spaceIndex;
                    }
                }
            }

            String chunk = normalized.substring(start, end).trim();
            if (!chunk.isEmpty()) {
                chunks.add(chunk);
            }

            if (end >= length) {
                break;
            }

            start = Math.max(start + 1, end - chunkOverlap);
        }

        log.info("Chunked document of {} characters into {} chunks (size={}, overlap={})",
                normalized.length(), chunks.size(), chunkSize, chunkOverlap);
        return chunks;
    }

    private int findLastPunctuation(String text, int searchStart, int searchEnd) {
        for (int i = searchEnd - 1; i >= searchStart; i--) {
            char c = text.charAt(i);
            if (c == '.' || c == '?' || c == '!' || c == '\n') {
                return i;
            }
        }
        return -1;
    }
}
