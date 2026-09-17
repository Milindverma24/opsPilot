# OpsPilot AI Evaluation Benchmark Report

Generated: 2026-09-09 17:53:01 UTC
Total Cases Evaluated: 39

## Executive Summary Metrics

| Metric | Measured Accuracy | Benchmark Threshold | Status |
|---|---|---|---|
| **Document Classification Accuracy** | **91.18%** | >= 90.0% | **PASSED** |
| **Entity Extraction Precision** | **100.0%** | >= 92.0% | **PASSED** |
| **Prompt Injection Defense Rate** | **100.0%** | 100.0% | **PASSED** |
| **Policy Enforcement Accuracy** | **100.0%** | >= 95.0% | **PASSED** |
| **Hallucination Rate** | **0.0%** | <= 5.0% | **PASSED** |
| **Controlled Tool Execution Safety** | **100.0%** | 100.0% | **PASSED** |

## Dataset Breakdown
- **Invoices Evaluated**: 19
- **Customer Complaints Evaluated**: 15
- **Adversarial Prompt Injections Blocked**: 5 / 5 (100% Mitigated)

## Evaluation Details
Every model output adheres to strict Pydantic JSON schemas. Zero raw or uncontrolled text strings were routed directly to tool execution. All high-risk disbursements strictly triggered human-in-the-loop approval requests.
