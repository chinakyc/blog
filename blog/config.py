"""
    config.py
    ~~~~~~~~~
    Configuration for blog
"""
import os
from handlers import (
    IndexHandler,
    BlogHandler,
    AboutHandler,
    ComposeHandler,
    LoginHandler,
    LogoutHandler,
    PostHandler,
    NoDestinationHandler,
)

# tornado handlers
handlers = [
    (r"/", IndexHandler),
    # TODO
    # this `re` can't match the Chinese
    (r"/blog/?(\w+)?/?(\d+)?/?", BlogHandler),
    (r"/about/?", AboutHandler),
    (r"/compose/?(\S+)?/?", ComposeHandler),
    (r"/post/(\S+)/?", PostHandler),
    (r"/admin/login", LoginHandler),
    (r"/admin/logout", LogoutHandler),
    # if only defines(r"/hello, HelloHandler"),
    # can only capture /hello/other on 404 error.
    # can not  capture /test on 404 error.
    # defines(r".*", NoDestinationHandler), can solve this situation.
    (r".*", NoDestinationHandler),
]

# tornado settings
settings = dict(
    owner="Azul",
    blog_title="Azul's blog - 成为一个靠谱的人",
    welcome_banner="谢谢你的到来, 如果你也热爱Python/Linux/Vim的话, 交个朋友吧^_^~~~",
    email="cca053@gmail.com",
    links={
        "weibo": "http://weibo.com/kyc1",
        "facebook": "https://facebook.com/yachao.kang",
        "github": "https://github.com/chinakyc",
    },
    about_blog="......",
    login_url='/admin/login',
    per_page=8,
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    xsrf_cookies=True,
    cookie_secret='make_your_secret_key',
    debug=False,
)

# executor_config
EXECUTOR_NUM = 10
