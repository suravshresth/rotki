from http import HTTPStatus
from typing import List

import requests
from eth_utils import to_checksum_address

from rotkehlchen.db.ens import DBEns
from rotkehlchen.tests.utils.api import (
    api_url_for,
    assert_error_response,
    assert_proper_response_with_result,
)
from rotkehlchen.types import ChecksumEthAddress


def _get_timestamps(db: DBEns, addresses: List[ChecksumEthAddress]):
    timestamps = []
    for value in db.get_reverse_ens(addresses).values():
        if isinstance(value, int):
            timestamps.append(value)
        else:
            timestamps.append(value.last_update)

    return timestamps


def test_reverse_ens(rotkehlchen_api_server):
    """Test that we can reverse resolve ENS names"""
    db = DBEns(rotkehlchen_api_server.rest_api.rotkehlchen.data.db)
    addrs_1 = [
        to_checksum_address('0x9531c059098e3d194ff87febb587ab07b30b1306'),
        to_checksum_address('0x2b888954421b424c5d3d9ce9bb67c9bd47537d12'),
    ]
    response = requests.post(
        api_url_for(
            rotkehlchen_api_server,
            'reverseensresource',
        ),
        json={'ethereum_addresses': addrs_1},
    )
    result = assert_proper_response_with_result(response)
    expected_resp_1 = {
        addrs_1[0]: 'rotki.eth',
        addrs_1[1]: 'lefteris.eth',
    }
    assert result == expected_resp_1

    addrs_2 = [
        to_checksum_address('0x9531c059098e3d194ff87febb587ab07b30b1306'),
        to_checksum_address('0xa4b73b39f73f73655e9fdc5d167c21b3fa4a1ed6'),
        to_checksum_address('0x71C7656EC7ab88b098defB751B7401B5f6d8976F'),
    ]
    timestamps_before_request = _get_timestamps(db, addrs_1)
    response = requests.post(
        api_url_for(
            rotkehlchen_api_server,
            'reverseensresource',
        ),
        json={'ethereum_addresses': addrs_2},
    )
    result = assert_proper_response_with_result(response)
    all_addrs = list(set(addrs_1) | set(addrs_2))
    expected_resp_2 = {
        addrs_2[0]: 'rotki.eth',
        addrs_2[1]: 'abc.eth',
    }
    assert result == expected_resp_2
    timestamps_after_request = _get_timestamps(db, addrs_1)
    assert timestamps_before_request == timestamps_after_request

    response = requests.post(
        api_url_for(
            rotkehlchen_api_server,
            'reverseensresource',
        ),
        json={'ethereum_addresses': ['0xqwerty']},
    )
    assert_error_response(
        response=response,
        contained_in_msg='Given value 0xqwerty is not an ethereum address',
        status_code=HTTPStatus.BAD_REQUEST,
    )

    timestamps_before_request = _get_timestamps(db, all_addrs)
    requests.post(
        api_url_for(
            rotkehlchen_api_server,
            'reverseensresource',
        ),
        json={'ethereum_addresses': all_addrs, 'ignore_cache': True},
    )
    timestamps_after_request = _get_timestamps(db, all_addrs)
    assert all(map(lambda t_pair: t_pair[0] < t_pair[1], zip(timestamps_before_request, timestamps_after_request)))  # noqa: E501