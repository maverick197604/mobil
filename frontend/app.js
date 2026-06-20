/**
 * CAD Viewer — Frontend App Logic
 *
 * - File upload with drag-and-drop
 * - File list from /api/files
 * - 3D STL viewer using Three.js + STLLoader + OrbitControls
 * - Touch-friendly OrbitControls for mobile
 * - Auto-fit camera after model load
 * - German UI
 */

'use strict';

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const API_BASE = ''; // same origin

// ---------------------------------------------------------------------------
// DOM references
// ---------------------------------------------------------------------------

const uploadZone       = document.getElementById('upload-zone');
const fileInput        = document.getElementById('file-input');
const uploadBtn        = document.getElementById('upload-btn');
const selectedFileName = document.getElementById('selected-file-name');
const uploadProgress   = document.getElementById('upload-progress');
const uploadProgressBar= document.getElementById('upload-progress-bar');
const fileList         = document.getElementById('file-list');
const emptyState       = document.getElementById('empty-state');
const viewerPanel      = document.getElementById('viewer-panel');
const viewerCanvas     = document.getElementById('viewer-canvas');
const viewerPlaceholder= document.getElementById('viewer-placeholder');
const viewerLoading    = document.getElementById('viewer-loading');
const viewerError      = document.getElementById('viewer-error');
const loadingMessage   = document.getElementById('loading-message');
const errorMessage     = document.getElementById('error-message');
const viewerHint       = document.getElementById('viewer-hint');
const toastContainer   = document.getElementById('toast-container');

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let activeFileId = null;

// ---------------------------------------------------------------------------
// Three.js scene
// ---------------------------------------------------------------------------

let renderer, scene, camera, controls, currentMesh, animFrameId;

function initThree() {
  renderer = new THREE.WebGLRenderer({
    canvas: viewerCanvas,
    antialias: true,
    alpha: false,
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x0f1117, 1);
  renderer.setSize(viewerPanel.clientWidth, viewerPanel.clientHeight);
  renderer.shadowMap.enabled = true;

  scene = new THREE.Scene();

  // Camera
  camera = new THREE.PerspectiveCamera(
    45,
    viewerPanel.clientWidth / viewerPanel.clientHeight,
    0.01,
    10000,
  );
  camera.position.set(0, 0, 5);

  // Lights
  const ambient = new THREE.AmbientLight(0xffffff, 0.45);
  scene.add(ambient);

  const key = new THREE.DirectionalLight(0xffffff, 0.85);
  key.position.set(5, 10, 7);
  key.castShadow = true;
  scene.add(key);

  const fill = new THREE.DirectionalLight(0x8899ff, 0.3);
  fill.position.set(-6, -4, -5);
  scene.add(fill);

  // OrbitControls — touch support enabled by default
  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.screenSpacePanning = true;
  controls.minDistance = 0.1;
  controls.maxDistance = 5000;
  controls.touches = {
    ONE: THREE.TOUCH.ROTATE,
    TWO: THREE.TOUCH.DOLLY_PAN,
  };

  // Resize observer
  const ro = new ResizeObserver(() => onResize());
  ro.observe(viewerPanel);

  renderLoop();
}

function renderLoop() {
  animFrameId = requestAnimationFrame(renderLoop);
  controls.update();
  renderer.render(scene, camera);
}

function onResize() {
  const w = viewerPanel.clientWidth;
  const h = viewerPanel.clientHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

function clearScene() {
  if (currentMesh) {
    scene.remove(currentMesh);
    currentMesh.geometry.dispose();
    if (currentMesh.material) currentMesh.material.dispose();
    currentMesh = null;
  }
}

/**
 * Load an STL from an ArrayBuffer and display it in the scene.
 */
function loadStlBuffer(buffer) {
  const loader = new THREE.STLLoader();
  const geometry = loader.parse(buffer);

  geometry.computeVertexNormals();
  geometry.center();

  const material = new THREE.MeshStandardMaterial({
    color: 0x4f8ef7,
    metalness: 0.25,
    roughness: 0.55,
    side: THREE.DoubleSide,
  });

  clearScene();
  currentMesh = new THREE.Mesh(geometry, material);
  currentMesh.castShadow = true;
  currentMesh.receiveShadow = true;
  scene.add(currentMesh);

  fitCameraToObject(currentMesh);
}

/**
 * Auto-fit camera so the model fills the viewport nicely.
 */
function fitCameraToObject(mesh) {
  const box = new THREE.Box3().setFromObject(mesh);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());

  const maxDim = Math.max(size.x, size.y, size.z);
  const fov = camera.fov * (Math.PI / 180);
  let distance = Math.abs(maxDim / (2 * Math.tan(fov / 2)));
  distance *= 1.6; // add some breathing room

  const direction = new THREE.Vector3(1, 0.6, 1).normalize();
  camera.position.copy(center).addScaledVector(direction, distance);
  camera.near = distance / 100;
  camera.far  = distance * 100;
  camera.updateProjectionMatrix();

  controls.target.copy(center);
  controls.update();
}

// ---------------------------------------------------------------------------
// Viewer state helpers
// ---------------------------------------------------------------------------

function showPlaceholder() {
  viewerPlaceholder.hidden = false;
  viewerLoading.hidden = true;
  viewerError.hidden = true;
  viewerHint.classList.remove('visible');
}

function showLoading(msg = 'Modell wird konvertiert …') {
  loadingMessage.textContent = msg;
  viewerPlaceholder.hidden = true;
  viewerLoading.hidden = false;
  viewerError.hidden = true;
  viewerHint.classList.remove('visible');
}

function showError(msg) {
  errorMessage.textContent = msg;
  viewerPlaceholder.hidden = true;
  viewerLoading.hidden = true;
  viewerError.hidden = false;
  viewerHint.classList.remove('visible');
}

function showModel() {
  viewerPlaceholder.hidden = true;
  viewerLoading.hidden = true;
  viewerError.hidden = true;
  viewerHint.classList.add('visible');
}

// ---------------------------------------------------------------------------
// Toast notifications
// ---------------------------------------------------------------------------

function showToast(message, type = 'info', duration = 3500) {
  const toast = document.createElement('div');
  toast.className = 'toast' + (type !== 'info' ? ` ${type}` : '');
  toast.textContent = message;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(6px)';
    toast.style.transition = 'opacity 0.3s, transform 0.3s';
    setTimeout(() => toast.remove(), 320);
  }, duration);
}

// ---------------------------------------------------------------------------
// File list rendering
// ---------------------------------------------------------------------------

const FILE_ICONS = {
  '.fcstd': '🔧',
  '.step':  '📐',
  '.stp':   '📐',
  '.iges':  '📏',
  '.igs':   '📏',
  '.stl':   '🧊',
};

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

function formatDate(isoString) {
  try {
    const d = new Date(isoString);
    return d.toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' });
  } catch {
    return isoString;
  }
}

function renderFileList(files) {
  fileList.innerHTML = '';

  if (!files || files.length === 0) {
    emptyState.hidden = false;
    return;
  }

  emptyState.hidden = true;

  files.forEach((file) => {
    const icon = FILE_ICONS[file.suffix] || '📄';

    const li = document.createElement('li');
    li.setAttribute('role', 'option');
    li.setAttribute('aria-selected', file.file_id === activeFileId ? 'true' : 'false');
    li.dataset.fileId = file.file_id;
    if (file.file_id === activeFileId) li.classList.add('active');

    li.innerHTML = `
      <div class="file-icon" aria-hidden="true">${icon}</div>
      <div class="file-info">
        <div class="file-name" title="${escapeHtml(file.original_name)}">${escapeHtml(file.original_name)}</div>
        <div class="file-meta">${formatSize(file.size)} · ${formatDate(file.uploaded_at)}</div>
      </div>
      <button class="file-delete" data-file-id="${file.file_id}"
              aria-label="Datei löschen: ${escapeHtml(file.original_name)}"
              title="Datei löschen">✕</button>
    `;

    // Click on row → open in viewer
    li.addEventListener('click', (e) => {
      if (e.target.closest('.file-delete')) return; // handled separately
      openFileInViewer(file.file_id, file.original_name);
    });

    // Delete button
    li.querySelector('.file-delete').addEventListener('click', (e) => {
      e.stopPropagation();
      deleteFile(file.file_id, file.original_name);
    });

    fileList.appendChild(li);
  });
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

async function fetchFileList() {
  try {
    const res = await fetch(`${API_BASE}/api/files`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const files = await res.json();
    renderFileList(files);
  } catch (err) {
    console.error('Dateiliste konnte nicht geladen werden:', err);
    showToast('Dateiliste konnte nicht geladen werden.', 'error');
  }
}

async function openFileInViewer(fileId, fileName) {
  // Update active state
  activeFileId = fileId;
  document.querySelectorAll('#file-list li').forEach((li) => {
    const active = li.dataset.fileId === fileId;
    li.classList.toggle('active', active);
    li.setAttribute('aria-selected', active ? 'true' : 'false');
  });

  showLoading(`„${fileName}" wird konvertiert …`);
  clearScene();

  try {
    const res = await fetch(`${API_BASE}/api/convert/${fileId}`);
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch (_) {}
      throw new Error(detail);
    }

    showLoading('3D-Modell wird geladen …');
    const buffer = await res.arrayBuffer();
    loadStlBuffer(buffer);
    showModel();
  } catch (err) {
    console.error('Viewer-Fehler:', err);
    showError(err.message || 'Das Modell konnte nicht geladen werden.');
  }
}

async function deleteFile(fileId, fileName) {
  if (!confirm(`Datei „${fileName}" wirklich löschen?`)) return;

  try {
    const res = await fetch(`${API_BASE}/api/files/${fileId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    showToast(`„${fileName}" wurde gelöscht.`, 'success');

    if (activeFileId === fileId) {
      activeFileId = null;
      clearScene();
      showPlaceholder();
    }

    await fetchFileList();
  } catch (err) {
    console.error('Löschen fehlgeschlagen:', err);
    showToast('Datei konnte nicht gelöscht werden.', 'error');
  }
}

// ---------------------------------------------------------------------------
// File upload
// ---------------------------------------------------------------------------

let selectedFile = null;

function onFileSelected(file) {
  if (!file) return;
  selectedFile = file;
  selectedFileName.textContent = file.name;
  uploadBtn.disabled = false;
  uploadBtn.textContent = '⬆ Hochladen';
}

async function uploadSelectedFile() {
  if (!selectedFile) return;

  uploadBtn.disabled = true;
  uploadBtn.textContent = 'Wird hochgeladen …';
  uploadProgress.classList.add('visible');
  uploadProgressBar.style.width = '0%';

  const formData = new FormData();
  formData.append('file', selectedFile);

  // Simulate progress via XHR for better mobile feedback
  await new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE}/api/upload`);

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        uploadProgressBar.style.width = `${pct}%`;
        uploadProgress.setAttribute('aria-valuenow', pct);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        let msg = `HTTP ${xhr.status}`;
        try {
          msg = JSON.parse(xhr.responseText).detail || msg;
        } catch (_) {}
        reject(new Error(msg));
      }
    });

    xhr.addEventListener('error', () => reject(new Error('Netzwerkfehler')));
    xhr.send(formData);
  }).then(async (data) => {
    uploadProgressBar.style.width = '100%';
    showToast(`„${data.original_name}" erfolgreich hochgeladen.`, 'success');

    // Reset upload area
    setTimeout(() => {
      selectedFile = null;
      fileInput.value = '';
      selectedFileName.textContent = '';
      uploadBtn.disabled = true;
      uploadBtn.textContent = 'Datei auswählen &amp; hochladen';
      uploadProgress.classList.remove('visible');
      uploadProgressBar.style.width = '0%';
    }, 600);

    await fetchFileList();
  }).catch((err) => {
    console.error('Upload-Fehler:', err);
    showToast(`Upload fehlgeschlagen: ${err.message}`, 'error');
    uploadBtn.disabled = false;
    uploadBtn.textContent = '⬆ Erneut versuchen';
    uploadProgress.classList.remove('visible');
  });
}

// ---------------------------------------------------------------------------
// Drag & drop
// ---------------------------------------------------------------------------

uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadZone.classList.add('drag-over');
});

uploadZone.addEventListener('dragleave', () => {
  uploadZone.classList.remove('drag-over');
});

uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) onFileSelected(file);
});

// Keyboard accessibility for the upload zone
uploadZone.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    fileInput.click();
  }
});

fileInput.addEventListener('change', () => {
  onFileSelected(fileInput.files[0]);
});

uploadBtn.addEventListener('click', () => {
  if (!selectedFile) {
    fileInput.click();
  } else {
    uploadSelectedFile();
  }
});

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', async () => {
  initThree();
  showPlaceholder();
  await fetchFileList();
});
