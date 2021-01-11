from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    got_request_exception,
)
from database.database_functions import (
    insert_into_users,
    insert_into_user_data,
    get_user,
    get_users,
    get_conversation,
)

from os import environ as env
from configparser import ConfigParser
from flask.json import JSONEncoder
from datetime import datetime
from authlib.integrations.flask_client import OAuth
from constants import *
from six.moves.urllib.parse import urlencode
from functools import wraps
from utils import handle_input, send_text, get_user_words, conversation_log
from dotenv import load_dotenv, find_dotenv
import constants
from werkzeug.exceptions import HTTPException
# Getting the environment settings
#parser = ConfigParser()
#parser.read("dev.ini")
#HOST = parser.get("website", "host")
#PORT = int(parser.get("website", "port"))

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

AUTH0_CALLBACK_URL = env.get(constants.AUTH0_CALLBACK_URL)
AUTH0_CLIENT_ID = env.get(constants.AUTH0_CLIENT_ID)
AUTH0_CLIENT_SECRET = env.get(constants.AUTH0_CLIENT_SECRET)
AUTH0_DOMAIN = env.get(constants.AUTH0_DOMAIN)
AUTH0_BASE_URL = 'https://' + AUTH0_DOMAIN
AUTH0_AUDIENCE = env.get(constants.AUTH0_AUDIENCE)

# used for encoding datetime into iso format whenever sending to the frontend using the jsonify function
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.isoformat()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


app = Flask(__name__, template_folder="client/templates", static_folder="client/static")
app.json_encoder = CustomJSONEncoder
app.secret_key = constants.SECRET_KEY
oauth = OAuth(app)

# we use auth0 for the authentication.
# should run on localhost:4000 or 127.0.0.1:4000 for the auth0
# to accept
@app.errorhandler(Exception)
def handle_auth_error(ex):
    response = jsonify(message=str(ex))
    response.status_code = (ex.code if isinstance(ex, HTTPException) else 500)
    return response
auth0 = oauth.register(
    'auth0',
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    api_base_url=AUTH0_BASE_URL,
    access_token_url=AUTH0_BASE_URL + '/oauth/token',
    authorize_url=AUTH0_BASE_URL + '/authorize',
    client_kwargs={
        'scope': 'openid profile email',
    },
)



def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if constants.PROFILE_KEY not in session:
            return redirect("/login")
        return f(*args, **kwargs)

    decorated.__name__ = f.__name__
    return decorated


def has_accepted(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)

    decorated.__name__ = f.__name__
    return decorated


@app.route("/callback")
def callback_handling():
    auth0.authorize_access_token()
    resp = auth0.get("userinfo")
    userinfo = resp.json()

    session[constants.JWT_PAYLOAD] = userinfo
    session[constants.PROFILE_KEY] = {
        "user_id": userinfo["sub"],
        "name": userinfo["name"],
        "picture": userinfo["picture"],
    }
    return redirect("/bot")


@app.route("/login")
def login():
    return auth0.authorize_redirect(redirect_uri="http://" + request.host + "/callback")


@app.route("/logout")
def logout():
    session.clear()
    params = {"returnTo": url_for("home", _external=True), "client_id": AUTH0_CLIENT_ID}
    return redirect(auth0.api_base_url + "/v2/logout?" + urlencode(params))


@app.route("/")
def render_home():
    return redirect('/login')

@app.route("/bot")
@login_required
def render_bot():
    user = get_user(session[constants.JWT_PAYLOAD]["name"])
    if len(user) == 0:
        insert_into_users(session[constants.JWT_PAYLOAD]["name"])
    return render_template("bot.html"), 200
@app.route("/dashboard")
@login_required
def render_dashboard():
    return render_template("tweets.html"), 200


@app.route("/get_users", methods=["GET"])
def return_users():
    print("HELLOOO")
    print(get_users())
    return jsonify(get_users())


@app.route("/get_user", methods=["GET"])
def return_user():
    email = request.args.get("email")
    return jsonify(get_user_words(email))


@app.route("/conversation")
@login_required
@login_required
def conversation():
    """
    gets the full chat lof of a user
    :return: json
    TODO: check why jsonify is done in database functions and not in flask app
    """
    return jsonify(get_conversation(session[constants.JWT_PAYLOAD]["name"]))


@app.route("/input", methods=["GET", "POST"])
@conversation_log
def get_input():
    """
    Function that handles the API calls
    :return: 200 HTTP code
    """
    data = request.form
    query = data["text"]
    return send_text(handle_input(query))


if __name__ == "__main__":
    app.run(debug=True, port=4000)
