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
from openpyxl.styles import Alignment, Border, Side, Font, PatternFill
from flask import Flask, send_file, request

# Flask app setup
app = Flask(__name__)

# Template file path
TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), "ARGX_Example.xlsx")

# Valid names of employees
VALID_NAMES = {
    "Adeniyi, Oluwaseyi", "Bhardwaj, Liam", "Donovan, Patrick", "Gallivan, David",
    "Janaway, Alexander", "Robichaud, Richard", "Santo, Jaime", "Tobin, James",
    "Ukwesa, Jennifer", "Vanderputten, Richard", "Woodland, Nathaniel"
}

# Base date for pay period calculations (Jan 13, 2025)
BASE_DATE = datetime(2025, 1, 13)

# Function to classify shifts based on start and end times
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

# Helper function to get pay period from date object
def get_pay_period(date_obj):
    return (date_obj - BASE_DATE.date()).days // 14

# Function to extract shift IDs from a line
def extract_shift_ids(line):
    return [t for t in line.split() if re.match(r'(SA[1-4]|[A-Z]*\d{3,4})$', t, re.IGNORECASE)]

# Function to parse the PDF file and extract shift data
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

# Function to get the latest PDF file based on date
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

# Function to apply shading to the Weekly Totals sheet
def apply_shading_to_weekly_totals(weekly_totals_ws):
    row_idx = 2
    rows = list(weekly_totals_ws.iter_rows(min_row=2, max_row=weekly_totals_ws.max_row, min_col=1, max_col=6))
    for i in range(len(rows)):  # Compare all rows, applying shading for the entire pay period
        date_obj = rows[i][0].value
        if isinstance(date_obj, datetime):
            current_period = get_pay_period(date_obj)
            if current_period % 2 == 0:  # Apply shading to even periods
                for col in range(1, 7):
                    weekly_totals_ws.cell(row=row_idx, column=col).fill = pay_period_shading
        row_idx += 1

# Function to apply shading to employee sheets
def apply_shading_to_employee_sheets(wb):
    for sheetname in wb.sheetnames:
        if sheetname == "Weekly Totals":
            continue  # Skip Weekly Totals sheet
        ws = wb[sheetname]
        row_idx = 2
        rows = list(ws.iter_rows(min_row=2, max_row=ws.max_row))
        for i in range(len(rows)):  # Compare all rows, applying shading for the entire pay period
            date_obj = rows[i][0].value
            if isinstance(date_obj, datetime):
                current_period = get_pay_period(date_obj)
                if current_period % 2 == 0:  # Apply shading to even periods
                    for col in range(1, 7):
                        cell = ws.cell(row=row_idx, column=col)
                        cell.fill = pay_period_shading
            row_idx += 1

# Function to write the ARGX output file
def write_argx(df, template_path):
    wb = load_workbook(template_path)
    grouped = df.groupby("Name")
    border_box = Border(left=Side(style="thin"), right=Side(style="thin"),
                        top=Side(style="thin"), bottom=Side(style="thin"))
    medium_bottom_border = Border(bottom=Side(style="medium"))
    bold_font = Font(bold=True)
    pay_period_shading = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")

    # Define the directory where files will be saved
    output_dir = os.path.join(os.path.dirname(__file__), "downloads")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # Create the directory if it doesn't exist

    if "Weekly Totals" in wb.sheetnames:
        weekly_totals_ws = wb["Weekly Totals"]
        apply_shading_to_weekly_totals(weekly_totals_ws)

    for name, group in grouped:
        sheetname = " ".join(name.replace(",", "").split()[::-1])
        if sheetname not in wb.sheetnames:
            continue
        ws = wb[sheetname]
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
                        cell = ws.cell(row=row_idx, column=col)
                        cell.border = medium_bottom_border
                        cell.fill = pay_period_shading
            row_idx += 1

    # Define the output file path
    out_file = os.path.join(output_dir, f"ARGX_{df['DateObj'].min().strftime('%Y-%m-%d')}.xlsx")
    wb.save(out_file)
    print(f"Saved: {out_file}")
    return out_file  # Return the path for the Flask route to send the file

# Flask route to download the file
@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    output_dir = os.path.join(os.path.dirname(__file__), 'downloads')
    filepath = os.path.join(output_dir, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return "File not found", 404

# Function to generate the ARGX and heatmap files
def generate_argx_and_heatmap(pdf_path, generate_argx=True, generate_heatmap=True):
    latest_files = [pdf_path]
    all_data = pd.concat([parse_pdf(pdf) for pdf in latest_files], ignore_index=True)
    if all_data.empty:
        print("No valid shifts found.")
        return []

    outputs = []

    if generate_argx:
        out_file = write_argx(all_data, TEMPLATE_FILE)
        outputs.append(out_file)
    
    if generate_heatmap:
        make_heatmap(all_data)
        outputs.append("ARGM_Weekly.png")

    return outputs  # Return the file paths as a list

# Route to handle index page and file upload
@app.route('/', methods=['POST'])
def index():
    # Extract the PDF file uploaded by the user
    uploaded_file = request.files['file']
    
    # Save the uploaded PDF file temporarily
    file_path = os.path.join(os.path.dirname(__file__), 'uploads', uploaded_file.filename)
    uploaded_file.save(file_path)

    # Generate ARGX and heatmap files
    output_paths = generate_argx_and_heatmap(file_path)

    if not output_paths:  # Check if output_paths is None or empty
        return "No valid shifts found or error generating files", 500

    # Ensure the files are accessible for downloading
    return render_template('index.html', output_files=output_paths)

# Main entry point to start Flask server
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=10000)
