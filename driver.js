const API_BASE = window.location.protocol === "file:" ? "http://localhost:8000/api" : "/api";

const state = {
  gps: null,
  gpsAllowed: false,
  geofenceMessage: "Debes validar tu ubicacion dentro de planta.",
  config: null,
  centerId: new URLSearchParams(window.location.search).get("center") || "",
  trackingToken: localStorage.getItem("driver_tracking_token") || "",
  driverSelfieDataUrl: "",
  signatureDataUrl: "",
  signatureHasDrawn: false,
  destinationMenuOpen: false,
  isSubmitting: false,
  activeQueueGroup: null,
};

const elements = {
  requestGpsButton: document.querySelector("#requestGpsButton"),
  gpsStatusTitle: document.querySelector("#gpsStatusTitle"),
  gpsStatusText: document.querySelector("#gpsStatusText"),
  geofenceAlert: document.querySelector("#geofenceAlert"),
  geofenceAlertText: document.querySelector("#geofenceAlertText"),
  publicStatusBanner: document.querySelector("#publicStatusBanner"),
  publicStatusTitle: document.querySelector("#publicStatusTitle"),
  publicStatusText: document.querySelector("#publicStatusText"),
  publicStatusList: document.querySelector("#publicStatusList"),
  publicVehicleForm: document.querySelector("#publicVehicleForm"),
  publicCarrierId: document.querySelector("#publicCarrierId"),
  publicDestinationToggle: document.querySelector("#publicDestinationToggle"),
  publicDestinationMenu: document.querySelector("#publicDestinationMenu"),
  publicDestinationHint: document.querySelector("#publicDestinationHint"),
  publicDestinationTurns: document.querySelector("#publicDestinationTurns"),
  publicSelfieInput: document.querySelector("#publicSelfieInput"),
  publicSelfiePreview: document.querySelector("#publicSelfiePreview"),
  signatureCanvas: document.querySelector("#signatureCanvas"),
  signatureStatus: document.querySelector("#signatureStatus"),
  clearSignatureButton: document.querySelector("#clearSignatureButton"),
  publicSubmitButton: document.querySelector("#publicSubmitButton"),
  publicTrackingCard: document.querySelector("#publicTrackingCard"),
  publicQueueList: document.querySelector("#publicQueueList"),
  publicCityQueues: document.querySelector("#publicCityQueues"),
  publicQueuePanel: document.querySelector("#publicQueuePanel"),
  publicCityQueuesPanel: document.querySelector("#publicCityQueuesPanel"),
  toast: document.querySelector("#toast"),
};

let toastTimer;
let signatureContext;
let drawingSignature = false;

bootstrap();

function bootstrap() {
  elements.requestGpsButton.addEventListener("click", requestGps);
  elements.publicVehicleForm.addEventListener("submit", submitPublicRegistration);
  elements.publicVehicleForm.addEventListener("input", () => {
    hideStatusBanner();
    updateSubmitState();
  });
  elements.publicVehicleForm.addEventListener("change", () => {
    hideStatusBanner();
    updateSubmitState();
  });
  elements.publicCarrierId.addEventListener("change", () => {
    state.activeQueueGroup = selectedQueueGroup();
    renderSelectedCityTurnsPreview();
    renderQueue(state.config?.liveQueue || []);
    renderCityQueues(state.config?.cityQueues || []);
  });
  elements.publicSelfieInput.addEventListener("change", handleSelfieChange);
  elements.clearSignatureButton.addEventListener("click", clearSignature);
  elements.publicDestinationToggle.addEventListener("click", toggleDestinationMenu);
  document.addEventListener("click", handleDocumentClick);
  setupSignaturePad();
  togglePublicQueuePanels(Boolean(state.trackingToken));
  loadConfig();
  if (state.trackingToken) {
    refreshTracking();
  }
  setInterval(refreshTracking, 20000);
  setInterval(loadQueueOnly, 30000);
  updateRegistrationGate();
}

async function loadConfig(centerIdOverride = state.centerId) {
  try {
    const data = await request(withCenterQuery("/public/config", centerIdOverride));
    state.config = data;
    state.centerId = data.centerId || centerIdOverride || state.centerId;
    populateSelect(elements.publicCarrierId, data.carriers, "Selecciona transportadora", (item) => `${item.code} - ${item.name}`);
    renderDestinationMenu(data.destinations || []);
    if (state.trackingToken) {
      renderQueue(data.liveQueue || []);
      renderCityQueues(data.cityQueues || []);
    }
    updateHero(data);
    if (!data.siteConfigured) {
      state.gpsAllowed = false;
      state.geofenceMessage = "Logistica debe configurar la geocerca antes de usar este registro QR.";
    } else if (!state.gps) {
      state.geofenceMessage = "Debes validar tu ubicacion para activar el formulario.";
    }
    updateRegistrationGate();
  } catch (error) {
    showToast(error.message);
  }
}

async function loadQueueOnly() {
  if (state.trackingToken) {
    return;
  }
  renderSelectedCityTurnsPreview();
}

function updateHero(data) {
  document.title = `Registro QR ${data.siteName || "conductores"}`;
  const eyebrow = document.querySelector(".public-hero .eyebrow");
  const title = document.querySelector(".public-hero h1");
  const description = document.querySelector(".public-hero .hero-text");
  if (eyebrow) eyebrow.textContent = `Registro QR · ${data.siteName || "Planta principal"}`;
  if (title) title.textContent = "Registro de conductores";
  if (description) {
    description.textContent = `Completa tu enturnamiento solo dentro de la sede autorizada. Debes validar GPS, tomar selfie y firmar en pantalla. Centro activo: ${data.siteName || "Planta principal"}.`;
  }
}

function populateSelect(select, rows, placeholder, formatter) {
  const selected = select.value;
  select.innerHTML = "";
  select.append(new Option(placeholder, "", true, true));
  rows.forEach((row) => {
    const option = new Option(formatter(row), row.id);
    option.selected = row.id === selected;
    select.append(option);
  });
}

function renderDestinationMenu(rows) {
  const selected = new Set(selectedDestinationIds());
  elements.publicDestinationMenu.innerHTML = rows.map((row) => `
    <label class="multi-select-option">
      <input type="checkbox" value="${escapeHtml(row.id)}" ${selected.has(row.id) ? "checked" : ""} />
      <span class="multi-select-copy">
        <strong>${escapeHtml(row.city)}</strong>
        <small>${escapeHtml(row.zone)}</small>
      </span>
    </label>
  `).join("");
  elements.publicDestinationMenu.querySelectorAll("input[type='checkbox']").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      syncDestinationSummary();
      renderSelectedCityTurnsPreview();
      updateSubmitState();
    });
  });
  syncDestinationSummary();
  renderSelectedCityTurnsPreview();
}

function selectedDestinationIds() {
  return Array.from(elements.publicDestinationMenu.querySelectorAll("input[type='checkbox']:checked"))
    .map((input) => input.value)
    .filter(Boolean);
}

function syncDestinationSummary() {
  const ids = selectedDestinationIds();
  const labels = ids
    .map((id) => state.config?.destinations?.find((item) => item.id === id))
    .filter(Boolean)
    .map((item) => `${item.city} - ${item.zone}`);
  if (!labels.length) {
    elements.publicDestinationToggle.textContent = "Selecciona uno o mas destinos";
  } else if (labels.length === 1) {
    elements.publicDestinationToggle.textContent = labels[0];
  } else {
    elements.publicDestinationToggle.textContent = `${labels.length} destinos seleccionados`;
  }
  elements.publicDestinationHint.textContent = labels.length
    ? `Seleccionados: ${labels.join(" | ")}`
    : "Selecciona al menos un destino.";
}

function toggleDestinationMenu(event) {
  if (event) event.preventDefault();
  if (elements.publicDestinationToggle.disabled) return;
  state.destinationMenuOpen = !state.destinationMenuOpen;
  elements.publicDestinationMenu.classList.toggle("hidden", !state.destinationMenuOpen);
  elements.publicDestinationToggle.setAttribute("aria-expanded", state.destinationMenuOpen ? "true" : "false");
}

function closeDestinationMenu() {
  state.destinationMenuOpen = false;
  elements.publicDestinationMenu.classList.add("hidden");
  elements.publicDestinationToggle.setAttribute("aria-expanded", "false");
}

function handleDocumentClick(event) {
  if (!state.destinationMenuOpen) return;
  const inside = event.target.closest("#publicDestinationPicker");
  if (!inside) closeDestinationMenu();
}

function renderSelectedCityTurnsPreview() {
  const destinationIds = selectedDestinationIds();
  const queueGroup = selectedQueueGroup();
  if (!destinationIds.length) {
    elements.publicDestinationTurns.innerHTML = "";
    return;
  }
  const chips = destinationIds.map((id) => {
    const destination = state.config?.destinations?.find((item) => item.id === id);
    if (!destination) return "";
    const cityGroup = (state.config?.cityQueues || []).find((item) => item.city === destination.city);
    const visibleRows = (cityGroup?.vehicles || []).filter((row) => !queueGroup || row.queueGroup === queueGroup);
    const estimatedTurn = visibleRows.length + 1;
    return `<span class="city-turn-chip">${escapeHtml(destination.city)}: turno estimado ${estimatedTurn}</span>`;
  }).filter(Boolean);
  elements.publicDestinationTurns.innerHTML = chips.join("");
}

function requestGps() {
  if (!navigator.geolocation) {
    state.gps = null;
    state.gpsAllowed = false;
    state.geofenceMessage = "Este dispositivo no soporta geolocalizacion.";
    setGpsStatus("GPS no disponible", state.geofenceMessage);
    updateRegistrationGate();
    return;
  }
  setGpsStatus("Validando ubicacion", "Espera unos segundos mientras se confirma tu posicion.");
  navigator.geolocation.getCurrentPosition(
    async (position) => {
      state.gps = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      };
      const match = detectCenterFromGps();
      if (!match) {
        state.gpsAllowed = false;
        state.geofenceMessage = "Estas fuera de la geocerca. Todos los campos quedan bloqueados hasta que ingreses a Yopal centro 1010 o Espinal centro 1000.";
        setGpsStatus("Fuera de planta", state.geofenceMessage);
        updateRegistrationGate();
        return;
      }
      state.gpsAllowed = true;
      state.geofenceMessage = `Ubicacion validada en ${match.name}. Ya puedes diligenciar el formulario.`;
      if (match.id !== state.centerId) {
        await loadConfig(match.id);
      } else {
        updateRegistrationGate();
      }
      setGpsStatus("Ubicacion validada", state.geofenceMessage);
    },
    (error) => {
      state.gps = null;
      state.gpsAllowed = false;
      state.geofenceMessage = `No se pudo obtener tu ubicacion: ${error.message}`;
      setGpsStatus("GPS bloqueado", state.geofenceMessage);
      updateRegistrationGate();
    },
    { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 },
  );
}

async function submitPublicRegistration(event) {
  event.preventDefault();
  const validationIssues = collectValidationIssues();
  if (validationIssues.length) {
    showStatusBanner(
      "error",
      "Faltan datos obligatorios",
      "Antes de guardar, completa los siguientes campos del registro.",
      validationIssues.map((issue) => issue.label),
    );
    focusValidationIssue(validationIssues[0]);
    showToast(`Falta: ${validationIssues[0].label}`);
    return;
  }
  const destinationIds = selectedDestinationIds();
  const payload = {
    plate: document.querySelector("#publicPlate").value,
    carrierId: elements.publicCarrierId.value,
    driverName: document.querySelector("#publicDriverName").value,
    driverId: document.querySelector("#publicDriverId").value,
    driverPhone: document.querySelector("#publicDriverPhone").value,
    emptyWeightKg: document.querySelector("#publicEmptyWeightKg").value,
    destinationId: destinationIds[0],
    destinationIds,
    gpsLat: state.gps.lat,
    gpsLng: state.gps.lng,
    driverSelfieDataUrl: state.driverSelfieDataUrl,
    driverSignatureDataUrl: state.signatureDataUrl,
  };
  try {
    setSubmittingState(true);
    hideStatusBanner();
    const data = await request(withCenterQuery("/public/register", state.centerId), { method: "POST", body: payload });
    state.trackingToken = data.vehicle.publicTrackingToken;
    localStorage.setItem("driver_tracking_token", state.trackingToken);
    elements.publicVehicleForm.reset();
    resetRegistrationMedia();
    renderTracking(data);
    showStatusBanner(
      "success",
      "Su informacion ha sido guardada correctamente",
      "Tu vehiculo ya quedo registrado en turno. En la parte inferior puedes ver el estado de calidad, tus observaciones y el turno por ciudad.",
    );
    showToast("Su informacion ha sido guardada correctamente.");
  } catch (error) {
    showStatusBanner("error", "No se pudo guardar la informacion", error.message);
    showToast(error.message);
  } finally {
    setSubmittingState(false);
  }
}

async function refreshTracking() {
  if (!state.trackingToken) {
    togglePublicQueuePanels(false);
    return;
  }
  try {
    const data = await request(`/public/tracking/${encodeURIComponent(state.trackingToken)}`);
    renderTracking(data);
  } catch {
    // noop
  }
}

function renderTracking(data) {
  const vehicle = data.vehicle;
  state.activeQueueGroup = vehicle.queueGroup || state.activeQueueGroup;
  const cityTurns = Object.entries(vehicle.cityTurns || {});
  const observations = vehicle.latestInspection?.observationsText || vehicle.latestInspection?.findingsSummary || vehicle.rejectionReason || "";
  elements.publicTrackingCard.innerHTML = `
    <div class="tracking-grid">
      <div>
        <h3>${escapeHtml(vehicle.plate)}</h3>
        <p><strong>Transportadora:</strong> ${escapeHtml(vehicle.carrier)}</p>
        <p><strong>Conductor:</strong> ${escapeHtml(vehicle.driverName)}</p>
        <p><strong>Estado logistica:</strong> ${escapeHtml(translateLogisticsStatus(vehicle.status))}</p>
        <p><strong>Estado calidad:</strong> ${escapeHtml(translateQualityStatus(vehicle.qualityStatus))}</p>
        <p><strong>Destinos:</strong> ${escapeHtml(renderDestinationsText(vehicle))}</p>
        ${renderTrackingCityCards(vehicle, cityTurns)}
        ${observations ? `<div class="tracking-note"><strong>Observaciones:</strong> ${escapeHtml(observations)}</div>` : ""}
      </div>
      <div class="driver-media-grid">
        ${renderTrackingMedia(vehicle.driverSelfieUrl, "Selfie")}
        ${renderTrackingMedia(vehicle.driverSignatureUrl, "Firma")}
      </div>
    </div>
    <p class="muted-text">Actualiza automaticamente cada 20 segundos. Frente de la fila: ${escapeHtml(data.frontOfQueue?.plate || "Sin fila")}</p>
  `;
  togglePublicQueuePanels(false);
}

function renderTrackingCityCards(vehicle, cityTurns) {
  const rows = cityTurns.length
    ? cityTurns
    : [[vehicle.city || "Destino principal", vehicle.turnPosition || "-"]];
  const cards = rows.map(([city, turn]) => {
    const matchingDestinations = (vehicle.destinationOptions || [])
      .filter((option) => option.city === city)
      .map((option) => option.zone)
      .filter(Boolean);
    const destinationLabel = matchingDestinations.length
      ? `${city} - ${matchingDestinations.join(", ")}`
      : city;
    return `
      <article class="tracking-city-card">
        <span class="tracking-city-name">${escapeHtml(city)}</span>
        <strong>Turno ${escapeHtml(String(turn || "-"))}</strong>
        <small>${escapeHtml(destinationLabel)}</small>
      </article>
    `;
  }).join("");
  return `
    <section class="tracking-city-section">
      <h4>${rows.length > 1 ? "Tus turnos por ciudad" : "Tu turno por ciudad"}</h4>
      <div class="tracking-city-grid ${rows.length === 1 ? "single" : ""}">
        ${cards}
      </div>
    </section>
  `;
}

function renderTrackingMedia(url, label) {
  if (!url) {
    return `<div class="capture-card compact"><strong>${escapeHtml(label)}</strong><span class="muted-text">Sin archivo</span></div>`;
  }
  return `
    <div class="capture-card compact">
      <strong>${escapeHtml(label)}</strong>
      <img class="tracking-media-preview" src="${url}" alt="${escapeHtml(label)}" />
    </div>
  `;
}

function togglePublicQueuePanels(show) {
  elements.publicQueuePanel.classList.toggle("hidden", !show);
  elements.publicCityQueuesPanel.classList.toggle("hidden", !show);
}

function renderQueue(rows, forcedGroup = null) {
  const activeGroup = forcedGroup || selectedQueueGroup();
  const visibleRows = activeGroup ? rows.filter((row) => row.queueGroup === activeGroup) : rows;
  if (!visibleRows.length) {
    elements.publicQueueList.innerHTML = `<div class="empty">Todavia no hay vehiculos en fila para esta cola.</div>`;
    return;
  }
  elements.publicQueueList.innerHTML = visibleRows.map((row) => `
    <article class="vehicle-card">
      <h4>${escapeHtml(row.plate)}</h4>
      <div class="vehicle-meta">
        <span><strong>Turno:</strong> ${row.turnPosition || "-"}</span>
        <span><strong>Cola:</strong> ${escapeHtml(row.queueGroupLabel || "-")}</span>
        <span><strong>Transportadora:</strong> ${escapeHtml(row.carrier)}</span>
        <span><strong>Destinos:</strong> ${escapeHtml(renderDestinationsText(row))}</span>
        <span><strong>Calidad:</strong> ${escapeHtml(translateQualityStatus(row.qualityStatus))}</span>
      </div>
    </article>
  `).join("");
}

function renderCityQueues(cityQueues, forcedGroup = null) {
  const activeGroup = forcedGroup || selectedQueueGroup();
  const html = cityQueues.map((group) => {
    const vehicles = activeGroup ? (group.vehicles || []).filter((row) => row.queueGroup === activeGroup) : (group.vehicles || []);
    if (!vehicles.length) {
      return `
        <section class="panel soft">
          <div class="panel-heading"><div><h3>${escapeHtml(group.city)}</h3><p>Sin vehiculos visibles para esta ciudad.</p></div></div>
        </section>
      `;
    }
    return `
      <section class="panel soft">
        <div class="panel-heading"><div><h3>${escapeHtml(group.city)}</h3><p>Turnos visibles para esta ciudad.</p></div></div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Turno</th><th>Placa</th><th>Transportadora</th><th>Cola</th></tr></thead>
            <tbody>
              ${vehicles.map((row) => `
                <tr>
                  <td>${row.turnPosition ? `<span class="turn">${row.turnPosition}</span>` : "-"}</td>
                  <td>${escapeHtml(row.plate)}</td>
                  <td>${escapeHtml(row.carrier)}</td>
                  <td>${escapeHtml(row.queueGroupLabel || "-")}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </section>
    `;
  }).join("");
  elements.publicCityQueues.innerHTML = html || `<div class="empty">No hay ciudades configuradas.</div>`;
}

async function handleSelfieChange(event) {
  const [file] = Array.from(event.target.files || []);
  if (!file) {
    state.driverSelfieDataUrl = "";
    elements.publicSelfiePreview.innerHTML = `<span class="muted-text">Aqui veras la selfie antes de enviar el registro.</span>`;
    updateSubmitState();
    return;
  }
  try {
    elements.publicSelfiePreview.innerHTML = `<span class="muted-text">Preparando selfie para un envio mas rapido...</span>`;
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
  if (!state.signatureHasDrawn) clearSignatureCanvas();
}

function startSignature(event) {
  if (!state.gpsAllowed) return;
  drawingSignature = true;
  const { x, y } = getCanvasPoint(event);
  signatureContext.beginPath();
  signatureContext.moveTo(x, y);
  event.preventDefault();
}

function moveSignature(event) {
  if (!drawingSignature || !state.gpsAllowed) return;
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
  return { x: event.clientX - bounds.left, y: event.clientY - bounds.top };
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
  state.gpsAllowed = false;
  state.activeQueueGroup = null;
  state.geofenceMessage = "Debes validar nuevamente tu ubicacion para un nuevo registro.";
  elements.publicSelfieInput.value = "";
  elements.publicSelfiePreview.innerHTML = `<span class="muted-text">Aqui veras la selfie antes de enviar el registro.</span>`;
  clearSignatureCanvas();
  elements.signatureStatus.textContent = "Firma pendiente.";
  setGpsStatus("GPS requerido", state.geofenceMessage);
  updateRegistrationGate();
}

function updateRegistrationGate() {
  let title = "GPS pendiente";
  let text = state.geofenceMessage || "Debes validar tu ubicacion.";
  let locked = true;

  if (!state.config?.siteConfigured) {
    title = "Geocerca sin configurar";
    text = "Logistica debe configurar la ubicacion de la planta antes de usar este registro por QR.";
  } else if (!state.gps) {
    title = "GPS pendiente";
    text = state.geofenceMessage || "Debes validar tu ubicacion para activar el formulario.";
  } else if (!state.gpsAllowed) {
    title = "Fuera de planta";
    text = state.geofenceMessage || "Estas fuera de la geocerca autorizada.";
  } else {
    locked = false;
    title = "Ubicacion validada";
    text = state.geofenceMessage || "Ya puedes diligenciar el formulario.";
  }

  setGpsStatus(title, text);
  elements.geofenceAlert.classList.toggle("hidden", !locked);
  elements.geofenceAlertText.textContent = text;
  setFormDisabled(locked);
  updateSubmitState();
}

function setFormDisabled(disabled) {
  elements.publicVehicleForm.querySelectorAll("input, select, button, textarea").forEach((control) => {
    if (control === elements.publicSubmitButton) return;
    control.disabled = disabled;
  });
  elements.publicDestinationToggle.disabled = disabled;
  elements.publicDestinationMenu.querySelectorAll("input").forEach((input) => {
    input.disabled = disabled;
  });
  if (disabled) closeDestinationMenu();
}

function updateSubmitState() {
  const formReady =
    !elements.publicCarrierId.disabled &&
    Boolean(document.querySelector("#publicPlate").value.trim()) &&
    Boolean(elements.publicCarrierId.value) &&
    Boolean(document.querySelector("#publicDriverName").value.trim()) &&
    Boolean(document.querySelector("#publicDriverId").value.trim()) &&
    Boolean(document.querySelector("#publicDriverPhone").value.trim()) &&
    Boolean(document.querySelector("#publicEmptyWeightKg").value.trim()) &&
    selectedDestinationIds().length > 0;
  const canSubmit =
    !state.isSubmitting &&
    formReady &&
    Boolean(state.gpsAllowed) &&
    Boolean(state.driverSelfieDataUrl) &&
    Boolean(state.signatureDataUrl);
  elements.publicSubmitButton.disabled = !canSubmit;
}

function selectedQueueGroup() {
  const carrier = state.config?.carriers?.find((item) => item.id === elements.publicCarrierId.value);
  if (!carrier) return state.activeQueueGroup || null;
  return carrier.code === "4000801" ? "DIANA_AGRICOLA" : "GENERAL";
}

function renderDestinationsText(item) {
  const options = Array.isArray(item.destinationOptions) && item.destinationOptions.length
    ? item.destinationOptions.map((option) => `${option.city} - ${option.zone}`)
    : [`${item.city || ""}${item.zone ? ` - ${item.zone}` : ""}`.trim()];
  return options.filter(Boolean).join(", ");
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
    IN_REVIEW: "En revision",
    APPROVED: "Apto",
    REWORK: "Requiere arreglos",
    REJECTED: "Rechazado",
  }[status] || status;
}

async function fileToDataUrl(file) {
  try {
    return await compressImageFile(file, 960, 0.72);
  } catch {
    return readFileAsDataUrl(file);
  }
}

function setGpsStatus(title, text) {
  elements.gpsStatusTitle.textContent = title;
  elements.gpsStatusText.textContent = text;
}

function withCenterQuery(path, centerId = state.centerId) {
  if (!centerId) return path;
  return `${path}${path.includes("?") ? "&" : "?"}center=${encodeURIComponent(centerId)}`;
}

function detectCenterFromGps() {
  if (!state.gps || !Array.isArray(state.config?.centers)) return null;
  const matches = state.config.centers
    .filter((center) => center.geofenceEnabled !== false)
    .map((center) => ({
      center,
      distance: haversineDistance(state.gps.lat, state.gps.lng, Number(center.siteLat), Number(center.siteLng)),
    }))
    .filter((item) => Number.isFinite(item.distance) && item.distance <= Number(item.center.siteRadiusM || 180))
    .sort((left, right) => left.distance - right.distance);
  return matches[0]?.center || null;
}

function haversineDistance(lat1, lng1, lat2, lng2) {
  const toRad = (value) => (value * Math.PI) / 180;
  const radius = 6371000;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return radius * (2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));
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

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function showToast(message) {
  clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  toastTimer = setTimeout(() => elements.toast.classList.remove("show"), 3200);
}

function collectValidationIssues() {
  const issues = [];
  const checks = [
    { ok: Boolean(state.gpsAllowed && state.gps), label: "Validar ubicacion GPS dentro de planta", element: elements.requestGpsButton },
    { ok: Boolean(document.querySelector("#publicPlate").value.trim()), label: "Placa", element: document.querySelector("#publicPlate") },
    { ok: Boolean(elements.publicCarrierId.value), label: "Transportadora", element: elements.publicCarrierId },
    { ok: Boolean(document.querySelector("#publicDriverName").value.trim()), label: "Nombre del conductor", element: document.querySelector("#publicDriverName") },
    { ok: Boolean(document.querySelector("#publicDriverId").value.trim()), label: "Cedula", element: document.querySelector("#publicDriverId") },
    { ok: Boolean(document.querySelector("#publicDriverPhone").value.trim()), label: "Numero de celular", element: document.querySelector("#publicDriverPhone") },
    { ok: Boolean(document.querySelector("#publicEmptyWeightKg").value.trim()), label: "Peso vacio del vehiculo", element: document.querySelector("#publicEmptyWeightKg") },
    { ok: selectedDestinationIds().length > 0, label: "Seleccionar al menos un destino", element: elements.publicDestinationToggle },
    { ok: Boolean(state.driverSelfieDataUrl), label: "Selfie del conductor", element: elements.publicSelfieInput },
    { ok: Boolean(state.signatureDataUrl), label: "Firma del conductor", element: elements.signatureCanvas },
  ];
  checks.forEach((check) => {
    if (!check.ok) issues.push(check);
  });
  return issues;
}

function focusValidationIssue(issue) {
  if (!issue?.element) return;
  issue.element.scrollIntoView({ behavior: "smooth", block: "center" });
  if (typeof issue.element.focus === "function") {
    setTimeout(() => issue.element.focus(), 120);
  }
}

function setSubmittingState(isSubmitting) {
  state.isSubmitting = isSubmitting;
  elements.publicSubmitButton.textContent = isSubmitting ? "Guardando informacion..." : "Registrarme en turno";
  updateSubmitState();
}

function showStatusBanner(type, title, message, items = []) {
  elements.publicStatusBanner.classList.remove("hidden", "success", "error");
  elements.publicStatusBanner.classList.add(type === "success" ? "success" : "error");
  elements.publicStatusTitle.textContent = title;
  elements.publicStatusText.textContent = message;
  if (items.length) {
    elements.publicStatusList.innerHTML = items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    elements.publicStatusList.classList.remove("hidden");
  } else {
    elements.publicStatusList.innerHTML = "";
    elements.publicStatusList.classList.add("hidden");
  }
  elements.publicStatusBanner.scrollIntoView({ behavior: "smooth", block: "center" });
}

function hideStatusBanner() {
  elements.publicStatusBanner.classList.add("hidden");
  elements.publicStatusList.classList.add("hidden");
  elements.publicStatusList.innerHTML = "";
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("No se pudo leer la selfie seleccionada."));
    reader.readAsDataURL(file);
  });
}

function compressImageFile(file, maxSize, quality) {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      try {
        const width = image.naturalWidth || image.width;
        const height = image.naturalHeight || image.height;
        const scale = Math.min(1, maxSize / Math.max(width, height));
        const targetWidth = Math.max(1, Math.round(width * scale));
        const targetHeight = Math.max(1, Math.round(height * scale));
        const canvas = document.createElement("canvas");
        canvas.width = targetWidth;
        canvas.height = targetHeight;
        const context = canvas.getContext("2d", { alpha: false });
        if (!context) {
          throw new Error("No se pudo preparar la selfie.");
        }
        context.fillStyle = "#ffffff";
        context.fillRect(0, 0, targetWidth, targetHeight);
        context.drawImage(image, 0, 0, targetWidth, targetHeight);
        const dataUrl = canvas.toDataURL("image/jpeg", quality);
        URL.revokeObjectURL(objectUrl);
        resolve(dataUrl);
      } catch (error) {
        URL.revokeObjectURL(objectUrl);
        reject(error);
      }
    };
    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("No se pudo procesar la selfie seleccionada."));
    };
    image.src = objectUrl;
  });
}
