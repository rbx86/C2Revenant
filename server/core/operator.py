"""
core/operator.py: Interactive operator terminal.

Run alongside the server:
    python -m core.operator

Commands:
    beacons                     — list all beacons
    use <uuid_prefix>           — select a beacon
    shell <command>             — queue a shell task on selected beacon
    tasks                       — list tasks for selected beacon
    results <task_id>           — show output of a task
    history                     — show recent results for selected beacon
    sleep <seconds> [jitter]    — change beacon sleep (queued as note; beacon reads it next check-in)
    clear                       — clear screen
    help                        — show this help
    exit / quit                 — exit operator shell
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.prompt import Prompt

console = Console()

BANNER = """
 ██████╗██████╗      ██████╗ ██████╗ 
██╔════╝╚════██╗    ██╔════╝██╔═══██╗
██║      █████╔╝    ██║     ╚█████╔╝ 
██║     ██╔═══╝     ██║      ╚═══██╗ 
╚██████╗███████╗    ╚██████╗██████╔╝ 
 ╚═════╝╚══════╝     ╚═════╝╚═════╝  
  Adversary Emulation Framework
"""


def ts(unix: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(unix))


def status_color(status: str) -> str:
    return {"alive": "green", "dead": "red"}.get(status, "yellow")


def task_color(status: str) -> str:
    return {"pending": "yellow", "sent": "cyan", "done": "green", "error": "red"}.get(status, "white")


class OperatorShell:
    def __init__(self):
        self.selected: dict | None = None

    def prompt_str(self) -> str:
        if self.selected:
            uid = self.selected["uuid"][:8]
            host = self.selected["hostname"]
            return f"[bold red]c2[/] [dim]>[/] [cyan]{host}[/] [dim]({uid})[/] [bold]»[/] "
        return "[bold red]c2[/] [dim]>[/] [bold]»[/] "

    def cmd_beacons(self, _args):
        db.mark_dead_beacons()
        beacons = db.get_all_beacons()
        if not beacons:
            console.print("[yellow]No beacons have checked in yet.[/]")
            return

        t = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold magenta")
        t.add_column("UUID (short)", style="cyan")
        t.add_column("Hostname")
        t.add_column("User")
        t.add_column("OS")
        t.add_column("PID")
        t.add_column("Sleep")
        t.add_column("Last Seen")
        t.add_column("Status")

        for b in beacons:
            color = status_color(b["status"])
            t.add_row(
                b["uuid"][:8],
                b["hostname"],
                b["username"],
                b["os"],
                str(b["pid"]),
                f"{b['sleep']}s ±{b['jitter']}s",
                ts(b["last_seen"]),
                f"[{color}]{b['status']}[/{color}]",
            )
        console.print(t)

    def cmd_use(self, args):
        if not args:
            console.print("[red]Usage: use <uuid_prefix>[/]")
            return
        prefix = args[0].lower()
        beacons = db.get_all_beacons()
        matches = [b for b in beacons if b["uuid"].startswith(prefix)]
        if not matches:
            console.print(f"[red]No beacon matches prefix '{prefix}'[/]")
        elif len(matches) > 1:
            console.print(f"[yellow]Ambiguous prefix — {len(matches)} matches. Be more specific.[/]")
        else:
            self.selected = matches[0]
            b = self.selected
            console.print(
                Panel(
                    f"[bold]UUID:[/]     {b['uuid']}\n"
                    f"[bold]Host:[/]     {b['hostname']}\n"
                    f"[bold]User:[/]     {b['username']}\n"
                    f"[bold]OS:[/]       {b['os']} ({b['arch']})\n"
                    f"[bold]PID:[/]      {b['pid']}\n"
                    f"[bold]Sleep:[/]    {b['sleep']}s ±{b['jitter']}s\n"
                    f"[bold]Status:[/]   [{status_color(b['status'])}]{b['status']}[/{status_color(b['status'])}]\n"
                    f"[bold]Last seen:[/]{ts(b['last_seen'])}",
                    title=f"[cyan]Beacon selected[/]",
                    border_style="cyan",
                )
            )

    def cmd_shell(self, args):
        if not self.selected:
            console.print("[red]No beacon selected. Run 'use <uuid>'[/]")
            return
        if not args:
            console.print("[red]Usage: shell <command>[/]")
            return
        cmd = " ".join(args)
        task_id = db.create_task(self.selected["uuid"], "shell", {"cmd": cmd})
        console.print(f"[green]✓[/] Task queued  [dim]id={task_id}[/]  cmd=[cyan]{cmd}[/]")
        console.print(f"  [dim]Run 'results {task_id}' after the beacon checks in to see output.[/]")

    def cmd_tasks(self, _args):
        if not self.selected:
            console.print("[red]No beacon selected.[/]")
            return
        tasks = db.get_all_tasks(self.selected["uuid"])
        if not tasks:
            console.print("[yellow]No tasks for this beacon.[/]")
            return

        t = Table(box=box.SIMPLE_HEAD, header_style="bold magenta")
        t.add_column("Task ID", style="cyan")
        t.add_column("Type")
        t.add_column("Command / Payload")
        t.add_column("Status")
        t.add_column("Created")

        for task in tasks:
            payload_str = task["payload"].get("cmd", str(task["payload"]))
            color = task_color(task["status"])
            t.add_row(
                task["task_id"],
                task["type"],
                payload_str,
                f"[{color}]{task['status']}[/{color}]",
                ts(task["created_at"]),
            )
        console.print(t)

    def cmd_results(self, args):
        if not args:
            console.print("[red]Usage: results <task_id>[/]")
            return
        results = db.get_results(args[0])
        if not results:
            console.print("[yellow]No results yet for that task_id.[/]")
            return
        for r in results:
            exit_color = "green" if r["exit_code"] == 0 else "red"
            console.print(
                Panel(
                    (r["stdout"] or "[dim](no stdout)[/]"),
                    title=f"task [cyan]{r['task_id']}[/]  exit=[{exit_color}]{r['exit_code']}[/{exit_color}]"
                          f"  ({r['exec_time_ms']}ms)",
                    border_style="dim",
                )
            )
            if r["stderr"]:
                console.print(Panel(r["stderr"], title="stderr", border_style="red"))

    def cmd_history(self, _args):
        if not self.selected:
            console.print("[red]No beacon selected.[/]")
            return
        results = db.get_recent_results(self.selected["uuid"])
        if not results:
            console.print("[yellow]No results yet.[/]")
            return
        for r in results:
            import json
            try:
                payload = json.loads(r["payload"])
                cmd = payload.get("cmd", "?")
            except Exception:
                cmd = "?"
            exit_color = "green" if r["exit_code"] == 0 else "red"
            console.print(
                f"[dim]{ts(r['received_at'])}[/]  "
                f"[cyan]{r['task_id']}[/]  "
                f"[bold]$ {cmd}[/]  "
                f"exit=[{exit_color}]{r['exit_code']}[/{exit_color}]"
            )
            if r["stdout"]:
                for line in r["stdout"].splitlines()[:5]:
                    console.print(f"  {line}")
                if len(r["stdout"].splitlines()) > 5:
                    console.print(f"  [dim]... (run 'results {r['task_id']}' for full output)[/]")

    def cmd_help(self, _args):
        console.print(Panel(__doc__, title="Help", border_style="dim"))

    def cmd_clear(self, _args):
        console.clear()

    COMMANDS = {
        "beacons": cmd_beacons,
        "use": cmd_use,
        "shell": cmd_shell,
        "tasks": cmd_tasks,
        "results": cmd_results,
        "history": cmd_history,
        "help": cmd_help,
        "clear": cmd_clear,
    }

    def run(self):
        db.init_db()
        console.clear()
        console.print(f"[bold red]{BANNER}[/]")
        console.print("  Type [bold]help[/] for available commands.\n")

        while True:
            try:
                raw = console.input(self.prompt_str()).strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Bye.[/]")
                break

            if not raw:
                continue

            parts = raw.split()
            cmd, args = parts[0].lower(), parts[1:]

            if cmd in ("exit", "quit"):
                console.print("[dim]Bye.[/]")
                break

            if cmd in self.COMMANDS:
                try:
                    self.COMMANDS[cmd](self, args)
                except Exception as e:
                    console.print(f"[red]Error:[/] {e}")
            else:
                console.print(f"[red]Unknown command:[/] {cmd}. Type 'help'.")


if __name__ == "__main__":
    OperatorShell().run()
