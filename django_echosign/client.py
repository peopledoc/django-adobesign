from os import path
from os.path import join, basename

import requests
from requests import HTTPError
from requests_oauthlib import OAuth2Session

from django_echosign.exceptions import EchoSignException

ADOBE_OAUTH_TOKEN_URL = 'https://api.echosign.com/oauth/token'


class EchoSignOAuthSession(object):
    def __init__(self, application_id, redirect_uri, account_type, state=None):
        self.oauth_session = OAuth2Session(
            client_id=application_id,
            redirect_uri=redirect_uri,
            scope=self.get_scopes(account_type),
            state=state)

    def get_authorization_url(self, root_url):
        url = join(root_url, 'public/oauth')
        authorization_url, state = self.oauth_session.authorization_url(url)
        return authorization_url

    @staticmethod
    def get_scopes(account_type):
        return [scope.format(account_type) for scope in (
            'user_login:{}',
            'agreement_send:{}',
            'agreement_read:{}',
            'agreement_write:{}')]

    def create_token(self, code, application_secret):
        response = self.oauth_session.fetch_token(
            ADOBE_OAUTH_TOKEN_URL,
            code=code,
            client_secret=application_secret,
            authorization_response='/')

        return response


class EchoSignClient(object):
    '''
    Echosign client use v6 api.
    See https://secure.na1.echosign.com/public/docs/restapi/v6
    '''

    def __init__(self, root_url, access_token, api_user=None,
                 on_behalf_of_user=None):
        self.root_url = root_url.strip('/')
        self.access_token = access_token
        self.on_behalf_of_user = on_behalf_of_user
        self.api_user = api_user

    def build_url(self, urlpath):
        return path.join(self.root_url, 'api/rest/v6', urlpath)

    def get_headers(self):
        header = {'Authorization': 'Bearer {}'.format(self.access_token)}
        if self.api_user:
            header['x-api-user'] = self.api_user
        if self.on_behalf_of_user:
            header['x-on-behalf-of-user'] = self.on_behalf_of_user
        return header

    def upload_document(self, document):
        url = self.build_url(urlpath='transientDocuments')
        data = {
            'File-Name': basename(document.file.name),
            'Mime-Type': 'application/pdf'
        }
        try:
            response = requests.post(url,
                                     headers=self.get_headers(),
                                     files={'File': document},
                                     data=data)
            response.raise_for_status()
        except (requests.exceptions.RequestException, HTTPError) as e:
            raise EchoSignException(e)

        return response.json()

    def jsonify_participant(self, name, email, order):
        return {
            'name': name,
            'memberInfos': [
                {'email': email}],
            'order': order,
            'role': 'SIGNER'
        }

    def post_agreement(self, transient_document_id, name, participants,
                       post_sign_redirect_url, post_sign_redirect_delay,
                       state='IN_PROCESS', **extra_data):
        '''
        Create signature with only one document

        https://secure.na1.echosign.com/public/docs/restapi/v6#!/agreements/createAgreement

        This is a primary endpoint which is used to create a new agreement.
        An agreement can be created using transientDocument, libraryDocument
        or a URL. You can create an agreement in one of the 3 mentioned
        states:
        a) DRAFT - to incrementally build the agreement before
        sending out,
        b) AUTHORING - to add/edit form fields in the agreement,
        c) IN_PROCESS - to immediately send the agreement.

        :param post_sign_redirect_delay: The delay (in seconds) before the user
        is taken to the success page. If this value is greater than 0, the user
        will first see the standard Adobe Sign success message, and then after
        a delay will be redirected to your success page,
        :param post_sign_redirect_url: A publicly accessible url to which the
        user will be sent after successfully completing the signing process
        :param document: file wrapper object
        :param name: name of document
        :param participants:  A list of one or more participant set.
        A participant set may have one or more participant.
        If any member of the participant set takes the action that has been
        assigned to the set(Sign/Approve/Acknowledge etc ), the action is
        considered as the action taken by whole participation set.
        For regular (non-MegaSign) documents, there is no limit on the number
        of electronic signatures in a single document. Written signatures are
        limited to four per document,
        :param extra_data: extra data to pass (see echosign documentation)
        '''

        # Send doc for signature
        url = self.build_url(urlpath='agreements')

        data = {
            'fileInfos': [{
                'transientDocumentId': transient_document_id
            }],
            'name': name,
            'participantSetsInfo': participants,
            'signatureType': 'ESIGN',
            'state': state
        }
        if post_sign_redirect_url:
            data['postSignOption'] = {
                "redirectDelay": post_sign_redirect_delay,
                "redirectUrl": post_sign_redirect_url
            }

        data.update(extra_data)

        try:
            response = requests.post(url,
                                     headers=self.get_headers(),
                                     json=data)
            response.raise_for_status()
        except (requests.exceptions.RequestException, HTTPError) as e:
            try:
                json_data = e.response.json()
                message = '{} {} {}'.format(e, json_data['code'],
                                            json_data['message'])
            except Exception:
                message = e
            raise EchoSignException(message)
        return response.json()

    def get_agreements(self, page_size, cursor=None, **extra_params):
        path_url = 'agreements'
        params = {'pageSize': page_size}
        if cursor:
            params['cursor'] = cursor
        params.update(extra_params)
        url = self.build_url(path_url)
        try:
            response = requests.get(url, headers=self.get_headers(),
                                    params=params)
            response.raise_for_status()
        except(requests.exceptions.RequestException, HTTPError) as e:
            raise EchoSignException(e)
        return response.json()
