from django_anysign import api as django_anysign


class EchoSignBackend(django_anysign.SignatureBackend):
    def __init__(self, echosign_client, name='EchoSign', code='echosign',
                 url_namespace='anysign'):
        """Setup.

        Additional keyword arguments are passed to
        :class:`~django_echosign.client.EchoSignclient` constructor, in order
        to setup :attr:`echosign client`.

        """
        super(EchoSignBackend, self).__init__(
            name=name,
            code=code,
            url_namespace=url_namespace,
        )
        self.echosign_client = echosign_client

    def get_echosign_participants(self, signature):
        """Return list of EchoSign's Signers for Signature instance.

        Default implementation reads name and email from database.

        """
        jsonified_signers = []
        signers = signature.signers.all().order_by('signing_order')
        for position, signer in enumerate(signers, start=1):
            signer = self.echosign_client.jsonify_participants(
                name=signer.full_name,
                email=signer.email,
                order=position
            )
            jsonified_signers.append(signer)
        return jsonified_signers

    def create_signature(self, signature, **extra_data):
        """Register ``signature`` in EchoSign service, return updated object.
        This method calls ``save()`` on ``signature`` and ``signer``.

        """
        document = next(signature.signature_documents())

        result = self.echosign_client.create_signature(
            document=document,
            name=signature.document_title,
            participants=self.get_echosign_participants(signature),
            state=signature.state,
            extra_data=extra_data)

        # Update signature instance with record_id
        signature.signature_backend_id = result['id']
        signature.save()

        return signature

    def get_agreements(self, page_size=20, cursor=None, **extra_params):
        """
            Return all agreements associated to the given access token
        """
        return self.echosign_client.get_agreements(page_size, cursor,
                                                   **extra_params)

# LE DROit de créer un signature avec son token ?
