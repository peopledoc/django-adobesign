from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_anysign import api as django_anysign


class SignatureType(django_anysign.SignatureType):
    root_url = models.CharField(
        _('Echosign root url'),
        max_length=255,
        default=settings.ECHOSIGN_ROOT_URL)

    application_id = models.CharField(
        _('Echosign application id'),
        max_length=100,
        help_text='https://www.adobe.io/apis/documentcloud/sign/docs/overview.'
                  'html',
        default='')

    application_secret = models.CharField(
        _('Echosign application secret'),
        max_length=100,
        help_text='https://www.adobe.io/apis/documentcloud/sign/docs/overview.'
                  'html',
        default='')

    access_token = models.CharField(
        _('Echosign token'),
        max_length=100,
        help_text='https://www.adobe.io/apis/documentcloud/sign/docs/overview.'
                  'html',
        default='')

    @property
    def signature_backend_options(self):
        return {
            'root_url': self.root_url,
            'token': self.access_token
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
        _('Echosign state'),
        max_length=100,
        help_text='https://secure.na1.echosign.com/public/docs/restapi/v6#ParticipantSetInfopost_agreements',
        default='IN_PROCESS'
    )

    def signature_documents(self):
        """Return list of documents (file wrappers) to sign.

        Part of `django_anysign`'s API implementation.

        """
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
