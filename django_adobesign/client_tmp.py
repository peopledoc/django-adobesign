"""
TO REMOVE
"""


import requests
import sys
import time

from pprint import pprint

from datetime import datetime
from requests_oauthlib import OAuth2Session

client_id = "XXXXXXXXXXXXXXXXXXX"
client_secret = "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
authorization_base_url = 'https://secure.eu1.adobesign.com/public/oauth'
token_url = 'https://api.echosign.com/oauth/token'
refresh_url = 'https://api.echosign.com/oauth/refresh'
redirect_uri = "https://localhost:8000"

# Session
scope = ['user_login:self', 'agreement_send:self', 'agreement_read:self']
session = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)


# Authorize
def authorize():
    authorization_url, state = session.authorization_url(
        authorization_base_url)

    print('Please go to %s and authorize access.'.format(authorization_url))


def fetch_token(code):
    response = session.fetch_token(token_url,
                                   code=code,
                                   client_secret=client_secret,
                                   authorization_response="/")
    print(response)
    return response['access_token']


def token_refresh(refresh_token):
    response = session.refresh_token(refresh_url,
                                     refresh_token=refresh_token,
                                     client_id=client_id,
                                     client_secret=client_secret,
                                     authorization_response="/")
    print(response)
    return response


def build_url(path):
    return "https://api.eu1.adobesign.com/api/rest/v5{}".format(path)


def test(token, url="http://api.eu1.adobesign.com/api/rest/v5/users"):
    # Test endpoint
    headers = {"Authorization": "Bearer {}".format(token)}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    print(response.json())


def upload_document(token, path):
    path_url = "/transientDocuments"
    url = build_url(path=path_url)

    headers = {"Authorization": "Bearer {}".format(token)}

    with open(path, 'rb') as pdf:
        files = {'File': pdf}
        data = {
            'File-Name': 'adobesign-test-{}.pdf'.format(datetime.now()),
            'Mime-Type': 'application/pdf'
        }

        response = requests.post(url, headers=headers, files=files, data=data)
    response.raise_for_status()

    print(response.json())
    return response.json()['transientDocumentId']


def send_doc_for_signature(token, doc_id):
    path_url = "/agreements"
    url = build_url(path=path_url)

    headers = {"Authorization": "Bearer {}".format(token)}
    data = {
        "documentCreationInfo": {
            "fileInfos": [{
                "transientDocumentId": doc_id
            }],
            "name": "MyTestAgreement {}".format(datetime.now()),
            "recipientSetInfos": [
                {
                    "recipientSetMemberInfos": [
                        {
                            "email": "jacques.rott@people-doc.com",
                            "fax": ""
                        }
                    ],
                    "recipientSetRole": "SIGNER"
                },
                {
                    "recipientSetMemberInfos": [
                        {
                            "email": "david.steinberger@people-doc.com",
                            "fax": ""
                        }
                    ],
                    "recipientSetRole": "SIGNER"
                }
            ],
            "signatureType": "ESIGN",
            "signatureFlow": "SEQUENTIAL"
        }
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    print(response.json())
    return response.json()['agreementId']


def get_agreement(token, agreement_id):
    path_url = "/agreements"
    url = build_url(path=path_url) + '/{}'.format(agreement_id)
    print(url)
    headers = {"Authorization": "Bearer {}".format(token)}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    print(response.json())
    return response.json()


def get_agreement_status(token, agreement_id):
    agreement = get_agreement(token, agreement_id)
    return agreement['status']


def send_reminders(token, agreement_id):
    pass


def signature_flow(token, path):
    print("UPLOAD document")
    doc_id = upload_document(token, path)

    print("SEND agreement")
    agreement_id = send_doc_for_signature(token, doc_id)

    checks = 0
    print("WAIT signers")
    while True:
        status = get_agreement_status(token, agreement_id)
        print (status)
        if status == 'SIGNED':
            break

        if checks > 10:
            print("SEND reminder")
            send_reminders(token, agreement_id)
            checks = 0
        checks += 1
        time.sleep(1.0)

    print("DONE")
    get_agreement(token, agreement_id)


def get_agreements(token):
    path_url = "/agreements"
    url = build_url(path=path_url)

    headers = {"Authorization": "Bearer {}".format(token)}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    pprint(response.json())


code = "XXXXXXXXXXXXXXXXXXXXXXXX"
token = 'XXXXXXXXXXXXXXXXXXXXXXXX'

if __name__ == '__main__':
    if 'authorize' in sys.argv:
        code = authorize()
        sys.exit(0)
    if 'token' in sys.argv:
        token = fetch_token(code)
        print(token)
        sys.exit(0)
    if 'agreements' in sys.argv:
        get_agreements(token)
        sys.exit(0)

    signature_flow(token, sys.argv[-1])
