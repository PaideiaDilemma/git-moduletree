import subprocess
from pathlib import Path


def bundle_repo_with_submodules():
    path = Path("repo")
    path.mkdir(exist_ok=True)

    subprocess.run(["git", "init"], cwd=path)
    subprocess.run(
        [
            "git",
            "submodule",
            "add",
            "https://github.com/PaideiaDilemma/dotnix",
            "dotnix",
        ],
        cwd=path,
    )
    subprocess.run(
        [
            "git",
            "submodule",
            "add",
            "https://github.com/PaideiaDilemma/hyprlock",
            "hyprlock",
        ],
        cwd=path,
    )

    with open(path / "README.md", "w") as f:
        f.write("Repo to demonstrate moduletree")

    subprocess.run(["git", "submodule", "init"], cwd=path)

    subprocess.run(["git", "add", "."], cwd=path)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=path)

    subprocess.run(["git", "bundle", "create", "../repo.bundle", "HEAD"], cwd=path)
    subprocess.run(["rm", "-rf", "./repo"], cwd=path.parent)


def clone_with_submodules():
    subprocess.run(["git", "clone", "--recursive", "repo.bundle", "submodule_repo"])


def clone_with_moduletree():
    subprocess.run(["git", "clone", "repo.bundle", "moduletree_repo"])
    subprocess.run(["python", "prototype.py", "-C", "moduletree_repo"])


def main():
    bundle_repo_with_submodules()
    clone_with_submodules()
    clone_with_moduletree()


if __name__ == "__main__":
    main()
