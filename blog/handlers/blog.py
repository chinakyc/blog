"""
    blog.py
    ~~~~~~~
    blog handlers
"""
import re
import datetime
import markdown2
import tornado.web
from tornado import gen
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
        user.last_seen = datetime.datetime.utcnow()
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

        self.render("blog.html",
                    posts=posts,
                    categorys=categorys,
                    current_category=category)


class PostHandler(MainHandler):

    def initialize(self, *args,  **kwargs):
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
            comment.create_time = datetime.datetime.utcnow()
            comment.author_name = self.form.author_name.data
            comment.author_email = self.form.author_email.data
            comment.author_url = self.form.author_url.data
            # Direct use user post data is unsafe,
            # so we convert `org_markdown_text` in the back-end
            comment.content = markdown2.markdown(self.form.content.data)
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
    _time_delta = datetime.timedelta(hours=8)

    def initialize(self, *args,  **kwargs):
        self.form = ComposeForm(self.request.arguments)

    def UTC2BeiJingTime(self, time):
        '''the server may be anywhere in the world,
        so we manually adjust the time'''
        return time + self._time_delta

    def BeiJing2UTCTime(self, time):
        return time - self._time_delta

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
        self.form.create_time.data = \
            self.UTC2BeiJingTime(datetime.datetime.utcnow())
        if post:
            self.form.post_id.data = post.id
            self.form.title.data = post.title
            self.form.content.data = post.content
            self.form.markdown.data = post.markdown
            self.form.create_time.data = \
                self.UTC2BeiJingTime(post.create_time)
            self.form.category.data = post.category.name
            self.form.tags.data = ','.join(post.tags)
        self.render("compose.html", form=self.form)

    @tornado.web.authenticated
    @gen.coroutine
    def post(self, title):
        if self.form.validate():
            post = None

            if self.form.post_id.data:
                post = yield Post.asyncQuery(id=self.form.post_id.data).first()
            if post:
                post.modified_time = datetime.datetime.utcnow()
            else:
                post = Post()
                post.create_time = \
                    self.BeiJing2UTCTime(self.form.create_time.data)

            title = self.form.title.data.replace(' ', '-')
            content = self.form.content.data
            markdown_text = self.form.markdown.data
            tags = self.separate_tags(self.form.tags.data)
            category_str = self.form.category.data.capitalize()
            category = yield Category.asyncQuery(
                name=category_str).first()
            if not category:
                category = Category()
                category.name = category_str
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
    def initialize(self, *args,  **kwargs):
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
