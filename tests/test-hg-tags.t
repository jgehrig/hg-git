Load commonly used test logic
  $ . "$TESTDIR/testutil"

  $ git init gitrepo
  Initialized empty Git repository in $TESTTMP/gitrepo/.git/
  $ cd gitrepo
  $ echo alpha > alpha
  $ git add alpha
  $ fn_git_commit -m "add alpha"
  $ git checkout -b not-master
  Switched to a new branch 'not-master'

  $ cd ..
  $ hg clone gitrepo hgrepo | grep -v '^updating'
  importing git objects into hg
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ cd hgrepo
  $ hg co master
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ fn_hg_tag alpha
  $ hg push
  pushing to $TESTTMP/gitrepo
  searching for changes
  adding objects
  added 1 commits with 1 trees and 1 blobs
  updating reference refs/heads/master
  adding reference refs/tags/alpha

  $ hg log --graph | egrep -v ': *(not-master|master)'
  @  changeset:   1:d529e9229f6d
  |  tag:         default/master
  |  tag:         tip
  |  user:        test
  |  date:        Mon Jan 01 00:00:11 2007 +0000
  |  summary:     Added tag alpha for changeset 3442585be8a6
  |
  o  changeset:   0:3442585be8a6
     tag:         alpha
     tag:         default/not-master
     user:        test <test@example.org>
     date:        Mon Jan 01 00:00:10 2007 +0000
     summary:     add alpha
  

  $ cd ..
  $ cd gitrepo
git should have the tag alpha
  $ git tag -l
  alpha

  $ cd ..
  $ hg clone gitrepo hgrepo2 | grep -v '^updating'
  importing git objects into hg
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg -R hgrepo2 log --graph | egrep -v ': *(not-master|master)'
  @  changeset:   1:d529e9229f6d
  |  tag:         default/master
  |  tag:         tip
  |  user:        test
  |  date:        Mon Jan 01 00:00:11 2007 +0000
  |  summary:     Added tag alpha for changeset 3442585be8a6
  |
  o  changeset:   0:3442585be8a6
     tag:         alpha
     tag:         default/not-master
     user:        test <test@example.org>
     date:        Mon Jan 01 00:00:10 2007 +0000
     summary:     add alpha
  

the tag should be in .hgtags
  $ cat hgrepo2/.hgtags
  3442585be8a60c6cd476bbc4e45755339f2a23ef alpha
