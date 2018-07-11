"""Declaration of API shortcuts.

Everything declared (or imported) in this module is exposed in
:mod:`django_opentrust.api` root package, i.e. available when one does
``from django_opentrust import api as django_opentrust``.

Here are the motivations of such an "api" module:

* as a `django-opentrust` library user, in order to use `django-opentrust`, I
  just do ``from django_opentrust import api as django_opentrust``.
  It is enough for most use cases. I do not need to bother with more
  `django_opentrust` internals. I know this API will be maintained,
  documented, and not deprecated/refactored without notice.

* as a `django-opentrust` library developer, in order to maintain
  `django-opentrust` API, I focus on things declared in
  :mod:`django_opentrust.api`. It is enough. It is required. I take care of
  this API. If there is a change in this API between consecutive releases, then
  I use :class:`DeprecationWarning` and I mention it in release notes.

It also means that things not exposed in :mod:`django_opentrust.api` are not
part of the deprecation policy. They can be moved, changed, removed without
notice.

"""
from django_echosign.backend import EchoSignBackend
from django_echosign.exceptions import EchoSignException
from django_echosign.client import EchoSignClient


__all__ = [
    'EchoSignBackend',
    'EchoSignException',
    'EchoSignClient'
]
