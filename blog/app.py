"""
    app.py
    ~~~~~
    app
"""
import sys
import config
import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado.options import define, options, parse_command_line

define('port', default=5555, help='run on the given port', type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = config.handlers
        settings = config.settings
        super(Application, self).__init__(handlers, **settings)


def main():
    parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port, '0.0.0.0')

    print('Starting Tornado on http://localhost:{}/'.format(options.port))
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    main()
