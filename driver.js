const API_BASE = window.location.protocol === "file:" ? "http://localhost:8000/api" : "/api";

const state = {
  gps: null,
  trackingToken: localStorage.getItem("driver_tracking_token") || "",
  driverSelfieDataUrl: "",
  signatureDataUrl: "",
  signatureHasDrawn: false,
};

const elements = {
  requestGpsButton: document.querySelector("#requestGpsButton"),
  gpsStatusTitle: document.querySelector("#gpsStatusTitle"),
  gpsStatusText: document.querySelector("#gpsStatusText"),
  publicVehicleForm: document.querySelector("#publicVehicleForm"),
  publicCarrierId: document.querySelector("#publicCarrierId"),
  publicDestinationId: document.querySelector("#publicDestinationId"),
  publicSelfieInput: document.querySelector("#publicSelfieInput"),
  publicSelfiePreview: document.querySelector("#publicSelfiePreview"),
  signatureCanvas: document.querySelector("#signatureCanvas"),
  signatureStatus: document.querySelector("#signatureStatus"),
  clearSignatureButton: document.querySelector("#clearSignatureButton"),
  publicSubmitButton: document.querySelector("#publicSubmitButton"),
  publicTrackingCard: document.querySelector("#publicTrackingCard"),
  publicQueueList: document.querySelector("#publicQueueList"),
  toast: document.querySelector("#toast"),
};

let toastTimer;
let signatureContext;
let drawingSignature = false;

bootstrap();

function bootstrap() {
  elements.requestGpsButton.addEventListener("click", requestGps);
  elements.publicVehicleForm.addEventListener("submit", submitPublicRegistration);
  elements.publicVehicleForm.addEventListener("input", updateSubmitState);
  elements.publicSelfieInput.addEventListener("change", handleSelfieChange);
  elements.clearSignatureButton.addEventListener("click", clearSignature);
  setupSignaturePad();
  loadConfig();
  if (state.trackingToken) {
    refreshTracking();
  }
  setInterval(refreshTracking, 20000);
  setInterval(loadQueueOnly, 20000);
  updateSubmitState();
}

async function loadConfig() {
  try {
    const data = await request("/public/config");
    populateSelect(elements.publicCarrierId, data.carriers, "Selecciona transportadora", (item) => `${item.code} - ${item.name}`);
    populateSelect(elements.publicDestinationId, data.destinations, "Selecciona destino", (item) => `${item.city} - ${item.zone}`);
    renderQueue(data.liveQueue || []);
    if (!data.siteConfigured) {
      setGpsStatus("Geocerca sin configurar", "Logística debe configurar la ubicación de planta antes de usar el registro por QR.");
    }
  } catch (error) {
    showToast(error.message);
  }
}

async function loadQueueOnly() {
  try {
    const data = await request("/public/config");
    renderQueue(data.liveQueue || []);
  } catch {}
}

function populateSelect(select, rows, placeholder, formatter) {
  select.innerHTML = "";
  select.append(new Option(placeholder, "", true, true));
  rows.forEach((row) => select.append(new Option(formatter(row), row.id)));
}

function requestGps() {
  if (!navigator.geolocation) {
    setGpsStatus("GPS no disponible", "Este dispositivo no soporta geolocalización.");
    return;
  }
  setGpsStatus("Validando ubicación", "Espera unos segundos mientras se confirma tu posición.");
  navigator.geolocation.getCurrentPosition(
    (position) => {
      state.gps = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      };
      setGpsStatus("Ubicación lista", "Ahora puedes registrarte en el turno.");
      updateSubmitState();
    },
    (error) => {
      state.gps = null;
      setGpsStatus("GPS bloqueado", `No se pudo obtener tu ubicación: ${error.message}`);
      updateSubmitState();
    },
    { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
  );
}

async function submitPublicRegistration(event) {
  event.preventDefault();
  if (!state.gps) {
    showToast("Primero debes validar tu GPS.");
    return;
  }
  if (!state.driverSelfieDataUrl) {
    showToast("Debes tomarte una selfie antes de registrarte.");
    return;
  }
  if (!state.signatureDataUrl) {
    showToast("Debes firmar en pantalla antes de registrarte.");
    return;
  }
  const payload = {
    plate: document.querySelector("#publicPlate").value,
    carrierId: elements.publicCarrierId.value,
    driverName: document.querySelector("#publicDriverName").value,
    driverId: document.querySelector("#publicDriverId").value,
    driverPhone: document.querySelector("#publicDriverPhone").value,
    emptyWeightKg: document.querySelector("#publicEmptyWeightKg").value,
    destinationId: elements.publicDestinationId.value,
    gpsLat: state.gps.lat,
    gpsLng: state.gps.lng,
    driverSelfieDataUrl: state.driverSelfieDataUrl,
    driverSignatureDataUrl: state.signatureDataUrl,
  };
  try {
    const data = await request("/public/register", { method: "POST", body: payload });
    state.trackingToken = data.vehicle.publicTrackingToken;
    localStorage.setItem("driver_tracking_token", state.trackingToken);
    elements.publicVehicleForm.reset();
    resetRegistrationMedia();
    await loadQueueOnly();
    renderTracking(data);
    showToast("Registro completado.");
  } catch (error) {
    showToast(error.message);
  }
}

async function refreshTracking() {
  if (!state.trackingToken) return;
  try {
    const data = await request(`/public/tracking/${encodeURIComponent(state.trackingToken)}`);
    renderTracking(data);
  } catch {}
}

function renderTracking(data) {
  const vehicle = data.vehicle;
  elements.publicTrackingCard.innerHTML = `
    <h3>${vehicle.plate}</h3>
    <p><strong>Turno actual:</strong> ${vehicle.turnPosition || "-"}</p>
    <p><strong>Estado logística:</strong> ${translateLogisticsStatus(vehicle.status)}</p>
    <p><strong>Estado calidad:</strong> ${translateQualityStatus(vehicle.qualityStatus)}</p>
    <p><strong>Transportadora:</strong> ${vehicle.carrier}</p>
    <p><strong>Destino:</strong> ${vehicle.city} - ${vehicle.zone}</p>
    <p><strong>Selfie:</strong> ${vehicle.driverSelfieUrl ? `<a href="${encodeURI(vehicle.driverSelfieUrl)}" target="_blank" rel="noopener noreferrer">Ver registro</a>` : "Pendiente"}</p>
    <p><strong>Firma:</strong> ${vehicle.driverSignatureUrl ? `<a href="${encodeURI(vehicle.driverSignatureUrl)}" target="_blank" rel="noopener noreferrer">Ver firma</a>` : "Pendiente"}</p>
    <p><strong>Al frente de la fila:</strong> ${data.frontOfQueue ? data.frontOfQueue.plate : "Sin fila"}</p>
    <p class="muted-text">Actualiza automáticamente cada 20 segundos.</p>
  `;
}

function renderQueue(rows) {
  if (!rows.length) {
    elements.publicQueueList.innerHTML = `<div class="empty">Todavía no hay vehículos en fila.</div>`;
    return;
  }
  elements.publicQueueList.innerHTML = rows.map((row) => `
    <article class="vehicle-card">
      <h4>${row.plate}</h4>
      <div class="vehicle-meta">
        <span><strong>Turno:</strong> ${row.turnPosition || "-"}</span>
        <span><strong>Transportadora:</strong> ${row.carrier}</span>
        <span><strong>Destino:</strong> ${row.city} - ${row.zone}</span>
        <span><strong>Calidad:</strong> ${translateQualityStatus(row.qualityStatus)}</span>
      </div>
    </article>
  `).join("");
}

async function handleSelfieChange(event) {
  const [file] = Array.from(event.target.files || []);
  if (!file) {
    state.driverSelfieDataUrl = "";
    elements.publicSelfiePreview.innerHTML = `<span class="muted-text">Aquí verás la selfie antes de enviar el registro.</span>`;
    updateSubmitState();
    return;
  }
  try {
    state.driverSelfieDataUrl = await fileToDataUrl(file);
    elements.publicSelfiePreview.innerHTML = `<img src="${state.driverSelfieDataUrl}" alt="Vista previa de selfie" />`;
    updateSubmitState();
  } catch (error) {
    state.driverSelfieDataUrl = "";
    showToast(error.message);
    updateSubmitState();
  }
}

function setupSignaturePad() {
  signatureContext = elements.signatureCanvas.getContext("2d");
  resizeSignatureCanvas();
  window.addEventListener("resize", resizeSignatureCanvas);

  elements.signatureCanvas.addEventListener("pointerdown", startSignature);
  elements.signatureCanvas.addEventListener("pointermove", moveSignature);
  elements.signatureCanvas.addEventListener("pointerup", endSignature);
  elements.signatureCanvas.addEventListener("pointerleave", endSignature);
}

function resizeSignatureCanvas() {
  const ratio = Math.max(window.devicePixelRatio || 1, 1);
  const bounds = elements.signatureCanvas.getBoundingClientRect();
  elements.signatureCanvas.width = Math.max(Math.floor(bounds.width * ratio), 320);
  elements.signatureCanvas.height = Math.max(Math.floor(bounds.height * ratio), 170);
  signatureContext = elements.signatureCanvas.getContext("2d");
  signatureContext.setTransform(1, 0, 0, 1, 0, 0);
  signatureContext.scale(ratio, ratio);
  signatureContext.lineCap = "round";
  signatureContext.lineJoin = "round";
  signatureContext.lineWidth = 2.4;
  signatureContext.strokeStyle = "#1769e0";
  if (!state.signatureHasDrawn) {
    clearSignatureCanvas();
  }
}

function startSignature(event) {
  drawingSignature = true;
  const { x, y } = getCanvasPoint(event);
  signatureContext.beginPath();
  signatureContext.moveTo(x, y);
  event.preventDefault();
}

function moveSignature(event) {
  if (!drawingSignature) return;
  const { x, y } = getCanvasPoint(event);
  signatureContext.lineTo(x, y);
  signatureContext.stroke();
  state.signatureHasDrawn = true;
  elements.signatureStatus.textContent = "Firma capturada correctamente.";
  event.preventDefault();
}

function endSignature() {
  if (!drawingSignature) return;
  drawingSignature = false;
  if (state.signatureHasDrawn) {
    state.signatureDataUrl = elements.signatureCanvas.toDataURL("image/png");
  }
  updateSubmitState();
}

function getCanvasPoint(event) {
  const bounds = elements.signatureCanvas.getBoundingClientRect();
  return {
    x: event.clientX - bounds.left,
    y: event.clientY - bounds.top,
  };
}

function clearSignatureCanvas() {
  const bounds = elements.signatureCanvas.getBoundingClientRect();
  signatureContext.clearRect(0, 0, bounds.width, bounds.height);
  signatureContext.fillStyle = "#ffffff";
  signatureContext.fillRect(0, 0, bounds.width, bounds.height);
}

function clearSignature() {
  state.signatureHasDrawn = false;
  state.signatureDataUrl = "";
  clearSignatureCanvas();
  elements.signatureStatus.textContent = "Firma pendiente.";
  updateSubmitState();
}

function resetRegistrationMedia() {
  state.driverSelfieDataUrl = "";
  state.signatureDataUrl = "";
  state.signatureHasDrawn = false;
  state.gps = null;
  elements.publicSelfieInput.value = "";
  elements.publicSelfiePreview.innerHTML = `<span class="muted-text">Aquí verás la selfie antes de enviar el registro.</span>`;
  clearSignatureCanvas();
  elements.signatureStatus.textContent = "Firma pendiente.";
  setGpsStatus("GPS requerido", "Debes permitir ubicación para validar que estás dentro de planta.");
  updateSubmitState();
}

function updateSubmitState() {
  const formReady =
    Boolean(document.querySelector("#publicPlate").value.trim()) &&
    Boolean(elements.publicCarrierId.value) &&
    Boolean(document.querySelector("#publicDriverName").value.trim()) &&
    Boolean(document.querySelector("#publicDriverId").value.trim()) &&
    Boolean(document.querySelector("#publicDriverPhone").value.trim()) &&
    Boolean(document.querySelector("#publicEmptyWeightKg").value.trim()) &&
    Boolean(elements.publicDestinationId.value);
  const canSubmit = formReady && Boolean(state.gps) && Boolean(state.driverSelfieDataUrl) && Boolean(state.signatureDataUrl);
  elements.publicSubmitButton.disabled = !canSubmit;
}

function translateLogisticsStatus(status) {
  return {
    QUEUED: "En turno",
    ASSIGNED: "Viaje asignado",
    REJECTED: "Rechazado",
  }[status] || status;
}

function translateQualityStatus(status) {
  return {
    PENDING: "Pendiente",
    IN_REVIEW: "En revisión",
    APPROVED: "Apto",
    REWORK: "Requiere arreglos",
    REJECTED: "Rechazado",
  }[status] || status;
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("No se pudo leer la selfie seleccionada."));
    reader.readAsDataURL(file);
  });
}

function setGpsStatus(title, text) {
  elements.gpsStatusTitle.textContent = title;
  elements.gpsStatusText.textContent = text;
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method || "GET",
    headers: { "Content-Type": "application/json" },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Error del servidor.");
  return data;
}

function showToast(message) {
  clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  toastTimer = setTimeout(() => elements.toast.classList.remove("show"), 3200);
}
