"""Custom exceptions."""
from django.utils import six

from requests.exceptions import RequestException


class AdobeSignException(Exception):
    """An error occurred with AdobeSign wrapper API."""

    @staticmethod
    def to_adobe_exception(exception):
        try:
            json_data = exception.response.json()
            message = '{} {} {}'.format(exception, json_data['code'],
                                        json_data['message'])
        except Exception:
            message = exception
        return AdobeSignException(message)

    def __str__(self):
        message = [repr(self)]
        if six.PY2:
            if isinstance(self.message, RequestException) \
                    and self.message.response:
                message.append('AdobeSign wrapper response: {}'.format(
                    self.message.response.body))
        else:
            if isinstance(self.args[0], RequestException) \
                    and self.args[0].response:
                message.append('AdobeSign wrapper response: {}'.format(
                    self.args[0].response.body))

        return '\n'.join(message)


class AdobeSignNoMoreSignerException(AdobeSignException):
    CODE_REASON = ('AGREEMENT_EXPIRED', 'AGREEMENT_NOT_SIGNABLE',
                   'AGREEMENT_NOT_VISIBLE')

    def __init__(self, e, reason):
        if reason not in AdobeSignNoMoreSignerException.CODE_REASON:
            reason = 'Unexpected reason: {}'.format(reason)
            self.reason = reason
            super(AdobeSignNoMoreSignerException, self).__init__(e)
