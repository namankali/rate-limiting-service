from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from app.algorithms.fixed_window import FixedWindowCounter


def test_rejects_requests_when_limit_is_reached() -> None:
    counter = FixedWindowCounter(limit=1, window_seconds=60)
    allow = counter.allow("naman")
    assert allow is True

    allow = counter.allow("naman")
    assert allow is False


def test_allows_requests_under_limit() -> None:
    counter = FixedWindowCounter(limit=2, window_seconds=60)
    allow = counter.allow("naman")
    allow_1 = counter.allow("naman")

    assert allow is True
    assert allow_1 is True


def test_rejects_requests_above_limit() -> None:
    counter = FixedWindowCounter(limit=2, window_seconds=60)
    allow = counter.allow("naman")
    allow_1 = counter.allow("naman")
    allow_2 = counter.allow("naman")

    assert allow is True
    assert allow_1 is True
    assert allow_2 is False


def test_allows_request_after_window_expires() -> None:
    current_time = [100.0]

    def fake_clock() -> float:
        return current_time[0]

    counter = FixedWindowCounter(window_seconds=3, limit=2, _clock=fake_clock)

    assert counter.allow("naman") is True
    assert counter.allow("naman") is True
    assert counter.allow("naman") is False

    current_time[0] = 105.0

    assert counter.allow("naman") is True


def test_resets_count_for_a_new_window() -> None:
    current_time = [100.0]

    def fake_clock() -> float:
        return current_time[0]

    counter = FixedWindowCounter(window_seconds=3, limit=2, _clock=fake_clock)
    allow = counter.allow("naman")
    allow_1 = counter.allow("naman")
    allow_2 = counter.allow("naman")

    assert allow is True
    assert allow_1 is True
    assert allow_2 is False

    current_time[0] = 110.0
    allow_3 = counter.allow("naman")
    assert allow_3 is True


def test_tracks_clients_independently() -> None:
    counter = FixedWindowCounter(window_seconds=4, limit=1)
    allow_1 = counter.allow("nikita")
    allow = counter.allow("naman")
    allow_2 = counter.allow("nikita")

    assert allow is True
    assert allow_1 is True
    assert allow_2 is False


def test_behavior_just_before_expiration() -> None:
    current_time = [0.0]

    def fake_clock() -> float:
        return current_time[0]

    counter = FixedWindowCounter(limit=2, window_seconds=60, _clock=fake_clock)
    assert counter.allow("naman") is True
    assert counter.allow("naman") is True

    current_time[0] = 59.999

    assert counter.allow("naman") is False


def test_behavior_exactly_at_expiration() -> None:
    current_time = [0.0]

    def fake_clock() -> float:
        return current_time[0]

    counter = FixedWindowCounter(limit=2, window_seconds=60, _clock=fake_clock)
    assert counter.allow("naman") is True
    assert counter.allow("naman") is True

    current_time[0] = 60.0

    assert counter.allow("naman") is True


def test_behavior_exactly_after_expiration() -> None:
    current_time = [0.0]

    def fake_clock() -> float:
        return current_time[0]

    counter = FixedWindowCounter(limit=2, window_seconds=60, _clock=fake_clock)
    assert counter.allow("naman") is True
    assert counter.allow("naman") is True

    current_time[0] = 60.001

    assert counter.allow("naman") is True


def test_concurrent_requests_respect_rate_limit() -> None:
    limit = 5
    number_of_requests = 50
    client_key = "naman"

    counter = FixedWindowCounter(limit=limit, window_seconds=60)
    barrier = Barrier(number_of_requests)

    def make_request() -> bool:
        barrier.wait()
        return counter.allow(client_key)

    with ThreadPoolExecutor(max_workers=number_of_requests) as executor:
        result = list(executor.map(lambda _: make_request(), range(number_of_requests)))

    allowed_req = sum(result)
    rejected_req = result.count(False)

    assert allowed_req == 5
    assert rejected_req == 45
