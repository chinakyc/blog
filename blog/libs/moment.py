"""
    moment.py
    ~~~~~~~~~~~
    implementation momentjs support
"""


class momentjs(object):
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def render(self, format):
        return "<script>\ndocument.write(moment(\"%s\").lang('zh-cn').%s);\n</script>" \
            % (self.timestamp.strftime("%Y-%m-%dT%H:%M:%S Z"), format)

    def format(self, fmt):
        return self.render("format(\"%s\)" % fmt)

    def calendar(self):
        return self.render("calendar()")

    def fromNow(self):
        return self.render("fromNow()")