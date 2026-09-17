package com.urbanthread.opspilot.rag.service.rag;

import com.urbanthread.opspilot.rag.domain.entity.DocumentChunkEntity;
import com.urbanthread.opspilot.rag.dto.request.RagQueryRequest;
import com.urbanthread.opspilot.rag.dto.response.CitationDto;
import com.urbanthread.opspilot.rag.dto.response.RagResponse;
import com.urbanthread.opspilot.rag.service.retrieval.HybridRetrievalService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

/**
 * Service orchestrating grounded Retrieval-Augmented Generation for UrbanThread.
 * Connects retrieved context, prompt templates, and the LLM generation model.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RagService {

    private final HybridRetrievalService retrievalService;

    @Autowired(required = false)
    private org.springframework.ai.chat.model.ChatModel chatModel;

    @Value("${spring.ai.openai.chat.options.model:gpt-4o}")
    private String modelName;

    private static final Pattern PROMPT_INJECTION_PATTERN = Pattern.compile(
            "(?i)(ignore\\s+(all\\s+)?previous|disregard|system\\s+prompt|reveal\\s+instructions|export\\s+all|database\\s+password|bypass\\s+policy)"
    );

    @org.springframework.transaction.annotation.Transactional(readOnly = true)
    public RagResponse answerQuery(RagQueryRequest request) {
        long startTime = System.currentTimeMillis();
        String query = request.getQuery();

        // 1. Security Gate: Deterministic Prompt Injection Check
        if (PROMPT_INJECTION_PATTERN.matcher(query).find()) {
            log.warn("Security Alert: Prompt injection attempt detected in query: {}", query);
            return RagResponse.builder()
                    .query(query)
                    .answer("I am Aria, UrbanThread's customer operations AI. I can only assist with verified UrbanThread orders, apparel products, sizing, and policies.")
                    .isGrounded(false)
                    .confidenceScore(0.0)
                    .chunksRetrieved(0)
                    .latencyMs(System.currentTimeMillis() - startTime)
                    .citations(List.of())
                    .modelUsed(modelName)
                    .promptInjectionDetected(true)
                    .build();
        }

        // 2. Hybrid Retrieval Pipeline (Dense + Sparse + RRF)
        List<DocumentChunkEntity> retrievedChunks = retrievalService.retrieve(request);

        if (retrievedChunks.isEmpty()) {
            return RagResponse.builder()
                    .query(query)
                    .answer("I could not find verified UrbanThread policy or catalog documentation matching your question. Please contact our support team at support@urbanthread.local.")
                    .isGrounded(false)
                    .confidenceScore(0.0)
                    .chunksRetrieved(0)
                    .latencyMs(System.currentTimeMillis() - startTime)
                    .citations(List.of())
                    .modelUsed(modelName)
                    .promptInjectionDetected(false)
                    .build();
        }

        // 3. Construct Context Window & Format Citations
        StringBuilder contextBuilder = new StringBuilder();
        List<CitationDto> citations = new ArrayList<>();
        double totalConfidence = 0.0;

        for (int i = 0; i < retrievedChunks.size(); i++) {
            DocumentChunkEntity chunk = retrievedChunks.get(i);
            String docTitle = chunk.getDocument() != null ? chunk.getDocument().getTitle() : "UrbanThread SOP";
            String category = chunk.getDocument() != null ? chunk.getDocument().getCategory() : "GENERAL";
            String sourceUrl = chunk.getDocument() != null ? chunk.getDocument().getSourceUrl() : null;
            double score = chunk.getScore() != null ? Math.min(1.0, chunk.getScore()) : 0.85;

            contextBuilder.append(String.format("[%d] Source: %s (%s)\nContent: %s\n\n",
                    i + 1, docTitle, category, chunk.getContent()));

            citations.add(CitationDto.builder()
                    .documentId(chunk.getDocument() != null ? chunk.getDocument().getId() : null)
                    .documentTitle(docTitle)
                    .category(category)
                    .chunkIndex(chunk.getChunkIndex())
                    .snippet(chunk.getContent().length() > 160 ? chunk.getContent().substring(0, 160) + "..." : chunk.getContent())
                    .confidence(Math.round(score * 100.0) / 100.0)
                    .sourceUrl(sourceUrl)
                    .build());

            totalConfidence += score;
        }

        double avgConfidence = Math.round((totalConfidence / retrievedChunks.size()) * 100.0) / 100.0;

        // 4. Prompt Template Construction
        String systemPrompt = """
                You are Aria, the intelligent autonomous operations and customer support assistant for UrbanThread.
                Answer the user's question using ONLY the provided verified context chunks below.
                If the answer cannot be determined from the context, state that human review is required.
                Always maintain a helpful, professional tone.
                
                --- VERIFIED URBANTHREAD KNOWLEDGE CHUNKS ---
                """ + contextBuilder + """
                ---------------------------------------------
                """;

        String finalAnswer;

        // 5. LLM Invocation or High-Fidelity Grounded Generation
        if (chatModel != null) {
            try {
                String promptText = systemPrompt + "\nUser Question: " + query + "\nAnswer:";
                finalAnswer = chatModel.call(promptText);
            } catch (Exception e) {
                log.warn("Spring AI ChatModel call failed or key invalid. Using grounded context synthesis: {}", e.getMessage());
                finalAnswer = formatGroundedSynthesis(retrievedChunks);
            }
        } else {
            finalAnswer = formatGroundedSynthesis(retrievedChunks);
        }

        long latency = System.currentTimeMillis() - startTime;
        log.info("RAG query processed in {} ms with {} chunks (confidence={})", latency, retrievedChunks.size(), avgConfidence);

        return RagResponse.builder()
                .query(query)
                .answer(finalAnswer)
                .isGrounded(true)
                .confidenceScore(avgConfidence)
                .chunksRetrieved(retrievedChunks.size())
                .latencyMs(latency)
                .citations(citations)
                .modelUsed(modelName)
                .promptInjectionDetected(false)
                .build();
    }

    private String formatGroundedSynthesis(List<DocumentChunkEntity> chunks) {
        DocumentChunkEntity top = chunks.get(0);
        String docTitle = top.getDocument() != null ? top.getDocument().getTitle() : "UrbanThread Guidelines";
        return String.format("According to %s: %s", docTitle, top.getContent());
    }
}
