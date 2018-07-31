"""Custom exceptions."""


def get_adobe_exception(exception):
    status_code = exception.response.status_code
    try:
        json_data = exception.response.json()
        reason = json_data['code']
        content = json_data['message']
        if AdobeSignNoMoreSignerException.is_no_more_signer(status_code,
                                                            reason):
            return AdobeSignNoMoreSignerException(content, reason,
                                                  cause=exception)

        if AdobeSignInvalidAccessTokenException.is_invalid_token(
                status_code, reason):
            return AdobeSignInvalidAccessTokenException(content,
                                                        cause=exception)
        message = '{} {} {}'.format(exception, reason, content)
    except Exception:
        try:
            message = '{} {} {}'.format(exception,
                                        status_code,
                                        exception.response.body)
        except Exception:
            message = exception
    return AdobeSignException(message, cause=exception)


class AdobeSignException(Exception):
    """An error occurred with AdobeSign wrapper API."""

    def __init__(self, message, cause=None):
        super(AdobeSignException, self).__init__(message)
        self.__cause__ = cause


class AdobeSignNoMoreSignerException(AdobeSignException):
    CODE_REASON = ('AGREEMENT_EXPIRED', 'AGREEMENT_NOT_SIGNABLE',
                   'AGREEMENT_NOT_VISIBLE')

    def __init__(self, message, reason, cause=None):
        if reason not in AdobeSignNoMoreSignerException.CODE_REASON:
            reason = 'Unexpected reason: {}'.format(reason)
        self.reason = reason
        super(AdobeSignNoMoreSignerException, self).__init__(message, cause)

    @staticmethod
    def is_no_more_signer(status_code, reason):
        return status_code == 404 and \
               reason in AdobeSignNoMoreSignerException.CODE_REASON


class AdobeSignInvalidAccessTokenException(AdobeSignException):
    def __init__(self, message, cause=None):
        super(AdobeSignInvalidAccessTokenException, self).__init__(message,
                                                                   cause)

    @staticmethod
    def is_invalid_token(status_code, reason):
        return 'INVALID_ACCESS_TOKEN' in reason
