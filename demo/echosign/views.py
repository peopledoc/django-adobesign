from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView, \
    RedirectView
from django.views.generic.detail import SingleObjectMixin
from echosign.models import Signer

from django_echosign.backend import EchoSignBackend
from django_echosign.client import EchoSignClient, EchoSignOAuthSession
from django_echosign.exceptions import EchoSignException
from .models import Signature, SignatureType

ECHOSIGN_ACCOUNT_TYPE = "self"


def get_echosign_backend(signature_type, api_user=None, on_behalf_of_user=None):
    echosign_client = EchoSignClient(root_url=signature_type.root_url,
                                     access_token=signature_type.access_token,
                                     api_user=api_user,
                                     on_behalf_of_user=on_behalf_of_user)
    return EchoSignBackend(echosign_client)


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
        backend = get_echosign_backend(signature_type)
        return backend.get_agreements(3)['userAgreementList']

    def get_context_data(self, **kwargs):
        data = super(HomeView, self).get_context_data(**kwargs)
        signature_type = SignatureType.objects.last()
        if signature_type:
            data['signature_type'] = signature_type
            data['latest_signatures'] = Signature.objects.all().order_by('-pk')
            data['agreements'] = []

            if signature_type.access_token:
                try:
                    data['agreements'] = self.get_agreements(signature_type)
                except EchoSignException as e:
                    data['agreements_list_error'] = e
        return data


class TokenView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        code = self.request.GET.get('code')
        signature_type = SignatureType.objects.last()
        redirect_uri = self.request.build_absolute_uri(reverse('token'))
        # TODO : signature has changed for EchoSignOAuthClient!
        echosign_oauth_client = EchoSignOAuthSession(
            redirect_uri=redirect_uri,
            application_id=signature_type.application_id,
            account_type=ECHOSIGN_ACCOUNT_TYPE)
        # Redirect user to Echosign authorization
        if not code:
            return echosign_oauth_client.get_authorization_url(
                signature_type.root_url)
        # Create token
        token_response = echosign_oauth_client.create_token(
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
        backend = get_echosign_backend(signature_type)
        backend.post_agreement(
            signature=signature,
            post_sign_redirect_url="https://localhost:8000/next")
        return reverse('home')


# TODO: finish this
def redirect_from_signature(request):
    from django.http import HttpResponse
    return HttpResponse("Yay", content_type="text/plain")
