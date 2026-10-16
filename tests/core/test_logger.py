import logging

from promptgauge.core.logger import Logger


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def _capture(name: str) -> _Capture:
    # Logger does not propagate to the root (so a host app's handlers never see it twice);
    # attach a collector to the named logger instead of using caplog.
    handler = _Capture()
    logging.getLogger(name).addHandler(handler)
    return handler


def test_api_key_is_masked_at_every_level() -> None:
    log = Logger("promptgauge.test1", level="DEBUG")
    capture = _capture("promptgauge.test1")
    log.debug("key sk-ant-api03-SECRETSECRET here")
    log.info("x", key="sk-ant-api03-SECRETSECRET")
    log.warning("sk-ant-abc_def-123")
    log.error("err", token="sk-ant-xyz")
    assert len(capture.messages) == 4
    for message in capture.messages:
        assert "SECRET" not in message
        assert "sk-ant-***" in message


def test_fields_are_appended_as_key_value() -> None:
    log = Logger("promptgauge.test2")
    capture = _capture("promptgauge.test2")
    log.info("done", calls=3, cost_usd=0.5)
    assert capture.messages == ["done calls=3 cost_usd=0.5"]


def test_level_filters_debug() -> None:
    log = Logger("promptgauge.test3", level="INFO")
    capture = _capture("promptgauge.test3")
    log.debug("hidden")
    log.info("shown")
    assert capture.messages == ["shown"]


def test_constructing_twice_adds_one_stream_handler() -> None:
    Logger("promptgauge.test4")
    Logger("promptgauge.test4")
    handlers = logging.getLogger("promptgauge.test4").handlers
    assert len(handlers) == 1 and isinstance(handlers[0], logging.StreamHandler)
