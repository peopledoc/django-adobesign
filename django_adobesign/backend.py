from django_anysign import api as django_anysign


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
                         post_sign_redirect_delay=0,
                         send_mail=True, **extra_data):
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
            post_sign_redirect_url=post_sign_redirect_url,
            post_sign_redirect_delay=post_sign_redirect_delay,
            send_mail=send_mail,
            **extra_data)

        # Update signature instance with record_id
        signature.signature_backend_id = result['id']
        signature.save(update_fields=['signature_backend_id'])

        # Update signers instance with external id
        self.map_adobe_signer_to_signer(signature)
        return signature

    def update_signer_status(self, signer, status):
        raise NotImplementedError()

    def map_adobe_signer_to_signer(self, signature):
        # Can raise a Signer.DoesNotExist
        for adobe_signer in self.get_all_signers(
                signature.signature_backend_id).get('participantSets', []):
            # We only have 1 signer by turn
            email = adobe_signer['memberInfos'][0]['email'].lower()
            signer = signature.signers.get(signing_order=adobe_signer['order'],
                                           email=email)
            signer.signature_backend_id = adobe_signer['id']
            signer.save(update_fields=['signature_backend_id'])
            self.update_signer_status(signer, adobe_signer['status'])

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
        return agreements or {'userAgreementList': [], 'page': {}}

    def get_next_signers(self, agreement_id):
        """ Return the next signer list."""
        members = self.adobesign_client. \
            get_members(agreement_id, include_next_participant_set=True)
        return members.get('nextParticipantSets', [])

    def get_next_signer_urls(self, agreement_id):
        """
            Return an array of urls for current signer set
        """
        return self.adobesign_client.get_signing_url(agreement_id)

    def get_next_signer_url(self, agreement_id):
        """
            Return the first next signer url and mail if exists
        """
        next_signers_url = self.get_next_signer_urls(agreement_id)
        if 'signingUrlSetInfos' in next_signers_url:
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

    def get_signer(self, argeement_id, signer_id):
        return self.adobesign_client.get_signer(argeement_id, signer_id)

    def get_signer_status(self, argeement_id, signer_id):
        signer = self.get_signer(argeement_id, signer_id)
        return signer.get('status')

    def is_last_signer(self, signer):
        """Return True if ``signer`` is the last signer for the signature
        request.
        """
        return not signer.signature.signers.filter(
            signing_order__gt=signer.signing_order).exists()

    def get_documents(self, agreement_id):
        documents_info = self.adobesign_client.get_documents(agreement_id)
        for doc_info in documents_info.get('documents', []):
            yield self.adobesign_client.get_document(agreement_id,
                                                     doc_info['id'])

    def get_refuse_comment(self, agreement_id):
        """
        Return the refuse comment from agreement
        """
        events = self.adobesign_client.get_events(agreement_id)
        for event in events.get('events'):
            if event.get('type') == "REJECTED":
                # comment is mandatory
                return event["comment"]
