from functools import wraps
from os import path
from os.path import join, basename

import requests
from requests import HTTPError
from requests_oauthlib import OAuth2Session

from django_adobesign.exceptions import get_adobe_exception

ADOBE_OAUTH_TOKEN_URL = 'https://api.echosign.com/oauth/token'
ADOBE_OAUTH_REFRESH_TOKEN_URL = 'https://api.echosign.com/oauth/refresh'


class AdobeSignOAuthSession(object):
    def __init__(self, application_id, redirect_uri, account_type, state=None):
        self.application_id = application_id
        self.oauth_session = OAuth2Session(
            client_id=self.application_id,
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

    @staticmethod
    def refresh_token(refresh_token, application_id, application_secret):
        oauth_session = OAuth2Session(client_id=application_id)
        response = oauth_session.refresh_token(
            ADOBE_OAUTH_REFRESH_TOKEN_URL,
            refresh_token=refresh_token,
            client_id=application_id,
            client_secret=application_secret,
            authorization_response="/")

        return response


def handle_adobe_exception(function):
    @wraps(function)
    def wrapper(*arg, **kwargs):
        try:
            return function(*arg, **kwargs)
        except (requests.exceptions.RequestException, HTTPError) as e:
            raise get_adobe_exception(e)

    return wrapper


class AdobeSignClient(object):
    '''
    AdobeSign client use v6 api.
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

    @handle_adobe_exception
    def upload_document(self, document):
        """
            Upload a document and get a transient document id
        """
        url = self.build_url(urlpath='transientDocuments')
        data = {
            'File-Name': basename(document.name),
            'Mime-Type': 'application/pdf'
        }

        response = requests.post(url,
                                 headers=self.get_headers(),
                                 files={'File': document.bytes},
                                 data=data)
        response.raise_for_status()
        return response.json()

    def jsonify_participant(self, name, email, order):
        return {
            'name': name,
            'memberInfos': [
                {'email': email}],
            'order': order,
            'role': 'SIGNER'
        }

    @handle_adobe_exception
    def post_agreement(self, transient_document_id, name, participants,
                       post_sign_redirect_url, post_sign_redirect_delay,
                       send_mail, state='IN_PROCESS', **extra_data):
        '''
        Create signature with only one document

        https://secure.na1.adobesign.com/public/docs/restapi/v6#!/agreements/createAgreement

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
        :param extra_data: extra data to pass (see adobesign documentation)
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
                'redirectDelay': post_sign_redirect_delay,
                'redirectUrl': post_sign_redirect_url
            }

        if not send_mail:
            data['emailOption'] = {
                'sendOptions': {
                    'completionEmails': 'NONE',
                    'inFlightEmails': 'NONE',
                    'initEmails': 'NONE'
                }
            }

        data.update(extra_data)
        response = requests.post(url,
                                 headers=self.get_headers(),
                                 json=data)
        response.raise_for_status()
        return response.json()

    @handle_adobe_exception
    def get_agreements(self, page_size, cursor=None, **extra_params):
        """
        Return the list of agreements with pagination
        """
        path_url = 'agreements'
        params = {'pageSize': page_size}
        if cursor:
            params['cursor'] = cursor
        params.update(extra_params)
        url = self.build_url(path_url)
        response = requests.get(url, headers=self.get_headers(),
                                params=params)
        response.raise_for_status()
        return response.json()

    @handle_adobe_exception
    def get_members(self, agreement_id, include_next_participant_set):
        """
        Return members of a given agreement id
        :param include_next_participant_set: add to the response the set of
        next participants
        """
        url = self.build_url('agreements/{}/members'.format(agreement_id))
        params = {
            'includeNextParticipantSet': include_next_participant_set}
        response = requests.get(url,
                                params=params,
                                headers=self.get_headers())
        response.raise_for_status()
        return response.json()

    @handle_adobe_exception
    def get_signing_url(self, agreement_id):
        """
        Return the next signing url for the agreement
        corresponding to the agreement_id.
        """
        url = self.build_url('agreements/{}/signingUrls'.format(agreement_id))
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json()

    @handle_adobe_exception
    def get_signer(self, agreement_id, signer_id):
        """
        Return the signer with the given signer_id who belongs to the agreement
        corresponding to the agreement_id.
        """
        url = self.build_url('agreements/{}/members/participantSets/{}'
                             .format(agreement_id, signer_id))
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json()

    @handle_adobe_exception
    def get_documents(self, agreement_id, **extra_data):
        """
        Return all document ids for a given agreement id
        """
        url = self.build_url('agreements/{}/documents'.format(agreement_id))
        response = requests.get(url, headers=self.get_headers(),
                                data=extra_data)
        response.raise_for_status()
        return response.json()

    @handle_adobe_exception
    def get_document(self, agreement_id, document_id):
        """
        Download a document
        """
        url = self.build_url('agreements/{}/documents/{}'
                             .format(agreement_id, document_id))
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.content

    @handle_adobe_exception
    def get_events(self, agreement_id):
        """
        Retrieves the events information for an agreement.
        """
        url = self.build_url('agreements/{}/events'.format(agreement_id))
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json()

    def rebuild_with_token(self, access_token):
        return AdobeSignClient(self.root_url, access_token, self.api_user,
                               self.on_behalf_of_user)
