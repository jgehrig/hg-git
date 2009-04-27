# git.py - git server bridge
#
# Copyright 2008 Scott Chacon <schacon at gmail dot com>
#   also some code (and help) borrowed from durin42  
#
# This software may be used and distributed according to the terms
# of the GNU General Public License, incorporated herein by reference.

'''push and pull from a Git server

This extension lets you communicate (push and pull) with a Git server.
This way you can use Git hosting for your project or collaborate with a 
project that is in Git.  A bridger of worlds, this plugin be.

'''

# just importing every damn thing because i don't know python that well
# and I have no idea what I actually need
from mercurial import util, repair, merge, cmdutil, commands, hg, url
from mercurial import extensions, ancestor
from mercurial.commands import templateopts
from mercurial.node import nullrev, nullid, short
from mercurial.i18n import _
import os, errno, sys
import subprocess
import dulwich
from git_handler import GitHandler

def gclone(ui, git_url, hg_repo_path=None):
    # determine new repo name
    if not hg_repo_path:
        hg_repo_path = hg.defaultdest(git_url)
        if hg_repo_path.endswith('.git'):
            hg_repo_path = hg_repo_path[:-4]
        hg_repo_path += '-hg'
    dest_repo = hg.repository(ui, hg_repo_path, create=True)

    # fetch the initial git data
    git = GitHandler(dest_repo, ui)
    git.remote_add('origin', git_url)
    git.fetch('origin')
    
    # checkout the tip
    node = git.remote_head('origin')
    hg.update(dest_repo, node)

def gpush(ui, repo, remote_name='origin'):
    git = GitHandler(repo, ui)
    git.push(remote_name)
    
def gpull(ui, repo):
    dest_repo.ui.status(_("pulling from git url\n"))
           
commands.norepo += " gclone"
cmdtable = {
  "gclone":
      (gclone,
       [ #('A', 'authors', '', 'username mapping filename'),
       ],
       'Clone a git repository into an hg repository.',
       ),
  "gpush":
        (gpush, [], _('hg gpush remote')),
  "gpull":
        (gpull, 
        [('m', 'merge', None, _('merge automatically'))],
        _('hg gpull [--merge] remote')),
}    
