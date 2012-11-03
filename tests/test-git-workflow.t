Load commonly used test logic
  $ . "$TESTDIR/testutil"

  $ hg init hgrepo
  $ cd hgrepo
  $ echo alpha > alpha
  $ hg add alpha
  $ fn_hg_commit -m "add alpha"
  $ hg log --graph --debug | grep -v phase:
  @  changeset:   0:0221c246a56712c6aa64e5ee382244d8a471b1e2
     tag:         tip
     parent:      -1:0000000000000000000000000000000000000000
     parent:      -1:0000000000000000000000000000000000000000
     manifest:    0:8b8a0e87dfd7a0706c0524afa8ba67e20544cbf0
     user:        test
     date:        Mon Jan 01 00:00:10 2007 +0000
     files+:      alpha
     extra:       branch=default
     description:
     add alpha
  
  

  $ cd ..

configure for use from git
  $ hg clone hgrepo gitrepo
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd gitrepo
  $ hg book master
  $ hg up null
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo "[git]" >> .hg/hgrc
  $ echo "intree = True" >> .hg/hgrc
  $ hg gexport

do some work
  $ git config core.bare false
  $ git checkout master 2>&1 | sed s/\'/\"/g
  Already on "master"
  $ echo beta > beta
  $ git add beta
  $ fn_git_commit -m 'add beta'

get things back to hg
  $ hg gimport
  importing git objects into hg
  $ hg log --graph --debug | grep -v ': *master' | grep -v phase:
  o  changeset:   1:7108ae7bd184226a29b8203619a8253d314643bf
  |  tag:         tip
  |  parent:      0:0221c246a56712c6aa64e5ee382244d8a471b1e2
  |  parent:      -1:0000000000000000000000000000000000000000
  |  manifest:    1:f0bd6fbafbaebe4bb59c35108428f6fce152431d
  |  user:        test <test@example.org>
  |  date:        Mon Jan 01 00:00:11 2007 +0000
  |  files+:      beta
  |  extra:       branch=default
  |  description:
  |  add beta
  |
  |
  o  changeset:   0:0221c246a56712c6aa64e5ee382244d8a471b1e2
     parent:      -1:0000000000000000000000000000000000000000
     parent:      -1:0000000000000000000000000000000000000000
     manifest:    0:8b8a0e87dfd7a0706c0524afa8ba67e20544cbf0
     user:        test
     date:        Mon Jan 01 00:00:10 2007 +0000
     files+:      alpha
     extra:       branch=default
     description:
     add alpha
  
  
gimport should have updated the bookmarks as well
  $ hg bookmarks
     master                    1:7108ae7bd184
