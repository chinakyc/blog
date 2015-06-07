"""
    concurrent.py
    ~~~~~~~~~~~
    custom concurrent
"""
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor


class CustomFuture(Future):
    def __getattr__(self, attr_name):
        """`__getattr__` is supposed to be invoked only after finding an
        appropriate attribute has failed.
        captures attr_name Instead of raise AttributeError,
        so we can access `BaseQuerySet.attr_name` by invoke `future.attr_name`
        """

        def _inner_custom_futer_doneCallback(query_set, attr_name,
                                             *args, **kwargs):
            """get resut by invoke BaseQuerySet.attr_name, and return result"""

            method = getattr(query_set, attr_name)
            return method(*args, **kwargs)

        def _inner_custom_futer_getattr(*args, **kwargs):
            """we can not directly return `BaseQuerySet.attr_name`,
            so we need this agency captures arguments from
            `future.attr_name(arguments)`. these arguments will use for
            `BaseQuerySet.attr_name(arguments)`.
            """

            # create sub future `cF`
            # sub future is not associated with asynchronous
            # just for invoke chaining
            cF = CustomFuture()

            def _handle_done_future(f):
                """set result to sub `future` when current has done
                invoke `_inner_custom_futer_doneCallback` get result
                """
                try:
                    cF.set_result(
                        _inner_custom_futer_doneCallback(
                            f.result(), attr_name, *args, **kwargs
                        )
                    )
                except Exception as e:
                    # when an error occurs here, tornado can not notice,
                    # so we set error to `cF`, notify tornado.
                    cF.set_exception(e)

            self.add_done_callback(_handle_done_future)

            # return `cF` to captures next attr_name,
            # so we can implement invoke chaining
            return cF

        return _inner_custom_futer_getattr


class CustomMixin(object):
    def submit(self, fn, *args, **kwargs):
        """overridden `submit` return `CustomFuture` instead `Future`"""
        cF = CustomFuture()
        f = super().submit(fn, *args, **kwargs)

        def _set_customFuture_result(f):
            try:
                cF.set_result(f.result())
            except Exception as e:
                cF.set_exception(e)

        f.add_done_callback(_set_customFuture_result)
        return cF


class CustomThreadPoolExecutor(CustomMixin, ThreadPoolExecutor):
    pass


class CustomProcessPoolExecutor(CustomMixin, ProcessPoolExecutor):
    pass
