"""
A messaging application for Django
"""
from __future__ import unicode_literals

from django.conf import settings
if getattr(settings, 'POSTMAN_I18N_URLS', False):
    from django.utils.translation import pgettext_lazy
else:
    def pgettext_lazy(c, m): return m

# following PEP 386: N.N[.N]+[{a|b|c|rc}N[.N]+][.postN][.devN]
VERSION = (3, 5, 0)
PREREL = ('a', 1)
POST = 0
DEV = 0

# as of Django 1.7
default_app_config = 'postman.apps.PostmanConfig'

# options
# Translators: keep consistency with the <option> parameter in url translations ; 'm' stands for 'messages'
OPTION_MESSAGES = pgettext_lazy('postman_url', 'm')


def get_version():
    version = '.'.join(map(str, VERSION))
    if PREREL:
        version += PREREL[0] + '.'.join(map(str, PREREL[1:]))
    if POST:
        version += ".post" + str(POST)
    if DEV:
        version += ".dev" + str(DEV)
    return version

__version__ = get_version()
