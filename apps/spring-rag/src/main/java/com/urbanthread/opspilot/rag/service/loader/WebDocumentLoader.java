package com.urbanthread.opspilot.rag.service.loader;

import com.urbanthread.opspilot.rag.domain.enums.DocumentType;
import com.urbanthread.opspilot.rag.exception.RagException;
import lombok.extern.slf4j.Slf4j;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.springframework.stereotype.Component;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;

@Slf4j
@Component
public class WebDocumentLoader implements DocumentLoader {

    @Override
    public boolean supports(DocumentType documentType) {
        return documentType == DocumentType.WEBSITE;
    }

    @Override
    public String extractText(InputStream inputStream, String filename) {
        log.info("Cleaning and extracting main content from HTML stream: {}", filename);
        try {
            String html = new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
            Document doc = Jsoup.parse(html);
            // Remove noise elements like scripts, styles, nav, footers
            doc.select("script, style, nav, footer, noscript, svg, header").remove();
            return doc.body().text();
        } catch (Exception e) {
            log.error("Failed to parse HTML stream: {}", e.getMessage());
            throw new RagException("Error parsing HTML stream", e);
        }
    }

    public String fetchAndExtractFromUrl(String url) {
        log.info("Fetching and extracting website content from URL: {}", url);
        try {
            Document doc = Jsoup.connect(url)
                    .userAgent("UrbanThread-OpsPilot-Crawler/1.0")
                    .timeout(10000)
                    .get();
            doc.select("script, style, nav, footer, noscript, svg, header").remove();
            return doc.body().text();
        } catch (Exception e) {
            log.error("Failed to crawl website URL {}: {}", url, e.getMessage());
            throw new RagException("Error fetching website URL: " + url, e);
        }
    }
}
