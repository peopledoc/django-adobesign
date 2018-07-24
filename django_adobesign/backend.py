import logging

from django_anysign import api as django_anysign

from django_adobesign.exceptions import AdobeSignNoMoreSignerException


class AdobeSignBackend(django_anysign.SignatureBackend):
    def __init__(self, adobesign_client, name='AdobeSign', code='adobesign',
                 url_namespace='anysign'):
        """Setup.

        Additional keyword arguments are passed to
        :class:`~django_adobesign.client.AdobeSignCient` constructor, in order
        to setup :attr:`adobesign client`.

        """
        super(AdobeSignBackend, self).__init__(
            name=name,
            code=code,
            url_namespace=url_namespace,
        )
        self.adobesign_client = adobesign_client

    def get_adobesign_participants(self, signature):
        """Return list of AdobeSign's Signers for Signature instance.

        Default implementation reads name and email from database.

        """
        jsonified_signers = []
        signers = signature.signers.all().order_by('signing_order')
        for position, signer in enumerate(signers, start=1):
            signer = self.adobesign_client.jsonify_participant(
                name=signer.full_name,
                email=signer.email,
                order=position
            )
            jsonified_signers.append(signer)
        return jsonified_signers

    def create_signature(self, signature, post_sign_redirect_url=None,
                         post_sign_redirect_delay=0, **extra_data):
        """Register ``signature`` in AdobeSign service, return updated object.
        This method calls ``save()`` on ``signature`` and ``signer``.

        """
        document = next(signature.signature_documents())

        # Upload document
        response = self.adobesign_client.upload_document(document)
        transient_document_id = response.get('transientDocumentId')

        result = self.adobesign_client.post_agreement(
            transient_document_id=transient_document_id,
            name=str(signature),
            participants=self.get_adobesign_participants(signature),
            state=signature.state,
            post_sign_redirect_url=post_sign_redirect_url,
            post_sign_redirect_delay=post_sign_redirect_delay,
            **extra_data)

        # Update signature instance with record_id
        signature.signature_backend_id = result['id']
        signature.save()
        return signature

    def get_agreements(self, page_size=20, cursor=None, **extra_params):
        """
            Return all agreements associated to the given access token

            Be careful: reply structure is not the same if there is agreements
            or not

            case not empty: {
                            "page": {"nextCursor": "..."}
                            "userAgreementList": [ agreement1, ... ]
                            }
            case empty: []

            For compliance, in case of empty agreement list we artificially
            return the structure above
        """
        agreements = self.adobesign_client.get_agreements(page_size, cursor,
                                                          **extra_params)
        return agreements or {'userAgreementList': []}

    def get_next_signers(self, agreement_id):
        """ Return the next signer list."""
        members = self.adobesign_client. \
            get_members(agreement_id, include_next_participant_set=True)
        return members.get('nextParticipantSets', [])

    def get_next_signer_urls(self, agreement_id):
        """
            Return an array of urls for current signer set
        """
        try:
            return self.adobesign_client.get_signing_url(agreement_id)
        except AdobeSignNoMoreSignerException as e:
            logging.warning(e)
            return {'signingUrlSetInfos': []}

    def get_next_signer_url(self, agreement_id):
        """
            Return the first next signer url and mail if exists
        """
        next_signers_url = self.get_next_signer_urls(agreement_id)
        set_infos = next_signers_url['signingUrlSetInfos']
        if set_infos and set_infos[0]['signingUrls']:
            return set_infos[0]['signingUrls'][0]['email'], \
                   set_infos[0]['signingUrls'][0]['esignUrl']
        return None, None

    def get_all_signers(self, agreement_id):
        """
            Return the list of all signers info
        """
        return self.adobesign_client. \
            get_members(agreement_id, include_next_participant_set=False)
