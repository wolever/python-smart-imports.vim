" python-smart-imports.vim - intelligently adds imports to Python files.
" 
" Maintainer: David Wolever <david@wolever.net>
" Version: 0.1
" Licence: VIM licence

if exists("g:did_python_smart_imports")
    finish " only load once
endif
let g:did_python_smart_imports = 1

if !has('python')
    echoerr "Error: the python-smart-imports.vim plugin requires Vim to be compiled with +python"
    finish
endif

python << EOF
import vim
import os.path
import sys

if sys.version_info[:2] < (2, 6):
    raise AssertionError('Vim must be compiled with Python 2.6 or higher; you have ' + sys.version)

from smart_imports import PythonSmartImporter

python_smart_imports = PythonSmartImporter()
EOF
