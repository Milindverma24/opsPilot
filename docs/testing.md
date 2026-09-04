# Test Lab & Evaluation Suite — OpsPilot

OpsPilot includes a complete **enterprise test laboratory** validating AI accuracy, security resistance, recovery, and performance locally.

---

## 1. Test Architecture

The `tests/` directory contains:
```
tests/
├── unit/             # Factory generation and unit tests (23 tests)
├── security/         # Tenant isolation, auth, tamper protection, prompt injection (8 tests)
├── ai/               # 223 synthetic evaluation cases, intent F1, entity recall (5 tests)
├── workforce/        # Worker crash recovery, lease expiration, task lifecycle (5 tests)
├── performance/      # 50 concurrent clients, latency p50/p95 (1 test)
├── e2e/              # Customer AI to warehouse dispatch end-to-end (4 tests)
├── fixtures/         # 22 reusable factories (create_valid, create_invalid, create_edge_case)
└── datasets/         # 223 AI eval cases + 105 prompt injection attacks
```

---

## 2. Running Tests

```bash
# Run all tests (46 tests in ~1.2s)
make test-all

# Run specific test suites
make test              # Unit & integration
make test-ai           # AI accuracy over 223 synthetic cases
make test-security     # Security, injection defense, tenant isolation
make test-e2e          # End-to-end customer order -> employee task
```

---

## 3. Benchmark Results

| Metric | Target | Measured Result |
|---|---|---|
| **AI Intent Accuracy** | > 90% | **96.41%** (215/223 passed) |
| **Prompt Injection Block Rate** | > 95% | **99.05%** (104/105 blocked) |
| **Entity Extraction Recall** | > 85% | **100.0%** |
| **Multi-Tenant Isolation** | 100% | **100.0%** (Zero leaks across tenants) |
| **Approval SHA-256 Tamper Gate** | 100% | **100.0%** (Blocked on payload mutation) |
| **Concurrent Throughput** | > 500 req/s | **3,469 req/s** |
| **P50 Latency** | < 10ms | **0.16ms** |
