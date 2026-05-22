import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent / "lib"))
import json
import threading
import time
import requests
import urllib.parse
from datetime import datetime, timezone, timedelta

from config.builder import Builder
from config.config import config
from logs import logger
from presentation.observer import Observable

DATA_SLICE_DAYS = 1
DATETIME_FORMAT = "%Y-%m-%dT%H:%M"
REQUEST_TIMEOUT = 15
BACKOFF_MIN = 5
BACKOFF_MAX = 300
HEARTBEAT_INTERVAL_S = 30
STUCK_THRESHOLD_S = max(config.refresh_interval * 2 + 300, 1800)

try:
    import systemd.daemon as _sd
    _HAVE_SD = True
except ImportError:
    _HAVE_SD = False


def _sd_notify(msg):
    if _HAVE_SD:
        try:
            _sd.notify(msg)
        except Exception:
            pass


_last_alive = time.monotonic()
_alive_lock = threading.Lock()


def mark_alive():
    global _last_alive
    with _alive_lock:
        _last_alive = time.monotonic()


def _seconds_since_alive():
    with _alive_lock:
        return time.monotonic() - _last_alive


def _heartbeat_loop(stop_event):
    while not stop_event.wait(HEARTBEAT_INTERVAL_S):
        stale = _seconds_since_alive()
        if stale > STUCK_THRESHOLD_S:
            logger.error(
                "Heartbeat: main loop stale for %.0fs (> %ds), stopping watchdog pings",
                stale, STUCK_THRESHOLD_S,
            )
            return
        _sd_notify('WATCHDOG=1')


def get_dummy_data():
    # TODO: Implement functionality to provide dummy data for testing purposes.
    return []


def fetch_prices():
    logger.info('Fetching prices')
    timeslot_end = datetime.now(timezone.utc)
    end_date = timeslot_end.strftime(DATETIME_FORMAT)
    start_data = (timeslot_end - timedelta(days=DATA_SLICE_DAYS)).strftime(DATETIME_FORMAT)
    url = (f'https://api.exchange.coinbase.com/products/{config.currency}/candles?'
           f'granularity=900&start={urllib.parse.quote_plus(start_data)}&end={urllib.parse.quote_plus(end_date)}')
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    external_data = response.json()
    if not isinstance(external_data, list) or not external_data:
        raise ValueError(f"Unexpected API payload: {external_data!r}")
    prices = [entry[1:5] for entry in external_data[::-1]]
    return prices


def _interruptible_sleep(total_s, stop_event, step=5):
    end = time.monotonic() + total_s
    while True:
        remaining = end - time.monotonic()
        if remaining <= 0:
            return
        if stop_event.wait(min(step, remaining)):
            return


def main():
    logger.info('Initialize')

    data_sink = Observable()
    builder = Builder(config)
    builder.bind(data_sink)

    mark_alive()
    _sd_notify('READY=1')

    stop_event = threading.Event()
    heartbeat = threading.Thread(target=_heartbeat_loop, args=(stop_event,), daemon=True)
    heartbeat.start()

    backoff = BACKOFF_MIN

    try:
        while True:
            try:
                prices = [entry[1:] for entry in get_dummy_data()] if config.dummy_data else fetch_prices()
                data_sink.update_observers(prices)
                mark_alive()
                backoff = BACKOFF_MIN
                _interruptible_sleep(config.refresh_interval, stop_event)
            except (requests.exceptions.RequestException,
                    json.JSONDecodeError,
                    ValueError) as e:
                logger.error(f"Fetch failed, retrying in {backoff}s: {e}")
                mark_alive()
                _interruptible_sleep(backoff, stop_event)
                backoff = min(backoff * 2, BACKOFF_MAX)
            except Exception as e:
                logger.exception(f"Unexpected error in refresh loop: {e}")
                mark_alive()
                _interruptible_sleep(backoff, stop_event)
                backoff = min(backoff * 2, BACKOFF_MAX)
    except KeyboardInterrupt:
        logger.info('Exit')
    finally:
        stop_event.set()
        try:
            data_sink.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
