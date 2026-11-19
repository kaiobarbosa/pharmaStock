import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv() 

from src.login_and_create_account.presentation.create_user_presentation import blueprint_create_director_account 

app = Flask(__name__)

CORS(app, supports_credentials=True) 

app.register_blueprint(blueprint_create_director_account)

if __name__ == "__main__":
    app.run(debug=True, port=5000)