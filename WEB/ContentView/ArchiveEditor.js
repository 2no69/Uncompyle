function getIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get("id");
}

const Backend_URL = "ENTER YOUR BACKEND URL"

async function loadData(host, id) {

    if (!id) {
        document.getElementById("tree").textContent = "No ID";
        return;
    }

    try {
        const res = await fetch(host + '/id/' + id);
        
        if (!res.ok) throw new Error("HTTP " + res.status);

        const data = await res.json();

        console.log("DATA:", data); //Debug

        buildTree(data.tree, document.getElementById("tree"), host);

    } catch (err) {
        console.error(err);
        document.getElementById("tree").textContent = "Files Loading Error";
    }
}

function buildTree(nodes, container, host, basePath = "") {
  nodes.forEach(node => {
    const el = document.createElement("div");

    const currentPath = basePath + "/" + node.name;

    if (node.type === "folder") {
        el.textContent = "📁 " + node.name;
        el.className = "folder";

        const childrenContainer = document.createElement("div");
        childrenContainer.className = "children";

        if (node.children) {
            buildTree(node.children, childrenContainer, host, currentPath);
        }

        el.addEventListener("click", (e) => {
            e.stopPropagation();
            el.classList.toggle("open");
        });

        el.appendChild(childrenContainer);
    }

    if (node.type === "file") {
        el.textContent = "📄 " + node.name;
        el.className = "file";

        el.addEventListener("click", async (e) => {
            e.stopPropagation();
            await openFile(currentPath, host);
        });
    }

    container.appendChild(el);
  });
}


async function openFile(filePath, host) {
  const id = getIdFromURL();

  selectedFile = filePath;

  try {
    const res = await fetch(
      `${host}/file/${id}/${encodeURIComponent(filePath)}`
    );

    const data = await res.json();

    if (!res.ok || data.error) {
      console.error(data.error || "Fetch failed");
      return;
    }

    const pyc_msg = document.getElementById("pyc-msg");
    const editorDiv = document.getElementById("editor");

    if (data.type === "pyc") {
        pyc_msg.style.display = "flex";
        editorDiv.style.display = "none";
    } else {
        pyc_msg.style.display = "none";
        editorDiv.style.display = "flex";
        openPopup(data.filename, data.content ?? "");
    }

    window.currentFileMeta = data;

    currentFile = {
        path: filePath,
    };

    console.log("Fichier courant :", currentFile);

  } catch (err) {
    console.error("Fetch error:", err);
  }
}

function openPopup(filename, code) {
    loadMonaco(filename, code);
}



function getLanguage(filename) {
  if (filename.endsWith(".py")) return "python";
  if (filename.endsWith(".pyc")) return "plaintext";
  return "plaintext";
}

function loadMonaco(filename, code) {
  require(["vs/editor/editor.main"], function () {

    // SAFE CHECK
    if (editor && typeof editor.dispose === "function") {
      editor.dispose();
    }

    editor = monaco.editor.create(
      document.getElementById("editor"),
      {
        value: code || "",
        language: getLanguage(filename),
        theme: "vs-dark",
        automaticLayout: true
      }
    );
  });
}

async function decompileFile(id, filename, host) {
    try {
        const response = await fetch(`${host}/decompile/id/${id}/${filename}`, {
            method: "POST"
        });

        const result = await response.text();
        console.log("Résultat :", result);
    } catch (error) {
        console.error("Erreur :", error);
    }
}

function getCurrentFile() {
    return currentFile;
}

function getCurrentFilePath() {
    return currentFile.path;
}

let currentFile = {
    path: null,
};

let editor = null;


require.config({
    paths: {
        vs: "https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs"
    }
});

window.addEventListener("DOMContentLoaded", () => {
    loadData(Backend_URL, getIdFromURL());
});