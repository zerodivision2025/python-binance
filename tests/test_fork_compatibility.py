"""Offline regression tests for fork behavior retained during upstream sync."""
import logging
from unittest.mock import patch

import pytest
import requests_mock

from binance import Client


def test_default_init_does_not_ping():
    with patch.object(Client, 'ping') as ping:
        client = Client()
        ping.assert_not_called()
        client.close_connection()
        client = Client(ping=True)
        ping.assert_called_once_with()
        client.close_connection()


@pytest.mark.parametrize('field, url', [
    ('margin', 'https://api.binance.com/sapi/v1/account/info'),
    ('options', 'https://eapi.binance.com/eapi/v1/account/info'),
])
def test_generic_call_routes_and_signs(field, url):
    client = Client('test-key', 'test-secret')
    try:
        with requests_mock.Mocker() as mock:
            mock.get(url, json={'ok': True})
            assert client.call(field, 'get', 'account/info', asset='BTC') == {'ok': True}
            assert mock.last_request.qs['asset'] == ['btc']
            assert 'signature' in mock.last_request.qs
    finally:
        client.close_connection()


def test_request_and_limit_logs(caplog):
    client = Client('test-key', 'test-secret')
    try:
        with caplog.at_level(logging.DEBUG, logger='python-binance'):
            with requests_mock.Mocker() as mock:
                mock.get('https://api.binance.com/api/v3/time', json={'serverTime': 1},
                         headers={'X-MBX-USED-WEIGHT-1M': '12', 'X-SAPI-USED-IP-WEIGHT-1M': '3'})
                assert client.get_server_time() == {'serverTime': 1}
        assert 'https://api.binance.com/api/v3/time' in caplog.text
        assert 'x-mbx-used-weight-1m=12' in caplog.text
        assert 'x-sapi-used-ip-weight-1m=3' in caplog.text
    finally:
        client.close_connection()
