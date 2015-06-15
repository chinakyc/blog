#!blog_env/bin/python3

import unittest
from handlers.base import BaseHandler, Flash_Msg
from handlers.blog import ComposeHandler


class dummyHandlerMixin(object):
    """In order to facilitate the test,
    override orginal `__init__`
    """
    def __init__(self):
        pass


class dummyBaseHandler(dummyHandlerMixin, BaseHandler):
    def __init__(self, flash_id):
        # test flash need `self._flash_id`
        self._flash_id = flash_id


class dummyComposeHandler(dummyHandlerMixin, ComposeHandler):
    pass


class BaseHandlerTestCase(unittest.TestCase):

    def setUp(self):
        self._handler = dummyBaseHandler(flash_id='test_flash_id')

    def tearDown(self):
        if self._handler._flash_id in self._handler._flash_msg_box:
            del self._handler._flash_msg_box[self._handler._flash_id]

    def test_write_flash(self):
        # for readable
        normal_msg = 'test_normal_flash'
        abnormal_msg = 'test_error_msg'
        flash_id = self._handler._flash_id
        flash_box = self._handler._flash_msg_box

        self.assertNotIn(flash_id, flash_box)

        # write_normal_flash
        self._handler.flash(normal_msg)

        self.assertIsInstance(flash_box[flash_id][0],
                              Flash_Msg)
        # normal message classified as `message`
        self.assertEqual('message',
                         flash_box[flash_id][0].category)
        self.assertEqual(normal_msg,
                         flash_box[flash_id][0].msg)

        # write_abnormal_message
        self._handler.flash(abnormal_msg, category='error')

        self.assertEqual('error',
                         flash_box[flash_id][1].category)
        self.assertEqual(abnormal_msg,
                         flash_box[flash_id][1].msg)

    def test_get_flashed_msg(self):
        flash_id = self._handler._flash_id
        flashed_msg_box = self._handler._flash_msg_box
        will_flash_msg = [Flash_Msg("normal1", "message"),
                          Flash_Msg("normal2", "message"),
                          Flash_Msg("error1", "error"),
                          Flash_Msg("error2", "error"),
                          Flash_Msg("other1", "other"),
                          Flash_Msg("other2", "other"),
                          Flash_Msg("another1", "another"),
                          Flash_Msg("another2", "another")]

        def _setUp():
            for msg in will_flash_msg:
                self._handler.flash(*msg)

        # test got flashed_messages before `flash`
        self.assertListEqual([], self._handler.get_flashed_messages())

        _setUp()
        # test got all flashed_messages without category
        flashed_messages = self._handler.get_flashed_messages()
        self.assertListEqual(flashed_messages, [m for m, c in will_flash_msg])
        self.assertNotIn(flash_id, flashed_msg_box)

        _setUp()
        # test got all flashed_messages with category
        msg_with_c = list(self._handler.get_flashed_messages(with_categories=True))
        self.assertListEqual(msg_with_c, will_flash_msg)
        self.assertNotIn(flash_id, flashed_msg_box)

        _setUp()
        # test got all flashed_messages filter by category without category
        msg_with_c = list(self._handler.get_flashed_messages(category_filter=["error"]))
        should_got_msg = [m for m in will_flash_msg if m.category in ["error"]]
        should_remain_msg = [m for m in will_flash_msg if m.category not in ["error"]]
        self.assertListEqual(msg_with_c, list(m.msg for m in should_got_msg))
        self.assertListEqual(flashed_msg_box[flash_id], list(should_remain_msg))

    def test_html2text(self):
        normal_htmlstr = \
            "<blockquote><p>Beautiful is better than ugly.<br></blockquote>"
        incomplete_htmlstr1 = \
            "<blockquote><p>Beautiful is better than ugly.<br></blockq"
        incomplete_htmlstr2 = \
            "<blockquote><p>Beautiful is better than ugly.<br></"
        incomplete_htmlstr3 = \
            "<blockquote><p>Beautiful is better than ugly.<br><"
        textstr = "Beautiful is better than ugly."
        self.assertEqual(textstr, self._handler.html2text(normal_htmlstr))
        self.assertEqual(textstr, self._handler.html2text(incomplete_htmlstr1))
        self.assertEqual(textstr, self._handler.html2text(incomplete_htmlstr2))
        self.assertEqual(textstr, self._handler.html2text(incomplete_htmlstr3))


class ComposeHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self._handler = dummyComposeHandler()

    def test_separate_tags(self):
        clear_tags = ['python', 'linux', 'tornado', 'flask']
        wild_tags_str = " Python, Linux,  Tornado | fLask  "

        self.assertListEqual(
            clear_tags, self._handler.separate_tags(wild_tags_str))


if __name__ == "__main__":
    unittest.main()
