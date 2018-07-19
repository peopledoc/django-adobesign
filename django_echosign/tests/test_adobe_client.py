import pytest

from django_echosign.client import EchoSignOAuthSession, \
    ADOBE_OAUTH_TOKEN_URL


@pytest.fixture()
def adobe_oauth_session():
    return EchoSignOAuthSession(application_id='na',
                                redirect_uri='na',
                                account_type='na')


def test_oauth_get_authorization_url(adobe_oauth_session):
    expected_root_url = 'https://toto'
    authorization_url = adobe_oauth_session.get_authorization_url(
        expected_root_url)

    assert authorization_url.startswith('https://toto/public/oauth')


def test_oauth_get_scopes():
    scopes = EchoSignOAuthSession.get_scopes(account_type='account')

    assert 'user_login:account' in scopes
    assert 'agreement_send:account' in scopes
    assert 'agreement_read:account' in scopes
    assert 'agreement_write:account' in scopes


def test_oauth_create(mocker, adobe_oauth_session):
    mocker.patch.object(adobe_oauth_session.oauth_session, 'fetch_token')
    adobe_oauth_session.create_token('code_test', 'appli_secret_test')
    mocked_function = adobe_oauth_session.oauth_session.fetch_token
    mocked_function.assert_called_with(ADOBE_OAUTH_TOKEN_URL,
                                       code='code_test',
                                       client_secret='appli_secret_test',
                                       authorization_response='/')
