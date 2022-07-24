import demistomock as demisto
from CommonServerPython import *  # noqa # pylint: disable=unused-wildcard-import
from CommonServerUserPython import *  # noqa

import urllib3
import traceback
from typing import Dict, Any, List

# Disable insecure warnings
urllib3.disable_warnings()  # pylint: disable=no-member


''' CONSTANTS '''

DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'  # ISO8601 format with UTC, default in XSOAR

EVENT_TYPES_V1 = ['application', 'audit', 'network']  # api version - v1
EVENT_TYPES_V2 = ['alert', 'application', 'audit', 'network']  # api version v2


''' CLIENT CLASS '''


class Client(BaseClient):
    """
    Client for Netskope RESTful API.

    Args:
        base_url (str): The base URL of Netskope.
        token (str): The token to authenticate against Netskope API.
        validate_certificate (bool): Specifies whether to verify the SSL certificate or not.
        proxy (bool): Specifies if to use XSOAR proxy settings.
    """

    def __init__(self, base_url: str, token: str, api_version: str, validate_certificate: bool, proxy: bool):
        super().__init__(base_url, verify=validate_certificate, proxy=proxy)
        if api_version == 'v1':
            self._session.params['token'] = token
        else:
            self.headers = {'Netskope-Api-Token': token}

    def get_events_request_v1(self, last_run: dict = None, limit: Optional[int] = None) -> List[Any] | Any:
        """
        Get all events extracted from Saas traffic and or logs.
        Args:
            last_run (dict): Get alerts from certain time period.
            limit (Optional[int]): The maximum number of alerts to return (up to 10000).
        Returns:
            events (list).
        """
        events = []
        url_suffix = 'events'
        for event_type in EVENT_TYPES_V1:
            body = {'timeperiod': last_run.get(event_type), 'limit': limit, 'type': event_type}
            response = self._http_request(method='GET', url_suffix=url_suffix, json_data=body)
            if response.get('status') == 'success':
                results = response.get('data', [])
                for event in results:
                    event['event_type'] = event_type
                events.extend(results)

        return events

    def v1_get_alerts_request(self, last_run: dict = None, limit: Optional[int] = None) -> list[Any] | Any:
        """
        Get alerts generated by Netskope, including policy, DLP, and watch list alerts.

        Args:
            last_run (dict): Get alerts from certain time period.
            limit (Optional[int]): The maximum number of alerts to return (up to 10000).

        Returns:
            List[str, Any]: Netskope alerts.
        """

        url_suffix = 'alerts'
        body = {'timeperiod': last_run.get('alert'), 'limit': limit}
        response = self._http_request(method='GET', url_suffix=url_suffix, json_data=body)
        if response.get('status') == 'success':
            results = response.get('data', [])
            for event in results:
                event['event_type'] = 'alert'
            return results
        return []

    def get_events_request_v2(self, last_run: dict, limit: Optional[int] = None,
                              is_test: bool = False) -> List[Any] | Any:
        """
        Get all events extracted from Saas traffic and or logs.
        Args:
            last_run (dict): Get alerts from certain time period.
            limit (Optional[int]): The maximum number of alerts to return (up to 10000).
            is_test (bool): if the request runs on test module or not.
        Returns:
            events (list).
        """
        events = []
        for event_type in EVENT_TYPES_V2:
            url_suffix = f'events/data/{event_type}'
            params = {'timeperiod': last_run.get(event_type), 'limit': limit}
            response = self._http_request(method='GET', url_suffix=url_suffix, headers=self.headers, params=params)
            if response.get('ok') == 1:
                results = response.get('result', [])
                for event in results:
                    event['event_type'] = event_type
                events.extend(results)
                if is_test:
                    return events
        return events


''' HELPER FUNCTIONS '''


def arg_to_seconds_timestamp(arg: Optional[str]) -> Optional[int]:
    """
    Converts an XSOAR date string argument to a timestamp in seconds.

    Args:
        arg (Optional[str]): The argument to convert.

    Returns:
        Optional[int]: A timestamp if arg can be converted,
        or None if arg is None.
    """

    if arg is None:
        return None

    return date_to_seconds_timestamp(arg_to_datetime(arg))


def date_to_seconds_timestamp(date_str_or_dt: Union[str, datetime]) -> int:
    """
    Converts date string or datetime object to a timestamp in seconds.

    Args:
        date_str_or_dt (Union[str, datetime]): The datestring or datetime.

    Returns:
        int: The timestamp in seconds.
    """

    return date_to_timestamp(date_str_or_dt) // 1000


def get_sorted_events_by_type(events: list, event_type: str = '') -> list:
    filtered_events = [event for event in events if event.get('event_type') == event_type]
    filtered_events.sort(key=lambda k: k.get('_id'))
    return filtered_events


def get_last_run(events: list, last_run: dict) -> dict:  # type: ignore
    """
    Args:
    events (list): list of the event from the api
    last_run (dict): the dictionary containing the last run times for the event types
    Returns:
    A dictionary with the times for the next run
    """
    alerts = get_sorted_events_by_type(events, event_type='alert')
    audit_events = get_sorted_events_by_type(events, event_type='audit')
    applications_events = get_sorted_events_by_type(events, event_type='application')
    network_events = get_sorted_events_by_type(events, event_type='network')
    if not alerts:
        alerts_time = last_run['alert']
    else:
        alerts_time = alerts[-1]['timestamp']
    if not applications_events:
        applications_time = last_run['application']
    else:
        applications_time = applications_events[-1]['timestamp']
    if not audit_events:
        audit_time = last_run['audit']
    else:
        audit_time = audit_events[-1]['timestamp']
    if not network_events:
        network_time = last_run['network']
    else:
        network_time = network_events[-1]['timestamp']
    return {'alert': alerts_time, 'application': applications_time, 'audit': audit_time,
            'network': network_time}


''' COMMAND FUNCTIONS '''


def test_module(client: Client, api_version: str, last_run: dict) -> str:
    if api_version == 'v1':
        last_run = {'alert': 604800}  # For v1 it supports only specific timestamps - - Last 30 days
        response = client.v1_get_alerts_request(last_run, limit=1)
    else:
        response = client.get_events_request_v2(last_run, limit=1, is_test=True)

    if response:
        return 'ok'
    else:
        return f'Test failed - {response.get("errorCode")}, {response.get("errors")}'


def v1_get_events_command(client: Client, args: Dict[str, Any], last_run: dict) -> CommandResults:
    limit = arg_to_number(args.get('limit', 20))

    events = client.get_events_request_v1(last_run, limit)
    alerts = client.v1_get_alerts_request(last_run, limit)
    if alerts:
        events.extend(alerts)

    for event in events:
        event['timestamp'] = timestamp_to_datestring(event['timestamp'] * 1000)

    readable_output = tableToMarkdown('Events List:', events,
                                      removeNull=True,
                                      headers=['_id', 'timestamp', 'type', 'access_method', 'app', 'traffic_type'],
                                      headerTransform=string_to_table_header)

    return CommandResults(outputs_prefix='Netskope.Event',
                          outputs_key_field='_id',
                          outputs=events,
                          readable_output=readable_output,
                          raw_response=events)


def v2_get_events_command(client: Client, args: Dict[str, Any], last_run: dict) -> CommandResults:
    limit = arg_to_number(args.get('limit', 50))

    events = client.get_events_request_v2(last_run, limit)
    for event in events:
        event['timestamp'] = timestamp_to_datestring(event['timestamp'] * 1000)

    readable_output = tableToMarkdown('Events List:', events,
                                      removeNull=True,
                                      headers=['_id', 'timestamp', 'type', 'access_method', 'app', 'traffic_type'],
                                      headerTransform=string_to_table_header)

    return CommandResults(outputs_prefix='Netskope.Event',
                          outputs_key_field='_id',
                          outputs=events,
                          readable_output=readable_output,
                          raw_response=events)


''' MAIN FUNCTION '''


def main() -> None:
    params = demisto.params()

    url = params.get('url')
    api_version = params.get('api_version')
    token = demisto.params().get('credentials', {}).get('password')
    base_url = urljoin(url, f'/api/{api_version}/')
    verify_certificate = not demisto.params().get('insecure', False)
    proxy = demisto.params().get('proxy', False)
    first_fetch = params.get('first_fetch')
    max_fetch = params.get('max_fetch')
    vendor, product = params.get('vendor', 'netskope'), params.get('product', 'netskope')

    demisto.debug(f'Command being called is {demisto.command()}')
    try:
        client = Client(base_url, token, api_version, verify_certificate, proxy)

        last_run = demisto.getLastRun()
        if 'alert' not in last_run and 'application' not in last_run and 'audit' not in last_run \
                and 'network' not in last_run:
            last_run = arg_to_seconds_timestamp(first_fetch)
            last_run = {
                'alert': last_run,
                'application': last_run,
                'audit': last_run,
                'network': last_run
            }

        if demisto.command() == 'test-module':
            # This is the call made when pressing the integration Test button.
            result = test_module(client, api_version, last_run)
            return_results(result)

        elif demisto.command() == 'netskope-get-events':
            if api_version == 'v1':
                return_results(v1_get_events_command(client, demisto.args(), last_run))
            else:
                return_results(v2_get_events_command(client, demisto.args(), last_run))
        elif demisto.command() == 'fetch-events':
            if api_version == 'v1':
                events = client.get_events_request_v1(last_run, max_fetch)
                alerts = client.v1_get_alerts_request(last_run, max_fetch)
                if alerts:
                    events.extend(alerts)
                demisto.setLastRun(get_last_run(events, last_run))
                demisto.debug(f'Setting the last_run to: {last_run}')
                send_events_to_xsiam(events=events, vendor=vendor, product=product)
            else:
                events = client.get_events_request_v2(last_run, max_fetch)
                demisto.setLastRun(get_last_run(events, last_run))
                demisto.debug(f'Setting the last_run to: {last_run}')
                send_events_to_xsiam(events=events, vendor=vendor, product=product)

    # Log exceptions and return errors
    except Exception as e:
        return_error(f'Failed to execute {demisto.command()} command.\nError:\n{str(e)}')


''' ENTRY POINT '''


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
