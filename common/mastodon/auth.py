from django.contrib.auth.backends import ModelBackend, UserModel
from django.shortcuts import reverse
from boofilsic.settings import MASTODON_DOMAIN_NAME, CLIENT_ID, CLIENT_SECRET
from .api import *


def obtain_token(request, code):
    """ Returns token if success else None. """
    # TODO change http!
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': f"https://{request.get_host()}{reverse('users:OAuth2_login')}",
        'grant_type': 'authorization_code',
        'code': code,
        'scope': 'read write'
    }
    from boofilsic.settings import DEBUG
    if DEBUG:
        payload['redirect_uri']= f"http://{request.get_host()}{reverse('users:OAuth2_login')}",
    url = 'https://' + MASTODON_DOMAIN_NAME + API_OBTAIN_TOKEN
    response = post(url, data=payload)
    if response.status_code != 200:
        return
    data = response.json()
    return data.get('access_token')


def get_user_data(token):
    url = 'https://' + MASTODON_DOMAIN_NAME + API_VERIFY_ACCOUNT
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = get(url, headers=headers)
    if response.status_code != 200:
        return None
    return response.json()


def revoke_token(token):
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': token
    }
    url = 'https://' + MASTODON_DOMAIN_NAME + API_REVOKE_TOKEN
    response = post(url, data=payload)


def verify_token(token):
    """ Check if the token is valid and is of local instance. """
    url = 'https://' + MASTODON_DOMAIN_NAME + API_VERIFY_ACCOUNT
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = get(url, headers=headers)
    if response.status_code == 200:
        res_data = response.json()
        # check if is local instance user
        if res_data['acct'] == res_data['username']:
            return True
    return False


class OAuth2Backend(ModelBackend):
    """ Used to glue OAuth2 and Django User model """
    # "authenticate() should check the credentials it gets and returns
    #  a user object that matches those credentials."
    # arg request is an interface specification, not used in this implementation
    def authenticate(self, request, token=None, username=None, **kwargs):
        """ when username is provided, assume that token is newly obtained and valid """
        if token is None:
            return

        if username is None:
            user_data = get_user_data(token)
            if user_data:
                username = user_data['username']
            else:
                # aquiring user data fail means token is invalid thus auth fail
                return None

        # when username is provided, assume that token is newly obtained and valid
        try:
            user = UserModel._default_manager.get_by_natural_key(user_data['username'])
        except UserModel.DoesNotExist:
            return None
        else:
            if self.user_can_authenticate(user):
                return user
            return None
