package com.urbanthread.opspilot.rag.service.retrieval;

import com.urbanthread.opspilot.rag.domain.entity.DocumentChunkEntity;
import com.urbanthread.opspilot.rag.dto.request.RagQueryRequest;
import com.urbanthread.opspilot.rag.repository.DocumentChunkRepository;
import com.urbanthread.opspilot.rag.service.embedding.EmbeddingService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * Hybrid retrieval pipeline executing parallel dense vector search and sparse keyword search.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class HybridRetrievalService {

    private final DocumentChunkRepository chunkRepository;
    private final EmbeddingService embeddingService;
    private final MetadataFilterService metadataFilterService;
    private final RerankingService rerankingService;

    public List<DocumentChunkEntity> retrieve(RagQueryRequest request) {
        String query = request.getQuery();
        String orgId = request.getOrganizationId() != null ? request.getOrganizationId() : "urbanthread";
        int topK = request.getTopK() != null ? request.getTopK() : 3;

        // 1. Fetch chunks for organization
        List<DocumentChunkEntity> allChunks = chunkRepository.findByOrganizationId(orgId);
        if (allChunks.isEmpty()) {
            log.warn("No knowledge chunks indexed for organization: {}", orgId);
            return List.of();
        }

        // Apply pre-retrieval metadata constraints
        List<DocumentChunkEntity> eligibleChunks = metadataFilterService.filter(allChunks, request);

        // 2. Dense Semantic Vector Search
        float[] queryEmbedding = embeddingService.computeEmbedding(query);
        List<DocumentChunkEntity> vectorRanked = new ArrayList<>(eligibleChunks);
        for (DocumentChunkEntity chunk : vectorRanked) {
            float[] chunkVec = embeddingService.stringToVector(chunk.getEmbeddingVector());
            double sim = embeddingService.cosineSimilarity(queryEmbedding, chunkVec);
            chunk.setScore(sim);
        }
        vectorRanked.sort(Comparator.comparingDouble(DocumentChunkEntity::getScore).reversed());

        // Filter by minimum similarity
        double minSim = request.getMinSimilarity() != null ? request.getMinSimilarity() : 0.15;
        List<DocumentChunkEntity> filteredVector = vectorRanked.stream()
                .filter(c -> c.getScore() != null && c.getScore() >= minSim)
                .toList();

        // 3. Sparse Lexical Search (Keyword Matching)
        String queryLower = query.toLowerCase();
        List<DocumentChunkEntity> lexicalRanked = new ArrayList<>(eligibleChunks);
        for (DocumentChunkEntity chunk : lexicalRanked) {
            String contentLower = chunk.getContent().toLowerCase();
            int matchCount = 0;
            for (String word : queryLower.split("\\s+")) {
                if (word.length() > 2 && contentLower.contains(word)) {
                    matchCount++;
                }
            }
            double lexicalScore = (double) matchCount / Math.max(1, queryLower.split("\\s+").length);
            chunk.setScore(lexicalScore);
        }
        lexicalRanked.sort(Comparator.comparingDouble(DocumentChunkEntity::getScore).reversed());

        // 4. Reranking (RRF or pure vector)
        if (Boolean.TRUE.equals(request.getEnableReranking())) {
            return rerankingService.rerankWithRrf(filteredVector, lexicalRanked, topK);
        }

        return filteredVector.stream().limit(topK).toList();
    }
}
