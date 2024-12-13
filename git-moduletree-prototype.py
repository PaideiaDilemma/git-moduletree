#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class GitSubmoduleConfig:
    path: str
    url: str
    branch: Optional[str] = None


def parse_gitmodules(repo_path) -> list[GitSubmoduleConfig]:
    try:
        with open(repo_path / ".gitmodules", "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"No submodules found here: {(repo_path / '.gitmodules').absolute()}")
        return []

    submodules = []
    submodule_indices = (i for i, line in enumerate(lines) if '[submodule "' in line)
    submodule_index = next(submodule_indices, len(lines))
    while submodule_index < len(lines):
        next_submodule_index = next(submodule_indices, len(lines))
        gen = (
            line.strip().split("=", 2)
            for line in lines[submodule_index + 1 : next_submodule_index]
            if not line.strip().startswith(";")  # igore comments
        )
        submodules.append(GitSubmoduleConfig(**{k.strip(): v.strip() for k, v in gen}))
        submodule_index = next_submodule_index

    return submodules


def purge_actual_submodules(repo_path: Path, submodules: list[GitSubmoduleConfig]):
    for submodule in submodules:
        # TODO: check if the submodule was cloned and refuse per default
        print(f"Removing {repo_path / submodule.path}")
        subprocess.run(["rm", "-r", repo_path / submodule.path])


def parse_submodule_status(repo_path: Path) -> list[tuple[str, str]]:
    output = subprocess.check_output(["git", "submodule", "status"], cwd=repo_path)
    res = []
    for line in output.decode().splitlines():
        if not line:
            continue

        rev, path = line.strip().split(" ")[:2]
        res.append((rev.lstrip("-").strip("+"), path))
    return res


@dataclass
class Module:
    relpath: Path
    url: str
    remote: str
    ref: str


def get_modules(repo_path: Path) -> list[Module]:
    submodule_configs = parse_gitmodules(repo_path)
    submodule_status = parse_submodule_status(repo_path)

    modules = []
    for submodule_config in submodule_configs:
        ref = next(
            (rev for rev, path in submodule_status if submodule_config.path == path),
            submodule_config.branch,
        )
        if not ref:
            print(f"No ref for {submodule_config.path}")
            continue
        remote_name = f"module-{submodule_config.path}"
        modules.append(
            Module(
                relpath=Path(submodule_config.path),
                url=submodule_config.url,
                remote=remote_name,
                ref=ref,
            )
        )

    return modules


def add_remote(repo_path: Path, module: Module):
    subprocess.run(
        ["git", "remote", "add", module.remote, module.url],
        cwd=repo_path,
    )


def add_worktree(repo_path: Path, module: Module):
    subprocess.run(
        ["git", "fetch", "--depth", "2", module.remote, module.ref], cwd=repo_path
    )
    subprocess.run(
        [
            "git",
            "worktree",
            "add",
            "-f",
            module.relpath,
            f"{module.ref}",
        ],
        cwd=repo_path,
    )


def init_module(repo_path: Path, submodule: Module):
    add_remote(repo_path, submodule)
    add_worktree(repo_path, submodule)


def get_current_module_commit(repo_path: Path, module: Module):
    return (
        subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_path / module.relpath
        )
        .decode()
        .strip()
    )


class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    RESET = "\033[0m"


def status_module(repo_path: Path, module: Module):
    commit = get_current_module_commit(repo_path, module)
    status = (
        f"{Colors.GREEN}In sync{Colors.RESET}"
        if commit == module.ref
        else f"{Colors.RED}Out of sync{Colors.RESET} (submodule state: {module.ref})"
    )
    print(f"{commit} {module.relpath} {status}")


def handle_command(
    command: Callable[[Path, Module], None],
    repo_path: Path,
    process_modules: list[str] = [],
    recursive: bool = False,
):
    modules = get_modules(repo_path)
    for module in modules:
        if process_modules and module.relpath not in process_modules:
            continue

        command(repo_path, module)

        if recursive:
            handle_command(
                command=command,
                repo_path=(repo_path / module.relpath).resolve(),
                process_modules=process_modules,
                recursive=recursive,
            )


COMMANDS = ["init", "status"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str, choices=COMMANDS)
    parser.add_argument(
        "-C",
        "--repo-path",
        type=Path,
        default=Path("."),
        help="Path to the repository. Defaults to the current directory.",
    )
    parser.add_argument(
        "-M",
        "--modules",
        nargs="+",
        help="(Sub)modules to process",
        default=[],
    )
    parser.add_argument(
        "--recursive", action="store_true", help="Process (sub)modules recursively"
    )

    parser.prog = "git moduletree"
    args = parser.parse_args()

    if args.command == "init":
        submodule_configs = parse_gitmodules(args.repo_path)
        purge_actual_submodules(args.repo_path, submodule_configs)
        handle_command(init_module, args.repo_path, args.modules, args.recursive)
    elif args.command == "status":
        handle_command(status_module, args.repo_path, args.modules, args.recursive)


if __name__ == "__main__":
    main()
