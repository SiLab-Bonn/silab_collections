# Git version control CLI commands for daily usage

## Cloning a repository to your local machine

Clone a *remote* repository with *remote_url* in the current folder

```bash

git clone remote_url

```

### Example

Clone `basil` into your current folder

```bash

git clone https://github.com/SiLab-Bonn/basil

```

## Checking status

While in a git repository, one can check the status of your local repository with regard to its

*remote origin* with

```bash

git status

```

## (Switching) Branches

Usually, a git repository has multiple *branches* which represent the same code in different states of development.

Conventionally, a `master` (recently also `main`) branch is set to be the default, stable version of the code. To switch from your current branch to *target_branch* use

```bash

git checkout target_branch

```

To get a list of all available branches

```bash

git branch -a

```

## Pull

To get the newest changes from the *remote origin* of you current branch, you simply

```bash

git pull

```

## Commit

If you made changes to code on your local repository, you need to `commit` them in order to

`push` them to the *remote origin*. Therefore, to commit changes in *target_file* within your

local repository (branch) you need to

```bash

git commit -m "MY COMMIT MESSAGE" path/to/target_file

```

Every commit needs a commit message. This is usually a short description of what has been changed/improved/fixed etc.

If you leave the `-m "MY COMMIT MESSAGE"` out, a terminal-based text editor (like [Nano](https://wiki.ubuntuusers.de/Nano/)

) will open up where you then have to type in a commit message. You can also commit many things at once.

If you want to commit everything in a *target_folder*, just type

```bash

git commit -m "MY COMMIT MESSAGE" path/to/target_folder

```

## Push

If `git status` shows you that your locally ahead of the *remote origin* you may want to push

your local changes. Therefore you simply do

```bash

git push

```

You may be asked to set your GitHub credentials on first use. Afterwards you will be asked to type your

*username* and *password*. After successful entry of both your changes will be pushed to the upstream.

## Creating new branches

When you're implementing a new feature you sometimes want to do this on your own version of the code which means creating your own *branch*.

This has the advantage that you're usually the only person working on that branch which makes it a little bit easier.

To create a new branch *feature_branch* locally

```bash

git checkout -b feature_branch

```

To then push your locally-created branch to the *remote origin* do

```bash

git push -u origin feature_branch

```

Then the new *feature_branch* will be also available after somebody does a `git clone` on your repository.

## Merging branches

If your *feature_branch* has implemented the new feature, you want to merge it back into `master` (or any

other branch). To do so, you merge the two branches locally and then push the changes to the upstream.

If you want to merge *feature_branch* back into *target_branch* do the following

```bash

git checkout target_branch  # Checkout the branch you want to merge into

git merge feature_branch  # Merge *feature_branch* into *target_branch*

```

If everything goes smoothly, this will open your terminal-based editor and ask you to type a commit

message for this merger. If there are **conflicts** between the two branches you're trying to merge,

git will ask you to resolve the conflicts manually. This means going through the code and finding

the places where git indicated a conflict and resolve it.

## Stashing temporal changes

Sometimes you want to `git pull` to get the newest changes from upstream but you also have some **non-comitted**

changes locally. Since it can occurr, that upstream changes include changes to code you modified (but not comitted) locally,

you want to safe your local, un-comitted changes temporary, to get the newest changes from upstream and then re-apply

your local, un-comitted modifictaions. To safe your current local state

```bash

git stash

```

To re-apply the latest saved stash to the local code

```bash

git stash apply

```

You can also use 

```bash

git stash pop

```

to re-apply the latest stash and simultaneously remove it from the stash list.

## Seeing the latest commits

To see a list of the last commits on your branch type

```bash

git log

```
