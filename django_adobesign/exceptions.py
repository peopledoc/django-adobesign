"""Custom exceptions."""


def get_adobe_exception(exception):
    reason = None
    try:
        status_code = exception.response.status_code
        json_data = exception.response.json()
        reason = json_data['code']
        content = json_data['message']
        if AdobeSignNoMoreSignerException.is_no_more_signer(status_code,
                                                            reason):
            return AdobeSignNoMoreSignerException(content,
                                                  cause=exception,
                                                  reason=reason)

        if AdobeSignInvalidAccessTokenException.is_invalid_token(
                status_code, reason):
            return AdobeSignInvalidAccessTokenException(content,
                                                        cause=exception,
                                                        reason=reason)
        if AdobeSignInvalidUserException.is_invalid_user(status_code, reason):
            return AdobeSignInvalidUserException(content,
                                                 cause=exception,
                                                 reason=reason)

        message = '{} {} {}'.format(exception, reason, content)
    except Exception:
        try:
            message = '{} {} {}'.format(exception,
                                        status_code,
                                        exception.response.body)
        except Exception:
            message = exception
    return AdobeSignException(message, cause=exception, reason=reason)


class AdobeSignException(Exception):
    """An error occurred with AdobeSign wrapper API."""

    def __init__(self, message, cause=None, reason=None):
        super(AdobeSignException, self).__init__(message)
        self.__cause__ = cause
        self.reason = reason


class AdobeSignNoMoreSignerException(AdobeSignException):
    CODE_REASON = ('AGREEMENT_EXPIRED', 'AGREEMENT_NOT_SIGNABLE',
                   'AGREEMENT_NOT_VISIBLE')

    @staticmethod
    def is_no_more_signer(status_code, reason):
        return status_code == 404 and \
               reason in AdobeSignNoMoreSignerException.CODE_REASON


class AdobeSignInvalidAccessTokenException(AdobeSignException):

    @staticmethod
    def is_invalid_token(status_code, reason):
        return status_code == 401 and 'INVALID_ACCESS_TOKEN' in reason


class AdobeSignInvalidUserException(AdobeSignException):

    @staticmethod
    def is_invalid_user(status_code, reason):
        return status_code == 401 and 'INVALID_USER' in reason
