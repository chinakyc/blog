"""
    app.py
    ~~~~~
    app
"""
import sys
import config

from logging.handlers import SMTPHandler

import tornado.web
import tornado.ioloop
import tornado.httpserver

from tornado.options import define, options, parse_command_line

from libs.concurrent import CustomThreadPoolExecutor

define('port', default=5555, help='run on the given port', type=int)


class AsyncSMTPHandler(SMTPHandler):
    _executor = CustomThreadPoolExecutor(2)

    def emit(self, record):
        self._executor.submit(super().emit, record)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = config.handlers
        settings = config.settings
        super().__init__(handlers, **settings)


def main():
    parse_command_line()
    app = Application()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port, '0.0.0.0')

    if not app.settings.get("debug"):
        import logging
        from logging import StreamHandler
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler('../tmp/blog.log', 'a',
                                           1 * 1024 * 1024, 10)

        RootLogger = logging.getLogger()

        # We have a File_handler so we don't need streamhandler
        for handler in RootLogger.handlers:
            # There are some Handler is a subclass of streamhandler
            # SO, using the type instead isinstance
            if type(handler) is StreamHandler:
                RootLogger.removeHandler(handler)

        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"))

        RootLogger.addHandler(file_handler)

        if hasattr(config, "MAIL_SERVER"):
            credentials = None
            if config.MAIL_USERNAME and config.MAIL_PASSWORD:
                credentials = (config.MAIL_USERNAME, config.MAIL_PASSWORD)
            mail_handler = AsyncSMTPHandler((config.MAIL_SERVER, config.MAIL_PORT),
                                            config.MAIL_USERNAME,
                                            config.ADMINS, "Blog failure",
                                            credentials)
            mail_handler.setLevel(logging.ERROR)
            RootLogger.addHandler(mail_handler)

    print('Starting Tornado on http://localhost:{}/'.format(options.port))
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    main()
