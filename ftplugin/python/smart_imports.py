import ast
import sys
import parser

parse_error = (parser.ParserError, IndentationError)

PY2_STDLIB_MODULES = set("""
    AL BaseHTTPServer Bastion CGIHTTPServer ColorPicker ConfigParser Cookie
    DEVICE DocXMLRPCServer EasyDialogs FL FrameWork GL HTMLParser MacOS
    MimeWriter MiniAEFrame Nav PixMapWrapper Queue SUNAUDIODEV ScrolledText
    SimpleHTTPServer SimpleXMLRPCServer SocketServer StringIO Tix Tkinter
    UserDict UserList UserString __builtin__ __future__ __main__ _winreg abc
    aepack aetools aetypes aifc al anydbm applesingle argparse array ast
    asynchat asyncore atexit audioop autoGIL base64 bdb binascii binhex bisect
    bsddb buildtools bz2 cPickle cProfile cStringIO calendar cd cfmfile cgi
    cgitb chunk cmath cmd code codecs codeop collections colorsys commands
    compileall contextlib cookielib copy copy_reg crypt csv ctypes datetime
    dbhash dbm decimal difflib dircache dis dl doctest dumbdbm dummy_thread
    dummy_threading errno exceptions fcntl filecmp fileinput findertools fl flp
    fm fnmatch formatter fpectl fpformat fractions ftplib functools
    future_builtins gc gdbm gensuitemodule getopt getpass gettext gl glob grp
    gzip hashlib heapq hmac htmlentitydefs htmllib httplib ic icopen imageop
    imaplib imgfile imghdr imp importlib imputil inspect io itertools jpeg json
    keyword lib2to3 linecache locale macerrors macostools macpath macresource
    mailbox mailcap marshal math md5 mhlib mimetools mimetypes mimify mmap
    modulefinder msilib msvcrt multifile mutex netrc new nis nntplib numbers
    operator optparse ossaudiodev parser pdb pickle pickletools pipes pkgutil
    platform plistlib popen2 poplib posix posixfile pprint profile pstats pty
    pwd py_compile pyclbr pydoc quopri random re readline repr resource rexec
    rfc822 rlcompleter robotparser runpy sched select sets sgmllib sha shelve
    shlex shutil signal site smtpd smtplib sndhdr socket spwd sqlite3 ssl stat
    statvfs string stringprep struct subprocess sunau sunaudiodev symbol
    symtable sys sysconfig syslog tabnanny tarfile telnetlib tempfile termios
    textwrap thread threading time timeit token tokenize trace traceback ttk
    tty turtle types unicodedata unittest urllib urllib2 urlparse user uu uuid
    videoreader warnings wave weakref webbrowser whichdb winsound xdrlib
    xmlrpclib zipfile zipimport zlib
""".split())
                         

class blackhole(object):
    write = flush = lambda *a, **k: None


class ImportVisitor(ast.NodeVisitor):
    def __init__(self, import_cls):
        self.Import = import_cls
        self.imports = []

    def visit_Import(self, node):
        for name in node.names:
            self.imports.append(self.Import.from_node(name.name, node, name))

    def visit_ImportFrom(self, node):
        for name in node.names:
            self.imports.append(self.Import.from_node(
                "%s.%s" %(node.module, name.name),
                node, name,
            ))


class Import(object):
    TYPE_STDLIB = "01-stdlib"
    TYPE_THIRDPARTY = "02-thirdparty"
    TYPE_PACKAGE = "03-package"
    TYPE_RELATIVE = "04-relative"
    stdlib_modules = PY2_STDLIB_MODULES

    def __init__(self, name, alias, lineno, is_toplevel):
        self.name = name
        self.alias = alias
        self.lineno = lineno
        self.is_toplevel = is_toplevel

    @classmethod
    def from_ast(cls, ast):
        visitor = ImportVisitor(cls)
        visitor.visit(ast)
        return visitor.imports

    @classmethod
    def from_node(cls, name, node, alias):
        prefix = "." * getattr(node, "level", 0)
        return cls(
            prefix + name,
            alias.asname,
            node.lineno,
            node.col_offset == 0,
        )

    @property
    def name_parts(self):
        return self.name.split(".")

    def get_type(self, fname):
        module = self.name_parts[0]
        if module in self.stdlib_modules:
            return self.TYPE_STDLIB


    def matches(self, name):
        if name == self.alias:
            return True
        if "." not in name:
            name = "." + name
        return self.name.endswith(name)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name, self.alias)


class PythonSmartImporter(object):
    def __init__(self, vim):
        self.vim = vim

    def parse_python_buf(self, buf):
        # Parse a buffer returning an AST or None if the buffer can't be
        # parsed. Stolen from pyflakes.vim.
        filename = buf.name

        contents = '\n'.join(buf) + '\n'

        vimenc = self.vim.eval('&encoding')
        if vimenc:
            contents = contents.decode(vimenc)

        old_stderr, sys.stderr = sys.stderr, blackhole()
        try:
            tree = ast.parse(contents, filename or '<unknown>')
        except parse_error:
            return None
        finally:
            sys.stderr = old_stderr

        return tree

    def get_buf_imports(self, buf):
        tree = self.parse_python_buf(buf)
        if tree is None:
            return []
        return Import.from_ast(tree)

    def search_for_import(self, name):
        for buf in self.vim.buffers:
            for impt in self.get_buf_imports(buf):
                if impt.matches(name):
                    yield impt

    def add_import_to_buf(self, impt, name, buf):
        buf_ast = self.parse_python_buf(buf)
        if buf_ast is None:
            return ("error", "Could not parse buffer")
        buf_imports = Import.from_ast(buf_ast)

        insert_target = None
        for buf_impt in buf_imports:
            if buf_impt == impt and buf_impt.is_toplevel:
                return ("warn", "%s is already imported on line %r" %(name, buf_impt.lineno))

