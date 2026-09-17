package com.urbanthread.opspilot.rag.service.embedding;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.regex.Pattern;

/**
 * Service producing 1536-dimensional vector embeddings for UrbanThread documents.
 * Supports both Spring AI OpenAiEmbeddingModel and deterministic local vector representation.
 */
@Slf4j
@Service
public class EmbeddingService {

    @Value("${opspilot.rag.embedding.dimensions:1536}")
    private int dimensions;

    @Value("${opspilot.rag.embedding.use-local-deterministic-fallback:true}")
    private boolean useLocalFallback;

    @Autowired(required = false)
    private org.springframework.ai.embedding.EmbeddingModel springAiEmbeddingModel;

    private static final Pattern WORD_PATTERN = Pattern.compile("[a-zA-Z0-9]+");

    /**
     * Computes 1536-dimensional embedding vector for input text.
     */
    public float[] computeEmbedding(String text) {
        if (text == null || text.trim().isEmpty()) {
            return new float[dimensions];
        }

        // 1. Try Spring AI if available and not configured to purely fallback
        if (!useLocalFallback && springAiEmbeddingModel != null) {
            try {
                List<Double> output = springAiEmbeddingModel.embed(text);
                if (output != null && !output.isEmpty()) {
                    float[] vec = new float[output.size()];
                    for (int i = 0; i < output.size(); i++) {
                        vec[i] = output.get(i).floatValue();
                    }
                    return vec;
                }
            } catch (Exception e) {
                log.warn("Spring AI embedding provider failed or key missing. Falling back to local deterministic embedding: {}", e.getMessage());
            }
        }

        // 2. Deterministic high-dimensional normalized embedding generator
        return computeDeterministicEmbedding(text, dimensions);
    }

    /**
     * Produces a deterministic unit-normalized dense float vector from text tokens.
     */
    public static float[] computeDeterministicEmbedding(String text, int dim) {
        float[] vector = new float[dim];
        String lower = text.toLowerCase();
        var matcher = WORD_PATTERN.matcher(lower);

        int tokenCount = 0;
        while (matcher.find()) {
            String word = matcher.group();
            if (word.length() > 2) {
                tokenCount++;
                int hash = Math.abs(hashWord(word)) % dim;
                vector[hash] += 1.0f;
                // Add n-gram feature dispersion for semantic proximity
                int subHash = Math.abs((hash * 31 + word.charAt(0))) % dim;
                vector[subHash] += 0.5f;
            }
        }

        if (tokenCount == 0) {
            return vector;
        }

        // L2 Unit Normalization: sum(v^2) == 1
        double sumSquares = 0.0;
        for (float v : vector) {
            sumSquares += (v * v);
        }
        double norm = Math.sqrt(sumSquares);
        if (norm > 0) {
            for (int i = 0; i < vector.length; i++) {
                vector[i] = (float) (vector[i] / norm);
            }
        }

        return vector;
    }

    /**
     * Cosine similarity between two unit-normalized vectors.
     */
    public double cosineSimilarity(float[] v1, float[] v2) {
        if (v1 == null || v2 == null || v1.length != v2.length || v1.length == 0) {
            return 0.0;
        }
        double dotProduct = 0.0;
        double normA = 0.0;
        double normB = 0.0;
        for (int i = 0; i < v1.length; i++) {
            dotProduct += (v1[i] * v2[i]);
            normA += (v1[i] * v1[i]);
            normB += (v2[i] * v2[i]);
        }
        if (normA == 0.0 || normB == 0.0) {
            return 0.0;
        }
        return Math.max(0.0, Math.min(1.0, dotProduct / (Math.sqrt(normA) * Math.sqrt(normB))));
    }

    public String vectorToString(float[] vector) {
        if (vector == null) return "[]";
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < vector.length; i++) {
            sb.append(vector[i]);
            if (i < vector.length - 1) {
                sb.append(",");
            }
        }
        sb.append("]");
        return sb.toString();
    }

    public float[] stringToVector(String vectorStr) {
        if (vectorStr == null || !vectorStr.startsWith("[") || !vectorStr.endsWith("]")) {
            return new float[dimensions];
        }
        String inner = vectorStr.substring(1, vectorStr.length() - 1).trim();
        if (inner.isEmpty()) {
            return new float[dimensions];
        }
        String[] parts = inner.split(",");
        float[] res = new float[parts.length];
        for (int i = 0; i < parts.length; i++) {
            res[i] = Float.parseFloat(parts[i].trim());
        }
        return res;
    }

    private static int hashWord(String word) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] digest = md.digest(word.getBytes(StandardCharsets.UTF_8));
            return ((digest[0] & 0xFF) << 24) |
                    ((digest[1] & 0xFF) << 16) |
                    ((digest[2] & 0xFF) << 8) |
                    (digest[3] & 0xFF);
        } catch (Exception e) {
            return word.hashCode();
        }
    }
}
