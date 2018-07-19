import pytest
from django.core.files import File
from django.db.models import FileField
from echosign.models import Signer, Signature, SignatureType
from mock import Mock, patch
from requests import Response

from django_echosign.backend import EchoSignBackend
from django_echosign.client import EchoSignClient


def get_echosign_backend():
    echosign_client = EchoSignClient(root_url='http://fake',
                                     access_token='ThisIsAToken')
    return EchoSignBackend(echosign_client)


def get_minimal_signature():
    signature_type = SignatureType()
    signature_type.save()
    signature = Signature(signature_type=signature_type)
    signature.document = Mock(FileField)
    signature.document.file = Mock(File)
    signature.document.file.name = '/tmp/uploaded_file.pdf'
    signature.document._committed = True
    signature.save()
    return signature


@pytest.mark.django_db
def test_get_echosign_participants_in_right_order():
    signer1 = Signer(full_name='Poney poney', email='poney@plop.com',
                     signing_order=1)
    signer2 = Signer(full_name='Pouet pouet', email='pouet@plop.com',
                     signing_order=2)
    signature = get_minimal_signature()
    signer2.signature = signature
    signer1.signature = signature
    signer2.save()
    signer1.save()

    backend = get_echosign_backend()
    echosign_signers = backend.get_echosign_participants(signature)

    assert len(echosign_signers) == 2

    expected_signer1 = {
        'name': 'Poney poney',
        'memberInfos': [
            {'email': 'poney@plop.com'}],
        'order': 1,
        'role': 'SIGNER'
    }
    expected_signer2 = {
        'name': 'Pouet pouet',
        'memberInfos': [
            {'email': 'pouet@plop.com'}],
        'order': 2,
        'role': 'SIGNER'
    }
    assert echosign_signers[0] == expected_signer1
    assert echosign_signers[1] == expected_signer2


def mock_request_create_signature(url, headers, files=None, data=None,
                                  json=None):
    response = Mock(spec=Response)
    response.status_code = 400
    if url.strip('/').endswith('transientDocuments'):
        response.json.return_value = {'transientDocumentId': 'test_upload_id'}
        response.status_code = 200
    elif url.strip('/').endswith('agreements'):
        response.json.return_value = {'id': 'test_agreement_id'}
        response.status_code = 200

    return response


@pytest.mark.django_db
def test_create_signature(mocker):
    mocker.patch('requests.post', mock_request_create_signature)
    signature = get_minimal_signature()
    signature.save()

    assert signature.signature_backend_id == u''

    backend = get_echosign_backend()
    backend.create_signature(signature)
    assert signature.signature_backend_id == 'test_agreement_id'


def mock_request_create_signature_full_options(url, headers, files=None,
                                               data=None,
                                               json=None):
    response = Mock(spec=Response)
    response.status_code = 400
    expected_header = {
        'Authorization': 'Bearer TestAccessToken',
        'x-api-user': 'PoneyUser',
        'x-on-behalf-of-user': 'PoneyOnBehalfUser'
    }
    assert headers == expected_header
    if url.strip('/').endswith('transientDocuments'):
        expected_data = {
            'File-Name': 'uploaded_file.pdf',
            'Mime-Type': 'application/pdf'}
        assert data == expected_data
        response.json.return_value = {'transientDocumentId': 'test_upload_id'}
        response.status_code = 200
    elif url.strip('/').endswith('agreements'):
        expected_json = {
            'fileInfos': [{
                'transientDocumentId': 'test_upload_id'
            }],
            'name': 'SignatureTitle',
            'participantSetsInfo': [{
                'name': 'Son Goku',
                'memberInfos': [
                    {'email': 'songoku@gmail.com'}],
                'order': 1,
                'role': 'SIGNER'
            }],
            'signatureType': 'ESIGN',
            'state': 'AUTHORING',
            'postSignOption': {
                "redirectDelay": 12,
                "redirectUrl": "https://TestRedirectUrl"
            },
            'poney': 'extra_value',
            'pouet': {'extra_extra': 'value'}
        }
        assert json == expected_json
        response.json.return_value = {'id': 'test_agreement_id'}
        response.status_code = 200

    return response


@pytest.mark.django_db
@patch('requests.post',
       Mock(side_effect=mock_request_create_signature_full_options))
def test_create_signature_full_options():
    # initialize signature
    signature_type = SignatureType()
    signature_type.access_token = 'TestAccessToken'
    signature_type.root_url = 'https://TestAdobe'
    signature_type.application_id = 'TestApplicationID'
    signature_type.application_secret = 'TestApplicationSecret'
    signature_type.signature_backend_code = 'TestSignatureBackendCode'
    signature_type.save()
    signature = Signature(signature_type=signature_type)
    signature.document_title = 'SignatureTitle'
    signature.state = 'AUTHORING'
    signature.document = Mock(FileField)
    signature.document.file = Mock(File)
    signature.document.file.name = '/tmp/uploaded_file.pdf'
    signature.document._committed = True

    signature.save()

    signer1 = Signer(full_name='Son Goku', email='songoku@gmail.com',
                     signing_order=1, signature=signature)
    signer1.save()
    # TODO redundant information url_root and access_token are hold by the
    # signature type and also given directly to the client
    echosign_client = EchoSignClient(root_url=signature_type.root_url,
                                     access_token=signature_type.access_token,
                                     api_user='PoneyUser',
                                     on_behalf_of_user='PoneyOnBehalfUser')
    backend = EchoSignBackend(echosign_client)
    signature = backend.create_signature(signature,
                                         post_sign_redirect_delay=12,
                                         post_sign_redirect_url='https://TestRedirectUrl',
                                         poney='extra_value',
                                         pouet={'extra_extra': 'value'})
    assert signature.signature_backend_id == 'test_agreement_id'
