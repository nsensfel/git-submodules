# nsensfel's git-submodules
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
* `$ git-submodules.py COMMAND` will apply `COMMAND` to all submodules in
`.gitsubmodules`.
* `$ git-submodules.py COMMAND PATH0 PATH1 ...` will apply `COMMAND` to the
submodules `PATH0`, `PATH1`, and so on...

Available commands:
* `add` Modifies `.gitsubmodules` to register or update the description of the
   selected submodules and/or paths. Said paths are added to `.gitignore` if not
   already present.
* `check` Prints information about any mismatch between the submodules'
   description and their clone within the working tree.
* `update-desc` Updates `.gitsubmodules` so that each submodule's description
   matches its clone within the working tree. Their paths are added to
   `.gitignore` if not already present.
* `update-dir` Updates or creates a clone of each submodule in the working tree,
   according to their description in `.gitsubmodules`. This is done recursively.
   Official Git Submodules are also loaded in each of these clones. Paths to
   the submodule clones are added to `.gitignore` if not already present.

## Example of .gitsubmodules
```
[submodule "ardupilot"]
   source = git@my_local_server.userdomain:repos/ardupilot
   source = https://github.com/ArduPilot/ardupilot
   commit = 30e8160aa191e0a0e3a4676b33e0f153d09856ff
   enable = True
[submodule "meta/git-submodules"]
   source = git@my_local_server.userdomain:repos/git-submodules
   source = https://git.noot-noot.org/clone/git-submodules
   source = https://github.com/nsensfel/git-submodules
   commit = d2c637e9f175b4a4618983253ec96a1edaff139b
   enable = True
```
