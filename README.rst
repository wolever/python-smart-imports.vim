python-smart-imports.vim
========================

**WORK IN PROGRESS**

A Vim plugin for intelligently adding Python imports.

Will be able to correctly handle:

* PEP8-style import formatting::

    import sys

    import fish

    from mypackage import foo

    from .local import thing

* Your project's preferred import style::

    m.CharField<c-f>
        - from django import models as m
        - from myproject import models as m

    WidgetFac<c-f>
        - from myproject.widgets import WidgetFactory

* No Python code will be executed while searching for imports. They will be
  discovered by:

    * Searching open buffers
    * Tags files
    * A custom list of preferred imports
