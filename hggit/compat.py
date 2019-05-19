from mercurial import (
    context,
    templatekw,
    ui,
    url,
    util as hgutil,
)

try:
    from mercurial import vfs as vfsmod
    hgvfs = vfsmod.vfs
except ImportError:
    # vfsmod was extracted in hg 4.2
    from mercurial import scmutil
    hgvfs = scmutil.vfs

try:
    from mercurial.utils import procutil, stringutil
    sshargs = procutil.sshargs
    shellquote = procutil.shellquote
    quotecommand = procutil.quotecommand
    binary = stringutil.binary
except ImportError:
    # these were moved in 4.6
    sshargs = hgutil.sshargs
    shellquote = hgutil.shellquote
    quotecommand = hgutil.quotecommand
    binary = hgutil.binary


def gitvfs(repo):
    """return a vfs suitable to read git related data"""
    # Mercurial >= 3.3:  repo.shared()
    if repo.sharedpath != repo.path:
        return hgvfs(repo.sharedpath)
    else:
        return repo.vfs


def passwordmgr(ui):
    try:
        realm = hgutil.urlreq.httppasswordmgrwithdefaultrealm()
        return url.passwordmgr(ui, realm)
    except (TypeError, AttributeError):
        # compat with hg < 3.9
        return url.passwordmgr(ui)

# hg 4.3 - osutil moved, but mercurial.util re-exports listdir
if hgutil.safehasattr(hgutil, 'listdir'):
    listdir = hgutil.listdir
else:
    from mercurial import osutil
    listdir = osutil.listdir


def memfilectx(repo, changectx, path, data, islink=False,
               isexec=False, copysource=None):
    # Different versions of mercurial have different parameters to
    # memfilectx.  Try them from newest to oldest.
    parameters_to_try = (
        ((repo, changectx, path, data), { 'copysource': copysource }), # hg >= 5.0
        ((repo, changectx, path, data), { 'copied': copysource }),     # hg 4.5 - 4.9.1
        ((repo, path, data),            { 'copied': copysource }),     # hg 3.1 - 4.4.2
    )
    for (args, kwargs) in parameters_to_try:
        try:
            return context.memfilectx(*args,
                                      islink=islink,
                                      isexec=isexec,
                                      **kwargs)
        except TypeError as ex:
            last_ex = ex
    raise last_ex


CONFIG_DEFAULTS = {
    'git': {
        'authors': None,
        'blockdotgit': True,
        'blockdothg': True,
        'branch_bookmark_suffix': None,
        'debugextrainmessage': False,   # test only -- do not document this!
        'findcopiesharder': False,
        'intree': None,
        'mindate': None,
        'public': list,
        'renamelimit': 400,
        'similarity': 0,
    },
    'hggit': {
        'mapsavefrequency': 0,
        'usephases': False,
    }
}

hasconfigitems = False


def registerconfigs(configitem):
    global hasconfigitems
    hasconfigitems = True
    for section, items in CONFIG_DEFAULTS.iteritems():
        for item, default in items.iteritems():
            configitem(section, item, default=default)


def config(ui, subtype, section, item):
    if subtype == 'string':
        subtype = ''
    getconfig = getattr(ui, 'config' + subtype)
    if hasconfigitems:
        return getconfig(section, item)
    return getconfig(section, item, CONFIG_DEFAULTS[section][item])


class templatekeyword(object):
    def __init__(self):
        self._table = {}

    def __call__(self, name):
        def decorate(func):
            templatekw.keywords.update({name: func})
            return func
        return decorate


class progress(object):
    '''Simplified implementation of mercurial.scmutil.progress for
    compatibility with hg < 4.7'''
    def __init__(self, ui, _updatebar, topic, unit="", total=None):
        self.ui = ui
        self.pos = 0
        self.topic = topic
        self.unit = unit
        self.total = total

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.complete()

    def _updatebar(self, item=""):
        self.ui.progress(self.topic, self.pos, item, self.unit, self.total)

    def update(self, pos, item="", total=None):
        self.pos = pos
        if total is not None:
            self.total = total
        self._updatebar(item)

    def increment(self, step=1, item="", total=None):
        self.update(self.pos + step, item, total)

    def complete(self):
        self.unit = ""
        self.total = None
        self.update(None)


if hgutil.safehasattr(ui.ui, 'makeprogress'):
    def makeprogress(ui, topic, unit="", total=None):
        return ui.makeprogress(topic, unit, total)
else:
    def makeprogress(ui, topic, unit="", total=None):
        return progress(ui, None, topic, unit, total)
