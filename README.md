# BladeList
Local terminal to-do list.
## Install
**Linux / macOS:**
```sh
curl -fsSL https://raw.githubusercontent.com/FadingBlade/BladeList/main/install.sh | sh
```
**Windows PowerShell:**
```powershell
irm https://raw.githubusercontent.com/FadingBlade/BladeList/main/install.ps1 | iex
```
The installer detects your OS and installs Python if needed and adds the `todo` command to your PATH.

---

## Commands
```
todo add <text>                    add a task
todo add <text> --high             add a high priority task
todo add <text> --due YYYY-MM-DD   add a task with a due date
todo add <text> --tag <tag>        add a task with a tag
todo list                          list all tasks
todo list --pending                show only undone tasks
todo list --done                   show only completed tasks
todo list --tag <tag>              filter by tag
todo list --due                    sort by due date
todo done <id>                     mark a task complete
todo undone <id>                   reopen a task
todo edit <id> <text>              edit task text
todo priority <id> <high|med|low>  change priority
todo tag <id> <tag>                add a tag to a task
todo due <id> <YYYY-MM-DD|clear>   set or clear a due date
todo remove <id>                   delete a task
todo search <keyword>              search tasks and tags
todo clear --done                  remove all completed tasks
todo clear --all                   remove everything
todo stats                         show summary stats
todo export [<file>]               dump tasks to a .txt file
todo update                        update to the latest version
todo uninstall                     remove BladeList
todo help                          show all commands
todo                               show all commands
```

---

## Requirements
- Python 3.7+ (installer handles this)
- Works fully offline — no internet needed after install

---

## Uninstall
**Linux / macOS:** `rm ~/.local/bin/todo ~/.local/bin/BladeList.py`

**Windows:** Delete `%USERPROFILE%\.BladeList` and remove it from PATH in System Settings.

(Or just run `todo uninstall`)
