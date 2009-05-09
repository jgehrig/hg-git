# repo.py -- For dealing wih git repositories.
# Copyright (C) 2007 James Westby <jw+debian@jameswestby.net>
# Copyright (C) 2008-2009 Jelmer Vernooij <jelmer@samba.org>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your option) any later version of 
# the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.

"""Repository access."""

import os
import stat
import zlib

from errors import (
    MissingCommitError,
    NotBlobError,
    NotCommitError,
    NotGitRepository,
    NotTreeError,
    )
from object_store import DiskObjectStore
from objects import (
    Blob,
    Commit,
    ShaFile,
    Tag,
    Tree,
    hex_to_sha
    )
from misc import make_sha

OBJECTDIR = 'objects'
SYMREF = 'ref: '
REFSDIR = 'refs'
INDEX_FILENAME = "index"

class Tags(object):
    """Tags container."""

    def __init__(self, tagdir, tags):
        self.tagdir = tagdir
        self.tags = tags

    def __getitem__(self, name):
        return self.tags[name]
    
    def __setitem__(self, name, ref):
        self.tags[name] = ref
        f = open(os.path.join(self.tagdir, name), 'wb')
        try:
            f.write("%s\n" % ref)
        finally:
            f.close()

    def __len__(self):
        return len(self.tags)

    def iteritems(self):
        for k in self.tags:
            yield k, self[k]


def read_packed_refs(f):
    """Read a packed refs file.

    Yields tuples with ref names and SHA1s.

    :param f: file-like object to read from
    """
    l = f.readline()
    for l in f.readlines():
        if l[0] == "#":
            # Comment
            continue
        if l[0] == "^":
            # FIXME: Return somehow
            continue
        yield tuple(l.rstrip("\n").split(" ", 2))


class Repo(object):
    """A local git repository."""

    ref_locs = ['', REFSDIR, 'refs/tags', 'refs/heads', 'refs/remotes']

    def __init__(self, root):
        if os.path.isdir(os.path.join(root, ".git", OBJECTDIR)):
            self.bare = False
            self._controldir = os.path.join(root, ".git")
        elif os.path.isdir(os.path.join(root, OBJECTDIR)):
            self.bare = True
            self._controldir = root
        else:
            raise NotGitRepository(root)
        self.path = root
        self.tags = Tags(self.tagdir(), self.get_tags())
        self._object_store = None

    def controldir(self):
        """Return the path of the control directory."""
        return self._controldir

    def index_path(self):
        """Return path to the index file."""
        return os.path.join(self.controldir(), INDEX_FILENAME)

    def open_index(self):
        """Open the index for this repository."""
        from index import Index
        return Index(self.index_path())

    def has_index(self):
        """Check if an index is present."""
        return os.path.exists(self.index_path())

    def find_missing_objects(self, determine_wants, graph_walker, progress):
        """Find the missing objects required for a set of revisions.

        :param determine_wants: Function that takes a dictionary with heads 
            and returns the list of heads to fetch.
        :param graph_walker: Object that can iterate over the list of revisions 
            to fetch and has an "ack" method that will be called to acknowledge 
            that a revision is present.
        :param progress: Simple progress function that will be called with 
            updated progress strings.
        :return: Iterator over (sha, path) pairs.
        """
        wants = determine_wants(self.get_refs())
        return self.object_store.find_missing_objects(wants, 
                graph_walker, progress)

    def fetch_objects(self, determine_wants, graph_walker, progress):
        """Fetch the missing objects required for a set of revisions.

        :param determine_wants: Function that takes a dictionary with heads 
            and returns the list of heads to fetch.
        :param graph_walker: Object that can iterate over the list of revisions 
            to fetch and has an "ack" method that will be called to acknowledge 
            that a revision is present.
        :param progress: Simple progress function that will be called with 
            updated progress strings.
        :return: tuple with number of objects, iterator over objects
        """
        return self.object_store.iter_shas(
            self.find_missing_objects(determine_wants, graph_walker, progress))

    def object_dir(self):
        """Return path of the object directory."""
        return os.path.join(self.controldir(), OBJECTDIR)

    @property
    def object_store(self):
        if self._object_store is None:
            self._object_store = DiskObjectStore(self.object_dir())
        return self._object_store

    def pack_dir(self):
        return os.path.join(self.object_dir(), PACKDIR)

    def _get_ref(self, file):
        f = open(file, 'rb')
        try:
            contents = f.read()
            if contents.startswith(SYMREF):
                ref = contents[len(SYMREF):]
                if ref[-1] == '\n':
                    ref = ref[:-1]
                return self.ref(ref)
            assert len(contents) == 41, 'Invalid ref in %s' % file
            return contents[:-1]
        finally:
            f.close()

    def ref(self, name):
        """Return the SHA1 a ref is pointing to."""
        for dir in self.ref_locs:
            file = os.path.join(self.controldir(), dir, name)
            if os.path.exists(file):
                return self._get_ref(file)
        packed_refs = self.get_packed_refs()
        if name in packed_refs:
            return packed_refs[name]

    def get_refs(self):
        """Get dictionary with all refs."""
        ret = {}
        if self.head():
            ret['HEAD'] = self.head()
        for dir in ["refs/heads", "refs/tags"]:
            for name in os.listdir(os.path.join(self.controldir(), dir)):
                path = os.path.join(self.controldir(), dir, name)
                if os.path.isfile(path):
                    ret["/".join([dir, name])] = self._get_ref(path)
        ret.update(self.get_packed_refs())
        return ret

    def get_packed_refs(self):
        """Get contents of the packed-refs file.

        :return: Dictionary mapping ref names to SHA1s

        :note: Will return an empty dictionary when no packed-refs file is 
            present.
        """
        path = os.path.join(self.controldir(), 'packed-refs')
        if not os.path.exists(path):
            return {}
        ret = {}
        f = open(path, 'r')
        try:
            for entry in read_packed_refs(f):
                ret[entry[1]] = entry[0]
            return ret
        finally:
            f.close()

    # takes refs passed from remote and renames them
    def set_remote_refs(self, refs, remote_name):
        keys = refs.keys()
        if not keys:
            return None
        for k in keys[0:]:
            ref_name = k
            parts = k.split('/')
            if parts[0] == 'refs': # strip off 'refs/heads'
                if parts[1] == 'heads':
                    ref_name = "/".join([v for v in parts[2:]])
                    self.set_ref('refs/remotes/' + remote_name + '/' + ref_name, refs[k])
                if parts[1] == 'tags':
                    ref_name = "/".join([v for v in parts[2:]])
                    self.set_ref('refs/tags/' + ref_name, refs[k])

    def set_refs(self, refs):
        keys = refs.keys()
        if not keys:
            return None
        for k in keys[0:]:
            self.set_ref(k, refs[k])


    def set_ref(self, name, value):
        file = os.path.join(self.controldir(), name)
        dirpath = os.path.dirname(file)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        f = open(file, 'w')
        try:
            f.write(value+"\n")
        finally:
            f.close()

    def remove_ref(self, name):
        """Remove a ref.

        :param name: Name of the ref
        """
        file = os.path.join(self.controldir(), name)
        if os.path.exists(file):
            os.remove(file)

    def tagdir(self):
        """Tag directory."""
        return os.path.join(self.controldir(), REFSDIR, 'tags')

    def get_tags(self):
        ret = {}
        for root, dirs, files in os.walk(self.tagdir()):
            for name in files:
                ret[name] = self._get_ref(os.path.join(root, name))
        return ret

    def heads(self):
        ret = {}
        for root, dirs, files in os.walk(os.path.join(self.controldir(), 'refs', 'heads')):
            for name in files:
                ret[name] = self._get_ref(os.path.join(root, name))
        return ret

    def remote_refs(self, remote_name):
        ret = {}
        for root, dirs, files in os.walk(os.path.join(self.controldir(), 'refs', 'remotes', remote_name)):
            for name in files:
                ret[name] = self._get_ref(os.path.join(root, name))
        return ret

    def head(self):
        return self.ref('HEAD')

    def _get_object(self, sha, cls):
        assert len(sha) in (20, 40)
        ret = self.get_object(sha)
        if ret._type != cls._type:
            if cls is Commit:
                raise NotCommitError(ret)
            elif cls is Blob:
                raise NotBlobError(ret)
            elif cls is Tree:
                raise NotTreeError(ret)
            else:
                raise Exception("Type invalid: %r != %r" % (ret._type, cls._type))
        return ret

    def get_object(self, sha):
        return self.object_store[sha]

    def get_parents(self, sha):
        return self.commit(sha).parents

    def commit(self, sha):
        return self._get_object(sha, Commit)

    # we call this a lot on import, so we're caching it a bit
    already_parsed_trees = {}
    def tree(self, sha):
        if sha in self.already_parsed_trees:
            return self.already_parsed_trees[sha]
        tree = self._get_object(sha, Tree)
        self.already_parsed_trees[sha] = tree
        return tree

    def tag(self, sha):
        return self._get_object(sha, Tag)

    def get_blob(self, sha):
        return self._get_object(sha, Blob)

    def write_blob(self, contents):
        sha = self.write_object('blob', contents)
        return sha

    # takes a hash of the commit data
    # {'author': 'Scott Chacon <schacon@gmail.com> 1240868341 -0700'
    #  'committer': 'Scott Chacon <schacon@gmail.com> 1240868341 -0700',
    #  'message': 'test commit two\n\n--HG--\nbranch : default\n',
    #  'tree': '36a63c12d097b487e4ed634c34d2f80870e64f68',
    #  'parents': ['ca82a6dff817ec66f44342007202690a93763949'],
    #  }
    def write_commit_hash(self, commit):
        if not 'committer' in commit:
            commit['committer'] = commit['author']
        commit_data = ''
        commit_data += 'tree ' + commit['tree'] + "\n"
        for parent in commit['parents']:
            commit_data += 'parent ' + parent + "\n"
        commit_data += 'author ' + commit['author'] + "\n"
        commit_data += 'committer ' + commit['committer'] + "\n"
        commit_data += "\n"
        commit_data += commit['message']
        sha = self.write_object('commit', commit_data)
        return sha

    # takes a multidim array
    # [ ['blob', 'filename', SHA, exec_flag, link_flag],
    #   ['tree', 'dirname/', SHA]
    #   ...
    # ]
    def write_tree_array(self, tree_array):
        tree_array.sort(key=lambda x: x[1])
        tree_data = ''
        for entry in tree_array:
            rawsha = hex_to_sha(entry[2])
            if entry[0] == 'tree':
                tree_name = entry[1][0:-1]
                tree_data += "%s %s\0%s" % ('040000', tree_name, rawsha)
            if entry[0] == 'blob':
                # TODO : respect the modes
                tree_data += "%s %s\0%s" % ('100644', entry[1], rawsha)
        sha = self.write_object('tree', tree_data)
        return sha

    def write_object(self, obj_type, obj_contents):
        raw_data = "%s %d\0%s" % (obj_type, len(obj_contents), obj_contents)
        git_sha = make_sha(raw_data)
        git_hex_sha = git_sha.hexdigest()
        if not git_hex_sha in self.object_store:
            object_dir = os.path.join(self.path, OBJECTDIR, git_hex_sha[0:2])
            if not os.path.exists(object_dir):
                os.mkdir(object_dir)
            object_path = os.path.join(object_dir, git_hex_sha[2:])
            data = zlib.compress(raw_data)
            open(object_path, 'w').write(data) # write the object
        return git_hex_sha

    # takes a commit object and a file path
    # returns the contents of that file at that commit
    def get_file(self, commit, f):
        otree = self.tree(commit.tree)
        parts = f.split('/')
        for part in parts:
            (mode, sha) = otree.entry(part)
            obj = self.get_object(sha)
            if isinstance (obj, Blob):
                return (mode, sha, obj._text)
            elif isinstance(obj, Tree):
                otree = obj

    # takes a commit and returns an array of the files that were changed
    # between that commit and it's parents
    def get_files_changed(self, commit):
        def filenames(basetree, comptree, prefix):
            basefiles = set()
            changes = list()
            csha = None
            ctree = None
            cmode = None
            if basetree:
                for (bmode, bname, bsha) in basetree.entries():
                    if bmode == 57344: # TODO : properly handle submodules
                        continue
                    basefiles.add(bname)
                    bobj = self.get_object(bsha)
                    if comptree:
                        (cmode, csha) = comptree.entry(bname)
                    if not ((csha == bsha) and (cmode == bmode)):
                        if isinstance (bobj, Blob):
                            changes.append (prefix + bname)
                        elif isinstance(bobj, Tree):
                            if csha:
                                ctree = self.get_object(csha)
                            changes.extend(filenames(bobj,
                                                     ctree,
                                                     prefix + bname + '/'))

            # handle removals
            if comptree:
                for (bmode, bname, bsha, ) in comptree.entries():
                    if bmode == 57344: # TODO: hande submodles
                        continue
                    if bname not in basefiles:
                        bobj = self.get_object(bsha)
                        if isinstance(bobj, Blob):
                            changes.append(prefix + bname)
                        elif isinstance(bobj, Tree):
                            changes.extend(filenames(None, bobj,
                                                     prefix + bname + '/'))
            return changes

        all_changes = list()
        otree = self.tree(commit.tree)
        if len(commit.parents) == 0:
            all_changes = filenames(otree, None, '')
        for parent in commit.parents:
            pcommit = self.commit(parent)
            ptree = self.tree(pcommit.tree)
            all_changes.extend(filenames(otree, ptree, ''))

        return all_changes

    def revision_history(self, head):
        """Returns a list of the commits reachable from head.

        Returns a list of commit objects. the first of which will be the commit
        of head, then following theat will be the parents.

        Raises NotCommitError if any no commits are referenced, including if the
        head parameter isn't the sha of a commit.

        XXX: work out how to handle merges.
        """
        # We build the list backwards, as parents are more likely to be older
        # than children
        pending_commits = [head]
        history = []
        while pending_commits != []:
            head = pending_commits.pop(0)
            try:
                commit = self.commit(head)
            except KeyError:
                raise MissingCommitError(head)
            if commit in history:
                continue
            i = 0
            for known_commit in history:
                if known_commit.commit_time > commit.commit_time:
                    break
                i += 1
            history.insert(i, commit)
            parents = commit.parents
            pending_commits += parents
        history.reverse()
        return history

    def __repr__(self):
        return "<Repo at %r>" % self.path

    @classmethod
    def init(cls, path, mkdir=True):
        controldir = os.path.join(path, ".git")
        os.mkdir(controldir)
        cls.init_bare(controldir)

    @classmethod
    def init_bare(cls, path, mkdir=True):
        for d in [[OBJECTDIR], 
                  [OBJECTDIR, "info"], 
                  [OBJECTDIR, "pack"],
                  ["branches"],
                  [REFSDIR],
                  ["refs", "tags"],
                  ["refs", "heads"],
                  ["hooks"],
                  ["info"]]:
            os.mkdir(os.path.join(path, *d))
        open(os.path.join(path, 'HEAD'), 'w').write("ref: refs/heads/master\n")
        open(os.path.join(path, 'description'), 'w').write("Unnamed repository")
        open(os.path.join(path, 'info', 'excludes'), 'w').write("")

    create = init_bare

