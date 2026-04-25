#!/usr/bin/env python3
"""
BladeList — terminal to-do manager. No cloud. No accounts. Just tasks.

  todo add <text> [--high|--med|--low] [--due YYYY-MM-DD] [--tag <tag>]
  todo list [--pending|--done] [--tag <tag>] [--due]
  todo done <id>
  todo undone <id>
  todo edit <id> <new text>
  todo priority <id> <high|med|low>
  todo tag <id> <tag>
  todo due <id> <YYYY-MM-DD|clear>
  todo remove <id>
  todo search <keyword>
  todo clear --done | --all
  todo stats
  todo export [<file>]
  todo update
  todo uninstall
  todo help
"""

import sys, os, json, shutil, urllib.request
from datetime import datetime, date
from pathlib import Path

VERSION   = "1.0.0"
DATA_DIR  = Path.home() / ".bladelist"
DATA_FILE = DATA_DIR / "todos.json"
DATE_FMT  = "%Y-%m-%d"
RAW       = "https://raw.githubusercontent.com/FadingBlade/BladeList/main/BladeList.py"

# ── Colors ────────────────────────────────────────────────────────────────────

class C:
    RST  = "\033[0m";  BOLD = "\033[1m";  DIM  = "\033[2m"
    BRED = "\033[91m"; BGRN = "\033[92m"; BYEL = "\033[93m"
    BBLU = "\033[94m"; BMAG = "\033[95m"; BCYN = "\033[96m"; BWHT = "\033[97m"
    RED  = "\033[31m"; GRN  = "\033[32m"; YEL  = "\033[33m"; CYN  = "\033[36m"

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7)
    except Exception:
        for attr in [a for a in vars(C) if not a.startswith("_")]:
            setattr(C, attr, "")

PRIORITY_COLOR = {"high": C.BRED, "med": C.BYEL, "low": C.BGRN}
PRIORITY_LABEL = {"high": "HIGH", "med": "MED ", "low": "LOW "}

# ── Storage ───────────────────────────────────────────────────────────────────

def load() -> list:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

def save(todos: list):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2, ensure_ascii=False)

def next_id(todos: list) -> int:
    return max((t["id"] for t in todos), default=0) + 1

# ── Helpers ───────────────────────────────────────────────────────────────────

def cols() -> int:
    return shutil.get_terminal_size((80, 24)).columns

def ruler(char="─"):
    return C.DIM + char * min(cols(), 72) + C.RST

def fmt_date(d):
    if not d:
        return ""
    try:
        dt    = datetime.strptime(d, DATE_FMT).date()
        today = date.today()
        delta = (dt - today).days
        if delta < 0:
            return f" {C.BRED}[overdue {abs(delta)}d]{C.RST}"
        elif delta == 0:
            return f" {C.BYEL}[due today]{C.RST}"
        elif delta <= 3:
            return f" {C.BYEL}[due in {delta}d]{C.RST}"
        else:
            return f" {C.DIM}[due {d}]{C.RST}"
    except ValueError:
        return f" {C.DIM}[{d}]{C.RST}"

def fmt_tags(tags: list) -> str:
    if not tags:
        return ""
    return " " + " ".join(f"{C.BMAG}#{t}{C.RST}" for t in tags)

def fmt_item(t: dict) -> str:
    tid    = f"{C.DIM}#{t['id']:>3}{C.RST} "
    done   = t.get("done", False)
    check  = f"{C.BGRN}✔{C.RST}" if done else f"{C.DIM}○{C.RST}"
    pri    = t.get("priority", "med")
    pcol   = C.DIM if done else PRIORITY_COLOR.get(pri, C.DIM)
    plabel = PRIORITY_LABEL.get(pri, "MED ")
    text   = f"{C.DIM}{t.get('text','')}{C.RST}" if done else t.get("text", "")
    tags   = fmt_tags(t.get("tags", []))
    due    = "" if done else fmt_date(t.get("due"))
    return f"  {tid}{check} {pcol}{plabel}{C.RST}  {text}{tags}{due}"

def parse_flags(raw: list):
    priority, due, tags, text_parts = "med", None, [], []
    i = 0
    while i < len(raw):
        a = raw[i]
        if   a == "--high":                    priority = "high"
        elif a == "--med":                     priority = "med"
        elif a == "--low":                     priority = "low"
        elif a == "--due"  and i+1 < len(raw): i += 1; due = raw[i]
        elif a == "--tag"  and i+1 < len(raw): i += 1; tags.append(raw[i].lstrip("#"))
        else:                                  text_parts.append(a)
        i += 1
    return " ".join(text_parts).strip(), priority, due, tags

def die(msg: str):
    print(f"\n  {C.BRED}✖ {msg}{C.RST}\n"); sys.exit(1)

def warn(msg: str):
    print(f"\n  {C.BYEL}⚠ {msg}{C.RST}\n")

def get_id(s: str) -> int:
    try:    return int(s.lstrip("#"))
    except: die(f"'{s}' is not a valid task ID.")

def find(todos: list, tid: int) -> dict:
    for t in todos:
        if t["id"] == tid:
            return t
    die(f"No task with ID #{tid}.")

def _find_self():
    script = os.path.abspath(__file__)
    folder = os.path.dirname(script)
    return script, folder

# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_add(args):
    text, priority, due, tags = parse_flags(args)
    if not text:
        die("Usage: todo add <text> [--high|--med|--low] [--due YYYY-MM-DD] [--tag <tag>]")
    if due:
        try: datetime.strptime(due, DATE_FMT)
        except ValueError: die(f"Invalid date '{due}' — use YYYY-MM-DD")
    todos = load()
    t = {
        "id":       next_id(todos),
        "text":     text,
        "priority": priority,
        "done":     False,
        "tags":     tags,
        "due":      due,
        "created":  date.today().isoformat(),
    }
    todos.append(t)
    save(todos)
    print(f"\n  {C.BGRN}✔ Added{C.RST}\n{fmt_item(t)}\n")

def cmd_list(args):
    todos       = load()
    filter_mode = "all"
    filter_tag  = None
    sort_due    = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--pending":             filter_mode = "pending"
        elif a == "--done":              filter_mode = "done"
        elif a == "--due":               sort_due = True
        elif a == "--tag" and i+1 < len(args): i += 1; filter_tag = args[i].lstrip("#")
        i += 1

    items = todos
    if filter_mode == "pending": items = [t for t in items if not t.get("done")]
    if filter_mode == "done":    items = [t for t in items if t.get("done")]
    if filter_tag:               items = [t for t in items if filter_tag in t.get("tags", [])]
    if sort_due:
        items = sorted(items, key=lambda t: t.get("due") or "9999-99-99")

    print()
    if not items:
        print(f"  {C.DIM}No tasks found.{C.RST}\n"); return

    label = {"all": "all tasks", "pending": "pending", "done": "completed"}[filter_mode]
    if filter_tag: label += f"  #{filter_tag}"
    print(f"  {C.BOLD}{C.BCYN}BladeList{C.RST}  {C.DIM}{label}  ({len(items)}){C.RST}")
    print(f"  {ruler()}")

    pw = {"high": 0, "med": 1, "low": 2}
    if filter_mode == "all":
        pending = sorted([t for t in items if not t.get("done")],
                         key=lambda t: pw.get(t.get("priority", "med"), 1))
        items   = pending + [t for t in items if t.get("done")]
    for t in items:
        print(fmt_item(t))
    print()

def cmd_done(args):
    if not args: die("Usage: todo done <id>")
    tid = get_id(args[0]); todos = load(); t = find(todos, tid)
    if t.get("done"): warn(f"Task #{tid} is already done."); return
    t["done"] = True; t["completed"] = date.today().isoformat()
    save(todos)
    print(f"\n  {C.BGRN}✔ Done{C.RST}\n{fmt_item(t)}\n")

def cmd_undone(args):
    if not args: die("Usage: todo undone <id>")
    tid = get_id(args[0]); todos = load(); t = find(todos, tid)
    if not t.get("done"): warn(f"Task #{tid} is not done."); return
    t["done"] = False; t.pop("completed", None)
    save(todos)
    print(f"\n  {C.BYEL}↩ Reopened{C.RST}\n{fmt_item(t)}\n")

def cmd_edit(args):
    if len(args) < 2: die("Usage: todo edit <id> <new text>")
    tid = get_id(args[0]); text = " ".join(args[1:]).strip()
    if not text: die("New text cannot be empty.")
    todos = load(); t = find(todos, tid); t["text"] = text
    save(todos)
    print(f"\n  {C.BCYN}✎ Updated{C.RST}\n{fmt_item(t)}\n")

def cmd_priority(args):
    if len(args) < 2: die("Usage: todo priority <id> <high|med|low>")
    tid = get_id(args[0]); p = args[1].lower()
    if p not in ("high", "med", "low"): die("Priority must be high, med, or low.")
    todos = load(); t = find(todos, tid); t["priority"] = p
    save(todos)
    print(f"\n  {C.BCYN}✎ Priority set{C.RST}\n{fmt_item(t)}\n")

def cmd_tag(args):
    if len(args) < 2: die("Usage: todo tag <id> <tag>")
    tid = get_id(args[0]); tag = args[1].lstrip("#")
    todos = load(); t = find(todos, tid)
    if tag not in t.setdefault("tags", []): t["tags"].append(tag)
    save(todos)
    print(f"\n  {C.BMAG}# Tagged{C.RST}\n{fmt_item(t)}\n")

def cmd_due(args):
    if len(args) < 2: die("Usage: todo due <id> <YYYY-MM-DD|clear>")
    tid = get_id(args[0]); val = args[1]
    if val.lower() == "clear":
        due = None
    else:
        try: datetime.strptime(val, DATE_FMT)
        except ValueError: die(f"Invalid date '{val}' — use YYYY-MM-DD")
        due = val
    todos = load(); t = find(todos, tid); t["due"] = due
    save(todos)
    msg = "Due date " + ("cleared" if due is None else f"set to {due}")
    print(f"\n  {C.BCYN}✎ {msg}{C.RST}\n{fmt_item(t)}\n")

def cmd_remove(args):
    if not args: die("Usage: todo remove <id>")
    tid = get_id(args[0]); todos = load(); t = find(todos, tid)
    todos.remove(t); save(todos)
    print(f"\n  {C.BRED}✖ Removed{C.RST}  {C.DIM}#{tid} \"{t['text']}\"{C.RST}\n")

def cmd_search(args):
    if not args: die("Usage: todo search <keyword>")
    q = " ".join(args).lower(); todos = load()
    found = [t for t in todos
             if q in t.get("text", "").lower()
             or any(q in tag.lower() for tag in t.get("tags", []))]
    print()
    if not found:
        print(f"  {C.DIM}No results for \"{q}\".{C.RST}\n"); return
    print(f"  {C.BOLD}Search:{C.RST} {C.DIM}\"{q}\"  ({len(found)} result{'s' if len(found)!=1 else ''}){C.RST}")
    print(f"  {ruler()}")
    for t in found: print(fmt_item(t))
    print()

def cmd_clear(args):
    if not args: die("Usage: todo clear --done | --all")
    todos = load()
    if "--all" in args:
        n = len(todos); save([])
        print(f"\n  {C.BRED}✖ Cleared all {n} task{'s' if n!=1 else ''}.{C.RST}\n")
    elif "--done" in args:
        before = len(todos)
        todos  = [t for t in todos if not t.get("done")]
        save(todos); n = before - len(todos)
        print(f"\n  {C.BYEL}✖ Removed {n} completed task{'s' if n!=1 else ''}.{C.RST}\n")
    else:
        die("Usage: todo clear --done | --all")

def cmd_stats(args):
    todos   = load()
    total   = len(todos)
    done    = sum(1 for t in todos if t.get("done"))
    pending = total - done
    high    = sum(1 for t in todos if t.get("priority")=="high" and not t.get("done"))
    med     = sum(1 for t in todos if t.get("priority")=="med"  and not t.get("done"))
    low     = sum(1 for t in todos if t.get("priority")=="low"  and not t.get("done"))
    today   = date.today().isoformat()
    overdue = sum(1 for t in todos if t.get("due") and not t.get("done") and t["due"] < today)
    tag_counts = {}
    for t in todos:
        for tag in t.get("tags", []): tag_counts[tag] = tag_counts.get(tag, 0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:5]
    w = 28
    print()
    print(f"  {C.BOLD}{C.BCYN}BladeList stats{C.RST}")
    print(f"  {ruler()}")
    print(f"  {'Total':<{w}} {C.BWHT}{total}{C.RST}")
    print(f"  {'Done':<{w}} {C.BGRN}{done}{C.RST}")
    print(f"  {'Pending':<{w}} {C.BYEL}{pending}{C.RST}")
    print(f"  {ruler('·')}")
    print(f"  {C.BRED}{'High priority (pending)':<{w}}{C.RST} {high}")
    print(f"  {C.BYEL}{'Med priority (pending)':<{w}}{C.RST}  {med}")
    print(f"  {C.BGRN}{'Low priority (pending)':<{w}}{C.RST}  {low}")
    if overdue:
        print(f"  {C.BRED}{'Overdue':<{w}}{C.RST} {overdue}")
    if top_tags:
        print(f"  {ruler('·')}")
        tag_str = "  ".join(f"{C.BMAG}#{tag}{C.RST} ({n})" for tag, n in top_tags)
        print(f"  Top tags   {tag_str}")
    print()

def cmd_export(args):
    todos   = load()
    outfile = args[0] if args else None
    today   = date.today().isoformat()
    lines   = [f"BladeList Export — {today}", "=" * 50, ""]
    pending = [t for t in todos if not t.get("done")]
    done    = [t for t in todos if t.get("done")]
    pw      = {"high": 0, "med": 1, "low": 2}
    if pending:
        lines.append("PENDING")
        lines.append("-" * 30)
        for t in sorted(pending, key=lambda t: pw.get(t.get("priority","med"), 1)):
            pri  = t.get("priority","med").upper()
            tags = ("  #" + " #".join(t["tags"])) if t.get("tags") else ""
            due  = (f"  due:{t['due']}") if t.get("due") else ""
            lines.append(f"  [ ] [{pri}] {t['text']}{tags}{due}")
        lines.append("")
    if done:
        lines.append("COMPLETED")
        lines.append("-" * 30)
        for t in done:
            lines.append(f"  [x] {t['text']}  (completed {t.get('completed','')})")
        lines.append("")
    output = "\n".join(lines)
    if outfile:
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\n  {C.BGRN}✔ Exported {len(todos)} task{'s' if len(todos)!=1 else ''} to {outfile}{C.RST}\n")
    else:
        print(); print(output)

def cmd_update(args):
    script, _ = _find_self()
    print(f"\n  {C.DIM}Checking for updates...{C.RST}", flush=True)
    try:
        with urllib.request.urlopen(RAW, timeout=8) as r:
            new_src = r.read()
        new_ver = VERSION
        for line in new_src.decode().splitlines():
            if line.strip().startswith("VERSION"):
                try: new_ver = line.split('"')[1]
                except IndexError: pass
                break
        if new_ver == VERSION:
            print(f"  {C.BGRN}✔ Already up to date{C.RST}  (v{VERSION})\n")
            return
        with open(script, "wb") as f:
            f.write(new_src)
        print(f"  {C.BGRN}✔ Updated{C.RST}  v{VERSION} → v{new_ver}\n")
    except Exception as e:
        print(f"  {C.BRED}✖ Update failed:{C.RST} {e}\n")

def cmd_uninstall(args):
    script, folder = _find_self()
    print(f"\n  {C.BYEL}This will remove BladeList from your machine.{C.RST}")
    try:
        ans = input("  Are you sure? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print(f"\n  {C.DIM}Cancelled.{C.RST}\n"); return
    if ans != "y":
        print(f"  {C.DIM}Cancelled.{C.RST}\n"); return

    removed = []
    # Remove data directory
    if DATA_DIR.exists():
        try:
            shutil.rmtree(DATA_DIR); removed.append(str(DATA_DIR))
        except Exception as e:
            print(f"  {C.DIM}Could not remove {DATA_DIR}: {e}{C.RST}")

    # Remove BladeList.py
    try: os.remove(script); removed.append(script)
    except Exception as e: print(f"  {C.DIM}Could not remove {script}: {e}{C.RST}")

    # Remove todo / todo.cmd wrappers
    for wrapper in [os.path.join(folder, "todo"), os.path.join(folder, "todo.cmd")]:
        if os.path.exists(wrapper):
            try: os.remove(wrapper); removed.append(wrapper)
            except Exception as e: print(f"  {C.DIM}Could not remove {wrapper}: {e}{C.RST}")

    if removed:
        print(f"\n  {C.BGRN}✔ Removed:{C.RST}")
        for f in removed: print(f"    {C.DIM}{f}{C.RST}")
    print(f"\n  {C.DIM}BladeList uninstalled. Goodbye.{C.RST}\n")

def cmd_help(args):
    print(f"""
  {C.BOLD}{C.BCYN}BladeList{C.RST} {C.DIM}v{VERSION}{C.RST}  — terminal to-do manager

  {C.BOLD}Commands:{C.RST}
    {C.BCYN}todo add <text>{C.RST} {C.DIM}[--high|--med|--low] [--due YYYY-MM-DD] [--tag <tag>]{C.RST}
    {C.BCYN}todo list{C.RST} {C.DIM}[--pending|--done] [--tag <tag>] [--due]{C.RST}
    {C.BCYN}todo done <id>{C.RST}                    mark task complete
    {C.BCYN}todo undone <id>{C.RST}                  reopen a task
    {C.BCYN}todo edit <id> <text>{C.RST}             edit task text
    {C.BCYN}todo priority <id> <high|med|low>{C.RST} change priority
    {C.BCYN}todo tag <id> <tag>{C.RST}               add a tag
    {C.BCYN}todo due <id> <YYYY-MM-DD|clear>{C.RST}  set or clear due date
    {C.BCYN}todo remove <id>{C.RST}                  delete a task
    {C.BCYN}todo search <keyword>{C.RST}             search tasks + tags
    {C.BCYN}todo clear --done | --all{C.RST}         bulk remove
    {C.BCYN}todo stats{C.RST}                        summary stats
    {C.BCYN}todo export [<file>]{C.RST}              dump tasks to .txt
    {C.BCYN}todo update{C.RST}                       update to latest version
    {C.BCYN}todo uninstall{C.RST}                    remove BladeList
    {C.BCYN}todo help{C.RST}                         show this help

  {C.BOLD}Shortcuts:{C.RST}
    {C.DIM}add→a  list→ls  done→d  remove→rm  search→s{C.RST}

  {C.BOLD}Priority colors:{C.RST}
    {C.BRED}HIGH{C.RST}   {C.BYEL}MED{C.RST}   {C.BGRN}LOW{C.RST}

  {C.DIM}Data stored at: {DATA_FILE}{C.RST}
""")

# ── Main ──────────────────────────────────────────────────────────────────────

ALIASES = {"a": "add", "ls": "list", "d": "done", "rm": "remove", "s": "search"}

DISPATCH = {
    "add":       cmd_add,
    "list":      cmd_list,
    "done":      cmd_done,
    "undone":    cmd_undone,
    "edit":      cmd_edit,
    "priority":  cmd_priority,
    "tag":       cmd_tag,
    "due":       cmd_due,
    "remove":    cmd_remove,
    "search":    cmd_search,
    "clear":     cmd_clear,
    "stats":     cmd_stats,
    "export":    cmd_export,
    "update":    cmd_update,
    "uninstall": cmd_uninstall,
    "help":      cmd_help,
}

def main():
    args = sys.argv[1:]
    if not args:
        cmd_help([]); return
    cmd  = ALIASES.get(args[0].lower(), args[0].lower())
    rest = args[1:]
    if cmd in DISPATCH:
        DISPATCH[cmd](rest)
    else:
        die(f"Unknown command: '{cmd}' — try todo help")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C.DIM}Bye.{C.RST}")
