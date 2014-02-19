import os

from mercurial.node import bin
from mercurial import util

from git_handler import GitHandler
from gitrepo import gitrepo


def generate_repo_subclass(baseclass):
    class hgrepo(baseclass):
        def pull(self, remote, heads=None, force=False):
            if isinstance(remote, gitrepo):
                return self.githandler.fetch(remote.path, heads)
            else: #pragma: no cover
                return super(hgrepo, self).pull(remote, heads, force)

        # TODO figure out something useful to do with the newbranch param
        def push(self, remote, force=False, revs=None, newbranch=False):
            if isinstance(remote, gitrepo):
                return self.githandler.push(remote.path, revs, force)
            else: #pragma: no cover
                return super(hgrepo, self).push(remote, force, revs, newbranch)

        def findoutgoing(self, remote, base=None, heads=None, force=False):
            if isinstance(remote, gitrepo):
                base, heads = self.githandler.get_refs(remote.path)
                out, h = super(hgrepo, self).findoutgoing(remote, base, heads, force)
                return out
            else: #pragma: no cover
                return super(hgrepo, self).findoutgoing(remote, base, heads, force)

        def _findtags(self):
            (tags, tagtypes) = super(hgrepo, self)._findtags()

            for tag, rev in self.githandler.tags.iteritems():
                tags[tag] = bin(rev)
                tagtypes[tag] = 'git'

            tags.update(self.gitrefs())
            return (tags, tagtypes)

        @util.propertycache
        def githandler(self):
            '''get the GitHandler for an hg repo

            This only makes sense if the repo talks to at least one git remote.
            '''
            return GitHandler(self, self.ui)

        def gitrefs(self):
            tagfile = self.join(os.path.join('git-remote-refs'))
            if os.path.exists(tagfile):
                tf = open(tagfile, 'rb')
                tagdata = tf.read().split('\n')
                td = [line.split(' ', 1) for line in tagdata if line]
                return dict([(name, bin(sha)) for sha, name in td])
            return {}

        def tags(self):
            if hasattr(self, 'tagscache') and self.tagscache:
                # Mercurial 1.4 and earlier.
                return self.tagscache
            elif hasattr(self, '_tags') and self._tags:
                # Mercurial 1.5 and later.
                return self._tags

            tagscache = super(hgrepo, self).tags()
            tagscache.update(self.gitrefs())
            for tag, rev in self.githandler.tags.iteritems():
                if tag in tagscache:
                    continue

                tagscache[tag] = bin(rev)
                if hasattr(self, '_tagstypecache'):
                    # Only present in Mercurial 1.3 and earlier.
                    self._tagstypecache[tag] = 'git'

            return tagscache

    return hgrepo
