import os
import uuid
from flask import Flask, request, jsonify
import json
from extractor import PyInstArchive
from werkzeug.utils import secure_filename
import threading
from markupsafe import escape
from flask_cors import CORS
import mimetypes
import importlib.util
import traceback


class Utils:
    UPLOAD_BASE = "pending_decompilation"
    Extraction_Status_File = "status.txt"

def InitBackend():
    os.makedirs(Utils.UPLOAD_BASE, exist_ok=True)

# Extract Files From .exe file

def Extract(extraction_id):
    # Sort Extraction
    base_dir = os.path.join("pending_decompilation", extraction_id)
    exe_files = [f for f in os.listdir(base_dir) if f.lower().endswith('.exe')]

    if len(exe_files) != 1:
        raise Exception("Invalid number of exe files")

    exe_path = os.path.join(base_dir, exe_files[0])

    arch = PyInstArchive(exe_path)

    if arch.open() and arch.checkFile() and arch.getCArchiveInfo():
        arch.parseTOC()
        arch.extractFiles(extraction_id)
        arch.close()
    else:
        raise Exception("Extraction failed")

def process_file(extraction_id):
    base_dir = os.path.join(Utils.UPLOAD_BASE, extraction_id)

    try:
        # status = processing
        with open(os.path.join(base_dir, Utils.Extraction_Status_File), "w") as f:
            f.write("processing")

        try:
            Extract(extraction_id)
        except Exception as e:
            print("[!] Extract failed:", e)

        write_index(base_dir)

        with open(os.path.join(base_dir, Utils.Extraction_Status_File), "w") as f:
            f.write("done")

    except Exception as e:
        print("[!] GLOBAL ERROR:", e)
        traceback.print_exc()
        with open(os.path.join(base_dir, Utils.Extraction_Status_File), "w") as f:
            f.write("error")

# Making the "index.json file" of the extraction

def build_index(path):
    tree = []

    for item in os.listdir(path):
        if item == "index.json":
            continue

        full_path = os.path.join(path, item)

        if os.path.isdir(full_path):
            tree.append({
                "type": "folder",
                "name": item,
                "children": build_index(full_path)
            })
        else:
            tree.append({
                "type": "file",
                "name": item
            })

    return tree

def write_index(base_dir):
    tree = build_index(base_dir)

    index_path = os.path.join(base_dir, "index.json")

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(tree, f, indent=4)


app = Flask(__name__)
CORS(app)
InitBackend()


###################################################################################
# File upload
###################################################################################

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Empty File Name"}), 400

    from werkzeug.utils import secure_filename

    filename = secure_filename(file.filename)

    if not filename.lower().endswith(".exe"):
        return jsonify({"error": "Only .exe files allowed"}), 400

    unique_id = str(uuid.uuid4())

    folder_path = os.path.join(Utils.UPLOAD_BASE, unique_id)
    os.makedirs(folder_path, exist_ok=True)

    file_path = os.path.join(folder_path, filename)
    file.save(file_path)

    with open(os.path.join(folder_path, "status.txt"), "w") as f:
        f.write("pending")

    process_file(unique_id)
    
    return jsonify({
        "id": unique_id
    })

###################################################################################
# File Index returner with ID
###################################################################################

@app.route('/id/<extraction_id>', methods=['GET'])
def return_index(extraction_id):

    file_path = os.path.join(Utils.UPLOAD_BASE, extraction_id, "index.json")

    if not os.path.exists(file_path):
        return jsonify({
            "error": "index.json not found"
        }), 404

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return jsonify({
        "id": extraction_id,
        "tree": data
    })

###################################################################################
# Files Details
###################################################################################

@app.route('/file/<extraction_id>/<path:filename>', methods=['GET'])
def get_file(extraction_id, filename):

    base_dir = os.path.join(Utils.UPLOAD_BASE, extraction_id)

    file_path = os.path.join(base_dir, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "file not found"}), 404

    if not os.path.isfile(file_path):
        return jsonify({"error": "not a file"}), 400

    # extension
    ext = os.path.splitext(filename)[1].lower()

    result = {
        "id": extraction_id,
        "filename": filename,
        "compiled": False,
        "type": "text",
        "content": None
    }

    try:
        if ext == ".pyc":
            result["compiled"] = True
            result["type"] = "pyc"

            with open(file_path, "rb") as f:
                data = f.read()

            result["content"] = data.hex()[:2000]

        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                result["content"] = f.read()

            result["type"] = "text"

    except Exception as e:
        # fallback binaire
        with open(file_path, "rb") as f:
            data = f.read()

        result["type"] = "binary"
        result["content"] = data.hex()[:2000]

    return jsonify(result)

###################################################################################
# Uncompile Request
###################################################################################

@app.route('/decompile/id/<id>/<path:filename>', methods=['Post'])
def Decompile(id, filename):
    pyc_path = Utils.UPLOAD_BASE + "/" + id + "/" + filename
    py_dest_path = Utils.UPLOAD_BASE + "/" + id
    base_name = os.path.basename(filename)
    name, ext = os.path.splitext(base_name)

    new_filename = "decompiled_" + name + ".py"
    pylingual_post_args = f"--out-dir {py_dest_path} {pyc_path} --trust-lnotab"

    
    os.system(r"C:\Users\Administrateur\Pylingual\venv\Scripts\activate && pylingual " + pylingual_post_args)

    new_entry = {
        "type": "file",
        "name": new_filename
    }

    with open(Utils.UPLOAD_BASE + "/" + id + "/index.json", "r") as f:
        data = json.load(f)

    data.append(new_entry)

    with open(Utils.UPLOAD_BASE + "/" + id + "/index.json", "w") as f:
        json.dump(data, f, indent=4)

    return py_dest_path


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)