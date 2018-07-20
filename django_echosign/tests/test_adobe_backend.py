import pytest
from django.core.files import File
from django.db.models import FileField
from echosign.models import Signer, Signature, SignatureType

from django_echosign.backend import EchoSignBackend
from django_echosign.client import EchoSignClient


@pytest.fixture()
def adobe_sign_backend():
    adobe_sign_client = EchoSignClient(root_url='http://fake',
                                       access_token='ThisIsAToken')
    return EchoSignBackend(adobe_sign_client)


@pytest.fixture()
def minimal_signature(mocker):
    signature_type = SignatureType()
    signature_type.save()
    signature = Signature(signature_type=signature_type)
    signature.document = mocker.Mock(FileField)
    signature.document.file = mocker.Mock(File)
    signature.document.file.name = '/tmp/uploaded_file.pdf'
    signature.document._committed = True
    signature.save()
    return signature


@pytest.mark.django_db
def test_get_echosign_participants_in_right_order(minimal_signature,
                                                  adobe_sign_backend):
    signer1 = Signer(full_name='Poney poney', email='poney@plop.com',
                     signing_order=1)
    signer2 = Signer(full_name='Pouet pouet', email='pouet@plop.com',
                     signing_order=2)

    signer2.signature = minimal_signature
    signer1.signature = minimal_signature

    signer2.save()
    signer1.save()
    adobe_sign_signers = adobe_sign_backend.get_echosign_participants(
        minimal_signature)

    assert len(adobe_sign_signers) == 2

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
    assert adobe_sign_signers[0] == expected_signer1
    assert adobe_sign_signers[1] == expected_signer2


@pytest.mark.django_db
def test_create_signature(mocker, minimal_signature, adobe_sign_backend):
    mocker.patch.object(EchoSignClient, 'upload_document',
                        return_value={'transientDocumentId': 'doc_id'})
    mocker.patch.object(EchoSignClient, 'post_agreement',
                        return_value={'id': 'test_agreement_id'})

    assert minimal_signature.signature_backend_id == u''

    adobe_sign_backend.create_signature(minimal_signature)
    assert minimal_signature.signature_backend_id == 'test_agreement_id'
