#!/usr/bin/env python3
"""
C++ Study Progress Tracker
A simple CLI tool to track progress through the C++ Quantitative Finance Learning Path
"""

import json
import re
import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import shutil
from collections import defaultdict

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.panel import Panel
    from rich import box
    from rich.text import Text
except ImportError:
    print("Please install 'rich' library: pip install rich")
    exit(1)

console = Console()


class StudyTracker:
    def __init__(
        self,
        markdown_file="cpp-quant-study-plan.md",
        progress_file=".study_progress.json",
    ):
        self.markdown_file = markdown_file
        self.progress_file = progress_file
        self.markdown_content = []
        self.checkboxes = []
        self.progress_data = self.load_progress()

    def load_progress(self) -> Dict:
        """Load progress data from hidden JSON file"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r") as f:
                    return json.load(f)
            except:
                return self.create_initial_progress()
        return self.create_initial_progress()

    def create_initial_progress(self) -> Dict:
        """Create initial progress structure"""
        return {
            "start_date": datetime.now().isoformat(),
            "last_activity": None,
            "completed_days": [],
            "history": [],
            "stats": {
                "total_study_sessions": 0,
                "longest_streak": 0,
                "current_streak": 0,
            },
        }

    def save_progress(self):
        """Save progress data to hidden JSON file"""
        with open(self.progress_file, "w") as f:
            json.dump(self.progress_data, f, indent=2)

    def parse_markdown(self):
        """Parse markdown file to find all checkboxes and their content"""
        if not os.path.exists(self.markdown_file):
            console.print(f"[red]Error: {self.markdown_file} not found![/red]")
            exit(1)

        with open(self.markdown_file, "r", encoding="utf-8") as f:
            self.markdown_content = f.readlines()

        self.checkboxes = []
        current_week = 0
        current_phase = ""

        for i, line in enumerate(self.markdown_content):
            # Track current week
            if "### Week" in line:
                week_match = re.search(r"Week (\d+)", line)
                if week_match:
                    current_week = int(week_match.group(1))

            # Track current phase
            if "## 📅 PHASE" in line:
                current_phase = line.strip()

            # Find checkboxes with Day pattern
            if "- [ ]" in line or "- [x]" in line or "- [X]" in line:
                day_match = re.search(r"Day (\d+)", line)
                if day_match:
                    day_num = int(day_match.group(1))
                    is_checked = "- [x]" in line.lower()
                    content = line.strip()

                    self.checkboxes.append(
                        {
                            "line_index": i,
                            "day": day_num,
                            "week": current_week,
                            "phase": current_phase,
                            "checked": is_checked,
                            "content": content,
                            "full_line": line,
                        }
                    )

    def get_current_day(self) -> int:
        """Get the next uncompleted day number"""
        for cb in self.checkboxes:
            if not cb["checked"]:
                return cb["day"]
        return len(self.checkboxes) + 1  # All completed

    def mark_day_complete(self, day: Optional[int] = None) -> bool:
        """Mark a day as complete"""
        if day is None:
            day = self.get_current_day()

        for cb in self.checkboxes:
            if cb["day"] == day and not cb["checked"]:
                # Update markdown content
                line_index = cb["line_index"]
                self.markdown_content[line_index] = self.markdown_content[
                    line_index
                ].replace("- [ ]", "- [x]")

                # Update progress data
                self.progress_data["completed_days"].append(day)
                self.progress_data["last_activity"] = datetime.now().isoformat()
                self.progress_data["stats"]["total_study_sessions"] += 1

                # Add to history
                self.progress_data["history"].append(
                    {
                        "action": "complete",
                        "day": day,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                # Update streak
                self.update_streak()

                # Save files
                self.save_markdown()
                self.save_progress()

                return True
        return False

    def save_markdown(self):
        """Save updated markdown content back to file"""
        with open(self.markdown_file, "w", encoding="utf-8") as f:
            f.writelines(self.markdown_content)

    def update_streak(self):
        """Update study streak statistics"""
        if not self.progress_data["history"]:
            return

        # Sort history by date
        dates = []
        for entry in self.progress_data["history"]:
            if entry["action"] == "complete":
                date = datetime.fromisoformat(entry["timestamp"]).date()
                if date not in dates:
                    dates.append(date)

        dates.sort()

        if not dates:
            return

        # Calculate current streak
        current_streak = 1
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        if dates[-1] == today or dates[-1] == yesterday:
            for i in range(len(dates) - 2, -1, -1):
                if dates[i + 1] - dates[i] == timedelta(days=1):
                    current_streak += 1
                else:
                    break
        else:
            current_streak = 0

        self.progress_data["stats"]["current_streak"] = current_streak
        self.progress_data["stats"]["longest_streak"] = max(
            self.progress_data["stats"]["longest_streak"], current_streak
        )

    def undo_last_action(self) -> bool:
        """Undo the last completed day"""
        if not self.progress_data["history"]:
            return False

        # Find last 'complete' action
        last_complete = None
        for entry in reversed(self.progress_data["history"]):
            if entry["action"] == "complete":
                last_complete = entry
                break

        if not last_complete:
            return False

        day = last_complete["day"]

        # Update markdown
        for cb in self.checkboxes:
            if cb["day"] == day and cb["checked"]:
                line_index = cb["line_index"]
                self.markdown_content[line_index] = self.markdown_content[
                    line_index
                ].replace("- [x]", "- [ ]")

                # Update progress data
                self.progress_data["completed_days"].remove(day)
                self.progress_data["history"].append(
                    {
                        "action": "undo",
                        "day": day,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                # Save files
                self.save_markdown()
                self.save_progress()
                return True

        return False

    def show_status(self):
        """Show detailed progress status"""
        self.parse_markdown()

        total_days = len(self.checkboxes)
        completed_days = len([cb for cb in self.checkboxes if cb["checked"]])
        current_day = self.get_current_day()

        # Calculate phase progress
        phase_progress = defaultdict(lambda: {"total": 0, "completed": 0})
        for cb in self.checkboxes:
            phase = (
                cb["phase"].replace("## 📅 ", "").strip() if cb["phase"] else "Unknown"
            )
            phase_progress[phase]["total"] += 1
            if cb["checked"]:
                phase_progress[phase]["completed"] += 1

        # Calculate week progress
        current_week = 0
        week_total = 0
        week_completed = 0
        for cb in self.checkboxes:
            if cb["day"] == current_day:
                current_week = cb["week"]
                break

        for cb in self.checkboxes:
            if cb["week"] == current_week:
                week_total += 1
                if cb["checked"]:
                    week_completed += 1

        # Create status panel
        progress_percent = (completed_days / total_days * 100) if total_days > 0 else 0

        status_text = f"""[bold cyan]Current:[/bold cyan] Day {current_day}/{total_days} ({progress_percent:.1f}%)
[bold cyan]Phase:[/bold cyan] {[cb["phase"].replace("## 📅 ", "") for cb in self.checkboxes if cb["day"] == current_day][0] if current_day <= total_days else "Completed!"}
[bold cyan]This Week:[/bold cyan] {week_completed}/{week_total} days completed (Week {current_week})
[bold cyan]Total Study Sessions:[/bold cyan] {self.progress_data["stats"]["total_study_sessions"]}
[bold cyan]Current Streak:[/bold cyan] {self.progress_data["stats"]["current_streak"]} days
[bold cyan]Longest Streak:[/bold cyan] {self.progress_data["stats"]["longest_streak"]} days"""

        # Milestones
        milestones = {84: "Junior C++ Level", 168: "Course Completion"}

        next_milestone = None
        for day, desc in sorted(milestones.items()):
            if day > completed_days:
                next_milestone = (
                    f"Day {day} - {desc} ({day - completed_days} days away)"
                )
                break

        if next_milestone:
            status_text += f"\n[bold cyan]Next Milestone:[/bold cyan] {next_milestone}"

        # Projects completed
        mini_projects = 0
        major_projects = 0
        for cb in self.checkboxes:
            if cb["checked"] and "Mini Project:" in cb["content"]:
                mini_projects += 1
            elif (
                cb["checked"]
                and "Project:" in cb["content"]
                and "Mini" not in cb["content"]
            ):
                major_projects += 1

        status_text += f"\n[bold cyan]Projects Completed:[/bold cyan] {mini_projects}/8 mini, {major_projects}/8 major"

        console.print(Panel(status_text, title="📊 Study Progress", box=box.ROUNDED))

        # Phase breakdown table
        if len(phase_progress) > 1:
            table = Table(title="Phase Breakdown", box=box.SIMPLE)
            table.add_column("Phase", style="cyan")
            table.add_column("Progress", style="green")
            table.add_column("Percentage", style="yellow")

            for phase, data in phase_progress.items():
                if phase and phase != "Unknown":
                    percentage = (
                        (data["completed"] / data["total"] * 100)
                        if data["total"] > 0
                        else 0
                    )
                    table.add_row(
                        phase,
                        f"{data['completed']}/{data['total']}",
                        f"{percentage:.1f}%",
                    )

            console.print(table)

    def show_next(self):
        """Show next day's tasks"""
        self.parse_markdown()
        current_day = self.get_current_day()

        if current_day > len(self.checkboxes):
            console.print(
                "[green]🎉 Congratulations! You've completed the entire course![/green]"
            )
            return

        # Find all tasks for the next day
        day_tasks = []
        week = 0
        phase = ""

        for cb in self.checkboxes:
            if cb["day"] == current_day:
                day_tasks.append(cb["content"])
                week = cb["week"]
                phase = cb["phase"].replace("## 📅 ", "") if cb["phase"] else ""

        # Check if it's a difficult topic
        is_difficult = any("🔥" in task for task in day_tasks)

        # Create next day panel
        next_text = f"[bold]Day {current_day} - Week {week}[/bold]\n"
        next_text += f"[dim]{phase}[/dim]\n\n"

        if is_difficult:
            next_text += "[red]🔥 Challenging Topic Alert![/red]\n\n"

        next_text += "[bold]Tasks:[/bold]\n"
        for task in day_tasks:
            # Clean up the task text
            task_clean = re.sub(r"^- \[.\] ", "", task)
            next_text += f"  • {task_clean}\n"

        # Check if weekend project
        if any("Project:" in task for task in day_tasks):
            next_text += "\n[yellow]📝 Project Day - Allow extra time![/yellow]"

        # Check if review day
        if any("REVIEW" in task for task in day_tasks):
            next_text += "\n[green]📚 Review Day - Consolidate your learning![/green]"

        console.print(Panel(next_text, title="📅 Next Study Session", box=box.ROUNDED))

    def show_week_summary(self):
        """Show current week's progress"""
        self.parse_markdown()
        current_day = self.get_current_day()

        # Find current week
        current_week = 1
        for cb in self.checkboxes:
            if cb["day"] >= current_day:
                current_week = cb["week"]
                break

        # Get all days in current week
        week_days = [cb for cb in self.checkboxes if cb["week"] == current_week]

        if not week_days:
            console.print("[red]No data found for current week[/red]")
            return

        # Create week summary
        table = Table(title=f"Week {current_week} Summary", box=box.SIMPLE)
        table.add_column("Day", style="cyan", width=8)
        table.add_column("Status", style="green", width=10)
        table.add_column("Topic", style="white")

        for cb in week_days:
            status = "✅ Done" if cb["checked"] else "⏳ Pending"
            topic = re.sub(r"^- \[.\] Day \d+ \([^)]+\)\s*", "", cb["content"])
            topic = topic[:50] + "..." if len(topic) > 50 else topic

            table.add_row(f"Day {cb['day']}", status, topic)

        console.print(table)

        # Week statistics
        completed = len([d for d in week_days if d["checked"]])
        total = len(week_days)
        percentage = (completed / total * 100) if total > 0 else 0

        stats_text = f"\n[bold]Week Progress:[/bold] {completed}/{total} days ({percentage:.1f}%)"

        # Check for projects this week
        projects = [d for d in week_days if "Project:" in d["content"]]
        if projects:
            stats_text += (
                f"\n[bold]Projects:[/bold] {len(projects)} project(s) this week"
            )
            for p in projects:
                project_name = re.search(r"Project: ([^-]+)", p["content"])
                if project_name:
                    status = "✅" if p["checked"] else "⏳"
                    stats_text += f"\n  {status} {project_name.group(1).strip()}"

        console.print(stats_text)

    def jump_to_day(self, day: int):
        """Jump to a specific day (mark all previous as complete)"""
        self.parse_markdown()

        if day < 1 or day > len(self.checkboxes):
            console.print(
                f"[red]Invalid day number. Must be between 1 and {len(self.checkboxes)}[/red]"
            )
            return

        completed_count = 0
        for cb in self.checkboxes:
            if cb["day"] < day and not cb["checked"]:
                self.mark_day_complete(cb["day"])
                completed_count += 1

        if completed_count > 0:
            console.print(f"[green]Marked {completed_count} days as complete[/green]")
            self.show_status()
        else:
            console.print(
                "[yellow]No changes needed - already at or past this day[/yellow]"
            )

    def show_stats(self):
        """Show overall statistics"""
        self.parse_markdown()

        total_days = len(self.checkboxes)
        completed_days = len([cb for cb in self.checkboxes if cb["checked"]])

        # Calculate time-based stats
        start_date = datetime.fromisoformat(self.progress_data["start_date"])
        days_since_start = (datetime.now() - start_date).days + 1

        # Study frequency
        study_frequency = (
            (
                self.progress_data["stats"]["total_study_sessions"]
                / days_since_start
                * 100
            )
            if days_since_start > 0
            else 0
        )

        # Average days per week
        weeks_elapsed = days_since_start / 7
        avg_days_per_week = (
            (self.progress_data["stats"]["total_study_sessions"] / weeks_elapsed)
            if weeks_elapsed > 0
            else 0
        )

        # Estimated completion
        if completed_days > 0 and days_since_start > 0:
            days_per_session = days_since_start / completed_days
            remaining_days = total_days - completed_days
            estimated_days = remaining_days * days_per_session
            estimated_completion = datetime.now() + timedelta(days=estimated_days)
            estimated_date = estimated_completion.strftime("%B %d, %Y")
        else:
            estimated_date = "N/A"

        # Create statistics panel
        stats_text = f"""[bold cyan]Overall Progress:[/bold cyan] {completed_days}/{total_days} days ({completed_days / total_days * 100:.1f}%)
[bold cyan]Study Since:[/bold cyan] {start_date.strftime("%B %d, %Y")} ({days_since_start} days ago)
[bold cyan]Total Sessions:[/bold cyan] {self.progress_data["stats"]["total_study_sessions"]}
[bold cyan]Study Frequency:[/bold cyan] {study_frequency:.1f}% of days
[bold cyan]Average:[/bold cyan] {avg_days_per_week:.1f} days per week
[bold cyan]Current Streak:[/bold cyan] {self.progress_data["stats"]["current_streak"]} days
[bold cyan]Longest Streak:[/bold cyan] {self.progress_data["stats"]["longest_streak"]} days
[bold cyan]Estimated Completion:[/bold cyan] {estimated_date}"""

        console.print(Panel(stats_text, title="📈 Study Statistics", box=box.ROUNDED))

        # Phase timeline
        phase_data = defaultdict(
            lambda: {"total": 0, "completed": 0, "start_day": 999, "end_day": 0}
        )

        for cb in self.checkboxes:
            phase = (
                cb["phase"].replace("## 📅 ", "").strip() if cb["phase"] else "Unknown"
            )
            phase_data[phase]["total"] += 1
            if cb["checked"]:
                phase_data[phase]["completed"] += 1
            phase_data[phase]["start_day"] = min(
                phase_data[phase]["start_day"], cb["day"]
            )
            phase_data[phase]["end_day"] = max(phase_data[phase]["end_day"], cb["day"])

        # Create phase timeline
        console.print("\n[bold]📍 Phase Timeline:[/bold]")
        for phase, data in phase_data.items():
            if phase and phase != "Unknown":
                percentage = (
                    (data["completed"] / data["total"] * 100)
                    if data["total"] > 0
                    else 0
                )
                status = "✅" if percentage == 100 else "🔄"
                console.print(
                    f"{status} {phase}: Days {data['start_day']}-{data['end_day']} ({percentage:.0f}% complete)"
                )

    def backup_markdown(self):
        """Create a backup of the markdown file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self.markdown_file}.backup_{timestamp}"

        try:
            shutil.copy2(self.markdown_file, backup_name)
            console.print(f"[green]✅ Backup created: {backup_name}[/green]")
        except Exception as e:
            console.print(f"[red]Error creating backup: {e}[/red]")


def main():
    parser = argparse.ArgumentParser(description="C++ Study Progress Tracker")
    parser.add_argument(
        "--done", action="store_true", help="Mark next uncompleted day as done"
    )
    parser.add_argument(
        "--status", action="store_true", help="Show detailed progress status (default)"
    )
    parser.add_argument("--next", action="store_true", help="Show next day's tasks")
    parser.add_argument(
        "--week-summary", action="store_true", help="Show current week summary"
    )
    parser.add_argument("--jump-to", type=int, help="Jump to specific day number")
    parser.add_argument("--stats", action="store_true", help="Show overall statistics")
    parser.add_argument("--undo", action="store_true", help="Undo last completed day")
    parser.add_argument(
        "--backup", action="store_true", help="Create backup of markdown file"
    )

    args = parser.parse_args()

    tracker = StudyTracker()

    # Handle commands
    if args.done:
        current_day = tracker.get_current_day()
        if tracker.mark_day_complete():
            console.print(f"[green]✅ Day {current_day} marked as complete![/green]\n")
            tracker.show_status()
        else:
            console.print("[red]Failed to mark day as complete[/red]")

    elif args.undo:
        if tracker.undo_last_action():
            console.print("[green]✅ Last action undone![/green]\n")
            tracker.show_status()
        else:
            console.print("[red]No action to undo[/red]")

    elif args.next:
        tracker.show_next()

    elif args.week_summary:
        tracker.show_week_summary()

    elif args.jump_to:
        tracker.jump_to_day(args.jump_to)

    elif args.stats:
        tracker.show_stats()

    elif args.backup:
        tracker.backup_markdown()

    else:  # Default to status
        tracker.show_status()


if __name__ == "__main__":
    main()
