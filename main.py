import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent / "lib"))
import json
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


def main():
    logger.info('Initialize')

    data_sink = Observable()
    builder = Builder(config)
    builder.bind(data_sink)

    _sd_notify('READY=1')
    backoff = BACKOFF_MIN

    try:
        while True:
            try:
                prices = [entry[1:] for entry in get_dummy_data()] if config.dummy_data else fetch_prices()
                data_sink.update_observers(prices)
                _sd_notify('WATCHDOG=1')
                backoff = BACKOFF_MIN
                time.sleep(config.refresh_interval)
            except (requests.exceptions.RequestException,
                    json.JSONDecodeError,
                    ValueError) as e:
                logger.error(f"Fetch failed, retrying in {backoff}s: {e}")
                time.sleep(backoff)
                backoff = min(backoff * 2, BACKOFF_MAX)
            except Exception as e:
                logger.exception(f"Unexpected error in refresh loop: {e}")
                time.sleep(backoff)
                backoff = min(backoff * 2, BACKOFF_MAX)
    except KeyboardInterrupt:
        logger.info('Exit')
        data_sink.close()


if __name__ == "__main__":
    main()
