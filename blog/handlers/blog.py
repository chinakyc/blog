"""
    blog.py
    ~~~~~~~
    blog handlers
"""
from tornado import gen
from forms import LoginForm
from datetime import datetime
from models import User, Post
from operator import itemgetter
from handlers.base import BaseHandler


class MainHandler(BaseHandler):
    def before_request(self):
        # Because all of the pages need `owner`, so save `owner` in g.
        self.g.owner = User.objects.get(nickname=self.settings['owner'])

    def get_current_user(self):
        email = self.get_secure_cookie("user")
        if not email:
            return None
        user = User.objects.get(email=email.decode())
        user.last_seen = datetime.utcnow()
        user.save()
        return user


class IndexHandler(MainHandler):
    @gen.coroutine
    def get(self):

        # This page requires special `owner.skills` order.
        # so we adapt it in this handler

        # use itemgetter faster than lambda
        self.g.owner.skills = sorted(self.g.owner.skills,
                                     key=itemgetter('value'))
        self.render("index.html")


class BlogHandler(MainHandler):
    @gen.coroutine
    def get(self, page):
        if not page:
            page = 1
        posts = yield Post.asyncQuery().paginate(
            page=int(page), per_page=self.settings['per_page'])
        self.render("blog.html", posts=posts)


class AboutHandler(MainHandler):
    @gen.coroutine
    def get(self):

        # This page requires special `owner.skills` order.
        # so we adapt it in this handler

        # use itemgetter faster than lambda
        self.g.owner.skills = sorted(self.g.owner.skills,
                                     key=itemgetter('value'), reverse=True)
        self.render("about.html")


class LoginHandler(MainHandler):
    def __init__(self, *args,  **kwargs):
        super().__init__(*args, **kwargs)
        self.form = LoginForm(self.request.arguments)

    def before_request(self):
        super().before_request()
        if self.current_user:
            self.flash('您已经登录过了哦')
            return self.redirect('/')

    def get(self):
        self.render("login.html", form=self.form)

    @gen.coroutine
    def post(self):
        if self.form.validate():
            user = yield User.asyncQuery().filter(
                email=self.form.email.data).first()
            if user:
                verify = yield user.verify_password(self.form.password.data)
                if verify:
                    if self.form.remember_me.data:
                        self.set_secure_cookie("user", user.email)
                    else:
                        self.set_secure_cookie("user", user.email,
                                               expires_days=None)
                    self.flash('welcome back!')
                    return self.redirect('/')
            self.flash('Invalid email or passwd')
        self.render("login.html", form=self.form)


class LogoutHandler(MainHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/"))


class NoDestinationHandler(MainHandler):
    def get(self):
        """for 404 error"""
        self.write_error(404)
