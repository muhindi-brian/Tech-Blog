from flask import Flask
from flask_mysqldb import MySQL
from flask_login import LoginManager
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Import routes at the end to avoid circular imports
from app import routes



# from flask import Flask
# from flask_mysqldb import MySQL
# from flask_login import LoginManager
# from config import Config


# app = Flask(__name__)
# app.config.from_object(Config)

# mysql = MySQL(app)
# login_manager = LoginManager(app)
# login_manager.login_view = 'login'


# from app import r
