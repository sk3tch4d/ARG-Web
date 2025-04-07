
import re
from datetime import datetime
from collections import defaultdict

REASON_CATEGORIES = {
    "sick": "🔵",
    "vacation": "🟠",
    "adjustment": "🟣",
    "bereavement": "⚫",
    "shift swap": "🔴",
    "banked": "🔴"
}

def clean_reason(reason):
    reason = reason.lower().replace("continued", "").replace("adjustm", "adjustment").strip()
    for key in REASON_CATEGORIES:
        if key in reason:
            return REASON_CATEGORIES[key], key.title()
    return "🔴", reason.title()

def flip_name(name):
    parts = name.split(",")
    return f"{parts[1].strip()} {parts[0].strip()}" if len(parts) == 2 else name

def get_day_emoji(start):
    try:
        hour = int(start.split(":")[0])
        if 6 <= hour < 14:
            return "☀️"
        elif 14 <= hour < 22:
            return "🌆"
        else:
            return "🌙"
    except:
        return "❓"

def parse_exceptions_section(text, date, records_df=None):
    swaps = []
    lines = text.splitlines()
    off_blocks = []
    on_blocks = []
    relief_lines = []

    for i, line in enumerate(lines):
        if line.startswith("Off:"):
            name_match = re.search(r"Off:\s+([^\d]+)\s+(\d{2}:\d{2})\s+-\s+(\d{2}:\d{2})\s+(.*)", line)
            if name_match:
                name = name_match.group(1).strip()
                start, end = name_match.group(2), name_match.group(3)
                reason = name_match.group(4).strip()
                off_blocks.append({
                    "name": name,
                    "start": start,
                    "end": end,
                    "reason": reason
                })
        elif "Relief:" in line:
            relief_lines.append(line)
        elif line.startswith("On:") and "Covering" in line:
            name_match = re.search(r"On:\s+([^\d]+)\s+(\d{2}:\d{2})\s+-\s+(\d{2}:\d{2})", line)
            if name_match:
                name = name_match.group(1).strip()
                start, end = name_match.group(2), name_match.group(3)
                on_blocks.append({
                    "name": name,
                    "start": start,
                    "end": end
                })

    # Parse relief lines to detect accurate coverage
    for line in relief_lines:
        match = re.search(r"Relief:\s+([^\d]+)\s+(\d{2}:\d{2})\s+-\s+(\d{2}:\d{2})", line)
        if match:
            name = match.group(1).strip()
            start, end = match.group(2), match.group(3)
            on_blocks.insert(0, {  # Prioritize relief-sourced coverage
                "name": name,
                "start": start,
                "end": end
            })

    for i in range(min(len(off_blocks), len(on_blocks))):
        off = off_blocks[i]
        on = on_blocks[i]

        if on["name"].strip().lower() == off["name"].strip().lower():
            continue  # skip self-coverage

        emoji, reason_label = clean_reason(off["reason"])
        time_range = f"{on['start']} - {on['end']}"
        shift_id = "?"

        if records_df is not None:
            on_name = on["name"]
            start = on["start"]
            end = on["end"]

            match = records_df[
                (records_df["Name"].str.lower() == on_name.lower()) &
                (records_df["DateObj"] == date) &
                (records_df["Start"] == start) &
                (records_df["End"] == end)
            ]
            if not match.empty:
                shift_id = match.iloc[0]["Shift"]

        if shift_id == "?":
            continue  # Skip swaps with no identifiable shift

        shift_emoji = get_day_emoji(on["start"])

        swaps.append({
            "date": date.strftime("%a, %b %d"),
            "shift": shift_id,
            "emoji": shift_emoji,
            "hours": time_range,
            "off": f"{emoji} {flip_name(off['name'])}",
            "on": f"🟢 {flip_name(on['name'])}",
            "reason": reason_label
        })

    return swaps
