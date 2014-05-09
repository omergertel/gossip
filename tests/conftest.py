import itertools

import gossip
import gossip.registry
import pytest

hook_id = itertools.count()

@pytest.fixture(autouse=True, scope="function")
def clear_registrations():
    gossip.registry.undefine_all()

@pytest.fixture(autouse=True, scope="function")
def reset_global_group():
    gossip.get_global_group().reset()

@pytest.fixture
def hook_name():
    return "hook{0}".format(next(hook_id))

@pytest.fixture
def hook(hook_name):
    return gossip.define(hook_name)

@pytest.fixture
def registered_hook(hook_name):
    return RegisteredHook(hook_name)

@pytest.fixture
def registered_hooks():
    returned = []
    for i in range(10):
        if i % 3 == 0:
            hook_name = "group{0}.hook{1}".format(next(hook_id), next(hook_id))
        else:
            hook_name = "hook{0}".format(next(hook_id))
        returned.append(RegisteredHook(hook_name))
    return returned

class RegisteredHook(object):

    def __init__(self, hook_name):
        super(RegisteredHook, self).__init__()

        self.name = hook_name
        self._fail = False
        self.kwargs = {"a": 1, "b": 2, "c": 3}
        self.num_called = 0

        class HandlerException(Exception):
            pass

        self.exception_class = HandlerException

        def handler(**kw):
            assert kw == self.kwargs
            self.num_called += 1
            if self._fail:
                raise self.exception_class()

        self.func = handler

        gossip.register(func=handler, hook_name=hook_name)

    @property
    def called(self):
        return self.num_called > 0

    def fail_when_called(self):
        self._fail = True

    def works(self):
        old_num_caled = self.num_called
        self.trigger()
        return self.num_called == old_num_caled + 1

    def trigger(self):
        gossip.trigger(self.name, **self.kwargs)

