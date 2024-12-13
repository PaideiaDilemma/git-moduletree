# git ${{\color{Gray}\tiny{\text{sub\}}}\text{module}\color{Gray}\tiny{\text{work\}}}\text{tree}\$

Git submodules can be a pain to work with.
This repository explores a different approach of using them.

**The idea**: Take a submodule, add it's upstream as a remote and then create a git worktree based on the current submodule commit.

## git-moduletree prototype

### `git moduletree init`

This command will parse `.gitmodules` and add a remote for each submodule.
It will then create a new worktree based on the added remote and the ref that `git submodule status` returns.

### `git moduletree status`

This command gets the current `HEAD` of the worktree and compares it to the ref that `git submodule status` returns.

### Updating

After updating the worktree of a submodule, changes can be added and committed as usual.

### Adding a new module

Not implemented yet. Use `git submodule add` and remove it afterwards.
