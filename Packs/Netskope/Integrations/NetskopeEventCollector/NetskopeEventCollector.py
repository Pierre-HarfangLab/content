import demistomock as demisto
from CommonServerPython import *  # noqa # pylint: disable=unused-wildcard-import
from CommonServerUserPython import *  # noqa

import urllib3
import traceback
from typing import Dict, Any

# Disable insecure warnings
urllib3.disable_warnings()  # pylint: disable=no-member


''' CONSTANTS '''

DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'  # ISO8601 format with UTC, default in XSOAR

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

    def __init__(self, base_url: str, token: str, validate_certificate: bool, proxy: bool):
        super().__init__(base_url, verify=validate_certificate, proxy=proxy)
        self._session.params['token'] = token

    def v1_get_events_request(self, timeperiod: Optional[int] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get events extracted from SaaS traffic and or logs.

        Args:
            timeperiod (Optional[int]): Get all events from a certain time period.
            limit (Optional[int]): The maximum amount of events to retrieve (up to 10000 events).

        Returns:
            Dict[str, Any]: Netskope events.
        """
        url_suffix = 'events'
        body = {'timeperiod': timeperiod, 'limit': limit}

        return self._http_request(method='GET', url_suffix=url_suffix, json_data=body)

    def v1_get_alerts_request(self, timeperiod: Optional[int] = None, limit: Optional[int] = None):
        """
        Get alerts generated by Netskope, including policy, DLP, and watch list alerts.

        Args:
            timeperiod (Optional[int]): Get alerts from certain time period.
            limit (Optional[int]): The maximum number of alerts to return (up to 10000).

        Returns:
            Dict[str, Any]: Netskope alerts.
        """

        url_suffix = 'alerts'
        body = {'timeperiod': timeperiod, 'limit': limit}

        return self._http_request(method='GET', url_suffix=url_suffix, json_data=body)

    def v2_get_alert_events_request(self, timeperiod: Optional[int] = None, limit: Optional[int] = None):
        """
        Get events of type alert generated by Netskope.

        Args:
            timeperiod (Optional[int]): Get alerts from certain time period.
            limit (Optional[int]): The maximum number of events to return (up to 10000).

        Returns:
            Dict[str, Any]: Netskope events.
        """
        url_suffix = 'events/data/alert'
        body = {'timeperiod': timeperiod, 'limit': limit}

        return self._http_request(method='GET', url_suffix=url_suffix, json_data=body)

    def v2_get_network_events_request(self, timeperiod: Optional[int] = None, limit: Optional[int] = None):
        """
        Get events of type network generated by Netskope.

        Args:
            timeperiod (Optional[int]): Get alerts from certain time period.
            limit (Optional[int]): The maximum number of events to return (up to 10000).

        Returns:
            Dict[str, Any]: Netskope events.
        """
        url_suffix = 'events/data/network'
        body = {'timeperiod': timeperiod, 'limit': limit}

        return self._http_request(method='GET', url_suffix=url_suffix, json_data=body)

    def v2_get_audit_events_request(self, timeperiod: Optional[int] = None, limit: Optional[int] = None):
        """
        Get events of type audit generated by Netskope.

        Args:
            timeperiod (Optional[int]): Get alerts from certain time period.
            limit (Optional[int]): The maximum number of events to return (up to 10000).

        Returns:
            Dict[str, Any]: Netskope events.
        """
        url_suffix = 'events/data/audit'
        body = {'timeperiod': timeperiod, 'limit': limit}

        return self._http_request(method='GET', url_suffix=url_suffix, json_data=body)

    def v2_get_application_events_request(self, timeperiod: Optional[int] = None, limit: Optional[int] = None):
        """
        Get events of type application generated by Netskope.

        Args:
            timeperiod (Optional[int]): Get alerts from certain time period.
            limit (Optional[int]): The maximum number of events to return (up to 10000).

        Returns:
            Dict[str, Any]: Netskope events.
        """
        url_suffix = 'events/data/application'
        body = {'timeperiod': timeperiod, 'limit': limit}

        return self._http_request(method='GET', url_suffix=url_suffix, json_data=body)


''' HELPER FUNCTIONS '''

# TODO: ADD HERE ANY HELPER FUNCTION YOU MIGHT NEED (if any)

''' COMMAND FUNCTIONS '''


def test_module(client: Client) -> str:
    """Tests API connectivity and authentication'

    Returning 'ok' indicates that the integration works like it is supposed to.
    Connection to the service is successful.
    Raises exceptions if something goes wrong.

    :type client: ``Client``
    :param Client: client to use

    :return: 'ok' if test passed, anything else will fail the test.
    :rtype: ``str``
    """

    message: str = ''
    try:
        # TODO: ADD HERE some code to test connectivity and authentication to your service.
        # This  should validate all the inputs given in the integration configuration panel,
        # either manually or by using an API that uses them.
        message = 'ok'
    except DemistoException as e:
        if 'Forbidden' in str(e) or 'Authorization' in str(e):  # TODO: make sure you capture authentication errors
            message = 'Authorization Error: make sure API Key is correctly set'
        else:
            raise e
    return message


# TODO: REMOVE the following dummy command function
def baseintegration_dummy_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    dummy = args.get('dummy', None)
    if not dummy:
        raise ValueError('dummy not specified')

    # Call the Client function and get the raw response
    result = client.baseintegration_dummy(dummy)

    return CommandResults(
        outputs_prefix='BaseIntegration',
        outputs_key_field='',
        outputs=result,
    )


''' MAIN FUNCTION '''


def main() -> None:
    params = demisto.params()

    url = params.get('url')
    api_version = params.get('api_version')
    token = demisto.params().get('credentials', {}).get('password')
    base_url = urljoin(url, f'/api/{api_version}')
    verify_certificate = not demisto.params().get('insecure', False)
    proxy = demisto.params().get('proxy', False)
    first_fetch = params.get('first_fetch')
    vendor, product = params.get('vendor'), params.get('product')

    demisto.debug(f'Command being called is {demisto.command()}')
    try:
        client = Client(base_url, token, verify_certificate, proxy)

        if demisto.command() == 'test-module':
            # This is the call made when pressing the integration Test button.
            result = test_module(client)
            return_results(result)

        # TODO: REMOVE the following dummy command case:
        elif demisto.command() == 'baseintegration-dummy':
            return_results(baseintegration_dummy_command(client, demisto.args()))
        # TODO: ADD command cases for the commands you will implement

    # Log exceptions and return errors
    except Exception as e:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute {demisto.command()} command.\nError:\n{str(e)}')


''' ENTRY POINT '''


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
