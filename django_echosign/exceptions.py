"""Custom exceptions."""
from django.utils import six

from requests.exceptions import RequestException


class EchoSignException(Exception):
    """An error occurred with EchoSign wrapper API."""

    def __str__(self):
        message = [repr(self)]
        if six.PY2:
            if isinstance(self.message, RequestException) \
                    and self.message.response:
                message.append('EchoSign wrapper response: {}'.format(
                    self.message.response.body))
        else:
            if isinstance(self.args[0], RequestException) \
                    and self.args[0].response:
                message.append('EchoSign wrapper response: {}'.format(
                    self.args[0].response.body))

        return '\n'.join(message)
