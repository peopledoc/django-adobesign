from adobesign.models import Signer
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView, \
    RedirectView
from django.views.generic.detail import SingleObjectMixin

from django_adobesign.backend import AdobeSignBackend
from django_adobesign.client import AdobeSignClient, AdobeSignOAuthSession
from django_adobesign.exceptions import AdobeSignException
from .models import Signature, SignatureType

ADOBESIGN_ACCOUNT_TYPE = 'self'


def get_adobesign_backend(signature_type, api_user=None, on_behalf_of_user=None):
    adobe_client = AdobeSignClient(root_url=signature_type.root_url,
                                   access_token=signature_type.access_token,
                                   api_user=api_user,
                                   on_behalf_of_user=on_behalf_of_user)
    return AdobeSignBackend(adobe_client)


class SettingsCreate(CreateView):
    model = SignatureType
    fields = ['root_url', 'application_id', 'application_secret']
    success_url = "/"


class SettingsUpdate(UpdateView):
    model = SignatureType
    fields = ['root_url', 'application_id', 'application_secret']
    success_url = "/"


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_agreements(self, signature_type):
        backend = get_adobesign_backend(signature_type)
        return backend.get_agreements(3)['userAgreementList']

    def get_signers_status(self, signature_id, signature_type):
        signers = []
        if signature_id:
            backend = get_adobesign_backend(signature_type)
            next_signer_mail, next_signer_url = backend.get_next_signer_url(
                signature_id)

            signers_data = backend.get_all_signers(signature_id)
            if 'participantSets' in signers_data:
                for signer_data in signers_data['participantSets']:
                    if 'name' in signer_data:
                        name = signer_data['name']
                    else:
                        name = signer_data['memberInfos'][0]['name']
                    email = signer_data['memberInfos'][0]['email']
                    url = next_signer_url if email == next_signer_mail else None
                    signers.append({'name': name,
                                    'status': signer_data['status'],
                                    'order': signer_data['order'],
                                    'mail': email,
                                    'url': url})
            signers.sort(key=lambda x: x['order'])
        return signers

    def get_latest_signature(self, signature_type):
        latest_signatures = []
        for signature in Signature.objects.all().order_by('-pk'):
            latest_signatures.append({
                'pk': signature.pk,
                'document_title': signature.document_title,
                'signature_backend_id': signature.signature_backend_id,
                'signers': self.get_signers_status(
                    signature.signature_backend_id, signature_type),
            })
        return latest_signatures

    def get_context_data(self, **kwargs):
        data = super(HomeView, self).get_context_data(**kwargs)
        signature_type = SignatureType.objects.last()
        if signature_type:
            data['signature_type'] = signature_type
            data['agreements'] = []
            data['latest_signatures'] = []

            if signature_type.access_token:
                try:
                    data['agreements'] = self.get_agreements(signature_type)
                except AdobeSignException as e:
                    data['agreements_list_error'] = e
                try:
                    data['latest_signatures'] = self.get_latest_signature(
                        signature_type)
                except AdobeSignException as e:
                    print(e)

        return data


class TokenView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        code = self.request.GET.get('code')
        signature_type = SignatureType.objects.last()
        redirect_uri = self.request.build_absolute_uri(reverse('token'))
        adobesign_oauth_client = AdobeSignOAuthSession(
            redirect_uri=redirect_uri,
            application_id=signature_type.application_id,
            account_type=ADOBESIGN_ACCOUNT_TYPE)
        # Redirect user to AdobeSign authorization
        if not code:
            return adobesign_oauth_client.get_authorization_url(
                signature_type.root_url)
        # Create token
        token_response = adobesign_oauth_client.create_token(
            code, signature_type.application_secret)
        signature_type.access_token = token_response.get('access_token')
        signature_type.save()
        return reverse('home')


class CreateSignatureView(CreateView):
    model = Signature
    fields = ['document', 'document_title']
    success_url = reverse_lazy('signer')

    def get_form_kwargs(self):
        self.object = Signature(
            signature_type=SignatureType.objects.last())
        return super(CreateSignatureView, self).get_form_kwargs()


class CreateSigner(CreateView):
    model = Signer
    fields = ['signing_order', 'full_name', 'email']
    success_url = reverse_lazy('home')

    def get_initial(self):
        return {'signing_order': 1}

    def form_valid(self, form):
        if 'saveadd' in self.get_form().data:
            self.success_url = reverse('signer')
        return super(CreateSigner, self).form_valid(form)

    def get_form_kwargs(self):
        self.object = Signer(signature=Signature.objects.last())
        return super(CreateSigner, self).get_form_kwargs()


class Sign(SingleObjectMixin, RedirectView):
    model = Signature

    def get_redirect_url(self, *args, **kwargs):
        signature = self.get_object()
        signature_type = signature.signature_type
        backend = get_adobesign_backend(signature_type)
        backend.create_signature(
            signature=signature,
            post_sign_redirect_url=self.request.build_absolute_uri(
                reverse('home')))
        return reverse('home')
