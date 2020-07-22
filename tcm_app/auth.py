import json
from functools import wraps
from urllib.parse import urlencode

from authlib.integrations.flask_client import OAuth
from flask import (
    Blueprint, abort, current_app, jsonify, redirect, render_template, request,
    session, url_for)
from jose import jwt
from six.moves.urllib import request as six_request
from werkzeug.exceptions import HTTPException


# ---
# AUTH0 LOGIN   (based on https://auth0.com/docs/quickstart/webapp/python)
# ---
bp = Blueprint('auth', __name__)

oauth = OAuth()
auth0 = oauth.register(
    'auth0',
    # Required for userinfo
    # https://auth0.com/docs/api/authentication#user-profile
    client_kwargs={'scope': 'openid email'})


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_email' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return wrapper


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/login')
def login():
    return auth0.authorize_redirect(
        redirect_uri=current_app.config['AUTH0_CALLBACK_URL'],
        audience=current_app.config['AUTH0_AUDIENCE'])


@bp.route('/callback')
def callback_handling():
    auth0.authorize_access_token()
    session['access_token'] = auth0.token['access_token']
    session['user_email'] = auth0.get('userinfo').json()['email']
    return redirect(url_for('auth.welcome'))


@bp.route('/welcome')
@require_auth
def welcome():
    return render_template(
        'welcome.html',
        user_email=session['user_email'],
        access_token=session['access_token'])


@bp.route('/logout')
def logout():
    session.clear()
    params = {
        'returnTo': url_for('auth.index', _external=True),
        'client_id': current_app.config['AUTH0_CLIENT_ID']
    }
    return redirect(f'{auth0.api_base_url}/v2/logout?{urlencode(params)}')


# ---
# SWAGGER UI AUTHORISATION REDIRECT (for implicitFlow securitySchemes)
# ---
@bp.route('/oauth2-redirect')
def oauth2_redirect():
    return render_template('oauth2-redirect.html')


# ---
# API AUTHORISATION AND ENDPOINT PROTECTION
# ---
def get_token_auth_header():
    """Get the Access Token from the Authorization Header
    """
    auth = request.headers.get('Authorization', None)
    if not auth:
        abort(401, description='Authorization header is missing.')

    parts = auth.split()
    message = "The Authorization headers' value {}, must be 'Bearer <token>'."

    if parts[0].lower() != 'bearer':
        abort(401, description=message.format("is missing 'Bearer'"))
    elif len(parts) == 1:
        abort(401, description=message.format('is missing a token'))
    elif len(parts) > 2:
        abort(401, description=message.format('contains too much'))

    token = parts[1]
    return token


def check_permissions(permission, payload):
    """Checks whether JWT payload includes any of the listed items in permission.
    Raises an exception when no permission.
    """
    if 'permissions' not in payload or permission not in payload['permissions']:
        message = 'You are not permitted to access the requested resource.'
        # Consider 404, as described at https://httpstatuses.com/403
        abort(403, description=message)
    return True


def verify_decode_jwt(token):
    """Partly based on example at https://auth0.com/docs/quickstart/backend/python/01-authorization
    """
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError as err:
        abort(401, description='Provided JWT malformed')
    if 'kid' not in unverified_header:
        abort(401, description='Provided JWT malformed.')

    jsonurl = six_request.urlopen('{}/.well-known/jwks.json'.format(
        current_app.config['AUTH0_API_BASE_URL']))
    jwks = json.loads(jsonurl.read())
    rsa_key = {}
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms='RS256',
                audience=current_app.config['AUTH0_AUDIENCE'],
                issuer=current_app.config['AUTH0_API_BASE_URL'] + '/')

            return payload

        except jwt.ExpiredSignatureError:
            abort(401, description='Provided JWT has expired.')
        except jwt.JWTClaimsError:
            abort(401, description='Incorrect claims in provided JWT. Please, \
                check the audience and issuer.')
        except Exception:
            abort(401, description='Unable to parse provided JWT.')

    abort(401, description='Unable to find the appropriate key in provided JWT.')


def get_email(token):
    """Get email from cookie or userinfo endpoint.
    https://auth0.com/docs/api/authentication#user-profile
    From cookie when allready provided from userinfo endpoint.
    """
    if 'email' not in session:
        request = six_request.Request(
            url='{}/userinfo'.format(current_app.config['AUTH0_API_BASE_URL']),
            headers={'Authorization': 'Bearer ' + token})
        response = six_request.urlopen(request)
        userinfo = json.loads(response.read())
        session['email'] = userinfo['email']
    return session['email']


def require_token(permission=''):
    """Decorator for endpoints
    """
    def decorator_require_token(f):
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            self.email = get_email(token)
            return f(self, *args, **kwargs)
        return wrapper
    return decorator_require_token
