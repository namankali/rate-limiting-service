from app.algorithms.sliding_window_log import SlidingWindowLog


def test_allow_request_under_limit() -> None:
    sliding_window_log = SlidingWindowLog(window_duration=60, limit=3)

    assert sliding_window_log.add("naman") is True
    assert sliding_window_log.add("naman") is True
    assert sliding_window_log.add("naman") is True


def test_rejects_requests_at_limit() -> None:
    sliding_window_log = SlidingWindowLog(window_duration=60, limit=3)

    assert sliding_window_log.add("naman") is True
    assert sliding_window_log.add("naman") is True
    assert sliding_window_log.add("naman") is True

    assert sliding_window_log.add("naman") is False


def test_allows_request_after_old_timestamp_expires() -> None:
    clock = [100.0]

    def fake_clock() -> float:
        return clock[0]

    sliding_window_log = SlidingWindowLog(window_duration=60, limit=3, _clock=fake_clock)

    assert sliding_window_log.add("naman") is True

    clock[0] = 110
    assert sliding_window_log.add("naman") is True

    clock[0] = 140
    assert sliding_window_log.add("naman") is True

    assert sliding_window_log.add("naman") is False

    clock[0] = 161
    assert sliding_window_log.add("naman") is True
    assert sliding_window_log.add("naman") is False


def test_clients_have_independent_request_limits() -> None:
    clock = [100.0]

    def fake_clock() -> float:
        return clock[0]

    sliding_window_log = SlidingWindowLog(window_duration=60, limit=2, _clock=fake_clock)

    assert sliding_window_log.add("naman") is True
    assert sliding_window_log.add("naman") is True
    assert sliding_window_log.add("naman") is False

    assert sliding_window_log.add("nikita") is True
    assert sliding_window_log.add("nikita") is True
    assert sliding_window_log.add("nikita") is False


def test_timestamp_expires_at_exact_window_boundary() -> None:
    clock = [100.0]

    def fake_clock() -> float:
        return clock[0]

    sliding_window_log = SlidingWindowLog(window_duration=60, limit=2, _clock=fake_clock)

    assert sliding_window_log.add("naman") is True
    assert sliding_window_log.add("naman") is True
    assert sliding_window_log.add("naman") is False

    clock[0] = 159.99
    assert sliding_window_log.add("naman") is False

    clock[0] = 160
    assert sliding_window_log.add("naman") is True


def test_allows_requests_when_window_becomes_empty() -> None:
    clock = [100.0]

    def fake_clock() -> float:
        return clock[0]

    sliding_window_log = SlidingWindowLog(window_duration=60, limit=2, _clock=fake_clock)

    assert sliding_window_log.add("naman") is True
    assert sliding_window_log.add("naman") is True
    assert sliding_window_log.add("naman") is False

    clock[0] = 160
    assert sliding_window_log.add("naman") is True
    assert sliding_window_log.add("naman") is True
    assert sliding_window_log.add("naman") is False
