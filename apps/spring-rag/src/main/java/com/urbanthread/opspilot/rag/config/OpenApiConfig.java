package com.urbanthread.opspilot.rag.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI opsPilotRagOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("OpsPilot — Spring Boot RAG Microservice API")
                        .description("Production-Style Retrieval-Augmented Generation & Vector Knowledge Subsystem for UrbanThread E-Commerce.")
                        .version("1.0.0")
                        .contact(new Contact()
                                .name("OpsPilot Engineering Team")
                                .email("engineering@urbanthread.local"))
                        .license(new License().name("MIT License").url("https://opensource.org/licenses/MIT")));
    }
}
