#!/usr/bin/env python3

import argparse
import io
import os
import re
import subprocess
import fileinput
import sys

args_parser = argparse.ArgumentParser(
    description = ("Git submodules, but useable.")
)

args_parser.add_argument(
    'cmd',
    type = str,
    nargs = 1,
    help = 'Command to be performed (add|status|from-official|rm|rm-desc|rm-dir|update-desc|update-dir)'
)

args_parser.add_argument(
    'paths',
    nargs = '*',
    help = (
        "Folders/Submodules to target (default: all)."
    )
)

args = args_parser.parse_args()

################################################################################
##### OS COMMANDS ##############################################################
################################################################################
def ensure_directory_exists (dir_name):
   subprocess.Popen(['mkdir', '-p', dir_name]).wait()

   return

def resolve_relative_path (repo_root_path, current_dir, file_or_dir):
    full_path = os.path.normpath(current_dir + "/" + file_or_dir)
    extra_prefix = os.path.commonprefix([repo_root_path, full_path])
    result = full_path[len(extra_prefix):]

    if (len(result) == 0):
        extra_prefix = os.path.commonprefix([repo_root_path, file_or_dir])
        result = file_or_dir[len(extra_prefix):]

    if ((len(result) > 0) and (result[0] == '/')):
        result = result[1:]

    return result

################################################################################
##### GIT COMMANDS #############################################################
################################################################################
def git_get_current_commit_hash (repo_path):
    git_cmd = subprocess.Popen(
        ['git', 'rev-parse', 'HEAD'],
        cwd = repo_path,
        stdout = subprocess.PIPE
    )

    for line in io.TextIOWrapper(git_cmd.stdout, encoding="utf-8"):
        search = re.findall(r'([a-z0-9]+)', line)

        if (search):
            return search[0]

    print(
        "[F] Unable to find commit hash for repository in \""
        + repo_path
        + "\"",
        file = sys.stderr
    )

    sys.exit(-1)

    return ""

def git_repository_has_uncommitted_changes (repo_path):
    git_cmd = subprocess.Popen(
        ['git', 'update-index', '--refresh'],
        cwd = repo_path,
        stdout = subprocess.PIPE
    )

    for line in io.TextIOWrapper(git_cmd.stdout, encoding="utf-8"):
        return True

    return False

def git_inflate_official_submodules (repo_path):
    subprocess.Popen(
        ['git', 'submodule', 'update', '--init', '--recursive'],
        cwd = repo_path,
        stdout = sys.stdout
    ).wait()

def git_get_official_submodule_paths (repo_path):
    result = []

    git_cmd = subprocess.Popen(
        ["git submodule --quiet foreach 'echo $path'"],
        shell = True, # This is apparently needed for echo to be defined.
        cwd = repo_path,
        stdout = subprocess.PIPE
    )

    for line in io.TextIOWrapper(git_cmd.stdout, encoding="utf-8"):
        result.append(line.strip())

    return result

def git_shallow_submodule_init (repo_path, module_path):
    subprocess.Popen(
        ['git', 'submodule', 'update', '--init', module_path],
        cwd = repo_path,
        stdout = sys.stdout
    ).wait()

def git_get_all_remotes (repo_path):
    remote_names = []

    git_cmd = subprocess.Popen(
        ['git', 'remote'],
        cwd = repo_path,
        stdout = subprocess.PIPE
    )

    for line in io.TextIOWrapper(git_cmd.stdout, encoding="utf-8"):
        remote_names.append(line.strip())

    result = []

    for remote_name in remote_names:
        git_cmd = subprocess.Popen(
            ['git', 'remote', 'get-url', '--all', remote_name],
            cwd = repo_path,
            stdout = subprocess.PIPE
        )

        for line in io.TextIOWrapper(git_cmd.stdout, encoding="utf-8"):
            result.append(line.strip())

    return result

def git_add_to_gitignore (entry_set, root_path):
    with open(root_path + "/.gitignore", 'r+') as file_stream:
        for line in file_stream:
            entry_set.discard(line.strip())

            if (len(entry_set) == 0):
                return

        for new_entry in entry_set:
            print(new_entry, file=file_stream)

def git_find_root_path ():
    # from https://stackoverflow.com/questions/22081209/find-the-root-of-the-git-repository-where-the-file-lives
    return subprocess.Popen(
        ['git', 'rev-parse', '--show-toplevel'],
        stdout = subprocess.PIPE
    ).communicate()[0].rstrip().decode('utf-8')

def git_is_repository_root (path):
    return (
        subprocess.Popen(
            ['git', 'rev-parse', '--show-toplevel'],
            stdout = subprocess.PIPE,
            cwd = path
        ).communicate()[0].rstrip().decode('utf-8') == path
    )

################################################################################
##### GIT SUBMODULE CLASS ######################################################
################################################################################
class GitSubmodule:
    def __init__ (self, path):
        self.path = path
        self.sources = []
        self.commit = None
        self.enabled = True

    def get_path (self):
        return self.path

    def get_sources (self):
        return self.sources

    def get_commit (self):
        return self.commit

    def get_is_enabled (self):
        return self.enabled

    def disable (self):
        self.enabled = False

    def add_source (self, source):
        if (not (source in self.get_sources())):
            self.sources.append(source)

    def set_commit (self, commit):
        self.commit = commit

    def print_to (self, file_stream):
        print('[submodule "' + self.get_path() + '"]', file = file_stream)

        for source in self.get_sources():
            print('   source = ' + source, file = file_stream)

        print('   commit = ' + self.get_commit(), file = file_stream)

        print('   enable = ' + str(self.get_is_enabled()), file = file_stream)

    def clone_repository (self, root_dir):
        repository_dir = root_dir + "/" + self.get_path()
        ensure_directory_exists(repository_dir)

        if (git_is_repository_root(repository_dir)):
            git_process = subprocess.Popen(
                ['git', 'fetch', '--all'],
                cwd = repository_dir
            )

            git_process = subprocess.Popen(
                ['git', 'checkout', self.commit],
                cwd = repository_dir
            )

            git_process.wait()

            if (git_process.returncode == 0):
                print("Submodule \"" + self.get_path() + "\" checked out.")
                return
            else:
                print(
                    "Target commit not available with current source for"
                    + " submodule \""
                    + self.get_path()
                    + "\". Resetting local copy."
                )

                subprocess.Popen(
                    ['rm', '-rf', self.get_path()],
                    cwd = root_dir
                ).wait()
                ensure_directory_exists(repository_dir)

        for source in self.get_sources():
            print(
                "Cloning submodule \""
                + self.get_path()
                + "\" from \""
                + source
                + "\"..."
            )

            git_process = subprocess.Popen(
                ['git', 'clone', source, self.get_path()],
                cwd = root_dir
            )

            git_process.wait()

            if (git_process.returncode != 0):

                print("Failed at Git clone.")

                continue

            git_process = subprocess.Popen(
                ['git', 'checkout', self.commit],
                cwd = repository_dir
            )

            git_process.wait()

            if (git_process.returncode == 0):
                print("Done.")

                return
            else:
                print(
                    "Failed at Git checkout for commit \""
                    + self.get_commit()
                    + "\" from source \""
                    + source
                    + "\"."
                )

                subprocess.Popen(
                    ['rm', '-rf', self.get_path()],
                    cwd = root_dir
                ).wait()
                ensure_directory_exists(repository_dir)

                print("Removed cloned repository.")

                continue

        print(
            "[F] Could not clone submodule \""
            + self.get_path()
            + "\" into \""
            + repository_dir
            +"\".",
            file = sys.stderr
        )
        sys.exit(-1)

    def clear_repository (self, root_dir):
        print("Clearing submodule \"" + self.get_path() + "\"...")

        subprocess.Popen(['rm', '-rf', self.get_path()], cwd = root_dir).wait()

        print("Done.")

    def update_description (self, root_dir):
        repository_dir = root_dir + "/" + self.get_path()

        if (not os.path.exists(repository_dir)):
            print(
                "[E] Submodule \""
                + self.get_path()
                + "\" has no directory to update its description from. Skipped."
            )

            return

        if (not git_is_repository_root(repository_dir)):
            print(
                "[E] The directory for submodule \""
                + self.get_path()
                + "\" is not a Git repository and thus cannot be used to update"
                + " its description. Skipped.",
                file = sys.stderr
            )

            return


        self.set_commit(git_get_current_commit_hash(repository_dir))

        for source in git_get_all_remotes(repository_dir):
            self.add_source(source)

    def check_description (self, root_dir):
        repository_dir = root_dir + "/" + self.get_path()
        is_the_same = True

        if (not os.path.exists(repository_dir)):
            print(
                "Submodule \""
                + self.get_path()
                + "\" has no directory to compare to."
            )

            return

        if (not git_is_repository_root(repository_dir)):
            print(
                "The directory for submodule \""
                + self.get_path()
                + "\" is not a Git repository."
            )

            return

        currently_used_hash = git_get_current_commit_hash(repository_dir)

        if (currently_used_hash != self.get_commit()):
            is_the_same = False

            print(
                "Submodule \""
                + self.get_path()
                + "\" is configured to use commit \""
                + self.get_commit()
                + "\" but its local clone is on commit \""
                + currently_used_hash
                + "\"."
            )

        for source in git_get_all_remotes(repository_dir):
            if (source not in self.get_sources()):
                is_the_same = False

                print(
                    "The local clone of the submodule \""
                    + self.get_path()
                    + "\" has a source not registered in .gitsubmodules: \""
                    + source
                    + "\"."
                )

        if (is_the_same):
            if (git_repository_has_uncommitted_changes(repository_dir)):
                print(
                    "The configuration for the \""
                    + self.get_path()
                    + "\" submodule is up-to-date, but there are uncommitted"
                    + " changes in its repository."
                )
            else:
                print(
                    "The configuration for the \""
                    + self.get_path()
                    + "\" submodule is up-to-date."
                )

    def parse_all (file_stream):
        result_as_list = list()
        result_as_dict = dict()

        submodule = None

        for line in file_stream:
            search = re.findall(r'^\s*\[submodule\s*"(.+)"\]', line)

            if search:
                path = search[0].strip(os.sep)

                if (path in result_as_dict):
                   submodule = result_as_dict[path]
                else:
                   submodule = GitSubmodule(search[0].strip(os.sep))
                   result_as_dict[path] = submodule
                   result_as_list.append(submodule)

                continue

            if (not submodule):
                continue

            search = re.findall(r'^\s*source\s*=\s*([^\s].*[^\s])\s*', line)

            if search:
                submodule.add_source(search[0])

                continue

            search = re.findall(r'^\s*commit\s*=\s*([^\s].*[^\s])\s*', line)

            if search:
                submodule.set_commit(search[0])

                continue

            search = re.findall(r'^\s*enable\s*=\s*([^\s].*[^\s])\s*', line)

            if search:
                enable_param_val = search[0].lower()
                if (
                    not (
                        (enable_param_val == "true")
                        or (enable_param_val == "t")
                        or (enable_param_val == "yes")
                        or (enable_param_val == "y")
                        or (enable_param_val == "1")
                    )
                ):
                    submodule.disable()

                continue

        return (result_as_list, result_as_dict)

################################################################################
##### GENERAL ##################################################################
################################################################################
def get_submodules_of (repository_path):
    try:
        with open(repository_path + "/.gitsubmodules", 'r') as file_stream:
            return GitSubmodule.parse_all(file_stream)

    except FileNotFoundError:
        return ([], dict())

def update_submodules_desc_file (
    repository_path,
    dict_of_submodules,
    paths_to_remove
):
    config_lines = []
    last_submodule_line_of = dict()
    last_commit_line_of = dict()
    last_enable_line_of = dict()
    missing_sources = dict()

    for submodule in dict_of_submodules:
        last_submodule_line_of[submodule] = -1
        last_commit_line_of[submodule] = -1
        last_enable_line_of[submodule] = -1
        missing_sources[submodule] = dict_of_submodules[submodule].get_sources()

    submodule_path = None
    read = True

    try:
        with open(repository_path + "/.gitsubmodules", 'r') as file_stream:
            for line in file_stream:
                if (read):
                    config_lines.append(line.rstrip())

                search = re.findall(r'^\s*\[submodule\s*"(.+)"\]', line)

                if (search):
                    submodule_path = search[0].strip(os.sep)

                    if (submodule_path in paths_to_remove):
                        read = False
                        config_lines = config_lines[:-1]
                    elif (not read):
                        read = True
                        config_lines.append(line.rstrip())

                    last_submodule_line_of[submodule_path] = (
                        len(config_lines) - 1
                    )
                    continue

                if (not submodule_path):
                    continue

                search = re.findall(r'^\s*source\s*=\s*([^\s].*[^\s])\s*', line)

                if (search and (submodule_path in missing_sources)):
                    missing_sources[submodule_path].remove(search[0])
                    continue

                search = re.findall(r'^\s*commit\s*=\s*([^\s].*[^\s])\s*', line)

                if (search):
                    last_commit_line_of[submodule_path] = len(config_lines) - 1
                    continue

                search = re.findall(r'^\s*enable\s*=\s*([^\s].*[^\s])\s*', line)

                if (search):
                    last_enable_line_of[submodule_path] = len(config_lines) - 1
                    continue

    except FileNotFoundError:
        print(
            "No \""
            + repository_path
            + "/.gitsubmodules\" file found. It will be created."
        )

    for submodule_path in dict_of_submodules:
        submodule = dict_of_submodules[submodule_path]

        if (submodule.get_commit() == None):
            print(
                "Skipping description update for submodule \""
                + submodule_path
                + "\" as it had no designed commit target."
            )

            continue

        write_index = last_submodule_line_of[submodule_path]
        if (write_index == -1):
            config_lines.append("[submodule \"" + submodule_path + "\"]")
            write_index = len(config_lines) - 1

        last_commit_line = last_commit_line_of[submodule_path]
        if (last_commit_line == -1):
            config_lines.insert(
                write_index + 1,
                "   commit = " + submodule.get_commit()
            )
            write_index = write_index + 1
            last_commit_line = write_index

        config_lines[last_commit_line] = "   commit = " + submodule.get_commit()

        last_enable_line = last_enable_line_of[submodule_path]
        if (last_enable_line == -1):
            config_lines.insert(
                write_index + 1,
                "   enable = " + str(submodule.get_is_enabled())
            )
            write_index = write_index + 1
            last_enable_line = write_index

        config_lines[last_enable_line] = (
            "   enable = " + str(submodule.get_is_enabled())
        )

        for source in missing_sources[submodule_path]:
            config_lines.insert(
                write_index + 1,
                "   source = " + source
            )
            write_index = write_index + 1

    with open(repository_path + "/.gitsubmodules", 'w') as file_stream:
        for line in config_lines:
            print(line, file = file_stream)

def restrict_dictionary_to (dict_of_submodules, list_of_paths):
    if (list_of_paths == []):
        return dict_of_submodules

    result = dict()

    for path in list_of_paths:
        if (path not in dict_of_submodules):
            print("[F] Unknown submodule \"" + path + "\".", file = sys.stderr)

            sys.exit(-1)

            return dict()
        else:
            if (not dict_of_submodules[path].get_is_enabled()):
                print(
                    "[E] Ignoring disabled submodule \""
                    + path
                    + "\".",
                    file = sys.stderr
                )

                continue

            result[path] = dict_of_submodules[path]

    return result

def apply_clone_to (submodule_dictionary, root_path):
    for submodule_path in submodule_dictionary:
        if (not submodule_dictionary[submodule_path].get_is_enabled()):
            print("Skipping disabled submodule \"" + submodule_path + "\".")
            continue

        repo_path = root_path + "/" + submodule_path

        print("Cloning \"" + repo_path + "\"...")

        submodule_dictionary[submodule_path].clone_repository(root_path)

        print(
            "Done. Handling any official Git submodules in \""
            + repo_path
            + "\"..."
        )
        git_inflate_official_submodules(repo_path)

        print("Done. Recursing clone in \"" + repo_path + "\"...")

        (recursive_list, recursive_dictionary) = get_submodules_of(repo_path)

        apply_clone_to(recursive_dictionary, root_path)

        print ("Recursive clone in \"" + repo_path + "\" completed.")


def apply_clear_to (submodule_dictionary, root_path):
    for submodule_path in submodule_dictionary:
        if (not submodule_dictionary[submodule_path].get_is_enabled()):
            print("Skipping disabled submodule \"" + submodule_path + "\".")
            continue

        submodule_dictionary[submodule_path].clear_repository(root_path)

        print("Cleared \"" + root_path + "/" + submodule_path + "\"...")

def apply_check_to (submodule_dictionary, root_path):
    for submodule_path in submodule_dictionary:
        if (not submodule_dictionary[submodule_path].get_is_enabled()):
            print("Skipping disabled submodule \"" + submodule_path + "\".")
            continue

        submodule_dictionary[submodule_path].check_description(root_path)

def apply_update_desc_to (submodules_dictionary, root_path):
    for submodule_path in submodule_dictionary:
        if (not submodule_dictionary[submodule_path].get_is_enabled()):
            print("Skipping disabled submodule \"" + submodule_path + "\".")
            continue

        repo_path = root_path + "/" + submodule_path

        print("Updating description of \"" + repo_path + "\"...")

        submodule_dictionary[submodule_path].update_description(root_path)

        print("Done (not written yet).")

################################################################################
##### MAIN #####################################################################
################################################################################
current_directory = os.getcwd()
root_directory = git_find_root_path()

(submodule_list, submodule_dictionary) = get_submodules_of(root_directory)

args.paths = [
    resolve_relative_path(
        root_directory,
        current_directory,
        path.strip(os.sep)
    ) for path in args.paths
]

if (args.cmd[0] == "rm-desc"):
    if (len(args.paths) == 0):
        args.paths = [path for path in submodule_dictionary]

    update_submodules_desc_file(root_directory, dict(), args.paths)

    sys.exit(0)

if (args.cmd[0] == "from-official"):
    if (len(args.paths) == 0):
        print("Shallow initialization of all Official Git Submodules...")
        git_shallow_submodule_init(root_directory, ".")
        print("Done.")
        args.paths = git_get_official_submodule_paths(root_directory)
    else:
        for path in args.paths:
            print(
                "Shallow Official Git Submodule initialization for \""
                + path
                + "\"..."
            )
            git_shallow_submodule_init(root_directory, path)
            print("Done.")

            if (path not in git_get_official_submodule_paths(root_directory)):
                print(
                    "[F] No Official Git Submodule registered at \""
                    + path
                    + "\".",
                    file = sys.stderr
                )
                sys.exit(-1)


    args.cmd[0] = "add"

if (args.cmd[0] == "add"):
    for path in args.paths:
        if (path not in submodule_dictionary):
            new_module = GitSubmodule(path)
            submodule_dictionary[path] = new_module
            submodule_list.append(new_module)

    args.cmd[0] = "update-desc"

if (submodule_list == []):
    print("[F] No submodules in " + root_directory + ".", file = sys.stderr)
    sys.exit(-1)

submodule_dictionary = restrict_dictionary_to(submodule_dictionary, args.paths)

if (args.cmd[0] == "update-dir"):
    apply_clone_to(submodule_dictionary, root_directory)
    git_add_to_gitignore(
        set([path for path in submodule_dictionary]),
        root_directory
    )
elif (args.cmd[0] == "status"):
    apply_check_to(submodule_dictionary, root_directory)
elif (args.cmd[0] == "rm"):
    if (len(args.paths) == 0):
        args.paths = [path for path in submodule_dictionary]

    update_submodules_desc_file(root_directory, dict(), args.paths)
    apply_clear_to(submodule_dictionary, root_directory)
elif (args.cmd[0] == "rm-dir"):
    apply_clear_to(submodule_dictionary, root_directory)
elif (args.cmd[0] == "update-desc"):
    apply_update_desc_to(submodule_dictionary, root_directory)

    update_submodules_desc_file(root_directory, submodule_dictionary, [])

    print("Updated description written.")

    git_add_to_gitignore(
        set([path for path in submodule_dictionary]),
        root_directory
    )
else:
    print("[F] Unknown command \"" + args.cmd[0] + "\".", file = sys.stderr)
    sys.exit(-1)
