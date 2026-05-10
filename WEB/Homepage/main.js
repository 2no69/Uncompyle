const Backend_URL = "ENTER YOUR BACKEND URL HERE";

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");

dropzone.addEventListener("click", () => {
  fileInput.click();
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file) handleFile(file);
});

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");

    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
});

function handleFile(file) {
  if (!file.name.endsWith(".exe")) {
    alert("Only .exe files is supported !")
    return;
  }
  else {
    Loading()
    uploadFile(file);
  }
}

async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(Backend_URL + "/upload", {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    if (!res.ok) {
      alert(data.error || "Upload Error !");
      return;
    }

    console.log("UPLOAD OK:", data);

    // redirect direct
    window.location.href = `../ContentView?id=${data.id}`;

  } catch (err) {
    console.error(err);
    alert("Backend is offline !");
  }
}

const Loader = document.getElementById("loading");
const Loader_Status = document.getElementById("loading-text");

function Loading() {
    Loader.style.display = "flex";
}