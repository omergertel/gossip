import gossip
import pytest
from gossip.exception_policy import Inherit

from .conftest import RegisteredHook


@pytest.mark.parametrize("invalid_policy", [object(), 1, None, gossip.RaiseImmediately])
def test_cannot_set_invalid_policy(invalid_policy):
    with pytest.raises(ValueError):
        gossip.set_exception_policy(invalid_policy)

def test_global_cannot_be_inherit():
    with pytest.raises(RuntimeError):
        gossip.set_exception_policy(Inherit())

def test_default_global_group_policy():
    assert isinstance(gossip.get_global_group().get_exception_policy(), gossip.RaiseImmediately)

def test_inherit_policy(exception_handling_policy):
    group = gossip.group.Group("some_group", parent=gossip.get_global_group())
    gossip.set_exception_policy(exception_handling_policy)
    group.set_exception_policy(Inherit())
    assert group.get_exception_policy() is exception_handling_policy

def test_inherit_policy_changing_parent():
    gossip.define("group.hook")
    group = gossip.get_group_by_name("group")
    for policy in (gossip.RaiseImmediately(), gossip.RaiseDefer(), gossip.IgnoreExceptions()):
        gossip.set_exception_policy(policy)
        assert group.get_exception_policy() is policy

def test_group_returns_to_default_after_reset():
    gossip.get_global_group().set_exception_policy(gossip.IgnoreExceptions())
    gossip.get_global_group().reset()
    test_default_global_group_policy()

def test_get_exception_policy(exception_handling_policy):
    group = gossip.group.Group("some_group", parent=gossip.get_global_group())
    group.set_exception_policy(exception_handling_policy)
    assert group.get_exception_policy() is exception_handling_policy

def test_exception_handling(hook, error_prone_handlers, exception_handling_policy):
    hook.group.set_exception_policy(exception_handling_policy)
    if isinstance(exception_handling_policy, gossip.IgnoreExceptions):
        hook(**error_prone_handlers[0].kwargs)
    else:
        with pytest.raises(error_prone_handlers[0].exception_class):
            hook(**error_prone_handlers[0].kwargs)

    assert error_prone_handlers[0].called
    for handler in error_prone_handlers[1:]:
        assert handler.called == (not isinstance(exception_handling_policy, gossip.RaiseImmediately))

@pytest.fixture(
    params=[gossip.RaiseDefer, gossip.RaiseImmediately, gossip.IgnoreExceptions])
def exception_handling_policy(request):
    return request.param()

@pytest.fixture
def error_prone_handlers(hook_name):
    returned = []
    num_handlers = 10
    for handler_index in range(num_handlers):
        handler = RegisteredHook(hook_name)
        if handler_index in (0, 5, num_handlers - 1):
            handler.fail_when_called()
        returned.append(handler)

    return returned
