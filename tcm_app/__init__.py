from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flasgger import APISpec, Swagger
from flask import Flask
from flask_session import Session
from flask_migrate import Migrate

from tcm_app.models import TradeSchema


def create_app(config_filename='config.py'):
    """Application factory based on:
    * https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/#basic-factories
    * https://flask.palletsprojects.com/en/1.1.x/tutorial/factory/#the-application-factory
    """
    app = Flask(
        __name__, static_url_path='/static/css', static_folder='./static/css')

    # ---
    # CONFIGURATION
    # ---
    app.config.from_pyfile(config_filename)
    app.config['JSON_SORT_KEYS'] = False
    app.config['SESSION_TYPE'] = 'filesystem'  # Flask-Session
    Session(app)


    # ---
    # MODELS
    # ---
    from tcm_app.models import db
    db.init_app(app)
    migrate = Migrate(app, db)


    # ---
    # AUTHORIZATION
    # ---
    from tcm_app import auth
    app.register_blueprint(auth.bp)
    auth.oauth.init_app(app)


    # ---
    # API ENDPOINTS
    # ---
    from tcm_app import api
    app.register_blueprint(api.bp)


    # ---
    # SWAGGER
    # ---
    spec = APISpec(
        title='Trade Compliance Monitor',
        version='0.0.1',
        openapi_version='3.0.2',
        plugins=[
            FlaskPlugin(),
            MarshmallowPlugin(),
        ],
        tags=[{
            'name': 'trades',
        }],
        components={
            'securitySchemes': {
                #  https://swagger.io/docs/specification/authentication/
                'bearerAuth': {
                    'type': 'http',
                    'scheme': 'bearer',
                    'bearerFormat': 'JWT'
                },
                # Alternative authorization. Requires pasting Client Id as well
                # as checking boxes for scope, but applies the token automatically.
                'implicitFlow': {
                    'type': 'oauth2',
                    'flows': {
                        'implicit': {
                            'authorizationUrl': '{}/authorize?audience={}'.format(
                                app.config['AUTH0_API_BASE_URL'],
                                app.config['AUTH0_AUDIENCE']
                            ),
                            'scopes':{
                                # Contrary to authorizationCodeFlow scope
                                # 'openid' is not needed.

                                # 'openid': '',
                                'email': ''
                            }
                        }
                    }
                },

                # # Currently not implemented
                # # Alternative authorization. Requires pasting Client Id and
                # # Secret as well as checking boxes for scope, but applies the
                # # token automatically.
                # 'authorizationCodeFlow': {
                #     'type': 'oauth2',
                #     'flows': {
                #         'authorizationCode': {
                #             'authorizationUrl': '{}/authorize?audience={}'.format(
                #                 app.config['AUTH0_API_BASE_URL'],
                #                 app.config['AUTH0_AUDIENCE']
                #             ),
                #             'tokenUrl': '{}/oauth/token'.format(
                #                 app.config['AUTH0_API_BASE_URL']
                #             ),
                #             'scopes': {
                #                 'openid': '',
                #                 'email': ''
                #             }
                #         }
                #     }
                # }
            }
        },
        security=[
            {
            'bearerAuth': [],
            },
            {
                'implicitFlow': []
            },
            # # Currently not implemented
            # {
            #     'authorizationCodeFlow': []
            # }
        ]
    )
    swagger_template = spec.to_flasgger(app, definitions=[TradeSchema])

    app.config['SWAGGER'] = {
        'uiversion': '3',
        'openapi': '3.0.2',
        'ui_params': {
            # Needed for implicitFlow
            'oauth2RedirectUrl': '{}/oauth2-redirect'.format(
                app.config['SWAGGER_BASE_URL']
            )
        }
    }

    Swagger(app, template=swagger_template)

    return app
