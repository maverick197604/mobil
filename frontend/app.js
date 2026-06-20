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

let renderer, scene, camera, controls, transformControls, currentMesh, animFrameId;
let editMode = 'orbit'; // 'orbit' | 'translate' | 'rotate' | 'scale'

// DOM refs for edit UI
const editToolbar     = document.getElementById('edit-toolbar');
const transformPanel  = document.getElementById('transform-panel');
const btnOrbit        = document.getElementById('btn-orbit');
const btnTranslate    = document.getElementById('btn-translate');
const btnRotate       = document.getElementById('btn-rotate');
const btnScale        = document.getElementById('btn-scale');
const btnReset        = document.getElementById('btn-reset');
const btnExport       = document.getElementById('btn-export');
const tpPx = document.getElementById('tp-px'), tpPy = document.getElementById('tp-py'), tpPz = document.getElementById('tp-pz');
const tpRx = document.getElementById('tp-rx'), tpRy = document.getElementById('tp-ry'), tpRz = document.getElementById('tp-rz');
const tpSx = document.getElementById('tp-sx'), tpSy = document.getElementById('tp-sy'), tpSz = document.getElementById('tp-sz');

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

  camera = new THREE.PerspectiveCamera(
    45,
    viewerPanel.clientWidth / viewerPanel.clientHeight,
    0.01,
    10000,
  );
  camera.position.set(0, 0, 5);

  const ambient = new THREE.AmbientLight(0xffffff, 0.45);
  scene.add(ambient);
  const key = new THREE.DirectionalLight(0xffffff, 0.85);
  key.position.set(5, 10, 7);
  key.castShadow = true;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x8899ff, 0.3);
  fill.position.set(-6, -4, -5);
  scene.add(fill);

  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.screenSpacePanning = true;
  controls.minDistance = 0.1;
  controls.maxDistance = 5000;
  controls.touches = { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN };

  // TransformControls
  transformControls = new THREE.TransformControls(camera, renderer.domElement);
  transformControls.addEventListener('dragging-changed', (e) => {
    controls.enabled = !e.value;
  });
  transformControls.addEventListener('change', syncTransformPanel);
  scene.add(transformControls);

  // Keyboard shortcuts
  window.addEventListener('keydown', (e) => {
    if (!currentMesh) return;
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'g' || e.key === 'G') setEditMode('translate');
    if (e.key === 'r' || e.key === 'R') setEditMode('rotate');
    if (e.key === 's' || e.key === 'S') setEditMode('scale');
    if (e.key === 'o' || e.key === 'O' || e.key === 'Escape') setEditMode('orbit');
  });

  // Toolbar buttons
  btnOrbit    .addEventListener('click', () => setEditMode('orbit'));
  btnTranslate.addEventListener('click', () => setEditMode('translate'));
  btnRotate   .addEventListener('click', () => setEditMode('rotate'));
  btnScale    .addEventListener('click', () => setEditMode('scale'));
  btnReset    .addEventListener('click', resetTransform);
  btnExport   .addEventListener('click', exportStl);

  // Numeric inputs → apply to mesh
  [tpPx,tpPy,tpPz].forEach((inp, i) => inp.addEventListener('change', () => applyPanelToMesh()));
  [tpRx,tpRy,tpRz].forEach((inp, i) => inp.addEventListener('change', () => applyPanelToMesh()));
  [tpSx,tpSy,tpSz].forEach((inp, i) => inp.addEventListener('change', () => applyPanelToMesh()));

  const ro = new ResizeObserver(() => onResize());
  ro.observe(viewerPanel);

  renderLoop();
}

function setEditMode(mode) {
  editMode = mode;
  [btnOrbit, btnTranslate, btnRotate, btnScale].forEach(b => b.classList.remove('active'));
  if (mode === 'orbit')     { btnOrbit.classList.add('active');     transformControls.detach(); controls.enabled = true; }
  if (mode === 'translate') { btnTranslate.classList.add('active'); transformControls.setMode('translate'); if (currentMesh) transformControls.attach(currentMesh); }
  if (mode === 'rotate')    { btnRotate.classList.add('active');    transformControls.setMode('rotate');    if (currentMesh) transformControls.attach(currentMesh); }
  if (mode === 'scale')     { btnScale.classList.add('active');     transformControls.setMode('scale');     if (currentMesh) transformControls.attach(currentMesh); }
}

function syncTransformPanel() {
  if (!currentMesh) return;
  const p = currentMesh.position, r = currentMesh.rotation, s = currentMesh.scale;
  const deg = THREE.MathUtils.radToDeg;
  tpPx.value = p.x.toFixed(2); tpPy.value = p.y.toFixed(2); tpPz.value = p.z.toFixed(2);
  tpRx.value = deg(r.x).toFixed(1); tpRy.value = deg(r.y).toFixed(1); tpRz.value = deg(r.z).toFixed(1);
  tpSx.value = s.x.toFixed(3); tpSy.value = s.y.toFixed(3); tpSz.value = s.z.toFixed(3);
}

function applyPanelToMesh() {
  if (!currentMesh) return;
  const deg = THREE.MathUtils.degToRad;
  currentMesh.position.set(+tpPx.value, +tpPy.value, +tpPz.value);
  currentMesh.rotation.set(deg(+tpRx.value), deg(+tpRy.value), deg(+tpRz.value));
  currentMesh.scale.set(+tpSx.value || 0.01, +tpSy.value || 0.01, +tpSz.value || 0.01);
}

function resetTransform() {
  if (!currentMesh) return;
  currentMesh.position.set(0, 0, 0);
  currentMesh.rotation.set(0, 0, 0);
  currentMesh.scale.set(1, 1, 1);
  syncTransformPanel();
  fitCameraToObject(currentMesh);
  showToast('Transform zurückgesetzt.', 'info');
}

function exportStl() {
  if (!currentMesh) return;
  // Apply transform to geometry copy and export as binary STL
  const geom = currentMesh.geometry.clone();
  geom.applyMatrix4(currentMesh.matrixWorld);

  const positions = geom.attributes.position;
  const triCount = positions.count / 3;
  const buf = new ArrayBuffer(84 + triCount * 50);
  const view = new DataView(buf);
  // Header (80 bytes)
  const header = 'CAD Viewer Export';
  for (let i = 0; i < 80; i++) view.setUint8(i, i < header.length ? header.charCodeAt(i) : 0);
  view.setUint32(80, triCount, true);

  let offset = 84;
  for (let i = 0; i < triCount; i++) {
    const ax = positions.getX(i*3),   ay = positions.getY(i*3),   az = positions.getZ(i*3);
    const bx = positions.getX(i*3+1), by = positions.getY(i*3+1), bz = positions.getZ(i*3+1);
    const cx = positions.getX(i*3+2), cy = positions.getY(i*3+2), cz = positions.getZ(i*3+2);
    // Normal
    const ux = bx-ax, uy = by-ay, uz = bz-az;
    const vx = cx-ax, vy = cy-ay, vz = cz-az;
    const nx = uy*vz - uz*vy, ny = uz*vx - ux*vz, nz = ux*vy - uy*vx;
    const nl = Math.sqrt(nx*nx+ny*ny+nz*nz) || 1;
    view.setFloat32(offset,    nx/nl, true); view.setFloat32(offset+4,  ny/nl, true); view.setFloat32(offset+8,  nz/nl, true);
    view.setFloat32(offset+12, ax, true);    view.setFloat32(offset+16, ay, true);    view.setFloat32(offset+20, az, true);
    view.setFloat32(offset+24, bx, true);    view.setFloat32(offset+28, by, true);    view.setFloat32(offset+32, bz, true);
    view.setFloat32(offset+36, cx, true);    view.setFloat32(offset+40, cy, true);    view.setFloat32(offset+44, cz, true);
    view.setUint16(offset+48, 0, true);
    offset += 50;
  }

  const blob = new Blob([buf], { type: 'model/stl' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'modell_bearbeitet.stl';
  a.click();
  URL.revokeObjectURL(a.href);
  showToast('STL-Datei heruntergeladen.', 'success');
  geom.dispose();
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
  syncTransformPanel();

  // Re-attach transform controls if a mode is active
  if (editMode !== 'orbit') transformControls.attach(currentMesh);
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
  editToolbar.hidden = true;
  transformPanel.hidden = true;
  transformControls.detach();
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
  editToolbar.hidden = false;
  transformPanel.hidden = false;
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
