import json

from rauth import OAuth2Service


def oauth_decode(data):
    new_data = data.decode("utf-8", "strict")

    return json.loads(new_data)


def get_access_token(client_id, secrete_key, base_url, access_token_url):
    service = OAuth2Service(
        name="foo",
        client_id=client_id,
        client_secret=secrete_key,
        access_token_url=access_token_url,
        authorize_url=access_token_url,
        base_url=base_url,
    )
    data = {'code': 'bar',
            'grant_type': 'client_credentials',
            'redirect_uri': 'http://example.com/'}

    session = service.get_auth_session(data=data, decoder=oauth_decode)
    access_token = session.access_token
    return access_token
