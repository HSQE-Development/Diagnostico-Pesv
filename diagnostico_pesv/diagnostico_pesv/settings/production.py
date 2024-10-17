from .base import *
from corsheaders.defaults import default_methods
from corsheaders.defaults import default_headers

DEBUG = False

CORS_ORIGIN_ALLOW_ALL = False
ALLOWED_HOSTS = ["apipesv.consultoriaycapacitacionhseq.com"]
CORS_ORIGIN_WHITELIST = ["https://pesvapp.consultoriaycapacitacionhseq.com"]
CORS_ALLOW_METHODS = list(default_methods)
CORS_ALLOW_HEADERS = list(default_headers) + ["Authorization"]
