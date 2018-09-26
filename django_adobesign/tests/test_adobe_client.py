import pytest
from requests import Response

from django_adobesign.client import AdobeSignOAuthSession, \
    ADOBE_OAUTH_TOKEN_URL, AdobeSignClient, ADOBE_OAUTH_REFRESH_TOKEN_URL
from django_adobesign.exceptions import AdobeSignException, \
    AdobeSignNoMoreSignerException, AdobeSignInvalidAccessTokenException, \
    AdobeSignInvalidUserException


@pytest.fixture()
def adobe_oauth_session():
    return AdobeSignOAuthSession(application_id='na',
                                 redirect_uri='na',
                                 account_type='na')


def test_oauth_get_authorization_url(adobe_oauth_session):
    expected_root_url = 'https://toto'
    authorization_url = adobe_oauth_session.get_authorization_url(
        expected_root_url)

    assert authorization_url.startswith('https://toto/public/oauth')


def test_oauth_get_scopes():
    scopes = AdobeSignOAuthSession.get_scopes(account_type='account')

    assert 'user_login:account' in scopes
    assert 'agreement_send:account' in scopes
    assert 'agreement_read:account' in scopes
    assert 'agreement_write:account' in scopes


def test_oauth_create(mocker, adobe_oauth_session):
    mocked_function = mocker.patch.object(adobe_oauth_session.oauth_session,
                                          'fetch_token')
    adobe_oauth_session.create_token('code_test', 'appli_secret_test')

    assert mocked_function.mock_calls == [mocker.call(
        ADOBE_OAUTH_TOKEN_URL,
        code='code_test',
        client_secret='appli_secret_test',
        authorization_response='/')]


def test_oauth_refresh_token(mocker):
    mocked_function = mocker.patch(
        "requests_oauthlib.OAuth2Session.refresh_token")
    AdobeSignOAuthSession.refresh_token('refresh_token_test', 'appli_id_test',
                                        'appli_secret_test')
    assert mocked_function.mock_calls == [mocker.call(
        ADOBE_OAUTH_REFRESH_TOKEN_URL,
        refresh_token='refresh_token_test',
        client_id='appli_id_test',
        client_secret='appli_secret_test',
        authorization_response='/')]


@pytest.fixture()
def adobe_sign_client():
    return AdobeSignClient(root_url='http://test',
                           access_token='TestToken',
                           api_user='test_api_user',
                           on_behalf_of_user='test_on_behalf_user')


@pytest.fixture()
def expected_headers():
    return {
        'Authorization': 'Bearer TestToken',
        'x-api-user': 'test_api_user',
        'x-on-behalf-of-user': 'test_on_behalf_user'
    }


@pytest.fixture()
def expected_participant():
    return {
        'name': 'Poney poney',
        'memberInfos': [
            {'email': 'poney@plop.com'}],
        'order': 1,
        'role': 'SIGNER'
    }


def test_adobe_api_version_should_be_v6(adobe_sign_client):
    assert adobe_sign_client.build_url(
        'mytest/resource') == 'http://test/api/rest/v6/mytest/resource'


def test_get_full_header(adobe_sign_client, expected_headers):
    headers = adobe_sign_client.get_headers()
    assert headers == expected_headers


def test_should_get_jsonified_participant(adobe_sign_client,
                                          expected_participant):
    jsonified_participant = adobe_sign_client.jsonify_participant(
        name='Poney poney',
        email='poney@plop.com',
        order=1)
    assert jsonified_participant == expected_participant


@pytest.fixture()
def test_document(mocker):
    document = mocker.Mock()
    document.name = '/tmp/test_document.pdf'
    document.bytes = b''
    return document


def test_call_upload_document(mocker, adobe_sign_client, expected_headers,
                              test_document):
    mocked_post = mocker.patch('requests.post')
    adobe_sign_client.upload_document(test_document)

    expected_data = {
        'File-Name': 'test_document.pdf',
        'Mime-Type': 'application/pdf'}
    mandatory_parameters = mocked_post.call_args[0]
    assert mandatory_parameters == (
        'http://test/api/rest/v6/transientDocuments',)

    kwargs_params = mocked_post.call_args[1]
    assert kwargs_params == {'headers': expected_headers,
                             'files': {'File': test_document.bytes},
                             'data': expected_data}


@pytest.fixture()
def response_with_error():
    def __get_response(error_code):
        response_with_client_error = Response()
        response_with_client_error.status_code = error_code
        return response_with_client_error

    return __get_response


@pytest.mark.parametrize('error_code', (404, 500))
def test_document_upload_client_or_server_error(error_code, mocker,
                                                response_with_error,
                                                adobe_sign_client,
                                                test_document):
    mocker.patch('requests.post', return_value=response_with_error(error_code))
    with pytest.raises(AdobeSignException):
        adobe_sign_client.upload_document(test_document)


def test_should_create_signature(mocker, adobe_sign_client,
                                 expected_participant, expected_headers):
    mocked_post = mocker.patch('requests.post')
    participants = [expected_participant]
    adobe_sign_client \
        .post_agreement(transient_document_id='test_doc_id',
                        name='test_name',
                        participants=participants,
                        post_sign_redirect_url='http://post/sign/red/url',
                        post_sign_redirect_delay=12,
                        state='AUTHORING',
                        send_mail=False,
                        extra_param_str='plop',
                        extra_param_dict={'poney': 42},
                        extra_param_list=[1, 2, 3])
    expected_json = {
        'fileInfos': [{
            'transientDocumentId': 'test_doc_id'
        }],
        'name': 'test_name',
        'participantSetsInfo': [expected_participant],
        'signatureType': 'ESIGN',
        'state': 'AUTHORING',
        'postSignOption': {
            "redirectDelay": 12,
            "redirectUrl": 'http://post/sign/red/url'
        },
        'emailOption': {'sendOptions': {'completionEmails': 'NONE',
                                        'inFlightEmails': 'NONE',
                                        'initEmails': 'NONE'}
                        },
        'extra_param_str': 'plop',
        'extra_param_dict': {'poney': 42},
        'extra_param_list': [1, 2, 3]
    }
    mandatory_parameters = mocked_post.call_args[0]
    assert mandatory_parameters == ('http://test/api/rest/v6/agreements',)

    kwargs_params = mocked_post.call_args[1]
    assert kwargs_params == {'headers': expected_headers,
                             'json': expected_json}


@pytest.mark.parametrize('error_code', (404, 500))
def test_post_agreement_client_or_server_error(error_code, mocker,
                                               response_with_error,
                                               adobe_sign_client):
    expected_json_reply_error = {'code': str(error_code),
                                 'message': 'error raison'}
    response = response_with_error(error_code)
    mocker.patch.object(response, 'json',
                        return_value=expected_json_reply_error)
    mocker.patch('requests.post', return_value=response)
    with pytest.raises(AdobeSignException) as e:
        adobe_sign_client.post_agreement('doc id', 'name', [], '-', '-', False)
    assert expected_json_reply_error['code'] in str(e)
    assert expected_json_reply_error['message'] in str(e)


def test_get_agreements(mocker, adobe_sign_client, expected_headers):
    mocked_get = mocker.patch('requests.get')
    adobe_sign_client.get_agreements(page_size=12,
                                     cursor=44,
                                     extra_param_test={'test': 1})
    expected_params = {'pageSize': 12,
                       'cursor': 44,
                       'extra_param_test': {'test': 1}}
    mandatory_parameters = mocked_get.call_args[0]
    assert mandatory_parameters == ('http://test/api/rest/v6/agreements',)

    kwargs_params = mocked_get.call_args[1]
    assert kwargs_params == {'headers': expected_headers,
                             'params': expected_params}


@pytest.mark.parametrize('error_code', (404, 500))
def test_agreement_client_or_server_error(error_code, mocker,
                                          response_with_error,
                                          adobe_sign_client):
    mocker.patch('requests.get', return_value=response_with_error(error_code))
    with pytest.raises(AdobeSignException):
        adobe_sign_client.get_agreements(11)


@pytest.mark.parametrize('include_next_participant_set', (True, False))
def test_get_members(include_next_participant_set, mocker, adobe_sign_client,
                     expected_headers):
    mocked_get = mocker.patch('requests.get')
    adobe_sign_client.get_members('test_agreement_id',
                                  include_next_participant_set)

    mandatory_parameters = mocked_get.call_args[0]
    assert mandatory_parameters == (
        'http://test/api/rest/v6/agreements/test_agreement_id/members',)

    kwargs_params = mocked_get.call_args[1]
    assert kwargs_params == {
        'params': {'includeNextParticipantSet': include_next_participant_set},
        'headers': expected_headers}


@pytest.mark.parametrize('error_code', (404, 500))
def test_get_members_client_or_server_error(error_code, mocker,
                                            response_with_error,
                                            adobe_sign_client):
    mocker.patch('requests.get', return_value=response_with_error(error_code))
    with pytest.raises(AdobeSignException):
        adobe_sign_client.get_members('id', True)


def test_get_signing_url(mocker, adobe_sign_client, expected_headers):
    mocked_get = mocker.patch('requests.get')
    adobe_sign_client.get_signing_url('test_agreement_id')

    mandatory_parameters = mocked_get.call_args[0]
    assert mandatory_parameters == (
        'http://test/api/rest/v6/agreements/test_agreement_id/signingUrls',)

    kwargs_parameters = mocked_get.call_args[1]
    assert kwargs_parameters == {'headers': expected_headers}


@pytest.mark.parametrize('error_code', (404, 500))
def test_get_signing_url_client_or_server_error(error_code, mocker,
                                                response_with_error,
                                                adobe_sign_client):
    mocker.patch('requests.get', return_value=response_with_error(error_code))
    with pytest.raises(AdobeSignException):
        adobe_sign_client.get_signing_url('id')


@pytest.mark.parametrize('code_reason', ('AGREEMENT_EXPIRED',
                                         'AGREEMENT_NOT_SIGNABLE',
                                         'AGREEMENT_NOT_VISIBLE'))
def test_get_signing_url_client_not_real_not_found_error(code_reason, mocker,
                                                         response_with_error,
                                                         adobe_sign_client):
    mocker.patch('requests.get', return_value=response_with_error(404))
    mocker.patch('requests.Response.json',
                 return_value={'code': code_reason, 'message': 'test'})
    with pytest.raises(AdobeSignNoMoreSignerException):
        adobe_sign_client.get_signing_url('id')


def test_get_signing_url_client_not_found_error(mocker,
                                                response_with_error,
                                                adobe_sign_client):
    mocker.patch('requests.get', return_value=response_with_error(404))
    mocker.patch('requests.Response.json',
                 return_value={'code': 'REAL_NOT_FOUND'})
    with pytest.raises(AdobeSignException) as excinfo:
        adobe_sign_client.get_signing_url('id')
    assert not excinfo.errisinstance(AdobeSignNoMoreSignerException)


def test_get_signer(mocker, adobe_sign_client, expected_headers):
    mocked_get = mocker.patch('requests.get')
    adobe_sign_client.get_signer('test_agreement_id', 'signer_id')

    mandatory_parameters = mocked_get.call_args[0]
    expected_url = 'http://test/api/rest/v6/agreements/test_agreement_id/' \
                   'members/participantSets/signer_id'
    assert mandatory_parameters == (expected_url,)

    kwargs_parameters = mocked_get.call_args[1]
    assert kwargs_parameters == {'headers': expected_headers}


@pytest.mark.parametrize('error_code', (404, 500))
def test_get_signer_client_or_server_error(error_code, mocker,
                                           response_with_error,
                                           adobe_sign_client):
    mocker.patch('requests.get', return_value=response_with_error(error_code))
    with pytest.raises(AdobeSignException):
        adobe_sign_client.get_signer('test_agreement_id', 'signer_id')


def test_get_documents(mocker, adobe_sign_client, expected_headers):
    mocked_get = mocker.patch('requests.get')
    adobe_sign_client.get_documents('test_agreement_id', test_data={'a': 2})

    mandatory_parameters = mocked_get.call_args[0]
    assert mandatory_parameters == ('http://test/api/rest/v6/agreements/'
                                    'test_agreement_id/documents',)

    kwargs_parameters = mocked_get.call_args[1]
    assert kwargs_parameters == {'headers': expected_headers,
                                 'data': {'test_data': {'a': 2}}}


@pytest.mark.parametrize('error_code', (404, 500))
def test_get_documents_client_or_server_error(error_code, mocker,
                                              response_with_error,
                                              adobe_sign_client):
    mocker.patch('requests.get', return_value=response_with_error(error_code))
    with pytest.raises(AdobeSignException):
        adobe_sign_client.get_documents('test_agreement_id')


def test_get_document(mocker, adobe_sign_client, expected_headers):
    mocked_get = mocker.patch('requests.get')
    adobe_sign_client.get_document('test_agreement_id', 'test_doc_id')

    mandatory_parameters = mocked_get.call_args[0]
    assert mandatory_parameters == ('http://test/api/rest/v6/agreements/'
                                    'test_agreement_id/documents/test_doc_id',)

    kwargs_parameters = mocked_get.call_args[1]
    assert kwargs_parameters == {'headers': expected_headers}


@pytest.mark.parametrize('error_code', (404, 500))
def test_get_document_client_or_server_error(error_code, mocker,
                                             response_with_error,
                                             adobe_sign_client):
    mocker.patch('requests.get', return_value=response_with_error(error_code))
    with pytest.raises(AdobeSignException):
        adobe_sign_client.get_document('test_agreement_id', 'test_doc_id')


def test_get_events(mocker, adobe_sign_client, expected_headers):
    mocked_get = mocker.patch('requests.get')
    adobe_sign_client.get_events('test_agreement_id')

    mandatory_parameters = mocked_get.call_args[0]
    assert mandatory_parameters == ('http://test/api/rest/v6/agreements/'
                                    'test_agreement_id/events',)

    kwargs_parameters = mocked_get.call_args[1]
    assert kwargs_parameters == {'headers': expected_headers}


@pytest.mark.parametrize('error_code', (404, 500))
def test_get_events_client_or_server_error(error_code, mocker,
                                           response_with_error,
                                           adobe_sign_client):
    mocker.patch('requests.get', return_value=response_with_error(error_code))
    with pytest.raises(AdobeSignException):
        adobe_sign_client.get_events('test_agreement_id')


def test_do_not_change_exception_if_not_invalid_token(mocker,
                                                      response_with_error,
                                                      adobe_sign_client):
    mocker.patch('requests.get', return_value=response_with_error(401))
    mocker.patch('requests.Response.json',
                 return_value={'code': 'other Reason',
                               'message': 'test'})
    with pytest.raises(AdobeSignException) as excinfo:
        adobe_sign_client.get_document('test_agreement_id', 'test_doc_id')
    assert not excinfo.errisinstance(AdobeSignInvalidAccessTokenException)


def test_raise_invalid_token_exception(mocker,
                                       response_with_error,
                                       adobe_sign_client):
    mocker.patch('requests.get', return_value=response_with_error(401))
    mocker.patch('requests.Response.json',
                 return_value={'code': 'INVALID_ACCESS_TOKEN',
                               'message': 'test'})
    with pytest.raises(AdobeSignInvalidAccessTokenException):
        adobe_sign_client.get_document('test_agreement_id', 'test_doc_id')


def test_raise_invalid_user_exception(mocker,
                                      response_with_error,
                                      adobe_sign_client):
    mocker.patch('requests.get', return_value=response_with_error(401))
    mocker.patch('requests.Response.json',
                 return_value={'code': 'INVALID_USER',
                               'message': 'test'})
    with pytest.raises(AdobeSignInvalidUserException):
        adobe_sign_client.get_document('test_agreement_id', 'test_doc_id')
