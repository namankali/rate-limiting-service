import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass
from random import Random
from statistics import median
from time import perf_counter

from app.algorithms.fixed_window import FixedWindowCounter
from app.algorithms.sliding_window_log import SlidingWindowLog


@dataclass
class BenchmarkResult:
    algorithm: str
    requests_processed: int
    requests_per_second: float
    p95_latency: float
    p99_latency: float
    peak_memory_bytes: int


def generate_workload(
    number_of_requests: int, number_of_clients: int, seed: int = 42
) -> list[str]:
    if number_of_requests <= 0:
        raise ValueError("number of requests must be positive")
    if number_of_clients <= 0:
        raise ValueError("number of clients must be positive")

    rng = Random(seed)

    return [
        f"client-{rng.randrange(number_of_clients)}" for _ in range(number_of_requests)
    ]


def calculate_percentiles(values: list[float], percentile: float) -> float:
    if not values:
        raise ValueError("Can't calculate percentile from empty data")

    if not 0 < percentile <= 100:
        raise ValueError("Percentile must be greater than 0 and at most 100")

    ordered = sorted(values)
    index = int((percentile / 100) * len(ordered))
    return ordered[min(index, len(ordered)) - 1]


def benchmark_algorithm(
    algo_name: str, allow_request: Callable[[str], bool], workload: list[str]
) -> BenchmarkResult:
    latencies: list[float] = []
    start_time = perf_counter()

    for client_id in workload:
        allow_request(client_id)

    elapsed_time = perf_counter() - start_time

    for client_id in workload:
        request_start = perf_counter()
        allow_request(client_id)
        request_end = perf_counter()

        latencies.append((request_end - request_start) * 1000)

    if elapsed_time <= 0:
        raise RuntimeError("Benchmark elapsed time must be positive")

    return BenchmarkResult(
        algorithm=algo_name,
        p95_latency=calculate_percentiles(latencies, 95),
        p99_latency=calculate_percentiles(latencies, 99),
        peak_memory_bytes=0,
        requests_per_second=len(workload) / elapsed_time,
        requests_processed=len(workload),
    )


def measure_memory(allow_request: Callable[[str], bool], workload: list[str]) -> int:
    tracemalloc.start()

    try:
        tracemalloc.reset_peak()
        for client_id in workload:
            allow_request(client_id)

        _, peak_memory = tracemalloc.get_traced_memory()
        # print("peak memory", peak_memory)

        return peak_memory
    finally:
        tracemalloc.stop()


def main() -> None:
    request_limit = 100
    window_duration = 60.0
    number_of_clients = 1_000
    number_of_requests = 100_000
    repetitions = 5

    workload = generate_workload(
        number_of_requests=number_of_requests,
        number_of_clients=number_of_clients,
        seed=42,
    )

    factories = {
        "Fixed Window": lambda: FixedWindowCounter(
            limit=request_limit, window_seconds=window_duration
        ),
        "Sliding Window": lambda: SlidingWindowLog(
            limit=request_limit, window_duration=window_duration
        ),
    }

    for name, factory in factories.items():
        throughput_runs: list[float] = []
        p95_runs: list[float] = []
        p99_runs: list[float] = []

        for _ in range(repetitions):
            algo = factory()
            result = benchmark_algorithm(
                algo_name=name,
                allow_request=algo.allow if name == "Fixed Window" else algo.add,
                workload=workload,
            )
            throughput_runs.append(result.requests_per_second)
            p95_runs.append(result.p95_latency)
            p99_runs.append(result.p99_latency)

        memory_algorithm = factory()
        allow_request = (
            memory_algorithm.allow if name == "Fixed Window" else memory_algorithm.add
        )
        peak_memory = measure_memory(allow_request, workload)

        print(f"\n{name}")
        print(f"Median throughput: {median(throughput_runs):,.0f} requests/sec")
        print(f"Median p95 latency: {median(p95_runs):.4f} ms")
        print(f"Median p99 latency: {median(p99_runs):.4f} ms")
        print(f"Peak traced memory: {peak_memory:,} bytes")


if __name__ == "__main__":
    main()
