
# === Auto-install missing packages ===
try:
    import fitz, pdfplumber, pandas, matplotlib, seaborn, openpyxl
except ImportError:
    import subprocess
    import sys
    print("Installing missing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install",
        "PyMuPDF", "pdfplumber", "pandas", "matplotlib", "seaborn", "openpyxl"])
    print("All dependencies installed. Continuing...")

import sys
import os
import re
import fitz
import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Side, Font

TEMPLATE_FILE = "ARGX_Example.xlsx"
VALID_NAMES = {
    "Adeniyi, Oluwaseyi", "Bhardwaj, Liam", "Donovan, Patrick", "Gallivan, David",
    "Janaway, Alexander", "Robichaud, Richard", "Santo, Jaime", "Tobin, James",
    "Ukwesa, Jennifer", "Vanderputten, Richard", "Woodland, Nathaniel"
}
BASE_DATE = datetime(2025, 1, 13)

def classify_shift(start, end, shift_ids):
    if "313" in shift_ids:
        return "Day"
    s = datetime.strptime(start, "%H:%M").time()
    e = datetime.strptime(end, "%H:%M").time()
    if s >= datetime.strptime("07:00", "%H:%M").time() and e <= datetime.strptime("15:00", "%H:%M").time():
        return "Day"
    if s >= datetime.strptime("15:00", "%H:%M").time() and e <= datetime.strptime("23:00", "%H:%M").time():
        return "Evening"
    if s >= datetime.strptime("23:00", "%H:%M").time() or e <= datetime.strptime("07:00", "%H:%M").time():
        return "Night"
    if (s >= datetime.strptime("08:00", "%H:%M").time() and e <= datetime.strptime("12:00", "%H:%M").time()):
        return "Day"
    return "Other"

def get_pay_period(date_obj):
    return (date_obj - BASE_DATE.date()).days // 14

def extract_shift_ids(line):
    return [t for t in line.split() if re.match(r'(SA[1-4]|[A-Z]*\d{3,4})$', t, re.IGNORECASE)]

def parse_pdf(pdf_path):
    records = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.splitlines() if text else []

            current_date = None
            for line in lines:
                if "Inventory Services" in line:
                    try:
                        current_date = datetime.strptime(line.split()[-1], "%d/%b/%Y").date()
                    except:
                        continue
                    continue
                if any(x in line for x in ["Off:", "On Call", "Relief"]):
                    continue
                tokens = line.strip().split()
                if len(tokens) >= 5:
                    try:
                        start_time = tokens[-4]
                        end_time = tokens[-3]
                        full_name = f"{tokens[-2].rstrip(',')}, {tokens[-1]}"
                        if full_name not in VALID_NAMES:
                            continue
                        shift_ids = extract_shift_ids(line)
                        full_shift_id = " ".join(shift_ids).strip()
                        dt_start = datetime.strptime(f"{current_date} {start_time}", "%Y-%m-%d %H:%M")
                        dt_end = datetime.strptime(f"{current_date} {end_time}", "%Y-%m-%d %H:%M")
                        if dt_end <= dt_start:
                            dt_end += timedelta(days=1)
                        hours = round((dt_end - dt_start).seconds / 3600, 1)
                        shift_type = classify_shift(start_time, end_time, shift_ids)
                        records.append({
                            "Name": full_name,
                            "Date": current_date.strftime("%a, %b %d"),
                            "DateObj": current_date,
                            "Shift": full_shift_id,
                            "Type": shift_type,
                            "Hours": hours,
                            "Start": start_time,
                            "End": end_time
                        })
                    except:
                        continue
    return pd.DataFrame(records)

def latest_pdf(files):
    by_date = {}
    for f in files:
        name = os.path.basename(f)
        match = re.search(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})", name)
        if match:
            date = match.group(1)
            timestamp = match.group(2)
            key = date
            if key not in by_date or timestamp > by_date[key][1]:
                by_date[key] = (f, timestamp)
    return [v[0] for v in by_date.values()]

def write_argx(df, template_path):
    wb = load_workbook(template_path)
    grouped = df.groupby("Name")
    border_box = Border(left=Side(style="thin"), right=Side(style="thin"),
                        top=Side(style="thin"), bottom=Side(style="thin"))
    medium_bottom_border = Border(bottom=Side(style="medium"))
    bold_font = Font(bold=True)
    for name, group in grouped:
        sheetname = " ".join(name.replace(",", "").split()[::-1])
        if sheetname not in wb.sheetnames:
            continue
        ws = wb[sheetname]
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row:
                cell.value = None
                cell.border = None
        group = group.sort_values("DateObj").reset_index(drop=True)
        row_idx = 2
        for i, row in group.iterrows():
            date_str = row["Date"]
            date_obj = row["DateObj"]
            current_period = get_pay_period(date_obj)
            ws.cell(row=row_idx, column=1, value=date_str).alignment = Alignment(horizontal="left")
            ws.cell(row=row_idx, column=2, value=row["Shift"]).alignment = Alignment(horizontal="center")
            ws.cell(row=row_idx, column=3, value=row["Type"]).alignment = Alignment(horizontal="left")
            ws.cell(row=row_idx, column=4, value=row["Hours"]).alignment = Alignment(horizontal="center")
            ws.cell(row=row_idx, column=5, value=row["Start"]).alignment = Alignment(horizontal="center")
            ws.cell(row=row_idx, column=6, value=row["End"]).alignment = Alignment(horizontal="center")
            for col in range(1, 7):
                ws.cell(row=1, column=col).font = bold_font
                ws.cell(row=1, column=col).border = border_box
            if i + 1 < len(group):
                next_period = get_pay_period(group.loc[i + 1, "DateObj"])
                if next_period != current_period:
                    for col in range(1, 7):
                        ws.cell(row=row_idx, column=col).border = medium_bottom_border
            row_idx += 1
    out_file = f"ARGX_{df['DateObj'].min().strftime('%Y-%m-%d')}.xlsx"
    wb.save(out_file)
    print(f"Saved: {out_file}")

def make_heatmap(df):
    summary = df.copy()
    summary["Week Start"] = summary["DateObj"].apply(lambda d: d - timedelta(days=d.weekday()))
    pivot = summary.groupby(["Name", "Week Start"]).agg(Total_Hours=("Hours", "sum")).reset_index()
    table = pivot.pivot(index="Name", columns="Week Start", values="Total_Hours").fillna(0)
    table = table.reindex(sorted(table.columns), axis=1)
    plt.figure(figsize=(len(table.columns) * 1.2, len(table) * 0.5))
    sns.set(font_scale=1)
    ax = sns.heatmap(table, annot=True, fmt=".1f", cmap="Blues", cbar=False, linewidths=0.5, linecolor='gray')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.title("Weekly Hours per Person", fontsize=14, pad=20)
    plt.tight_layout()
    plt.savefig("ARGM_Weekly.png", dpi=300)
    plt.close()
    print("Saved: ARGM_Weekly.png")

if __name__ == "__main__":
    input_files = sys.argv[1:]
    if not input_files:
        input("No files provided. Drag PDFs onto this script. Press Enter to exit.")
        sys.exit()
    latest_files = latest_pdf(input_files)
    all_data = pd.concat([parse_pdf(pdf) for pdf in latest_files], ignore_index=True)
    if all_data.empty:
        print("No valid shifts found.")
        sys.exit()
    write_argx(all_data, TEMPLATE_FILE)
    make_heatmap(all_data)
