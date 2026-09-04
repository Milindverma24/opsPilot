"""
Phase 17 — Local Performance & Latency Benchmark Test Suite.
Benchmarks:
- 50 concurrent customer operations queries
- P50, P90, P95, P99 latency thresholds
- Zero error rate under concurrent evaluation load
"""
import time
import concurrent.futures
import statistics
import pytest

from apps.api.app.services.ai.intent_service import IntentClassificationService
from apps.api.app.services.ai.entity_service import EntityExtractionService
from apps.api.app.services.ai.prompt_injection_scanner import PromptInjectionScanner


SAMPLE_QUERIES = [
    "Where is my order UT-10921? It has been 5 days.",
    "I want to return the Slim-Fit Chino in Navy size 32.",
    "Can you refund ₹1,850 for order UT-88219?",
    "Do you have the Oversized Hoodie in Sage Green size XL?",
    "My package was crushed upon delivery and item is torn. Terrible service!",
    "How long does standard delivery take to Bangalore?",
    "Can I exchange size M for size L in order UT-55410?",
    "Is COD available for pin code 560001?",
    "Track shipment DEL-100293 for my order.",
    "What fabric is used in the Classic Denim Jacket?",
]


def execute_single_query(query: str) -> float:
    start_time = time.perf_counter()

    # Step 1: Security Scan
    scan_res = PromptInjectionScanner.scan(query)

    # Step 2: Intent Classification
    intent_service = IntentClassificationService()
    intent_res = intent_service.classify(query, use_llm_fallback=False)

    # Step 3: Entity Extraction
    entity_service = EntityExtractionService()
    entity_res = entity_service.extract(query)

    duration_ms = (time.perf_counter() - start_time) * 1000.0
    return duration_ms


def test_50_concurrent_local_queries_performance():
    """
    Executes 50 concurrent local operations queries using ThreadPoolExecutor.
    Validates:
    - Zero error rate
    - P50 latency < 250ms
    - P95 latency < 600ms
    - P99 latency < 1200ms
    """
    num_queries = 50
    queries = [SAMPLE_QUERIES[i % len(SAMPLE_QUERIES)] for i in range(num_queries)]

    durations: list[float] = []
    errors: list[str] = []

    start_total = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_query = {executor.submit(execute_single_query, q): q for q in queries}
        for future in concurrent.futures.as_completed(future_to_query):
            try:
                lat = future.result()
                durations.append(lat)
            except Exception as exc:
                errors.append(str(exc))

    total_time_s = time.perf_counter() - start_total
    throughput = num_queries / total_time_s

    # Compute percentiles
    durations.sort()
    p50 = statistics.median(durations)
    p90 = durations[int(num_queries * 0.90) - 1]
    p95 = durations[int(num_queries * 0.95) - 1]
    p99 = durations[int(num_queries * 0.99) - 1]

    print("\n--- Local Performance Benchmark Report ---")
    print(f"Total Queries: {num_queries}")
    print(f"Total Time:    {total_time_s:.3f}s")
    print(f"Throughput:    {throughput:.2f} queries/sec")
    print(f"P50 Latency:   {p50:.2f}ms (threshold < 250ms)")
    print(f"P90 Latency:   {p90:.2f}ms")
    print(f"P95 Latency:   {p95:.2f}ms (threshold < 600ms)")
    print(f"P99 Latency:   {p99:.2f}ms (threshold < 1200ms)")
    print(f"Errors:        {len(errors)}")

    assert len(errors) == 0, f"Encountered {len(errors)} errors during concurrent benchmark"
    assert p50 < 250.0, f"P50 latency {p50:.2f}ms exceeded 250ms"
    assert p95 < 600.0, f"P95 latency {p95:.2f}ms exceeded 600ms"
    assert p99 < 1200.0, f"P99 latency {p99:.2f}ms exceeded 1200ms"
