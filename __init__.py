from flask import Flask
from jinja2 import Markup

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'james123'

    from .views import views
    from .auth import auth
    from .createnew import display_table
     
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    return app