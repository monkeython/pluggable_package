"""
A ``multipla`` (which is spelled like ``Multi-plug``) is one of the italian
words for a power strip. As you probably know, most kind of ``multipla`` have
(multiple) sockets capable of handling mulitiple types of plugs. I thought it
would have been a perfect name for a module that helps developer to write and
use extensible python distributions.

So, this module provides just one simple interface: the function
:py:func:`power_up`. It returns an instance of a plugin handling class
(:py:class:`Multipla`), that uses :py:mod:`pkg_resources` to add all entry
points from the abailable distributions. A :py:class:`Multipla` is a
:py:class:`RatedDict` of :py:class:`MultiPlugAdapter`s, which also are
:py:class:`RatedDict`s. So, thanks to a simple rating system, you'll be able to
handle multiple implementation of multiple plugins trough just a single class.
"""
#     Copyright (c) 2014, Luca De Vitis <luca at monkeython.com>
#     All rights reserved.

#     Redistribution and use in source and binary forms, with or without
#     modification, are permitted provided that the following conditions are
#     met:

#     1. Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.

#     2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.

#     3. Neither the name of the copyright holder nor the names of its
#     contributors may be used to endorse or promote products derived from this
#     software without specific prior written permission.

#     THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#     IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#     THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#     PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
#     CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#     EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#     PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#     PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#     LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#     NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#     SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

__author__ = "Luca De Vitis <luca at monkeython.com>"
__version__ = '0.3.3'
__keywords__ = ['multipla', 'multi-plugs', 'multi-socket', 'plugs', 'plugin']
__classifiers__ = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: Implementation :: CPython',
    'Programming Language :: Python :: Implementation :: Jython',
    'Programming Language :: Python :: Implementation :: PyPy',
    'Topic :: Software Development :: Libraries :: Python Modules']

__all__ = ['power_up']

import collections
import functools
import importlib
import sys

import pkg_resources

try:
    thread = importlib.import_module('thread')
except ImportError:     # pragma: no cover
    try:
        thread = importlib.import_module('_thread')
    except ImportError:
        try:
            thread = importlib.import_module('dummy_thread')
        except ImportError:
            thread = importlib.import_module('_dummy_thread')

PY2 = sys.version_info[0] == 2

iteritems = lambda o: iter(o.iteritems() if PY2 else o.items())
iterkeys = lambda o: iter(o.iterkeys() if PY2 else o.keys())


def _public2(method):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        return method(*args, **kwargs)
    wrapper.__name__ = method.__name__.lstrip('_')
    return wrapper


def _list_iterator(method):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        return list(method(*args, **kwargs))
    wrapper.__name__ = method.__name__[6:]
    return wrapper


def _public3(method):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        return method(*args, **kwargs)
    wrapper.__name__ = method.__name__[6:]
    return wrapper


def _iterkeys(instance):
    "Returns a generator of its own keys, sorted by rating."
    return (k for k in instance._ratings)


def _itervalues(instance):
    "Returns a generator of its own values, sorted by rating."
    return (instance._dict[k] for k in instance._ratings)


def _iteritems(instance):
    "Returns a generator of ``(key, value)`` pairs, sorted by rating."
    return ((k, instance._dict[k]) for k in instance._ratings)


def _iterratings(instance):
    "Returns a generator of ``(key, rating)`` pairs, sorted by rating."
    return (r for r in instance._ratings.items())


def _viewkeys(instance):
    "Returns a :py:class:`collections.KeysView` of its own keys."
    return collections.KeysView(instance._dict)


def _viewvalues(instance):
    "Returns a :py:class:`collections.ValuesView` of its own values."
    return collections.ValuesView(instance._dict)


def _viewitems(instance):
    "Returns a :py:class:`collections.ItemsView` of its own items."
    return collections.ItemsView(instance._dict)


def _viewratings(instance):
    "Returns a :py:class:`collections.ItemsView` of its own ratings."
    return collections.ItemsView(instance._ratings)


class Lock(object):
    def __init__(self):
        self.__lock = thread.allocate_lock()

    if PY2:
        def __nonzero__(self):
            return self.__lock.locked()
    else:
        def __bool__(self):
            return self.__lock.locked()

    def __enter__(self):
        self.__lock.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__lock.release()


class RatedDict(collections.Mapping):
    """A :py:class:`dict`-like class that lets you rate its objects.

    This implementation is meant to be thread-safe. It supports
    the following :py:class:`dict`-like methods as you would expect:

    * ``__setitem__``, ``__getitem__``, ``__delitem__``
    * ``__contains__``, ``__len__``
    * ``__iter__``, ``__reversed__``
    * ``__str__``
    * ``__eq__``, ``__ne__``
    * ``update``
    """
    def __init__(self):
        self._ratings = collections.OrderedDict()
        self._dict = dict()
        self.locked = Lock()

    def __str__(self):
        try:
            name = self.name
        except AttributeError:
            name = id(self)
        return "<{} '{}'>".format(self.__class__.__name__, name)

    def _setitem_(self, key, value):
        self._dict[key] = value
        self._ratings.setdefault(key, 0)
        return value

    def __setitem__(self, key, value):
        with self.locked:
            self._setitem_(key, value)

    def __getitem__(self, key):
        return self._dict[key]

    def __delitem__(self, key):
        with self.locked:
            del self._dict[key]
            del self._ratings[key]

    def __contains__(self, key):
        return self._dict.__contains__(key)

    def __len__(self):
        return self._dict.__len__()

    def __iter__(self):
        return self._ratings.__iter__()

    def __reversed__(self):
        return self._ratings.__reversed__()

    def update(self, other=None, **updated):

        with self.locked:
            if other is not None:
                try:
                    for key, value in iteritems(other):
                        self._setitem_(key, value)
                except AttributeError:
                    try:
                        for key in iterkeys(other):
                            self._setitem_(key, other[key])
                    except AttributeError:
                        for key, value in other:
                            self._setitem_(key, value)
            for key in updated:
                self._setitem_(key, updated[key])

    def rate(self, ratings=None, **args):
        """Rate the items into the dictionary.

        :param ratings:                 A ``key: rating`` mapping or an
                                        iterable yielding ``(key, rating)``.
        :param args:                    Anyway, variable keyword arguments
                                        ``args`` will be used to update the
                                        item ratings.
        :raises KeyError:               If unexpected keys are found.

        This method behaves like the :py:meth:`dict.update`, but affects only
        items ratings. At the end of the update, dictionary keys are sorted by
        rating, from greater to lower rating value. Rating is supposed to be
        any kind of number equal or greater than 0. Default item rating is 0.
        """

        ratings = dict(ratings if ratings is not None else (), **args)
        with self.locked:
            unexpected = set(ratings.keys()) - set(self._dict.keys())
            if unexpected:
                error = '{}.rate: unexpected keys {}'
                raise KeyError(error.format(self, unexpected))
            self._ratings.update(ratings)
            # Here we take advantage of the ordering of
            # :py:class:`collections.OrderedDict` and stability of
            # :py:func:`sorted`
            by_rate = sorted(self._ratings.items(), key=lambda kv: -kv[1])
            self._ratings = collections.OrderedDict(by_rate)

    def top(self, amount=None):
        """Returns the top rated items.

        :param int amount:              The number of items to return. Defaults
                                        to all items.
        :returns:                       A list of ``(key, value)`` pairs,
                                        sorted by key ratings.
        :raises ValueError:             If ``amount`` is greater than the
                                        available items.
        """
        top_rated = list()
        with self.locked:
            if amount is None:
                amount = len(self._ratings)
            item = iter(self._ratings)
            try:
                for counter in range(amount):
                    key = next(item)
                    top_rated.append((key, self._dict[key]))
            except StopIteration:
                error = '{}.top: asked {} items, got {}'
                raise ValueError(error.format(self, amount, counter))
        return top_rated

    @property
    def highest_rated(self):
        """The value of the highest rated item.

        :raises ValueError:             If container is empty.
        """
        with self.locked:
            try:
                return self._dict[next(iter(self._ratings))]
            except StopIteration:
                error = '{}.highest_rated: empty container'
                raise ValueError(error.format(self))

    def rating(self, key):
        """Returns the rating of ``key``.

        :raises KeyError:               If ``key`` does not exists.
        """
        return self._ratings[key]

    if PY2:
        iterkeys = _public2(_iterkeys)
        itervalues = _public2(_itervalues)
        iteritems = _public2(_iteritems)
        iterratings = _public2(_iterratings)
        viewkeys = _public2(_viewkeys)
        viewvalues = _public2(_viewvalues)
        viewitems = _public2(_viewitems)
        viewratings = _public2(_viewratings)
        keys = _list_iterator(_iterkeys)
        values = _list_iterator(_itervalues)
        items = _list_iterator(_iteritems)
        ratings = _list_iterator(_iterratings)
    else:
        keys = _public3(_viewkeys)
        values = _public3(_viewvalues)
        items = _public3(_viewitems)
        ratings = _public3(_viewratings)


class MultiPlugAdapter(RatedDict):
    """The multi-plug adapter that holds all the plugin implementations.

    :param name:                        The name of the plug adapter (i.e. the
                                        name of the entry point).

    This class represents all the plugins that implement the give entry point
    name. Since this class inherit from :py:class:`RatedDict`, it's possible to
    rate each implementation. The ``pkg_resources`` classes allows each
    distribution to provide their own implementation of a given plugin name:
    for example, 2 distributions might provide the same ``YAML`` serialization
    functions, but each using a different ``YAML`` library.
    """
    def __init__(self, name):
        self.name = name
        super(MultiPlugAdapter, self).__init__()

    def plug_in(self, name, plug):
        """Try to plug an object in.

        :param str name:                The ``plug`` implementation name.
        :param plug:                    The object to plug in.
        :raises KeyError:               If another object with the same
                                        ``name`` is already plugghed in.

        If you want to explicitly overrid a plug implementation, you must use
        dictionary item setting syntax.
        """
        with self.locked:
            try:
                value = self._dict[name]
            except KeyError:
                return self._setitem_(name, plug)
        error = '{}.plug_in: {} is already set with {}'
        raise KeyError(error.format(self, name, value))


class Multipla(RatedDict):
    """The power strip to put yout plugs into.

    :param name:                        The name of the power strip (i.e. the
                                        entry point group).

    This class represents the plugin group. Since this class inherits from
    :py:class:`RatedDict`, it's possible to use it almost as a dictionary, and
    also rate your plugin names. Each item in an instance of this class is an
    instance of :py:class:`MultiPlugAdapter`, actually, so you can use more
    implementation of a given plugin name. On the average you want to use the
    higest rated implementation trough the :py:meth:`Multipla.get` method, but
    you can also use the dictionary item access syntax to reach for all the
    implementations a achieve your goal.
    """

    def __init__(self, name):
        self.name = name
        super(Multipla, self).__init__()

    def __call__(self, distribution):   # pragma: no cover
        for ep in distribution.get_entry_map(self.name).values():
            implementation = ':'.join([ep.module_name, '.'.join(ep.attrs)])
            self.switch_on(ep.name).plug_in(implementation, ep.load())

    def switch_on(self, name):
        """Switch on a socket.

        :param str name:                The socket (entry point) name.
        :returns:                       The :py:class:`MultiPlugAdapter`
                                        associated with the ``name``.

        If the specified :py:class:`MultiPlugAdapter` already exists, it is
        returned. If there is no :py:class:`MultiPlugAdapter` for the
        specified plugin name, a new one is created and returned.
        """
        with self.locked:
            try:
                adapter = self._dict[name]
            except KeyError:
                adapter = self._setitem_(name, MultiPlugAdapter(name))
        return adapter

    def get(self, name, default=None):
        """Get the higest rated ``plug`` for the given plug ``name``.

        :param name:                    The plugin name.
        :param default:                 The default value to return if lookup
                                        fails.
        :returns:                       The highest rated plugin.
        :raises KeyError:               If ``name`` lookup fails.
        :raises ValueError:             See :py:data:`RatedDict.highest_rated`.
        """
        try:
            return self[name].highest_rated
        except KeyError:
            return default


_register = dict()
_locked_register = Lock()


def power_up(name, *args):
    """Creates and returns a rated dictionary of plugins.

    :param str name:                    The multi-plug name (i.e. entry point
                                        group).
    :param args:                        Variable argument list of
                                        :py:class:`pkg_resources.WorkingSet`.
    :rtype:                             :py:class:`Multipla`

    I meant to have just one :py:class:`Multipla` instances for each group of
    entry points. They are powered up by subscribing (as per
    :py:meth:`pkg_resources.WorkingSet.subscribe`) to each
    :py:class:`pkg_resources.WorkingSet` in the variable argument list. If no
    extra argument is provided, (default) :py:data:`pkg_resources.working_set`
    is used. Subscription causes the :py:class:`Multipla` instance to register
    any plugin in the given :py:class:`pkg_resources.WorkingSet`, and let it be
    notified of any plugin that will be added in the future. Subscribing a
    :py:class:`Multipla` twice (or more) to the same
    :py:class:`pkg_resources.WorkingSet` neither add any overhead, nor makes
    the instance to register a give plugin more than once, so it's safer to use
    this function as the only module interface.

    >>> import multipla
    >>>
    >>> multipla.power_up('plugin_group')
    <Multipla 'plugin_group'>
    >>>
    >>> plugin_group = multipla.power_up('plugin_group')
    >>> plugin_group is multipla.power_up('plugin_group')
    True
    >>> isinstance(plugin_group, multipla.Multipla)
    True
    """
    with _locked_register:
        try:
            multipla = _register[name]
        except KeyError:
            _register[name] = multipla = Multipla(name)
    if not args:
        args = [pkg_resources.working_set]
    for working_set in args:
        working_set.subscribe(multipla)
    return multipla
