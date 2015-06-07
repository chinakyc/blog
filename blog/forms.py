from libs.wtforms import Form
from wtforms import TextField, BooleanField
from wtforms.validators import Required, Email


class LoginForm(Form):
    email = TextField('email', validators=[Required(),
                                           Email()])
    password = TextField('password', validators=[Required()])
    remember_me = BooleanField('remember_me', default=False)
