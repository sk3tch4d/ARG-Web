import os
import threading
import time
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from ARGX_Generator import generate_argx_and_heatmap

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pdf_file = request.files.get('pdf_file')
        output_argx = request.form.get('generate_argx') == 'on'
        output_heatmap = request.form.get('generate_heatmap') == 'on'

        if not pdf_file or not (output_argx or output_heatmap):
            return render_template("index.html", error="Please upload a PDF and select at least one option.")

        filename = secure_filename(pdf_file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        pdf_file.save(pdf_path)

        output_paths = generate_argx_and_heatmap(
            pdf_path,
            generate_argx=output_argx,
            generate_heatmap=output_heatmap
        )

        for path in output_paths:
            threading.Thread(target=delete_later, args=(path,)).start()

        return render_template("result.html", outputs=output_paths)

    return render_template("index.html")

@app.route('/download/<filename>')
def download(filename):
    print(f"[DOWNLOAD] {filename} requested")
    return send_file(filename, as_attachment=True)

def delete_later(filepath, delay=600):  # <- this sets default delay to 10 minutes
    time.sleep(delay)
    if os.path.exists(filepath):
        os.remove(filepath)
        print(f"[CLEANUP] Deleted: {filepath}")

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
