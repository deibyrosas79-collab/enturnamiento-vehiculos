const API_BASE = window.location.protocol === "file:" ? "http://localhost:8000/api" : "/api";

const state = {
  gps: null,
  trackingToken: localStorage.getItem("driver_tracking_token") || "",
};

const elements = {
  requestGpsButton: document.querySelector("#requestGpsButton"),
  gpsStatusTitle: document.querySelector("#gpsStatusTitle"),
  gpsStatusText: document.querySelector("#gpsStatusText"),
  publicVehicleForm: document.querySelector("#publicVehicleForm"),
  publicCarrierId: document.querySelector("#publicCarrierId"),
  publicDestinationId: document.querySelector("#publicDestinationId"),
  publicSubmitButton: document.querySelector("#publicSubmitButton"),
  publicTrackingCard: document.querySelector("#publicTrackingCard"),
  publicQueueList: document.querySelector("#publicQueueList"),
  toast: document.querySelector("#toast"),
};

let toastTimer;

bootstrap();

function bootstrap() {
  elements.requestGpsButton.addEventListener("click", requestGps);
  elements.publicVehicleForm.addEventListener("submit", submitPublicRegistration);
  loadConfig();
  if (state.trackingToken) {
    refreshTracking();
  }
  setInterval(refreshTracking, 20000);
  setInterval(loadQueueOnly, 20000);
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
      elements.publicSubmitButton.disabled = false;
      setGpsStatus("Ubicación lista", "Ahora puedes registrarte en el turno.");
    },
    (error) => {
      elements.publicSubmitButton.disabled = true;
      setGpsStatus("GPS bloqueado", `No se pudo obtener tu ubicación: ${error.message}`);
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
  };
  try {
    const data = await request("/public/register", { method: "POST", body: payload });
    state.trackingToken = data.vehicle.publicTrackingToken;
    localStorage.setItem("driver_tracking_token", state.trackingToken);
    elements.publicVehicleForm.reset();
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
    <p><strong>Estado logística:</strong> ${vehicle.status}</p>
    <p><strong>Estado calidad:</strong> ${vehicle.qualityStatus}</p>
    <p><strong>Transportadora:</strong> ${vehicle.carrier}</p>
    <p><strong>Destino:</strong> ${vehicle.city} - ${vehicle.zone}</p>
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
        <span><strong>Calidad:</strong> ${row.qualityStatus}</span>
      </div>
    </article>
  `).join("");
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
