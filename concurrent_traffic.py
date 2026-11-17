import asyncio
import math
import time
from collections import Counter, defaultdict

import httpx

# Service instances
BASE_URLS = [
    "http://127.0.0.1:8002",
    "http://127.0.0.1:8003",
    "http://127.0.0.1:8004",
]

ENDPOINT = "/rate/v1/check"

# Must match the Fixed Window policy in PostgreSQL.
WINDOW_SECONDS = 60

# Progressive concurrency levels
CONCURRENCY_LEVELS = [50, 100, 200, 500]

# Keep the same identity for every run.
PAYLOAD = {
    "client_id": "7220990a-425b-4e94-8498-1f9d58d4c988",
    "resource": "ai-devops",
    "route": "api/users/v1/login",
    "identity_type": "user",
    "identity_value": "user-123",
}

REQUEST_TIMEOUT = 30.0


def percentile(values: list[float], percentage: int) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)
    index = math.ceil((percentage / 100) * len(ordered)) - 1
    return ordered[max(0, index)]


async def send_request(
    client: httpx.AsyncClient,
    request_number: int,
) -> dict:
    base_url = BASE_URLS[request_number % len(BASE_URLS)]
    instance = base_url.rsplit(":", 1)[-1]

    start = time.perf_counter()

    try:
        response = await client.post(
            f"{base_url}{ENDPOINT}",
            json=PAYLOAD,
        )

        latency_ms = (time.perf_counter() - start) * 1000

        try:
            body = response.json()
        except ValueError:
            body = {}

        return {
            "instance": instance,
            "status": response.status_code,
            "allowed": body.get("allowed"),
            "latency_ms": latency_ms,
            "error": None,
        }

    except (TimeoutError, httpx.HTTPError) as exc:
        latency_ms = (time.perf_counter() - start) * 1000

        return {
            "instance": instance,
            "status": None,
            "allowed": None,
            "latency_ms": latency_ms,
            "error": str(exc),
        }


async def run_concurrency_level(
    client: httpx.AsyncClient,
    concurrency: int,
    run_number: int,
) -> None:
    print("\n" + "=" * 65)
    print(f"RUN {run_number}: {concurrency} CONCURRENT REQUESTS")
    print("=" * 65)

    print("Sending requests...")

    start = time.perf_counter()

    results = await asyncio.gather(
        *[send_request(client, request_number) for request_number in range(concurrency)]
    )

    total_duration = time.perf_counter() - start

    allowed = sum(result["allowed"] is True for result in results)
    rejected = sum(result["allowed"] is False for result in results)
    errors = sum(result["error"] is not None for result in results)

    status_counts = Counter(result["status"] for result in results if result["status"] is not None)

    latencies = [result["latency_ms"] for result in results if result["error"] is None]

    instance_counts = defaultdict(lambda: {"total": 0, "allowed": 0, "rejected": 0, "errors": 0})

    for result in results:
        stats = instance_counts[result["instance"]]
        stats["total"] += 1

        if result["allowed"] is True:
            stats["allowed"] += 1
        elif result["allowed"] is False:
            stats["rejected"] += 1
        else:
            stats["errors"] += 1

    print("\nRESULTS")
    print("-" * 65)
    print(f"Total requests:       {concurrency}")
    print(f"Allowed:              {allowed}")
    print(f"Rejected:             {rejected}")
    print(f"Errors:               {errors}")
    print(f"HTTP status counts:   {dict(status_counts)}")
    print(f"Total duration:       {total_duration:.3f}s")

    if latencies:
        print(f"Average latency:      {sum(latencies) / len(latencies):.2f} ms")
        print(f"P50 latency:          {percentile(latencies, 50):.2f} ms")
        print(f"P95 latency:          {percentile(latencies, 95):.2f} ms")
        print(f"P99 latency:          {percentile(latencies, 99):.2f} ms")

    print("\nPER-INSTANCE BREAKDOWN")
    print("-" * 65)

    for instance, stats in sorted(instance_counts.items()):
        print(
            f"Port {instance}: "
            f"total={stats['total']}, "
            f"allowed={stats['allowed']}, "
            f"rejected={stats['rejected']}, "
            f"errors={stats['errors']}"
        )

    if allowed + rejected != concurrency - errors:
        print("\nWARNING: Some responses did not contain a boolean 'allowed' field.")

    print("\nCheck Redis before proceeding to the next run.")


async def main() -> None:
    limits = httpx.Limits(
        max_connections=600,
        max_keepalive_connections=100,
    )

    timeout = httpx.Timeout(REQUEST_TIMEOUT)

    async with httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
    ) as client:
        print("=" * 65)
        print("FIXED WINDOW - DISTRIBUTED CONCURRENCY EXPERIMENT")
        print("=" * 65)

        print(f"Instances: {', '.join(BASE_URLS)}")
        print(f"Window duration: {WINDOW_SECONDS} seconds")
        print(f"Concurrency levels: {CONCURRENCY_LEVELS}")

        for run_number, concurrency in enumerate(
            CONCURRENCY_LEVELS,
            start=1,
        ):
            wait_seconds = WINDOW_SECONDS + 2

            print(f"\nWaiting {wait_seconds} seconds for the previous Fixed Window to expire...")

            await asyncio.sleep(wait_seconds)

            await run_concurrency_level(
                client=client,
                concurrency=concurrency,
                run_number=run_number,
            )

        print("\n" + "=" * 65)
        print("ALL CONCURRENCY RUNS COMPLETED")
        print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
