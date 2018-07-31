from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_anysign import api as django_anysign

from django_adobesign.client import AdobeSignClient


class SignatureType(django_anysign.SignatureType):
    root_url = models.CharField(
        _('AdobeSign root url'),
        max_length=255,
        default=settings.ADOBESIGN_ROOT_URL)

    application_id = models.CharField(
        _('AdobeSign application id'),
        max_length=100,
        help_text='https://www.adobe.io/apis/documentcloud/sign/docs/overview.'
                  'html',
        default='')

    application_secret = models.CharField(
        _('AdobeSign application secret'),
        max_length=100,
        help_text='https://www.adobe.io/apis/documentcloud/sign/docs/overview.'
                  'html',
        default='')

    access_token = models.CharField(
        _('AdobeSign token'),
        max_length=100,
        help_text='https://www.adobe.io/apis/documentcloud/sign/docs/overview.'
                  'html',
        default='')

    refresh_token = models.CharField(
        _('AdobeSign refresh token'),
        max_length=100,
        help_text='https://www.adobe.io/apis/documentcloud/sign/docs/overview.'
                  'html',
        default='')

    @property
    def signature_backend_options(self):
        return {
            'adobesign_client': AdobeSignClient(self.root_url,
                                                self.access_token)
        }


class Signature(django_anysign.SignatureFactory(SignatureType)):
    document = models.FileField(
        _('document'),
        upload_to='signatures',
    )
    document_title = models.CharField(
        _('title'),
        max_length=100,
    )
    state = models.CharField(
        _('AdobeSign state'),
        max_length=100,
        default='DEMO_NOT_YET_SIGN'
    )

    def signature_documents(self):
        """Return list of documents (file wrappers) to sign.

        Part of `django_anysign`'s API implementation.

        """
        # For compliance with other signature backends
        # Will be removed in major version
        self.document.bytes = self.document
        yield self.document

    def __str__(self):
        return self.document_title


class Signer(django_anysign.SignerFactory(Signature)):
    full_name = models.CharField(
        _('full name'),
        max_length=50,
        db_index=True,
    )
    email = models.EmailField(
        _('email'),
        db_index=True,
    )

    current_status = models.CharField(
        _('Internal signer status'),
        max_length=50,
        db_index=True,
        default='NOT_YET_VISIBLE'
    )
    adobe_id = models.CharField(
        _('Internal adobe id'),
        max_length=50,
        db_index=True,
        default=u''
    )
