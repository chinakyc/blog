"""
    blog.py
    ~~~~~~~
    blog handlers
"""
import re
import tornado.web
from tornado import gen
from datetime import datetime
from operator import itemgetter
from handlers.base import BaseHandler
from models import User, Post, Category, Comment
from forms import LoginForm, ComposeForm, CommentForm

__all__ = ["MainHandler", "IndexHandler", "BlogHandler", "AboutHandler",
           "ComposeHandler", "LoginHandler", "LogoutHandler", "PostHandler",
           "NoDestinationHandler", ]


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
    def get(self):

        # This page requires special `owner.skills` order.
        # so we adapt it in this handler

        # use itemgetter faster than lambda
        self.g.owner.skills = sorted(self.g.owner.skills,
                                     key=itemgetter('value'))
        self.render("index.html")


class BlogHandler(MainHandler):
    @gen.coroutine
    def get(self, category, page):
        if not page:
            page = 1

        if not category:
            # Because of need `category` when template rendering.
            # modify `request.paht` not very friendly
            # so just redirect
            return self.redirect('/blog/All')

        if category.upper() == "ALL":
            posts = yield Post.asyncQuery().order_by("-create_time").paginate(
                page=int(page), per_page=self.settings['per_page'])
        else:
            c = yield Category.asyncQuery(name=category).first()
            if not c:
                raise tornado.web.HTTPError(404)
            posts = yield Post.asyncQuery(
                category=c).order_by("-create_time").paginate(
                page=int(page), per_page=self.settings['per_page'])

        categorys = yield Category.asyncQuery()

        self.render("blog.html", posts=posts, categorys=categorys)


class PostHandler(MainHandler):
    def __init__(self, *args,  **kwargs):
        super().__init__(*args, **kwargs)
        self.form = CommentForm(self.request.arguments)

    @gen.coroutine
    def get(self, title):
        post = yield Post.asyncQuery(title=title).first()
        if not post:
            raise tornado.web.HTTPError(404)
        self.render("post.html", post=post, form=self.form)

    @gen.coroutine
    def post(self, title):
        post = yield Post.asyncQuery(title=title).first()

        if not post:
            raise tornado.web.HTTPError(404)

        if self.form.validate():
            comment = Comment()
            comment.create_time = datetime.utcnow()
            comment.author_name = self.form.author_name.data
            comment.author_email = self.form.author_email.data
            comment.author_url = self.form.author_url.data
            comment.content = self.form.content.data
            post.comments.append(comment)
            yield post.save()
            self.flash("评论提交成功~")
            return self.redirect("{path}{id}".format(
                path=self.request.path, id="#comment"))
        self.render("post.html", post=post, form=self.form)


class AboutHandler(MainHandler):
    def get(self):

        # This page requires special `owner.skills` order.
        # so we adapt it in this handler

        # use itemgetter faster than lambda
        self.g.owner.skills = sorted(self.g.owner.skills,
                                     key=itemgetter('value'), reverse=True)
        self.render("about.html")


class ComposeHandler(MainHandler):
    _re_tags_separator = re.compile(r'(\/|\\|\,|\ |\|){1,}')

    def __init__(self, *args,  **kwargs):
        super().__init__(*args, **kwargs)
        self.form = ComposeForm(self.request.arguments)

    def separate_tags(self, tags_str):
        # first,converted to lowercase and
        # all of the separator is replaced with ` `
        # second, strip repalced_str  (sometimes user input tags :"linux,")
        # third, split with ` `
        # more flexible than direct invoke `re.split`
        return self._re_tags_separator.sub(
            ' ', tags_str.lower()).strip().split()

    @tornado.web.authenticated
    @gen.coroutine
    def get(self, title):
        post = yield Post.asyncQuery(title=title).first()
        self.form.create_time.data = datetime.now()
        if post:
            self.form.title.data = post.title
            self.form.content.data = post.content
            self.form.markdown.data = post.markdown
            self.form.create_time.data = post.create_time
            self.form.category.data = post.category.name
            self.form.tags.data = ','.join(post.tags)
        self.render("compose.html", form=self.form)

    @tornado.web.authenticated
    @gen.coroutine
    def post(self, title):
        if self.form.validate():
            post = yield Post.asyncQuery(title=self.form.title.data).first()

            if post:
                post.modified_time = datetime.utcnow()
            else:
                post = Post()
                post.create_time = self.form.create_time.data.utcnow()

            title = self.form.title.data.replace(' ', '-')
            content = self.form.content.data
            markdown_text = self.form.markdown.data
            tags = self.separate_tags(self.form.tags.data)
            category = yield Category.asyncQuery(
                name=self.form.category.data).first()
            if not category:
                category = Category()
                category.name = self.form.category.data.capitalize()
                yield category.save()

            post.title = title
            post.content = content
            post.markdown = markdown_text
            post.category = category
            post.tags = tags
            post.author = self.current_user

            yield post.save()
            self.flash("compose finsh!")
            return self.redirect('/blog')
        self.render("compose.html", form=self.form)


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
            user = yield User.asyncQuery(email=self.form.email.data).first()
            if user:
                verify = yield user.verify_password(self.form.password.data)
                if verify:
                    if self.form.remember_me.data:
                        self.set_secure_cookie("user", user.email)
                    else:
                        self.set_secure_cookie("user", user.email,
                                               expires_days=None)
                    self.flash('welcome back!')
                    return self.redirect(self.get_argument("next", "/"))
            self.flash('Invalid email or passwd')
        self.render("login.html", form=self.form)


class LogoutHandler(MainHandler):
    def get(self):
        self.clear_cookie("user")
        self.flash('已登出')
        self.redirect(self.get_argument("next", "/"))


class NoDestinationHandler(MainHandler):
    def get(self):
        """for 404 error"""
        self.write_error(404)
