"""
    base.py
    ~~~~~~~
    base for handlers
"""
import re
import uuid
import threading
import tornado.web
# from functools import partial
from libs.moment import momentjs
from collections import defaultdict, namedtuple

Flash_Msg = namedtuple("Flash_Msg", ["msg", "category"])

# unique private instance of object for get_flashed_messages's arg
_no_value = object()


class _Global(object):
    """This class for implement `g`"""
    pass


class BaseHandler(tornado.web.RequestHandler):
    """BaseHandler"""

    _flash_msg_box = defaultdict(list)
    _flash_lock = threading.Lock()
    _re_html_tags = re.compile(r"<\w+.*?>|<\/\w+>")
    _re_html_img_tag = re.compile(r'<img\ src="(.*?)"\ \/>')

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        # like g in flask
        self.g = _Global()

    def before_request(self):
        """dummy `before_request handler` like `before_request` in flask.
        """
        pass

    def _execute(self, transforms, *args, **kwargs):
        """overridden _execute with handy extras
        In order to keep the code simple, so we without @gen.coroutine
        If you want to with @gen.coroutine, Please copy the original `_execute`
        error_handle portion. Otherwise, the error will silence that raise here.
        """
        # TODO
        # `self.redirect` and `self.before_request` need `self._transforms`
        # so we set up it here
        # but `self._transforms` will set up twice
        self._transforms = transforms

        # dummy flash handle
        flashId = self.get_secure_cookie("flash_id")
        if not flashId:
            id = uuid.uuid4()
            self.set_secure_cookie("flash_id", str(id), expires_days=None)
            self._flash_id = str(id)
            self.flash(self.settings.get("welcome_banner", "welcome"))
            self.redirect(self.request.uri)
        else:
            # `self.get_secure_cookie` return byte
            self._flash_id = flashId.decode()

        self.before_request()

        return super(BaseHandler, self)._execute(transforms, *args, **kwargs)

    def get_template_namespace(self):
        """overridden get_template_namespace add some values"""

        namespace = super().get_template_namespace()
        namespace.update({
            'get_flashed_messages': self.get_flashed_messages,
            'momentjs': momentjs,
            'g': self.g,
            'html2text': self.html2text
        })
        return namespace

    def flash(self, msg, category='message'):
        """dummy `flash handler` like `flash` in flask
        Flashes a message to the next request. In order to remove the flashed
        mesage from the session and to display it to the user, the template
        has to call `get_flashed_messages`

        : arg string msg: the message to be flashed.
        : arg string category: the category for the message.
            The following values are recommended:'message' for any kind of
            message, 'error' for errors, 'info' for information messages
            and 'warning' for warnings.
            However any kind of string can be used as category.
        """

        assert hasattr(self, "_flash_id"), ("should had `._flash_id`")

        with BaseHandler._flash_lock:
            BaseHandler._flash_msg_box[self._flash_id].append(
                Flash_Msg(msg, category)
            )

    def get_flashed_messages(self, with_categories=False,
                             category_filter=_no_value):
        """the values assigned as defaults should always be immutable objects,
        such as None, True, False, numbers, or strings. Specifically, never
        write code like this:
            def spam(a, b=[]) #NO!
        To avoid this, it's better to assign a unique private instance of
        object, as shown in the solution (the _no_value variable)"
                                           --quote from python cookbook3 7.5

        `get_flashed_messages` slightly different with `get_flashed_messages` in flask

        Pulls all flased messages from the cache and returns them in default.
        When pass argument `category_filter`, the rest of the message will be retained.
        By default just a iter of messages are returned, but when
        with_categories is set to True, the return value will be a iter of
        namedtuple instead.

        Filter the flased messages to one or more category by providing those
        categories in category_filter. This allows rendering categories in
        separate html blocks. The with_categories and category_filter arg are
        distnct


        :arg bool with_categories: controls whether categories are returned with
            message text
        :arg list category_filter: filters the messages down to only those
            matching the provided categories.

        """
        assert hasattr(self, "_flash_id"), ("should had `._flash_id`")

        with BaseHandler._flash_lock:
            # To avoid unnecessary operation
            if self._flash_id not in BaseHandler._flash_msg_box:
                return []

            if category_filter is _no_value:
                messages = BaseHandler._flash_msg_box.pop(self._flash_id)
            else:
                assert isinstance(category_filter, list), (
                    "arg `category_filter` should be a `list`")
                messages = [m for m in BaseHandler._flash_msg_box[self._flash_id]
                            if m.category in category_filter]
                BaseHandler._flash_msg_box[self._flash_id] =\
                    [m for m in BaseHandler._flash_msg_box[self._flash_id]
                     if m.category not in category_filter]

            if with_categories:
                return messages
            return [m.msg for m in messages]

    def html2text(self, html):
        """Remove Html tags"""

        # to complete incomplete tag
        html += 'inc>'
        # In my case, may have single image posts, so convert img tag to
        # meaingful content is comfortable
        html = self._re_html_tags.sub(
            '', self._re_html_img_tag.sub('[图片]', html))
        if html.endswith('inc>'):
            return html[:-4]
        return html

    def write_error(self, status_code, **kwargs):
        if self.settings.get('debug'):
            super(BaseHandler, self).write_error(status_code, **kwargs)
        else:
            try:
                self.render("{}.html".format(status_code))
            except:
                self.render("500.html")
