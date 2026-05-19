from gls_replay.classifier import classify_failure
from gls_replay.models import SpyglassRule, WaveMarker


def test_xprop_classification():
    c = classify_failure(
        "UVM_ERROR X value reached compare path",
        [WaveMarker(10.0, "dut.valid_q", "X", "first x-prop")],
        [SpyglassRule("RST_UNSYNC", "High", "dut.valid_q", "reset release not synchronized")],
    )
    assert c.failure_class == "x_propagation"
    assert "dut.valid_q" in c.suspects


def test_timing_classification():
    c = classify_failure(
        "Warning timing violation hold",
        [WaveMarker(20.0, "dut.ptr_q", "0", "timing glitch")],
        [SpyglassRule("GENCLK_DEF", "High", "dut.clk", "generated-clock constraint incomplete")],
    )
    assert c.failure_class == "timing_mismatch"
    assert c.first_failure_ns == 20.0
