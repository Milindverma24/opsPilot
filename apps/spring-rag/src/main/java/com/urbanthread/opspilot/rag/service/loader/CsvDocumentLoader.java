package com.urbanthread.opspilot.rag.service.loader;

import com.urbanthread.opspilot.rag.domain.enums.DocumentType;
import com.urbanthread.opspilot.rag.exception.RagException;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;
import org.springframework.stereotype.Component;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

@Slf4j
@Component
public class CsvDocumentLoader implements DocumentLoader {

    @Override
    public boolean supports(DocumentType documentType) {
        return documentType == DocumentType.CSV;
    }

    @Override
    public String extractText(InputStream inputStream, String filename) {
        log.info("Extracting and serializing tabular text from CSV document: {}", filename);
        StringBuilder sb = new StringBuilder();
        try (InputStreamReader reader = new InputStreamReader(inputStream, StandardCharsets.UTF_8);
             CSVParser parser = new CSVParser(reader, CSVFormat.DEFAULT.builder().setHeader().setSkipHeaderRecord(true).build())) {

            List<String> headers = parser.getHeaderNames();
            sb.append("Table Headers: ").append(String.join(", ", headers)).append("\n\n");

            for (CSVRecord record : parser) {
                sb.append("Record: ");
                for (String header : headers) {
                    if (record.isSet(header)) {
                        sb.append(header).append("=").append(record.get(header)).append("; ");
                    }
                }
                sb.append("\n");
            }
            return sb.toString().trim();
        } catch (Exception e) {
            log.error("Failed to parse CSV {}: {}", filename, e.getMessage());
            throw new RagException("Error parsing CSV file: " + filename, e);
        }
    }
}
