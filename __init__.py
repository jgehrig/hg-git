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

from mercurial import commands
from mercurial import hg
from mercurial.i18n import _
from git_handler import GitHandler

# support for `hg clone git://github.com/defunkt/facebox.git`
# also hg clone git+ssh://git@github.com/schacon/simplegit.git
import gitrepo, hgrepo
hg.schemes['git'] = gitrepo
hg.schemes['git+ssh'] = gitrepo
hg.schemes['file'] = hgrepo

def gclone(ui, git_url, hg_repo_path=None):
    # determine new repo name
    if not hg_repo_path:
        hg_repo_path = hg.defaultdest(git_url)
        if hg_repo_path.endswith('.git'):
            hg_repo_path = hg_repo_path[:-4]
        hg_repo_path += '-hg'
    dest_repo = hg.repository(ui, hg_repo_path, create=True)

    print dest_repo

    # fetch the initial git data
    git = GitHandler(dest_repo, ui)
    git.remote_add('origin', git_url)
    git.fetch('origin')
    
    # checkout the tip
    node = git.remote_head('origin')
    hg.update(dest_repo, node)

def gpush(ui, repo, remote_name='origin', branch=None):
    git = GitHandler(repo, ui)
    import cProfile, pstats
    import lsprofcalltree
    prof = cProfile.Profile()
    prof = prof.runctx("git.push(remote_name)", globals(), locals())
    stats = pstats.Stats(prof)
    k = lsprofcalltree.KCacheGrind(prof)
    data = open('/tmp/prof.kgrind', 'w+')
    k.output(data)
    data.close()
    stats.sort_stats("cumulative")  # Or cumulative
    stats.print_stats(80)  # 80 = how many to print
    # The rest is optional.
    #stats.print_callees()
    #stats.print_callers()

def gimport(ui, repo, remote_name=None):
    git = GitHandler(repo, ui)
    git.import_commits(remote_name)

def gexport(ui, repo):
    git = GitHandler(repo, ui)
    git.export_commits()

def gremote(ui, repo, *args):
    git = GitHandler(repo, ui)

    if len(args) == 0:
        git.remote_list()
    elif len(args) < 2:
        repo.ui.warn(_("must supply an action and a remote\n"))
    else:
        verb = args[0]
        nick = args[1]

        if verb == 'add':
            if len(args) == 3:
                git.remote_add(nick, args[2])
            else:
                repo.ui.warn(_("must supply a url to add as a remote\n"))
        elif verb == 'rm':
            git.remote_remove(nick)
        elif verb == 'show':
            git.remote_show(nick)
        else:
            repo.ui.warn(_("unrecognized command to gremote\n"))

def gclear(ui, repo):
    repo.ui.status(_("clearing out the git cache data\n"))
    git = GitHandler(repo, ui)
    git.clear()

def gfetch(ui, repo, remote_name='origin'):
    repo.ui.status(_("pulling from git url\n"))
    git = GitHandler(repo, ui)
    git.fetch(remote_name)
    
commands.norepo += " gclone"
cmdtable = {
  "gclone":
      (gclone, [],
       _('Clone a git repository into an hg repository.'),
       ),
  "gpush":
        (gpush, [], _('hg gpush remote')),
  "gimport":
        (gimport, [], _('hg gimport')),
  "gexport":
        (gexport, [], _('hg gexport')),
  "gfetch":
        (gfetch, [],
        #[('m', 'merge', None, _('merge automatically'))],
        _('hg gfetch remote')),
  "gremote":
      (gremote, [], _('hg gremote add remote (url)')),
  "gclear":
      (gclear, [], _('Clears out the Git cached data')),
}    
