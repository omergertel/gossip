Advanced Usage
==============

Hook Arguments
--------------

Hooks can receive arguments, which are then passed to the handlers. 

.. code-block:: python
   
		>>> import gossip

		>>> @gossip.register('with_arguments')
		... def handler(a, b, c):
		...     print('Called: {0} {1} {2}'.format(a, b, c))
		
		>>> gossip.trigger('with_arguments', a=1, b=2, c=3)
		Called: 1 2 3

Note that argument mismatches means a runtime error:

.. code-block:: python
		
		>>> gossip.trigger('with_arguments', a=1) # doctest: +IGNORE_EXCEPTION_DETAIL
		Traceback (most recent call last):
		 ...
		TypeError: handler() takes exactly 3 arguments (1 given)

.. note::
   Since hook handlers are likely to be spread across many locations in your projects, argument ordering changes make your code more likely to break. This is why gossip forces all arguments to be passed by keywords, and not as positionals.


Hook Tags
---------

Hooks can receive tags, enabling you to divide callbacks into several categories.

.. code-block:: python

		>>> @gossip.register('hook', tags=['a'])
		... def callback_a():
		...     print('A called')
		>>> @gossip.register('hook', tags=['b'])
		... def callback_a():
		...     print('B called')
		>>> gossip.trigger_with_tags('hook', tags=['a'])
		A called
		>>> gossip.trigger_with_tags('hook', tags=['b'])
		B called

.. note:: registering with multiple tags will fire the callback if *any* of the tags match.

.. note:: hook tags have a special relationship to strictness, see :ref:`below <tag_strictness>` for more details.


Defining Hooks Explicitly
-------------------------

By default, registering hooks in with :func:`gossip.register` takes care of hook definition and registration at the same time. In several cases, however, you may want to simply define a hook, but not register anything to it yet. For this we have the :func:`gossip.define` API:

.. code-block:: python

		>>> import gossip
		>>> hook = gossip.define('hook_name_here')
		>>> @hook.register
		... def handler():
		...     pass

The :func:`gossip.register` returns the :class:`gossip.hooks.Hook` object for the defined hook, so further operations can be executed against it.

Hooks cannot be ``define``-d more than once:

.. code-block:: python

		>>> import gossip
		>>> hook = gossip.define('some_hook')
		>>> gossip.define('some_hook') # doctest: +IGNORE_EXCEPTION_DETAIL
		Traceback (most recent call last):
		   ...
		NameAlreadyUsed: ...

Strict Registration
-------------------

By default, handlers can be registered to hooks that haven't been :func:`defined <gossip.define>` yet. While this is ok for most uses, in some cases you may want to limit this behavior, to avoid typos like this one:

.. code-block:: python

		>>> @gossip.register('my_group.on_initialize')
		... def handler():
		...     pass

		>>> gossip.trigger('my_group.on_initailize') # spot the difference?

To do this, you can make any hook group into a *strict group*, meaning it requires registered hooks to be properly defined first:

.. code-block:: python

		>>> group = gossip.create_group('some_group')
		>>> group.set_strict()

		>>> @gossip.register('some_group.nonexisting') # doctest: +IGNORE_EXCEPTION_DETAIL
		... def handler():
		...     pass
		Traceback (most recent call last):
		   ...
		UndefinedHook: hook 'some_group.nonexisting' wasn't defined yet

This also works if you set a group as a strict group *after* you registered hooks to it -- any existing hook that wasn't formally defined will trigger an exception:

.. code-block:: python

		>>> group = gossip.create_group('other_group')
		>>> @gossip.register('other_group.nonexisting')
		... def handler():
		...     pass

		>>> group.set_strict() # doctest: +IGNORE_EXCEPTION_DETAIL
		Traceback (most recent call last):
		   ...
		UndefinedHook: hook 'other_group.nonexisting' was already registered, but not defined

.. _tag_strictness:

Strictness and Tags
~~~~~~~~~~~~~~~~~~~

Strict hooks always perform checks on the tags that are passed to them:

.. code-block:: python
       
       >>> gossip.create_group('strict_group').set_strict()
       >>> _ = gossip.define('strict_group.hook1', tags=['a', 'b'])
       >>> @gossip.register('strict_group.hook1', tags=['c']) # doctest: +IGNORE_EXCEPTION_DETAIL
       ... def f():
       ...     pass
       Traceback (most recent call last):
           ...
       UnsupportedHookTags: ...
       		

Token Registration
------------------

Handlers can be registered with *tokens*. A token is anything that supports equality and hashing, but it is most commonly used for Python strings. Token are useful to unregister a group of handlers in a single operation, with :func:`gossip.unregister_token`:

.. code-block:: python

		>>> @gossip.register('some_hook', token='token1')
		... def handler1():
		...     pass

		>>> @gossip.register('some_hook', token='token1')
		... def handler2():
		...     pass

		>>> gossip.unregister_token('token1') # unregisters all handlers of all hooks that were registered with 'token1'




Getting Hooks by Name
---------------------

Once a hook is defined you can get the underlying :class:`gossip.hooks.Hook` object by using :func:`gossip.get_hook`:

.. code-block:: python

		>>> gossip.get_hook('some_hook')
		<Hook some_hook()>

However, in this way the hook is never defined for you:

.. code-block:: python

		>>> gossip.get_hook('nonexisting_hook') # doctest: +IGNORE_EXCEPTION_DETAIL
		Traceback (most recent call last):
		   ...
		HookNotFound: ...
		

Muting Hooks
------------

You can selectively mute hooks (prevent their callbacks from being called) through the :func:`.mute_context` context:

.. code-block:: python

		>>> def function_that_triggers_hooks():
		...     gossip.trigger('my.hook.name')

		>>> with gossip.mute_context(['my.hook.name']):
		...     function_that_triggers_hooks()  # <--- nothing happens
