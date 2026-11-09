from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from app.algorithms.token_bucket import TokenBucket


def test_initial_full_bucket_capacity() -> None:
    token_bucket = TokenBucket(capacity=100, refill_rate=10)

    assert token_bucket.current_tokens == token_bucket.capacity


def test_accepting_requests_when_token_available() -> None:
    token_bucket = TokenBucket(capacity=100, refill_rate=10)

    assert token_bucket.allow_request() is True
    assert token_bucket.current_tokens == 99


def test_reject_request_when_bucket_empty() -> None:
    token_bucket = TokenBucket(capacity=2, refill_rate=10)

    assert token_bucket.allow_request() is True
    assert token_bucket.allow_request() is True
    assert token_bucket.allow_request() is False
    assert token_bucket.current_tokens == 0


def test_token_available_after_time_passes() -> None:
    current_time = [100]

    def fake_call() -> float:
        return current_time[0]

    token_bucket = TokenBucket(capacity=2, refill_rate=2, _clock=fake_call)

    assert token_bucket.allow_request() is True
    assert token_bucket.allow_request() is True
    assert token_bucket.allow_request() is False
    assert token_bucket.current_tokens == 0

    current_time[0] = 101
    assert token_bucket.allow_request() is True
    assert token_bucket.allow_request() is True
    assert token_bucket.current_tokens == 0


def test_bucket_never_exceeds_capacity() -> None:
    current_time = [100.0]

    def fake_call() -> float:
        return current_time[0]

    token_bucket = TokenBucket(capacity=2, refill_rate=2, _clock=fake_call)

    # Consume both available tokens
    assert token_bucket.allow_request() is True
    assert token_bucket.allow_request() is True
    assert token_bucket.current_tokens == 0

    # Advance time enough to generate more tokens than the bucket can hold
    current_time[0] = 110.0

    assert token_bucket.allow_request() is True
    assert token_bucket.current_tokens == 1

    assert token_bucket.allow_request() is True
    assert token_bucket.current_tokens == 0

    # Trigger another refill after enough time has passed
    current_time[0] = 120.0

    assert token_bucket.allow_request() is True
    assert token_bucket.current_tokens == 1
    assert token_bucket.current_tokens <= token_bucket.capacity


def test_tokenbucket_instance_independent_state() -> None:
    token_bucket_1 = TokenBucket(capacity=2, refill_rate=2)
    token_bucket_2 = TokenBucket(capacity=2, refill_rate=2)

    assert token_bucket_1.allow_request() is True
    assert token_bucket_1.current_tokens == 1
    assert token_bucket_2.current_tokens == 2


def test_rejects_invalid_configuration() -> None:
    with pytest.raises(ValueError, match="Capacity should be positive"):
        TokenBucket(capacity=0, refill_rate=2)

    with pytest.raises(ValueError, match="Refill rate should be positive"):
        TokenBucket(capacity=100, refill_rate=0)

    with pytest.raises(ValueError, match="Capacity should be positive"):
        TokenBucket(capacity=-1, refill_rate=2)

    with pytest.raises(ValueError, match="Refill rate should be positive"):
        TokenBucket(capacity=100, refill_rate=-2)


def test_concurrent_requests() -> None:
    current_clock: list[float] = [100.0]

    def fake_clock() -> float:
        return current_clock[0]

    number_of_request = 60
    token_bucket = TokenBucket(capacity=50, refill_rate=2, _clock=fake_clock)

    barrier = Barrier(number_of_request)

    def make_request() -> bool:
        barrier.wait()
        return token_bucket.allow_request()

    with ThreadPoolExecutor(max_workers=number_of_request) as executor:
        result = list(executor.map(lambda _: make_request(), range(number_of_request)))

    allowed_req = sum(result)
    rejected_request = result.count(False)
    request_made = len(result)

    assert allowed_req == 50
    assert rejected_request == 10
    assert request_made == 60
    assert token_bucket.current_tokens == 0


def test_allows_initial_burst_up_to_capacity() -> None:
    current_clock: list[float] = [100.0]

    def fake_clock() -> float:
        return current_clock[0]

    number_of_request = 100

    token_bucket = TokenBucket(capacity=100, refill_rate=10, _clock=fake_clock)
    barrier = Barrier(number_of_request)

    def make_request() -> bool:
        barrier.wait()
        return token_bucket.allow_request()

    with ThreadPoolExecutor(max_workers=number_of_request) as executor:
        result = list(executor.map(lambda _: make_request(), range(number_of_request)))

    assert sum(result) == 100
    assert token_bucket.current_tokens == 0
    assert token_bucket.allow_request() is False


def test_refills_tokens_after_burst_is_exhausted() -> None:
    current_clock: list[float] = [100.0]

    def fake_clock() -> float:
        return current_clock[0]

    number_of_request = 100

    token_bucket = TokenBucket(capacity=100, refill_rate=10, _clock=fake_clock)
    barrier = Barrier(number_of_request)

    def make_request() -> bool:
        barrier.wait()
        return token_bucket.allow_request()

    with ThreadPoolExecutor(max_workers=number_of_request) as executor:
        list(executor.map(lambda _: make_request(), range(number_of_request)))

    current_clock[0] = 101

    assert token_bucket.allow_request() is True
    assert token_bucket.current_tokens == 9
