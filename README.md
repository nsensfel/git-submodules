# nsensfel's git-submodules (name TBD)
An alternative to the official
[Git Submodule](https://git-scm.com/docs/git-submodule) features. Same
principles, but ridiculously much simpler to use and maintain.

The submodules are described in a plain text file at the root of the repository
(`.gitsubmodules`) and that is the only place describing them.

The described submodules repositories can be added to the working tree through
a command. Conversely, repositories in the working tree can be added to the
submodule description file through a command.

Adding a submodule is easy: either edit the `.gitsubmodules` file directly, or
just clone the submodule's repository in your working tree and `add` it.

Unlike Git Submodule, this tool allows you to specify alternative source URLs
for submodules.

## How to use
Usage: `git-submodules.py COMMAND PARAM0 PARAM1...`

The important commands are `add`, `status`, `update-description`, and `update-directory`.

---
**COMMAND** `add`

**PARAMETERS** list of local paths to Git repositories. No effect if no path is given.

**EFFECT** updates the description file to include each path so that it matches their current state.

---
**COMMAND** `foreach`

**PARAMETERS** list of local paths to Git repositories and a shell command to execute as last parameter. All entries from the description file if no path is given.

**EFFECT** executes the shell command for each submodule. See 'help foreach' for more details.

---
**COMMAND** `foreach-enabled`

**PARAMETERS** list of local paths to Git repositories and a shell command to execute as last parameter. All entries from the description file if no path is given.

**EFFECT** executes the shell command for each submodule, provided they are enabled. See `help foreach` for more details.

---
**COMMAND** `foreach-enabled-recursive`

**PARAMETERS** list of local paths to Git repositories and a shell command to execute as last parameter. All entries from the description file if no path is given.

**EFFECT** executes the shell command for each submodule, provided they are enabled. The execution recurses into each such submodule. See `help foreach` for more details.

---
**COMMAND** `foreach-recursive`

**PARAMETERS** list of local paths to Git repositories and a shell command to execute as last parameter. All entries from the description file if no path is given.

**EFFECT** executes the shell command for each submodule. The execution recurses into each submodule. See `help foreach` for more details.

---
**COMMAND** `match-target`

**PARAMETERS** list of paths to submodules. All described submodules are selected if no path is given.

**EFFECT** updates the submodule's local copy to match the submodule's target (instead of its commit) regardless of the 'target_overrides_commit' parameter, then updates the submodule's description so that it matches the updated local copy.

---
**COMMAND** `from-official`

**PARAMETERS** list of local paths to official Git Submodules. All official Git Submdule are selected if no path is given.

**EFFECT** updates the description to include the selected official Git Submodules. These do not need to have been initialized.

---
**COMMAND** `help`

**PARAMETERS** one COMMAND.

**EFFECT** provides detailed help about a command.

---
**COMMAND** `list`

**PARAMETERS** list of local paths. The root repository's path is selected if no path is given.

**EFFECT** lists all submodules in those directories.

---
**COMMAND** `remove`

**PARAMETERS** list of paths to submodules. All described submodules are selected if no path is given.

**EFFECT** removes these submodules from the description and removes their local copy.

---
**COMMAND** `remove-description`

**PARAMETERS** list of paths to submodules. All described submodules are selected if no path is given.

**EFFECT** removes these submodules from the description.

---
**COMMAND** `remove-directory`

**PARAMETERS** list of paths to submodules. All described submodules are selected if no path is given.

**EFFECT** removes the local copy of these submodules.

---
**COMMAND** `seek`

**PARAMETERS** list of paths. The repository's root is used if no path is given.

**EFFECT** lists subfolders eligible to become submodules.

---
**COMMAND** `status`

**PARAMETERS** list of paths to submodules. All described submodules are selected if no path is given.

**EFFECT** compares description and local copy of the submodules.

---
**COMMAND** `to-official`

**PARAMETERS** list of paths to submodules. All described submodules are selected if no path is given.

**EFFECT** Not available.

---
**COMMAND** `update-description`

**PARAMETERS** list of paths to submodules. All described submodules are selected if no path is given.

**EFFECT** updates the description file to match the submodules' local copies.

---
**COMMAND** `update-directory`

**PARAMETERS** list of paths to submodules. All described submodules are selected if no path is given.

**EFFECT** updates the local copy of the submodules to match the description file.

## Foreach environment variables
* `SNSM_COMMIT` is the commit for this submodule.
* `SNSM_ENABLED` is `1` if the submodule is enabled, `0` otherwise.
* `SNSM_SOURCES` is a newline separated list of anonymous sources for the submodule.
* `SNSM_NAMED_SOURCES` is a newline separated list of named sources for the submodule. Each entry is first the name, a space, then the source.
* `SNSM_TARGET_TYPE` is the target type for this submodule. `commit`, `branch`, and `tag` are all 3 possible values.
* `SNSM_TARGET` is the actual target for this submodule. It is equal to `SNSM_COMMIT` if `SNSM_TARGET_TYPE` is `commit`.
* `SNSM_TARGET_OVERRIDES_COMMIT` is `1` if the submodule is configured to use the target instead of the commit, `0` otherwise.
* `SNSM_ROOT` is an absolute path to the root repository.
* `SNSM_ABSOLUTE_PATH` is an absolute path to the submodule.
* `SNSM_PATH` is a path to the submodule relative to the direct parent repository.
* `SNSM_PARENT` is an absolute path to the direct parent repository.
* `SNSM_PARENTS` is a newline separated list of absolute path to each of the parent repositories.

## Syntax of .gitsubmodules

Submodules are described in sections starting with `[submodule "<LOCAL_PATH>"]` with `<LOCAL_PATH>` being the submodule's local directory.

The `source = <URL>` parameter specifies `<URL>` as a remote for the submodule. Multiple remotes can be specified. The order in which they are given will also be used when attempting to connect to them.
The `source.<NAME> = <URL>` parameter specifies `<URL>` as the remote `<NAME>` for the submodule.

The `commit = <HASH>` parameter specifies `<HASH>` as the commit for the submodule's working directory.

The `target = commit <HASH>` parameter specifies that `<HASH>` is the reference commit for the submodule's working directory (it may differ from the current commit).
The `target = branch <BRANCH_NAME>` parameter specifies that `<BRANCH_NAME>` is the reference branch for the submodule's working directory (it may differ from the current commit's).
The `target = tag <TAG_NAME>` parameter specifies that `<TAG_NAME>` is the reference tag for the submodule's working directory (it may differ from the current commit's).

The `target_overrides_commit = <True|False>` parameter specifies whether the `commit` parameter should be ignored in favor of the `target` one when updating the working directory. This is useful when wanting to always have the most up-to-date commit of a particular branch, for example.

The `enable = <True|False>` parameter specifies whether the submodule is active or should be ignored.

**Example**:
```
[submodule "ardupilot"]
   source = git@my_local_server.userdomain:repos/ardupilot
   source.github = https://github.com/ArduPilot/ardupilot
   commit = 30e8160aa191e0a0e3a4676b33e0f153d09856ff
   enable = True
[submodule "meta/git-submodules"]
   source = git@my_local_server.userdomain:repos/git-submodules
   source.noot = https://git.noot-noot.org/clone/git-submodules
   source.github = https://github.com/nsensfel/git-submodules
   target = commit
   commit = d2c637e9f175b4a4618983253ec96a1edaff139b
   enable = True
[submodule "meta/meep-meep"]
   source = git@my_local_server.userdomain:repos/meep-meep
   target = branch dev
   target_overrides_commit = True
   enable = True
```
