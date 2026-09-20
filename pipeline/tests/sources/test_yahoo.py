import json
from datetime import date
from decimal import Decimal

from portfolio.sources.yahoo import YahooFinanceSource

# Bars are stamped at the session open in exchange-local time. Yahoo returns
# 2026-09-18's ASX session as 1789689600 (00:00 UTC on the 18th), which with
# the +10h offset is 10am on the 18th in Sydney.
SEP_16 = 1789516800
SEP_17 = 1789603200
SEP_18 = 1789689600
SYDNEY_OFFSET = 36000


def _payload(closes, timestamps, currency="AUD", offset=SYDNEY_OFFSET):
    return {
        "chart": {
            "error": None,
            "result": [
                {
                    "meta": {"symbol": "IVV.AX", "currency": currency, "gmtoffset": offset},
                    "timestamp": timestamps,
                    "indicators": {
                        "quote": [{"close": closes}],
                        "adjclose": [{"adjclose": [c * 1.02 if c else c for c in closes]}],
                    },
                }
            ],
        }
    }


def _fetch(payload):
    return lambda url: json.dumps(payload).encode()


def test_maps_asx_instrument_to_a_yahoo_symbol(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        return json.dumps(_payload([71.59], [SEP_18])).encode()

    source = YahooFinanceSource(tmp_path, fetch=fetch)
    source.get_price("ASX:IVV", date(2026, 9, 18))

    assert "/chart/IVV.AX?" in seen[0]


def test_session_date_comes_from_the_exchange_offset_not_utc(tmp_path):
    source = YahooFinanceSource(tmp_path, fetch=_fetch(_payload([71.59], [SEP_18])))

    quote = source.get_price("ASX:IVV", date(2026, 9, 18))

    assert quote is not None
    assert quote.price == Decimal("71.59")
    assert quote.currency == "AUD"


def test_float_noise_is_rounded_away(tmp_path):
    # What Yahoo actually returns for a 71.59 close.
    source = YahooFinanceSource(
        tmp_path, fetch=_fetch(_payload([71.58999633789062], [SEP_18]))
    )
    quote = source.get_price("ASX:IVV", date(2026, 9, 18))
    assert quote.price == Decimal("71.59")


def test_uses_raw_close_not_adjusted_close(tmp_path):
    # adjclose in the fixture is 2% higher. Using it would double-count the
    # distributions the benchmark adds separately from iShares.
    source = YahooFinanceSource(tmp_path, fetch=_fetch(_payload([100.0], [SEP_18])))
    quote = source.get_price("ASX:IVV", date(2026, 9, 18))
    assert quote.price == Decimal("100")


def test_missing_bars_are_skipped(tmp_path):
    # Yahoo pads halted or non-trading sessions with nulls.
    payload = _payload([71.0, None, 71.5], [SEP_16, SEP_17, SEP_18])
    source = YahooFinanceSource(tmp_path, fetch=_fetch(payload))

    assert source.get_price("ASX:IVV", date(2026, 9, 16)) is not None
    assert source.get_price("ASX:IVV", date(2026, 9, 17)) is None
    assert source.get_price("ASX:IVV", date(2026, 9, 18)) is not None


def test_second_lookup_uses_the_cache(tmp_path):
    calls = []

    def fetch(url):
        calls.append(url)
        return json.dumps(_payload([71.59], [SEP_18])).encode()

    source = YahooFinanceSource(tmp_path, fetch=fetch)
    source.get_price("ASX:IVV", date(2026, 9, 18))
    source.get_price("ASX:IVV", date(2026, 9, 18))

    assert len(calls) == 1


def test_non_asx_instrument_raises(tmp_path):
    source = YahooFinanceSource(tmp_path, fetch=lambda url: b"{}")
    try:
        source.get_price("NASDAQ:AAPL", date(2026, 9, 18))
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_error_payload_raises(tmp_path):
    payload = {"chart": {"error": {"code": "Not Found", "description": "No data found"}, "result": None}}
    source = YahooFinanceSource(tmp_path, fetch=_fetch(payload))
    try:
        source.get_price("ASX:ZZZ", date(2026, 9, 18))
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass
