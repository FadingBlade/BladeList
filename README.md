# BladeList

Terminal to-do manager. No cloud. No accounts. Just tasks.

```
todo add "finish the report" --high --due 2026-05-01 --tag work
todo list
todo done 1
todo stats
```

---

## Install

**Windows — PowerShell**
```powershell
irm https://raw.githubusercontent.com/FadingBlade/BladeList/main/install.ps1 | iex
```

**Linux / macOS**
```sh
curl -fsSL https://raw.githubusercontent.com/FadingBlade/BladeList/main/install.sh | sh
```

Requires **Python 3.7+**. The installer will offer to install Python automatically if it's missing.

---

## Commands

| Command | Shortcut | Description |
|---|---|---|
| `todo add <text>` | `todo a` | Add a task |
| `todo list` | `todo ls` | List all tasks |
| `todo list --pending` | | Show only undone |
| `todo list --done` | | Show only completed |
| `todo list --tag <tag>` | | Filter by tag |
| `todo list --due` | | Sort by due date |
| `todo done <id>` | `todo d` | Mark task complete |
| `todo undone <id>` | | Reopen a task |
| `todo edit <id> <text>` | | Edit task text |
| `todo priority <id> high\|med\|low` | | Change priority |
| `todo tag <id> <tag>` | | Add a tag |
| `todo due <id> <YYYY-MM-DD\|clear>` | | Set or clear due date |
| `todo remove <id>` | `todo rm` | Delete a task |
| `todo search <keyword>` | `todo s` | Search tasks + tags |
| `todo clear --done` | | Remove all completed |
| `todo clear --all` | | Remove everything |
| `todo stats` | | Summary statistics |
| `todo export [<file>]` | | Dump tasks to .txt |
| `todo update` | | Update to latest version |
| `todo uninstall` | | Remove BladeList |
| `todo help` | | Show help |

## Flags for `add`

| Flag | Description |
|---|---|
| `--high` / `--med` / `--low` | Priority (default: `med`) |
| `--due YYYY-MM-DD` | Set a due date |
| `--tag <tag>` | Add a tag (repeat for multiple) |

## Priority colors

| Priority | Color |
|---|---|
| `HIGH` | Red |
| `MED` | Yellow |
| `LOW` | Green |

---

## Examples

```sh
# Add tasks
todo add "buy milk" --low
todo add "finish report" --high --due 2026-05-01 --tag work
todo add "call dentist" --med --due 2026-04-30 --tag personal --tag health

# View tasks
todo list
todo list --pending --tag work
todo list --due

# Manage tasks
todo done 2
todo edit 1 "buy oat milk"
todo priority 3 high
todo tag 3 urgent
todo due 3 2026-06-01
todo due 3 clear

# Bulk & stats
todo stats
todo search dentist
todo export ~/my-tasks.txt
todo clear --done

# Maintenance
todo update
todo uninstall
```

---

## Data

Tasks are stored at `~/.bladelist/todos.json` — plain JSON, yours forever.

---

Made by FadingBlade · [BladeChat](https://github.com/FadingBlade/BladeChat)
