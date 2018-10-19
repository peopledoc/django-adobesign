import pytest
from adobesign.models import Signer, Signature, SignatureType
from django.core.files import File
from django.db.models import FileField

from django_adobesign.backend import AdobeSignBackend
from django_adobesign.client import AdobeSignClient
from django_adobesign.exceptions import AdobeSignNoMoreSignerException


class AdobeSignBackendTest(AdobeSignBackend):

    def update_signer_status(self, signer, status):
        pass


@pytest.fixture()
def adobe_sign_backend():
    adobe_sign_client = AdobeSignClient(root_url='http://fake',
                                        access_token='ThisIsAToken')
    return AdobeSignBackendTest(adobe_sign_client)


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
def test_get_adobesign_participants_in_right_order(minimal_signature,
                                                   adobe_sign_backend):
    signer1 = Signer(full_name='Poney poney', email='poney@plop.com',
                     signing_order=1)
    signer2 = Signer(full_name='Pouet pouet', email='pouet@plop.com',
                     signing_order=2)

    signer2.signature = minimal_signature
    signer1.signature = minimal_signature

    signer2.save()
    signer1.save()
    adobe_sign_signers = adobe_sign_backend.get_adobesign_participants(
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
    mocker.patch.object(AdobeSignClient, 'upload_document',
                        return_value={'transientDocumentId': 'doc_id'})
    mocker.patch.object(AdobeSignClient, 'post_agreement',
                        return_value={'id': 'test_agreement_id'})
    mocker.patch.object(
        AdobeSignClient, 'get_members',
        return_value={
            'participantSets': [
                # Check email are case sensitive case (only side Adobe)
                {'memberInfos': [{'email': 'PoUeT@plop.com'}],
                 'id': 'fooid',
                 'status': 'NOT_YET_VISIBLE',
                 'order': 2},
                {'memberInfos': [{'email': 'poney@plop.com'}],
                 'id': 'barid',
                 'status': 'CANCELLED',
                 'order': 1}]})

    # Signers
    signer1 = Signer(full_name='Poney poney', email='poney@plop.com',
                     signing_order=1)
    signer2 = Signer(full_name='Pouet pouet', email='pouet@plop.com',
                     signing_order=2)
    signer2.signature = minimal_signature
    signer1.signature = minimal_signature
    signer2.save()
    signer1.save()

    assert signer1.signature_backend_id == ""
    assert signer2.signature_backend_id == ""

    assert minimal_signature.signature_backend_id == ""

    adobe_sign_backend.create_signature(minimal_signature)

    minimal_signature.refresh_from_db()
    assert minimal_signature.signature_backend_id == 'test_agreement_id'

    signer1.refresh_from_db()
    signer2.refresh_from_db()
    assert signer1.signature_backend_id == "barid"
    assert signer2.signature_backend_id == "fooid"


def test_get_next_signer_urls(mocker, adobe_sign_backend):
    mocker.patch.object(AdobeSignClient, 'get_signing_url',
                        side_effect=AdobeSignNoMoreSignerException(
                            'm', Exception('c')))
    with pytest.raises(AdobeSignNoMoreSignerException):
        adobe_sign_backend.get_next_signer_urls('12')


def test_get_next_signer_url(mocker, adobe_sign_backend):
    data = {'signingUrlSetInfos': [{
        'signingUrls': [{
            'email': 'pouet@truc.com',
            'esignUrl': 'url'},
            {'other': 'potential signer'}
        ]}
    ]}
    mocker.patch.object(AdobeSignClient, 'get_signing_url',
                        return_value=data)
    mail, url = adobe_sign_backend.get_next_signer_url('12')
    assert (mail, url) == ('pouet@truc.com', 'url')


@pytest.mark.django_db
def test_is_last_signer(adobe_sign_backend, minimal_signature):
    signer1 = Signer(full_name='A', email='a@b.c', signing_order=1)
    signer2 = Signer(full_name='B', email='d@e.f', signing_order=2)
    signer2.signature = minimal_signature
    signer1.signature = minimal_signature
    signer2.save()
    signer1.save()

    assert not adobe_sign_backend.is_last_signer(signer1)
    assert adobe_sign_backend.is_last_signer(signer2)


def test_get_refuse_comment(mocker, adobe_sign_backend):
    data = {
        "events": [
            {
                "type": "CREATED",
            },
            {
                "type": "ACTION_REQUESTED",
            },
            {
                "type": "REJECTED",
                "comment": "test comment message"
            }
        ]
    }
    mocker.patch.object(AdobeSignClient, 'get_events',
                        return_value=data)
    comment = adobe_sign_backend.get_refuse_comment('12')
    assert comment == "test comment message"
