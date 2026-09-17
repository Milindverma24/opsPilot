package com.urbanthread.opspilot.rag.service.retrieval;

import com.urbanthread.opspilot.rag.domain.entity.DocumentChunkEntity;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.*;

/**
 * Service implementing Reciprocal Rank Fusion (RRF) reranking.
 * Combines ranked lists from dense vector search and sparse keyword search.
 */
@Slf4j
@Service
public class RerankingService {

    @Value("${opspilot.rag.retrieval.rrf-k:60}")
    private int rrfK;

    public List<DocumentChunkEntity> rerankWithRrf(
            List<DocumentChunkEntity> vectorRanked,
            List<DocumentChunkEntity> lexicalRanked,
            int topK) {

        Map<String, DocumentChunkEntity> entityMap = new HashMap<>();
        Map<String, Double> scoreMap = new HashMap<>();

        // 1. Accumulate dense vector ranks
        for (int rank = 0; rank < vectorRanked.size(); rank++) {
            DocumentChunkEntity chunk = vectorRanked.get(rank);
            entityMap.put(chunk.getId(), chunk);
            double rrfScore = 1.0 / (rrfK + (rank + 1));
            scoreMap.merge(chunk.getId(), rrfScore, Double::sum);
        }

        // 2. Accumulate sparse lexical ranks
        for (int rank = 0; rank < lexicalRanked.size(); rank++) {
            DocumentChunkEntity chunk = lexicalRanked.get(rank);
            entityMap.put(chunk.getId(), chunk);
            double rrfScore = 1.0 / (rrfK + (rank + 1));
            scoreMap.merge(chunk.getId(), rrfScore, Double::sum);
        }

        // 3. Sort by aggregated RRF score descending
        List<Map.Entry<String, Double>> sortedEntries = new ArrayList<>(scoreMap.entrySet());
        sortedEntries.sort((a, b) -> Double.compare(b.getValue(), a.getValue()));

        List<DocumentChunkEntity> result = new ArrayList<>();
        for (int i = 0; i < Math.min(topK, sortedEntries.size()); i++) {
            String chunkId = sortedEntries.get(i).getKey();
            DocumentChunkEntity chunk = entityMap.get(chunkId);
            chunk.setScore(sortedEntries.get(i).getValue());
            result.add(chunk);
        }

        log.info("RRF Reranking produced {} consensus chunks from {} vector and {} lexical candidates",
                result.size(), vectorRanked.size(), lexicalRanked.size());
        return result;
    }
}
