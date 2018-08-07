from django_adobesign.backend import AdobeSignBackend


class DemoAdobeSignBackend(AdobeSignBackend):

    def update_signer_status(self, signer, status):
        signer.current_status = status
        signer.save(update_fields=['current_status'])
