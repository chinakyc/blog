"""
    forms.py
    ~~~~~~~~
    from:
        http://my.oschina.net/stardriver/blog/163724
"""
import re
from tornado.escape import to_unicode
from wtforms.ext.i18n.form import Form as wtForm


class Form(wtForm):
    """
    Using this Form instead of wtforms.Form

    Example::
        class SigninForm(Form):
            email = EmailField('email')
            password = PasswordField('password')

        class SigninHandler(RequestHandler):
            def get(self):
                form = SigninForm(self.request.arguments)
    """
    LANGUAGES = ['zh']

    def __init__(self, formdata=None, obj=None, prefix='', **kwargs):
        super().__init__(formdata, obj, prefix, **kwargs)

    def process(self, formdata=None, obj=None, **kwargs):
        if formdata is not None and not hasattr(formdata, 'getlist'):
            formdata = TornadoArgumentsWrapper(formdata)
        super().process(formdata, obj, **kwargs)


class TornadoArgumentsWrapper(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError

    def getlist(self, key):
        try:
            values = []
            for v in self[key]:
                v = to_unicode(v)
                v = re.sub(r"[\x00-\x08\x0e-\x1f]", " ", v)
                values.append(v)
            return values
        except KeyError:
            raise AttributeError
