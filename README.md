Hg-Git Mercurial Plugin
=======================

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
system.  The only dependencies are Mercurial and Dulwich.  The plugin
is known to work on Hg versions 1.3 through 1.5 and requires at least
Dulwich 0.6.0.

Usage
=====

You can clone a Git repository from Hg by running `hg clone [url]`.  For
example, if you were to run

    $ hg clone git://github.com/schacon/hg-git.git

hg-git would clone the repository down into the directory 'munger.git', then
convert it to an Hg repository for you.

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

If you are starting from an existing Hg repository, you have to setup
a Git repository somewhere that you have push access to, add it as
default path or default-push path in your .hg/hgrc and then run `hg
push` from within your project.  For example:

    $ cd hg-git # (an Hg repository)
    $ # edit .hg/hgrc and add the target git url in the paths section
    $ hg push

This will convert all your Hg data into Git objects and push them up to the Git server.

Now that you have an Hg repository that can push/pull to/from a Git
repository, you can fetch updates with `hg pull`.

    $ hg pull

That will pull down any commits that have been pushed to the server in
the meantime and give you a new head that you can merge in.

Hg-Git can also be used to convert a Mercurial repository to Git.  As
Dulwich doesn't support local repositories yet, the easiest way is to
setup up a local SSH server.  Then use the following commands to
convert the repository (it assumes your running this in $HOME).

    $ mkdir git-repo; cd git-repo; git init; cd ..
    $ cd hg-repo
    $ hg bookmarks hg
    $ hg push git+ssh://localhost:git-repo

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

gclear
------

TODO

gimport
-------

TODO

gexport
-------

TODO

git-cleanup
-----------

TODO

Hg Bookmarks Integration
========================

If you have the bookmarks extension enabled, Hg-Git will use it. It
will push your bookmarks up to the Git server as branches and will
pull Git branches down and set them up as bookmarks.

Installing
==========

Clone this repository somewhere and make the 'extensions' section in
your `~/.hgrc` file look something like this:

    [extensions]
    hgext.bookmarks =
    hggit = [path-to]/hg-git/hggit

That will enable the Hg-Git extension for you.  The bookmarks section
is not compulsory, but it makes some things a bit nicer for you.

Configuration
=============

git.intree
----------

hg-git keeps a git repository clone for reading and updating. By default, the
git clone is the subdirectory `git` in your local Mercurial repository. If you
would like this git clone to be at the same level of your Mercurial repository
instead (named `.git`), add the following to your `hgrc`:

    [git]
    intree = True

git.authors
-----------

Git uses a strict convention for "author names" when representing changesets,
using the form `[realname] [email address]`.   Mercurial encourages this
convention as well but is not as strict, so it's not uncommon for a Mercurial
repo to have authors listed as simple usernames.   hg-git by default will 
translate such names using the email address `none@none`, which then shows up
unpleasantly on GitHub as "illegal email address".

The `git.authors` option provides for an "authors translation file" that will 
be used during outgoing transfers from mercurial to git only, by modifying 
`hgrc` as such:

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
