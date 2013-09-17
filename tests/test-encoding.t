# -*- coding: utf-8 -*-

Load commonly used test logic
  $ . "$TESTDIR/testutil"

  $ git init gitrepo
  Initialized empty Git repository in $TESTTMP/gitrepo/.git/
  $ cd gitrepo

utf-8 encoded commit message
  $ echo alpha > alpha
  $ git add alpha
  $ fn_git_commit -m 'add älphà'

Create some commits using latin1 encoding
The warning message changed in Git 1.8.0
  $ . $TESTDIR/latin-1-encoding
  Warning: commit message (did|does) not conform to UTF-8. (re)
  You may want to amend it after fixing the message, or set the config
  variable i18n.commitencoding to the encoding your project uses.
  Warning: commit message (did|does) not conform to UTF-8. (re)
  You may want to amend it after fixing the message, or set the config
  variable i18n.commitencoding to the encoding your project uses.

  $ cd ..
  $ git init --bare gitrepo2
  Initialized empty Git repository in $TESTTMP/gitrepo2/

  $ hg clone gitrepo hgrepo | grep -v '^updating'
  importing git objects into hg
  4 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd hgrepo

Latin1 commit messages started being automatically converted to UTF-8 in
Git 1.8.0, so we accept the output of either version.
  $ HGENCODING=utf-8 hg log --graph --debug | grep -v ': *master' | grep -v 'phase:' | grep -v ': *author=' | grep -v ': *message='
  @  changeset:   3:(8549ee7fe0801b2dafc06047ca6f66d36da709f5|c3d3e39fc04f7e2e8cdb95f090415ec1ddc1be70) (re)
  |  tag:         default/master
  |  tag:         tip
  |  parent:      2:(0422fbb4ec39fb69e87b94a3874ac890333de11a|f8aa41895a3a771a72520ca205a4685b76649fdd) (re)
  |  parent:      -1:0000000000000000000000000000000000000000
  |  manifest:    3:ea49f93388380ead5601c8fcbfa187516e7c2ed8
  |  user:        tést èncödîng <test@example.org>
  |  date:        Mon Jan 01 00:00:13 2007 +0000
  |  files+:      delta
  |  extra:       branch=default
  |  extra:       committer=test <test@example.org> 1167609613 0
  |  extra:       encoding=latin-1
  |  description:
  |  add déltà
  |
  |
  o  changeset:   2:(0422fbb4ec39fb69e87b94a3874ac890333de11a|f8aa41895a3a771a72520ca205a4685b76649fdd) (re)
  |  parent:      1:(9f6268bfc9eb3956c5ab8752d7b983b0ffe57115|955b24cf6f8f293741d3f39110c6fe554c292533) (re)
  |  parent:      -1:0000000000000000000000000000000000000000
  |  manifest:    2:f580e7da3673c137370da2b931a1dee83590d7b4
  |  user:        tést èncödîng <test@example.org>
  |  date:        Mon Jan 01 00:00:12 2007 +0000
  |  files+:      gamma
  |  extra:       branch=default
  |  extra:       committer=test <test@example.org> 1167609612 0
  |  description:
  |  add gämmâ
  |
  |
  o  changeset:   1:(9f6268bfc9eb3956c5ab8752d7b983b0ffe57115|955b24cf6f8f293741d3f39110c6fe554c292533) (re)
  |  parent:      0:bb7d36568d6188ce0de2392246c43f6f213df954
  |  parent:      -1:0000000000000000000000000000000000000000
  |  manifest:    1:f0bd6fbafbaebe4bb59c35108428f6fce152431d
  |  user:        tést èncödîng <test@example.org>
  |  date:        Mon Jan 01 00:00:11 2007 +0000
  |  files+:      beta
  |  extra:       branch=default
  |  extra:       committer=test <test@example.org> 1167609611 0
  |  description:
  |  add beta
  |
  |
  o  changeset:   0:bb7d36568d6188ce0de2392246c43f6f213df954
     parent:      -1:0000000000000000000000000000000000000000
     parent:      -1:0000000000000000000000000000000000000000
     manifest:    0:8b8a0e87dfd7a0706c0524afa8ba67e20544cbf0
     user:        test <test@example.org>
     date:        Mon Jan 01 00:00:10 2007 +0000
     files+:      alpha
     extra:       branch=default
     description:
     add älphà
  
  

  $ hg gclear
  clearing out the git cache data
  $ hg push ../gitrepo2
  pushing to ../gitrepo2
  searching for changes
  adding objects
  added 4 commits with 4 trees and 4 blobs

  $ cd ..
Latin1 commit messages started being automatically converted to UTF-8 in
Git 1.8.0, so we accept the output of either version.
  $ git --git-dir=gitrepo2 log --pretty=medium
  commit (da0edb01d4f3d1abf08b1be298379b0b2960e680|51c509c1c7eeb8f0a5b20aa3e894e8823f39171f) (re)
  Author: t\xe9st \xe8nc\xf6d\xeeng <test@example.org> (esc)
  Date:   Mon Jan 1 00:00:13 2007 +0000
  
      add d\xe9lt\xe0 (esc)
  
  commit (2372b6c8f1b91f2db8ae5eb0f9e0427c318b449c|bd576458238cbda49ffcfbafef5242e103f1bc24) (re)
  Author: * <test@example.org> (glob)
  Date:   Mon Jan 1 00:00:12 2007 +0000
  
      add g*mm* (glob)
  
  commit (9ef7f6dcffe643b89ba63f3323621b9a923e4802|7a7e86fc1b24db03109c9fe5da28b352de59ce90) (re)
  Author: * <test@example.org> (glob)
  Date:   Mon Jan 1 00:00:11 2007 +0000
  
      add beta
  
  commit 0530b75d8c203e10dc934292a6a4032c6e958a83
  Author: test <test@example.org>
  Date:   Mon Jan 1 00:00:10 2007 +0000
  
      add älphà
