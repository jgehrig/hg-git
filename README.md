Hg-Git Mercurial Plugin
=======================

* Homepage: https://hg-git.github.io/
* https://bitbucket.org/durin42/hg-git (primary)
* https://github.com/schacon/hg-git (mirror)

This is the Hg-Git plugin for Mercurial, adding the ability to push
and pull to/from a Git server repository from Hg.  This means you can
collaborate on Git based projects from Hg, or use a Git server as a
collaboration point for a team with developers using both Git and Hg.

The Hg-Git plugin can convert commits/changesets losslessly from one
system to another, so you can push via an Hg repository and another Hg
client can pull it and their changeset node ids will be identical -
Mercurial data does not get lost in translation.  It is intended that
Hg users may wish to use this to collaborate even if no Git users are
involved in the project, and it may even provide some advantages if
you're using Bookmarks (see below).

Dependencies
============

This plugin is implemented entirely in Python - there are no Git
binary dependencies, you do not need to have Git installed on your
system.  The only dependencies are Mercurial and Dulwich. See the
Makefile for information about which versions of Mercurial are
known to work, and setup.py for which versions of Dulwich are required.

Installing
==========

Clone this repository somewhere and make the 'extensions' section in
your `~/.hgrc` file look something like this:

    [extensions]
    hggit = [path-to]/hg-git/hggit

That will enable the Hg-Git extension for you.

See the Makefile for a list of compatible Mercurial versions.

Contributing
============

Patches preferred via e-mail to the [hg-git Google Group][1],
[hg-git@googlegroups.com][2]. We use a variant of Mercurial's own
contribution system. https://www.mercurial-scm.org/wiki/ContributingChanges
contains their full guidelines. See the [CONTRIBUTING](CONTRIBUTING) file
in the source for more details.

[1]: https://groups.google.com/forum/#!forum/hg-git
[2]: mailto:hg-git@googlegroups.com

Usage
=====

You can clone a Git repository from Hg by running `hg clone <url> [dest]`.  For
example, if you were to run

    $ hg clone git://github.com/schacon/hg-git.git

Hg-Git would clone the repository and convert it to an Hg repository
for you.

If you want to clone a github repository for later pushing (or any
other repository you access via ssh), you need to convert the ssh url
to a format with an explicit protocol prefix. For example, the git url
with push access

    git@github.com:schacon/hg-git.git

would read

    git+ssh://git@github.com/schacon/hg-git.git

(Mind the switch from colon to slash after the host!)

Your clone command would thus look like this:

    $ hg clone git+ssh://git@github.com/schacon/hg-git.git

If you are starting from an existing Hg repository, you have to set up
a Git repository somewhere that you have push access to, add a path entry
for it in your .hg/hgrc file, and then run `hg push [name]` from within
your repository.  For example:

    $ cd hg-git # (an Hg repository)
    $ # edit .hg/hgrc and add the target git url in the paths section
    $ hg push

This will convert all your Hg data into Git objects and push them to the Git server.

Now that you have an Hg repository that can push/pull to/from a Git
repository, you can fetch updates with `hg pull`.

    $ hg pull

That will pull down any commits that have been pushed to the server in
the meantime and give you a new head that you can merge in.

Hg-Git pushes your bookmarks up to the Git server as branches and will
pull Git branches down and set them up as bookmarks.

Hg-Git can also be used to convert a Mercurial repository to Git.  You can use
a local repository or a remote repository accessed via SSH, HTTP or HTTPS.  Use
the following commands to convert the repository (it assumes you're running this
in $HOME).

    $ mkdir git-repo; cd git-repo; git init; cd ..
    $ cd hg-repo
    $ hg bookmarks hg
    $ hg push ../git-repo

The hg bookmark is necessary to prevent problems as otherwise hg-git
pushes to the currently checked out branch confusing Git. This will
create a branch named hg in the Git repository. To get the changes in
master use the following command (only necessary in the first run,
later just use git merge or rebase).

    $ cd git-repo
    $ git checkout -b master hg

To import new changesets into the Git repository just rerun the hg
push command and then use git merge or git rebase in your Git
repository.

Commands
========

See `hg help -e hggit`.

Configuration
=============

git.authors
-----------

Git uses a strict convention for "author names" when representing changesets,
using the form `[realname] [email address]`. Mercurial encourages this
convention as well but is not as strict, so it's not uncommon for a Mercurial
repo to have authors listed as, for example, simple usernames. hg-git by default
will attempt to translate Mercurial usernames using the following rules:

* If the Mercurial username fits the pattern `NAME <EMAIL>`, the git name will be
  set to NAME and the email to EMAIL.
* If the Mercurial username looks like an email (if it contains an `@`), the
  git name and email will both be set to that email.
* If the Mercurial username consists of only a name, the email will be set to `none@none`.
* Illegal characters (stray `<`s or `>`s) will be stripped out, and for `NAME <EMAIL>`
  usernames, any content after the right-bracket (for example, a second `>`) will be
  turned into a url-encoded sigil like `ext:(%3E)` in the git author name.

Since these default behaviors may not be what you want (`none@none`, for example,
shows up unpleasantly on Github as "illegal email address"), the `git.authors`
option provides for an "authors translation file" that will be used during outgoing
transfers from mercurial to git only, by modifying `hgrc` as such:

    [git]
    authors = authors.txt

Where `authors.txt` is the name of a text file containing author name translations,
one per each line, using the following format:

    johnny = John Smith <jsmith@foo.com>
    dougie = Doug Johnson <dougiej@bar.com>

Empty lines and lines starting with a "#" are ignored.

It should be noted that **this translation is on the hg->git side only**.  Changesets
coming from Git back to Mercurial will not translate back into hg usernames, so
it's best that the same username/email combination be used on both the hg and git sides;
the author file is mostly useful for translating legacy changesets.

git.blockdotgit
---------------

Blocks exporting revisions to Git that contain a directory named .git or any
letter-case variation thereof. This prevents creating repositories that newer
versions of Git and many Git hosting services block due to security
concerns. Defaults to True.

git.blockdothg
--------------

Blocks importing revisions from Git that contain a directory named .hg. Defaults
to True.

git.branch_bookmark_suffix
---------------------------

hg-git does not convert between Mercurial named branches and git branches as
the two are conceptually different; instead, it uses Mercurial bookmarks to
represent the concept of a git branch. Therefore, when translating an hg repo
over to git, you typically need to create bookmarks to mirror all the named
branches that you'd like to see transferred over to git. The major caveat with
this is that you can't use the same name for your bookmark as that of the
named branch, and furthermore there's no feasible way to rename a branch in
Mercurial. For the use case where one would like to transfer an hg repo over
to git, and maintain the same named branches as are present on the hg side,
the `branch_bookmark_suffix` might be all that's needed. This presents a
string "suffix" that will be recognized on each bookmark name, and stripped
off as the bookmark is translated to a git branch:

    [git]
    branch_bookmark_suffix=_bookmark

Above, if an hg repo had a named branch called `release_6_maintenance`, you could
then link it to a bookmark called `release_6_maintenance_bookmark`.   hg-git will then
strip off the `_bookmark` suffix from this bookmark name, and create a git branch
called `release_6_maintenance`.   When pulling back from git to hg, the `_bookmark`
suffix is then applied back, if and only if an hg named branch of that name exists.
E.g., when changes to the `release_6_maintenance` branch are checked into git, these
will be placed into the `release_6_maintenance_bookmark` bookmark on hg.  But if a
new branch called `release_7_maintenance` were pulled over to hg, and there was
not a `release_7_maintenance` named branch already, the bookmark will be named
`release_7_maintenance` with no usage of the suffix.

The `branch_bookmark_suffix` option is, like the `authors` option, intended for
migrating legacy hg named branches.   Going forward, an hg repo that is to
be linked with a git repo should only use bookmarks for named branching.

git.findcopiesharder
--------------------

Whether to consider unmodified files as copy sources. This is a very expensive
operation for large projects, so use it with caution. Similar to `git diff`'s
--find-copies-harder option.

git.intree
----------

hg-git keeps a git repository clone for reading and updating. By default, the
git clone is the subdirectory `git` in your local Mercurial repository. If you
would like this git clone to be at the same level of your Mercurial repository
instead (named `.git`), add the following to your `hgrc`:

    [git]
    intree = True

git.mindate
-----------

If set, branches where the latest commit's commit time is older than this will
not be imported. Accepts any date formats that Mercurial does -- see
`hg help dates` for more.

git.public
----------

A list of Git branches that should be considered "published", and therefore
converted to Mercurial in the 'public' phase. This is only used if
hggit.usephases is set.

git.renamelimit
---------------

The number of files to consider when performing the copy/rename detection.
Detection is disabled if the number of files modified in a commit is above the
limit. Detection is O(N^2) in the number of files modified, so be sure not to
set the limit too high. Similar to Git's `diff.renameLimit` config. The default
is "400", the same as Git.

git.similarity
--------------

Specify how similar files modified in a Git commit must be to be imported as
Mercurial renames or copies, as a percentage between "0" (disabled) and "100"
(files must be identical). For example, "90" means that a delete/add pair will
be imported as a rename if more than 90% of the file has stayed the same. The
default is "0" (disabled).

hggit.mapsavefrequency
----------------------

Controls how often the mapping between Git and Mercurial commit hashes gets
saved when importing or exporting changesets. Set this to a number greater than
0 to save the mapping after converting that many commits. This can help when the
conversion encounters an error partway through a large batch of
changes. Defaults to 0, so that the mapping is saved once at the end.

hggit.usephases
---------------

When converting Git revisions to Mercurial, place them in the 'public' phase as
appropriate. Namely, revisions that are reachable from the remote Git
repository's HEAD will be marked 'public'. For most repositories, this means the
remote 'master' will be converted as public. This speeds up some local Mercurial
operations including `hg shelve`.
