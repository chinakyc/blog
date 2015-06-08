from libs.wtforms import Form
from wtforms.validators import Required, Email, Length
from wtforms import TextField, BooleanField, TextAreaField


class LoginForm(Form):
    email = TextField('email', validators=[Required(), Length(1, 100), Email()])
    password = TextField('password', validators=[Required()])
    remember_me = BooleanField('remember_me', default=False)


class ComposeForm(Form):
    title = TextField('title', validators=[Required(), Length(1, 200)])
    content = TextAreaField('content')
    markdown = TextAreaField('markdown')
    tags = TextField('tags', validators=[Required()])
    category = TextField('category', validators=[Required()])


class CommentForm(Form):
    content = TextAreaField('content', validators=[Required(), ])
    author_email = TextField('email', validators=[Required(),
                                                  Length(1, 100), Email()])
    author_name = TextField('name', validators=[Required(),
                                                Length(1, 100)])
    author_url = TextField('author_url')
