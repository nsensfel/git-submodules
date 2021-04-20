#!/usr/bin/env python3

import argparse
import io
import os
import re
import subprocess
import fileinput

args_parser = argparse.ArgumentParser(
    description = ("Git submodules, but useable.")
)

args_parser.add_argument(
    'cmd',
    type = str,
    nargs = 1,
    help = 'Command to be performed (clone|clear|update-desc).'
)

args_parser.add_argument(
    'paths',
    nargs = '*',
    help = (
        "Folders/Submodules to target (default: all)."
    )
)

args = args_parser.parse_args()

def ensure_directory_exists (dir_name):
   subprocess.Popen(['mkdir', '-p', dir_name]).wait()

   return

def git_get_current_commit_hash (repo_path):
    git_rev_parse = subprocess.Popen(
        ['git', 'rev-parse', 'HEAD'],
        cwd = repo_path,
        stdout = subprocess.PIPE
    )

    for line in io.TextIOWrapper(git_rev_parse.stdout, encoding="utf-8"):
        search = re.findall(r'([a-z0-9]+)', line)

        if (search):
            return search[0]

    print(
        "[F] Unable to find commit hash for repository in \""
        + repo_path
        + "\"",
        file = sys.stderr
    )

    # TODO: crash.

    return "HEAD"

def git_get_all_remotes (repo_path):
    result = []
    gitconfig_file = repo_path + "/.git/config"

    should_read_url = False

    try:
        with open(gitconfig_file, 'r') as file_stream:
            for line in file_stream:
                search = re.findall(r'\s*\[remote\s*"(.+)"\]', line)

                if search:
                    should_read_url = True

                    continue

                if (should_read_url):
                    search = re.findall(r'\s*url\s*=\s*([^\s].*[^\s])\s*', line)

                    if (search):
                        result.append(search[0])

                        continue

                    search = re.findall(r'\s*\[', line)

                    if search:
                        should_read_url = False

    except FileNotFoundError:
        print(
            "[E] Could not find file \""
            + gitconfig_file
            + "\".",
            file = sys.stderr
        )

    return result

def git_add_to_gitignore (entry_set, root_path):
    with open(root_path + "/.gitignore", 'r+') as file_stream:
        for line in file_stream:
            entry_set.discard(line)

            if (entry_set.isEmpty()):
                return

        for new_entry in entry_set:
            print(new_entry, file=file_stream)

def git_find_root_path ():
    # from https://stackoverflow.com/questions/22081209/find-the-root-of-the-git-repository-where-the-file-lives
    return subprocess.Popen(
        ['git', 'rev-parse', '--show-toplevel'],
        stdout = subprocess.PIPE
    ).communicate()[0].rstrip().decode('utf-8')


class GitSubmodule:
    def __init__ (self, path):
        self.path = path
        self.sources = []
        self.commit = "HEAD"
        self.enabled = True

    def get_path (self):
        return self.path

    def get_sources (self):
        return self.sources

    def get_commit (self):
        return self.commit

    def get_is_enabled (self):
        return self.is_enabled

    def disable (self):
        self.is_enabled = False

    def add_source (self, source):
        if (not (source in self.get_sources())):
            self.sources.append(source)

    def set_commit (self, commit):
        self.commit = commit

    def print_to (self, file_stream):
        print('[submodule "' + self.get_path() + '"]', file_stream)

        for source in self.get_sources():
            print('   source = ' + source, file_stream)

        print('   commit = ' + self.get_commit(), file_stream)

        print('   enable = ' + self.get_is_enabled(), file_stream)

    def clone_repository (self, root_dir):
        repository_dir = root_dir + "/" + self.get_path()
        ensure_directory_exists(repository_dir)

        git_process = subprocess.Popen(
            ['git', 'checkout', self.commit],
            cwd = repository_dir
        )

        git_process.wait()

        if (git_process.returncode == 0):
            print("Submodule \"" + self.get_path() + "\" checked out.")

            return

        for source in self.sources:
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

                subprocess.Popen(['rm', '-rf', repository_dir]).wait()

                print("Removed cloned repository.")

                continue

        print("[F] Could not clone submodule \"" + self.get_path() + "\".")

    def clear_repository (self, root_dir):
        print("Clearing submodule \"" + self.get_path() + "\"...")

        subprocess.Popen(['rm', '-rf', root_dir + self.get_path()]).wait()

        print("Done.")

    def update_description (self, root_dir):
        repository_dir = root_dir + self.get_path()

        self.set_commit(git_get_current_commit_hash(repository_dir))

        for source in git_get_all_remotes(repository_dir):
            self.add_source(source)

    def update_description (self, root_dir):
        repository_dir = root_dir + self.get_path()

        self.set_commit(git_get_current_commit_hash(repository_dir))

        for source in git_get_all_remotes(repository_dir):
            self.add_source(source)

    def list_as_a_dict (submodule_list):
        result = dict()

        for submodule in submodule_list:
            result[submodule.get_path()] = submodule

        return result

    def parse_all (file_stream):
        result = list()
        submodule = None

        for line in file_stream:
            search = re.findall(r'\s*\[submodule\s*"(.+)"\]', line)

            if search:
                submodule = GitSubmodule(search[0])

                result.append(submodule)

                continue

            if (not submodule):
                continue

            search = re.findall(r'\s*source\s*=\s*([^\s].*[^\s])\s*', line)

            if search:
                submodule.add_source(search[0])

                continue

            search = re.findall(r'\s*commit\s*=\s*([^\s].*[^\s])\s*', line)

            if search:
                submodule.set_commit(search[0])

                continue

            search = re.findall(r'\s*enable\s*=\s*([^\s].*[^\s])\s*', line)

            if search:
                if (bool(search[0]) == False):
                    submodule.disable()

                continue

        return result


def get_submodules_of (repository_path):
    as_list = []

    try:
        with open(repository_path + "/.gitsubmodules", 'r') as file_stream:
            as_list = GitSubmodule.parse_all(file_stream)

    except FileNotFoundError:
        as_list = []

    return (as_list, GitSubmodule.list_as_a_dict(as_list))

def restrict_dictionary_to (dict_of_submodules, list_of_paths):
    if (list_of_paths == []):
        return dict_of_submodules

    result = dict()

    for path in list_of_paths:
        if (path not in dict_of_submodules):
            print("[F] Unknown submodule \"" + path + "\".", file = sys.stderr)

            # TODO: crash

            return dict()
        else:
            if (not dict_of_submodules[path].get_is_enabled()):
                print("[E] Ignoring disabled submodule \"" + path + "\".")

                continue

            result[path] = dict_of_submodules[path]


    return result

def apply_clone_to (submodule_dictionary, root_path):
    for submodule_path in submodule_dictionary:
        repo_path = root_path + submodule_path

        print("Cloning \"" + repo_path + "\"...")

        submodule_dictionary[submodule_path].clone_repository(root_path)

        # TODO: inflate all official Git submodules

        print("Done. Recursing clone in \"" + repo_path + "\"...")

        (recursive_list, recursive_dictionary) = get_submodules_of(repo_path)

        apply_clone_to(recursive_dictionary, root_path)

        print ("Recursive clone in \"" + repo_path + "\" completed.")


def apply_clear_to (submodule_dictionary, root_path):
    for submodule_path in submodule_dictionary:

        submodule_dictionary[submodule_path].clear(root_path)

        print("Cleared \"" + root_path + submodule_path + "\"...")

def apply_update_desc_to (submodules_dictionary, root_path):
    for submodule_path in submodule_dictionary:
        repo_path = root_path + submodule_path

        print("Updating description of \"" + repo_path + "\"...")

        submodule_dictionary[submodule_path].update_description(root_path)

        print("Done (not written yet).")

root_directory = git_find_root_path()

(submodule_list, submodule_dictionary) = get_submodules_of(root_directory)

submodule_dictionary = restrict_dictionary_to(submodule_dictionary, args.paths)

if (args.cmd == "clone"):
    apply_clone_to(submodule_dictionary, root_directory)
    git_add_to_gitignore(
        set([path for path in submodule_dictionary]),
        root_directory
    )

elif (args.cmd == "clear"):
    apply_clear_to(submodule_dictionary, root_directory)

elif (args.cmd == "update-desc"):
    git_add_to_gitignore(
        set([path for path in submodule_dictionary]),
        root_directory
    )
