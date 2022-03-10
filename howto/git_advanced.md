# Git version control CLI commands for advanced usage

## Adding features via pull request

If you do not have write permissions to a repository you want to contribute to (or are requested to by the maintainers), you need to fork the repository (copy it into your account) and create a pull-request to add changes back to the original repository.

To follow this procedure, create the forked repository via the web interface first.
Afterwards you can follow instructions in [git_basics](git_basics.md) to clone your fork to your local machine, make changes, commit them and push them to the forked repository under your account.

Alternatively, you can add the forked repository as a second remote to your local copy of the original repository.
```
git remote add <remote_name> <url_to_fork>
```
Now you can make changes in this repository and push them to your forked version with
```
git push <remote_name> <branch_name_in_fork>
```
and create a pull request from `yourfork/branch_name_in_fork` to the original repository.
