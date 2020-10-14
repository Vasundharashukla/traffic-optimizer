import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or b'_5#y2L"F4Q8z\n\xec]/'
    PERMANENT_SESSION_LIFETIME = 6000
    
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'dev.db')
    #SQLALCHEMY_TRACK_MODIFICATIONS = False

    ## Flask-mail config
    ## MAIL_SERVER= 'smtp.gmail.com'
    ## MAIL_PORT= 465
    ## MAIL_USE_TLS= False
    ## MAIL_USE_SSL= True
    ## MAIL_USERNAME= ''
    ## MAIL_PASSWORD= ''
    ## MAIL_DEFAULT_SENDER= 'tester'

