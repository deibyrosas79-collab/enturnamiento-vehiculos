const API_BASE = window.location.protocol === "file:" ? "http://localhost:8000/api" : "/api";

const CHECKLIST_ITEMS = [
  { key: "foodLegend", label: "Cuenta con leyenda visible Transporte de alimentos", evidence: true },
  { key: "cleanliness", label: "Libre de suciedad", evidence: true },
  { key: "strangeSmells", label: "Libre de olores extraños", evidence: false },
  { key: "stains", label: "Libre de manchas", evidence: true },
  { key: "damage", label: "Libre de orificios y averías", evidence: true },
  { key: "humidity", label: "Libre de humedad", evidence: true },
  { key: "infestation", label: "Libre de infestación", evidence: true },
  { key: "bulkWallsFloor", label: "Granel en paredes y piso limpio y en buen estado", evidence: true },
  { key: "containerHoles", label: "Trompos limpios y protegidos", evidence: true },
  { key: "fumigationIn", label: "Fumigación ingreso", evidence: true },
  { key: "fumigationOut", label: "Fumigación salida", evidence: true },
];

const state = {
  user: null,
  appState: null,
  currentView: "dashboard",
  queueTab: "queued",
  rejectVehicle: null,
  qualityVehicle: null,
};

const elements = {
  authScreen: document.querySelector("#authScreen"),
  appShell: document.querySelector("#appShell"),
  loginForm: document.querySelector("#loginForm"),
  logoutButton: document.querySelector("#logoutButton"),
  openPublicPageButton: document.querySelector("#openPublicPageButton"),
  welcomeText: document.querySelector("#welcomeText"),
  roleText: document.querySelector("#roleText"),
  navTabs: document.querySelectorAll(".nav-tab"),
  appViews: document.querySelectorAll(".app-view"),
  vehicleForm: document.querySelector("#vehicleForm"),
  carrierSelect: document.querySelector("#carrierId"),
  destinationSelect: document.querySelector("#destinationId"),
  searchInput: document.querySelector("#searchInput"),
  queueTables: document.querySelector("#queueTables"),
  queueTabs: document.querySelectorAll("[data-queue-tab]"),
  destinationForm: document.querySelector("#destinationForm"),
  carrierForm: document.querySelector("#carrierForm"),
  userForm: document.querySelector("#userForm"),
  siteForm: document.querySelector("#siteForm"),
  destinationsTable: document.querySelector("#destinationsTable"),
  carriersTable: document.querySelector("#carriersTable"),
  usersTable: document.querySelector("#usersTable"),
  publicRegistrationUrl: document.querySelector("#publicRegistrationUrl"),
  publicQrImage: document.querySelector("#publicQrImage"),
  countQueued: document.querySelector("#countQueued"),
  countQualityPending: document.querySelector("#countQualityPending"),
  countQualityApproved: document.querySelector("#countQualityApproved"),
  countRejected: document.querySelector("#countRejected"),
  qualityPendingCount: document.querySelector("#qualityPendingCount"),
  qualityReworkCount: document.querySelector("#qualityReworkCount"),
  qualityApprovedCount: document.querySelector("#qualityApprovedCount"),
  qualityRejectedCount: document.querySelector("#qualityRejectedCount"),
  qualityPendingList: document.querySelector("#qualityPendingList"),
  qualityReworkList: document.querySelector("#qualityReworkList"),
  qualityApprovedList: document.querySelector("#qualityApprovedList"),
  qualityRejectedList: document.querySelector("#qualityRejectedList"),
  carrierRejectReport: document.querySelector("#carrierRejectReport"),
  reasonReport: document.querySelector("#reasonReport"),
  suitabilityReport: document.querySelector("#suitabilityReport"),
  qualityDecisionReport: document.querySelector("#qualityDecisionReport"),
  rejectModal: document.querySelector("#rejectModal"),
  rejectForm: document.querySelector("#rejectForm"),
  rejectVehicleLabel: document.querySelector("#rejectVehicleLabel"),
  rejectReason: document.querySelector("#rejectReason"),
  cancelRejectButton: document.querySelector("#cancelRejectButton"),
  qualityModal: document.querySelector("#qualityModal"),
  qualityForm: document.querySelector("#qualityForm"),
  qualityModalTitle: document.querySelector("#qualityModalTitle"),
  qualityMeta: document.querySelector("#qualityMeta"),
  qualityChecklistGrid: document.querySelector("#qualityChecklistGrid"),
  observationsText: document.querySelector("#observationsText"),
  finalDecision: document.querySelector("#finalDecision"),
  cancelQualityButton: document.querySelector("#cancelQualityButton"),
  siteName: document.querySelector("#siteName"),
  siteLat: document.querySelector("#siteLat"),
  siteLng: document.querySelector("#siteLng"),
  siteRadiusM: document.querySelector("#siteRadiusM"),
  geofenceEnabled: document.querySelector("#geofenceEnabled"),
  toast: document.querySelector("#toast"),
};

let toastTimer;

bootstrap();

function bootstrap() {
  renderChecklistForm();
  bindEvents();
  loadSession();
}

function bindEvents() {
  elements.loginForm.addEventListener("submit", submitLogin);
  elements.logoutButton.addEventListener("click", logout);
  elements.openPublicPageButton.addEventListener("click", () => window.open("/driver.html", "_blank"));
  elements.vehicleForm.addEventListener("submit", submitVehicle);
  elements.destinationForm.addEventListener("submit", submitDestination);
  elements.carrierForm.addEventListener("submit", submitCarrier);
  elements.userForm.addEventListener("submit", submitUser);
  elements.siteForm.addEventListener("submit", submitSiteConfig);
  elements.searchInput.addEventListener("input", renderQueueTables);
  elements.rejectForm.addEventListener("submit", submitRejectVehicle);
  elements.cancelRejectButton.addEventListener("click", closeRejectModal);
  elements.qualityForm.addEventListener("submit", submitQualityInspection);
  elements.cancelQualityButton.addEventListener("click", closeQualityModal);
  elements.navTabs.forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view)));
  elements.queueTabs.forEach((button) => button.addEventListener("click", () => switchQueueTab(button.dataset.queueTab)));
  elements.rejectModal.addEventListener("click", (event) => {
    if (event.target === elements.rejectModal) closeRejectModal();
  });
  elements.qualityModal.addEventListener("click", (event) => {
    if (event.target === elements.qualityModal) closeQualityModal();
  });
}

async function loadSession() {
  try {
    const data = await request("/auth/me");
    state.user = data.user;
    await refreshAppState();
  } catch {
    showAuth();
  }
}

async function refreshAppState() {
  const data = await request("/app-state");
  state.user = data.user;
  state.appState = data;
  showApp();
  renderApp();
}

async function submitLogin(event) {
  event.preventDefault();
  const form = new FormData(elements.loginForm);
  try {
    const data = await request("/auth/login", {
      method: "POST",
      body: {
        username: form.get("username"),
        password: form.get("password"),
      },
    });
    state.user = data.user;
    state.appState = data;
    elements.loginForm.reset();
    showApp();
    renderApp();
    showToast(`Bienvenido, ${data.user.fullName}.`);
  } catch (error) {
    showToast(error.message);
  }
}

async function logout() {
  await request("/auth/logout", { method: "POST" }).catch(() => {});
  state.user = null;
  state.appState = null;
  showAuth();
}

function showAuth() {
  elements.authScreen.classList.remove("hidden");
  elements.appShell.classList.add("hidden");
}

function showApp() {
  elements.authScreen.classList.add("hidden");
  elements.appShell.classList.remove("hidden");
}

function switchView(view) {
  state.currentView = view;
  elements.navTabs.forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  elements.appViews.forEach((panel) => panel.classList.toggle("active", panel.id === `${view}View`));
}

function switchQueueTab(tabName) {
  state.queueTab = tabName;
  elements.queueTabs.forEach((button) => button.classList.toggle("active", button.dataset.queueTab === tabName));
  renderQueueTables();
}

function renderApp() {
  if (!state.appState) return;
  const { user, queued, rejected, quality, settings, destinations, carriers, users, analytics } = state.appState;
  elements.welcomeText.textContent = `Hola, ${user.fullName}`;
  elements.roleText.textContent = `Rol activo: ${user.role}`;
  applyRoleVisibility(user.role);
  switchView(user.role === "CALIDAD" ? "quality" : state.currentView);
  populateSelect(elements.carrierSelect, carriers, "Selecciona transportadora", (item) => `${item.code} - ${item.name}`);
  populateSelect(elements.destinationSelect, destinations, "Selecciona destino", (item) => `${item.city} - ${item.zone}`);
  elements.publicRegistrationUrl.value = state.appState.publicRegistrationUrl;
  elements.publicQrImage.src = state.appState.publicQrUrl;
  elements.countQueued.textContent = queued.length;
  elements.countQualityPending.textContent = quality.pending.length;
  elements.countQualityApproved.textContent = quality.approved.length;
  elements.countRejected.textContent = rejected.length;
  elements.qualityPendingCount.textContent = quality.pending.length;
  elements.qualityReworkCount.textContent = quality.rework.length;
  elements.qualityApprovedCount.textContent = quality.approved.length;
  elements.qualityRejectedCount.textContent = quality.rejected.length;
  elements.siteName.value = settings.siteName;
  elements.siteLat.value = settings.siteLat;
  elements.siteLng.value = settings.siteLng;
  elements.siteRadiusM.value = settings.siteRadiusM;
  elements.geofenceEnabled.checked = settings.geofenceEnabled;

  renderQueueTables();
  renderMastersTables(destinations, carriers, users);
  renderQualityLists();
  renderReport(elements.carrierRejectReport, analytics.rejectedByCarrier, "No hay rechazos por transportadora.");
  renderReport(elements.reasonReport, analytics.topRejectionReasons, "No hay motivos registrados.");
  renderReport(elements.suitabilityReport, analytics.suitabilityCounts, "Sin datos de compatibilidad.");
  renderReport(elements.qualityDecisionReport, analytics.qualityDecisionCounts, "Sin decisiones de calidad.");
}

function applyRoleVisibility(role) {
  const logisticsOnly = ["dashboard", "masters", "reports", "settings"];
  elements.navTabs.forEach((button) => {
    const restricted = logisticsOnly.includes(button.dataset.view);
    button.classList.toggle("hidden", role === "CALIDAD" && restricted);
  });
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

function renderQueueTables() {
  if (!state.appState) return;
  const rows = filterVehicles(state.appState[state.queueTab]);
  const columns = {
    queued: [
      ["Turno", (item) => item.turnPosition ? `<span class="turn">${item.turnPosition}</span>` : ""],
      ["Placa", (item) => item.plate],
      ["Transportadora", (item) => `${item.carrierCode || ""} ${item.carrier}`.trim()],
      ["Conductor", (item) => item.driverName],
      ["Celular", (item) => item.driverPhone || ""],
      ["P. vacío (kg)", (item) => formatNumber(item.emptyWeightKg)],
      ["Destino", (item) => `${item.city} - ${item.zone}`],
      ["Calidad", (item) => qualityBadge(item.qualityStatus)],
      ["Canal", (item) => `<span class="badge channel">${item.registrationChannel}</span>`],
      ["Soportes", renderVehicleSupports],
      ["Ingreso", (item) => formatDate(item.createdAt)],
      ["Acciones", renderQueueActions],
    ],
    assigned: [
      ["#", (_item, index) => index + 1],
      ["Placa", (item) => item.plate],
      ["Transportadora", (item) => item.carrier],
      ["Conductor", (item) => item.driverName],
      ["Celular", (item) => item.driverPhone || ""],
      ["P. vacío (kg)", (item) => formatNumber(item.emptyWeightKg)],
      ["Destino", (item) => `${item.city} - ${item.zone}`],
      ["Soportes", renderVehicleSupports],
      ["Ingreso", (item) => formatDate(item.createdAt)],
      ["Asignado", (item) => formatDate(item.assignedAt)],
    ],
    rejected: [
      ["#", (_item, index) => index + 1],
      ["Placa", (item) => item.plate],
      ["Transportadora", (item) => item.carrier],
      ["Conductor", (item) => item.driverName],
      ["Celular", (item) => item.driverPhone || ""],
      ["Destino", (item) => `${item.city} - ${item.zone}`],
      ["Calidad", (item) => qualityBadge(item.qualityStatus)],
      ["Soportes", renderVehicleSupports],
      ["Motivo", (item) => item.rejectionReason || "No informado"],
      ["Rechazado", (item) => formatDate(item.rejectedAt)],
    ],
  }[state.queueTab];

  elements.queueTables.innerHTML = renderTable(columns, rows, `No hay registros en ${state.queueTab}.`);
  bindQueueActions();
}

function renderQueueActions(item) {
  if (item.status !== "QUEUED") return "";
  return `
    <div class="actions">
      <button class="primary small-action" type="button" data-action="assign" data-id="${item.id}">Asignar</button>
      <button class="danger small-action" type="button" data-action="reject" data-id="${item.id}">Rechazar</button>
    </div>
  `;
}

function bindQueueActions() {
  elements.queueTables.querySelectorAll("[data-action='assign']").forEach((button) => {
    button.addEventListener("click", () => assignVehicle(button.dataset.id));
  });
  elements.queueTables.querySelectorAll("[data-action='reject']").forEach((button) => {
    const vehicle = state.appState.queued.find((item) => item.id === button.dataset.id);
    button.addEventListener("click", () => openRejectModal(vehicle));
  });
}

function renderMastersTables(destinations, carriers, users) {
  elements.destinationsTable.innerHTML = renderTable(
    [["Ciudad", (item) => item.city], ["Zona", (item) => item.zone], ["Acción", (item) => `<button class="danger small-action" data-destination-delete="${item.id}" type="button">Eliminar</button>`]],
    destinations,
    "No hay destinos."
  );
  elements.carriersTable.innerHTML = renderTable(
    [["Código", (item) => item.code], ["Transportadora", (item) => item.name], ["Acción", (item) => `<button class="danger small-action" data-carrier-delete="${item.id}" type="button">Eliminar</button>`]],
    carriers,
    "No hay transportadoras."
  );
  elements.usersTable.innerHTML = renderTable(
    [["Usuario", (item) => item.username], ["Nombre", (item) => item.fullName], ["Rol", (item) => item.role], ["Estado", (item) => item.active ? "Activo" : "Inactivo"]],
    users,
    "No hay usuarios."
  );
  bindMasterActions();
}

function bindMasterActions() {
  document.querySelectorAll("[data-destination-delete]").forEach((button) => {
    button.addEventListener("click", () => deleteEntity("destinations", button.dataset.destinationDelete));
  });
  document.querySelectorAll("[data-carrier-delete]").forEach((button) => {
    button.addEventListener("click", () => deleteEntity("carriers", button.dataset.carrierDelete));
  });
}

function renderQualityLists() {
  if (!state.appState) return;
  renderQualityStack(elements.qualityPendingList, state.appState.quality.pending, true, "Sin pendientes.");
  renderQualityStack(elements.qualityReworkList, state.appState.quality.rework, true, "Sin vehículos en arreglos.");
  renderQualityStack(elements.qualityApprovedList, state.appState.quality.approved, false, "Sin vehículos aptos.");
  renderQualityStack(elements.qualityRejectedList, state.appState.quality.rejected, false, "Sin rechazos de calidad.");
}

function renderQualityStack(container, rows, allowInspect, emptyText) {
  if (!rows.length) {
    container.innerHTML = `<div class="empty">${emptyText}</div>`;
    return;
  }
  container.innerHTML = rows.map((item) => `
    <article class="vehicle-card">
      <h4>${escapeHtml(item.plate)} <span class="badge ${badgeClass(item.qualityStatus)}">${escapeHtml(translateQualityStatus(item.qualityStatus))}</span></h4>
      <div class="vehicle-meta">
        <span><strong>Transportadora:</strong> ${escapeHtml(item.carrier)}</span>
        <span><strong>Turno:</strong> ${item.turnPosition || "-"}</span>
        <span><strong>Conductor:</strong> ${escapeHtml(item.driverName)}</span>
        <span><strong>Celular:</strong> ${escapeHtml(item.driverPhone || "")}</span>
        <span><strong>Destino:</strong> ${escapeHtml(item.city)} - ${escapeHtml(item.zone)}</span>
        <span><strong>Responsable última:</strong> ${escapeHtml(item.latestInspection?.inspectorName || "-")}</span>
      </div>
      ${renderVehicleSupports(item)}
      <p class="muted-text">${escapeHtml(item.latestInspection?.findingsSummary || "Pendiente de checklist")}</p>
      ${allowInspect ? `<div class="actions"><button class="primary" type="button" data-quality-review="${item.id}">Revisar vehículo</button></div>` : ""}
    </article>
  `).join("");
  container.querySelectorAll("[data-quality-review]").forEach((button) => {
    const vehicle = rows.find((item) => item.id === button.dataset.qualityReview);
    button.addEventListener("click", () => openQualityModal(vehicle));
  });
}

function renderReport(container, rows, emptyText) {
  if (!rows?.length) {
    container.innerHTML = `<div class="empty">${emptyText}</div>`;
    return;
  }
  container.innerHTML = renderTable(
    [["Concepto", (item) => translateReportLabel(item.label)], ["Cantidad", (item) => item.count]],
    rows,
    emptyText
  );
}

function renderChecklistForm() {
  elements.qualityChecklistGrid.innerHTML = CHECKLIST_ITEMS.map((item) => `
    <section class="quality-item" data-check-item="${item.key}">
      <h4>${item.label}</h4>
      <div class="item-grid">
        <label>Resultado
          <select data-field="status">
            <option value="CUMPLE">Cumple</option>
            <option value="NO_CUMPLE">No cumple</option>
          </select>
        </label>
        ${item.evidence ? `<label>Foto evidencia<input data-field="evidence" type="file" accept="image/*" multiple /></label>` : ""}
      </div>
    </section>
  `).join("");
}

async function submitVehicle(event) {
  event.preventDefault();
  const form = new FormData(elements.vehicleForm);
  try {
    await request("/vehicles", {
      method: "POST",
      body: {
        plate: form.get("plate"),
        carrierId: form.get("carrierId"),
        driverName: form.get("driverName"),
        driverId: form.get("driverId"),
        driverPhone: form.get("driverPhone"),
        emptyWeightKg: form.get("emptyWeightKg"),
        destinationId: form.get("destinationId"),
      },
    });
    elements.vehicleForm.reset();
    await refreshAppState();
    showToast("Vehículo enturnado correctamente.");
  } catch (error) {
    showToast(error.message);
  }
}

async function submitDestination(event) {
  event.preventDefault();
  const form = new FormData(elements.destinationForm);
  try {
    await request("/destinations", { method: "POST", body: { city: form.get("destinationCity"), zone: form.get("destinationZone") } });
    elements.destinationForm.reset();
    await refreshAppState();
    showToast("Destino guardado.");
  } catch (error) {
    showToast(error.message);
  }
}

async function submitCarrier(event) {
  event.preventDefault();
  const form = new FormData(elements.carrierForm);
  try {
    await request("/carriers", { method: "POST", body: { code: form.get("carrierCode"), name: form.get("carrierName") } });
    elements.carrierForm.reset();
    await refreshAppState();
    showToast("Transportadora guardada.");
  } catch (error) {
    showToast(error.message);
  }
}

async function submitUser(event) {
  event.preventDefault();
  const form = new FormData(elements.userForm);
  try {
    await request("/users", {
      method: "POST",
      body: {
        username: form.get("newUsername"),
        fullName: form.get("newFullName"),
        role: form.get("newRole"),
        password: form.get("newPassword"),
      },
    });
    elements.userForm.reset();
    await refreshAppState();
    showToast("Usuario creado.");
  } catch (error) {
    showToast(error.message);
  }
}

async function submitSiteConfig(event) {
  event.preventDefault();
  try {
    await request("/settings/site", {
      method: "POST",
      body: {
        siteName: elements.siteName.value,
        siteLat: elements.siteLat.value,
        siteLng: elements.siteLng.value,
        siteRadiusM: elements.siteRadiusM.value,
        geofenceEnabled: elements.geofenceEnabled.checked,
      },
    });
    await refreshAppState();
    showToast("Geocerca actualizada.");
  } catch (error) {
    showToast(error.message);
  }
}

async function deleteEntity(entity, id) {
  if (!confirm("¿Seguro que deseas eliminar este registro?")) return;
  try {
    await request(`/${entity}/${encodeURIComponent(id)}`, { method: "DELETE" });
    await refreshAppState();
    showToast("Registro eliminado.");
  } catch (error) {
    showToast(error.message);
  }
}

async function assignVehicle(vehicleId) {
  try {
    await request(`/vehicles/${encodeURIComponent(vehicleId)}/assign`, { method: "POST" });
    await refreshAppState();
    showToast("Viaje asignado.");
  } catch (error) {
    showToast(error.message);
  }
}

function openRejectModal(vehicle) {
  state.rejectVehicle = vehicle;
  elements.rejectVehicleLabel.textContent = `Placa ${vehicle.plate} - ${vehicle.driverName}`;
  elements.rejectReason.value = vehicle.rejectionReason || "";
  elements.rejectModal.classList.remove("hidden");
}

function closeRejectModal() {
  state.rejectVehicle = null;
  elements.rejectForm.reset();
  elements.rejectModal.classList.add("hidden");
}

async function submitRejectVehicle(event) {
  event.preventDefault();
  if (!state.rejectVehicle) return;
  try {
    await request(`/vehicles/${encodeURIComponent(state.rejectVehicle.id)}/reject`, {
      method: "POST",
      body: { reason: elements.rejectReason.value },
    });
    closeRejectModal();
    await refreshAppState();
    showToast("Vehículo rechazado.");
  } catch (error) {
    showToast(error.message);
  }
}

function openQualityModal(vehicle) {
  state.qualityVehicle = vehicle;
  const inspection = vehicle.latestInspection || {};
  elements.qualityModalTitle.textContent = `Checklist ${vehicle.plate}`;
  elements.qualityMeta.textContent = `Conductor: ${vehicle.driverName} | Turno: ${vehicle.turnPosition || "-"} | Responsable: ${state.user.fullName}`;
  elements.observationsText.value = inspection.observationsText || "";
  elements.finalDecision.value = inspection.finalDecision || (vehicle.qualityStatus === "REWORK" ? "REWORK" : "APPROVED");
  document.querySelectorAll("[name='suitability']").forEach((checkbox) => {
    checkbox.checked = (inspection.suitability || []).includes(checkbox.value);
  });
  CHECKLIST_ITEMS.forEach((item) => {
    const wrapper = elements.qualityChecklistGrid.querySelector(`[data-check-item='${item.key}']`);
    const select = wrapper.querySelector("[data-field='status']");
    const existing = inspection.checklist?.[item.key];
    select.value = existing?.status || "CUMPLE";
    const input = wrapper.querySelector("[data-field='evidence']");
    if (input) input.value = "";
  });
  elements.qualityModal.classList.remove("hidden");
}

function closeQualityModal() {
  state.qualityVehicle = null;
  elements.qualityForm.reset();
  document.querySelectorAll("[name='suitability']").forEach((checkbox) => { checkbox.checked = false; });
  elements.qualityModal.classList.add("hidden");
}

async function submitQualityInspection(event) {
  event.preventDefault();
  if (!state.qualityVehicle) return;
  try {
    const checklist = {};
    for (const item of CHECKLIST_ITEMS) {
      const wrapper = elements.qualityChecklistGrid.querySelector(`[data-check-item='${item.key}']`);
      const status = wrapper.querySelector("[data-field='status']").value;
      const evidenceInput = wrapper.querySelector("[data-field='evidence']");
      const evidences = evidenceInput ? await filesToDataUrls(Array.from(evidenceInput.files || [])) : [];
      checklist[item.key] = { label: item.label, status, evidences };
    }
    const suitability = Array.from(document.querySelectorAll("[name='suitability']:checked")).map((item) => item.value);
    await request(`/quality/${encodeURIComponent(state.qualityVehicle.id)}/inspect`, {
      method: "POST",
      body: {
        finalDecision: elements.finalDecision.value,
        observationsText: elements.observationsText.value,
        suitability,
        checklist,
      },
    });
    closeQualityModal();
    await refreshAppState();
    showToast("Checklist guardado.");
  } catch (error) {
    showToast(error.message);
  }
}

function renderTable(columns, rows, emptyText) {
  if (!rows?.length) return `<div class="empty">${emptyText}</div>`;
  return `
    <div class="table-wrap">
      <table>
        <thead><tr>${columns.map(([title]) => `<th>${title}</th>`).join("")}</tr></thead>
        <tbody>
          ${rows.map((row, index) => `
            <tr>
              ${columns.map(([, renderer]) => `<td>${renderer(row, index) ?? ""}</td>`).join("")}
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function filterVehicles(rows) {
  const query = elements.searchInput.value.trim().toLowerCase();
  if (!query) return rows || [];
  return (rows || []).filter((row) =>
    [row.plate, row.carrier, row.carrierCode, row.driverName, row.driverId, row.driverPhone, row.city, row.zone, row.rejectionReason]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(query))
  );
}

function qualityBadge(status) {
  return `<span class="badge ${badgeClass(status)}">${escapeHtml(translateQualityStatus(status || "PENDING"))}</span>`;
}

function renderVehicleSupports(item) {
  const links = [];
  if (item.driverSelfieUrl) {
    links.push(`<a class="support-link" href="${encodeURI(item.driverSelfieUrl)}" target="_blank" rel="noopener noreferrer">Ver selfie</a>`);
  }
  if (item.driverSignatureUrl) {
    links.push(`<a class="support-link" href="${encodeURI(item.driverSignatureUrl)}" target="_blank" rel="noopener noreferrer">Ver firma</a>`);
  }
  return links.length ? `<div class="support-links">${links.join("")}</div>` : `<span class="muted-text">Sin soportes visuales.</span>`;
}

function badgeClass(status) {
  return {
    APPROVED: "approved",
    PENDING: "pending",
    IN_REVIEW: "pending",
    REWORK: "rework",
    REJECTED: "rejected",
    ASSIGNED: "assigned",
  }[status] || "pending";
}

function translateQualityStatus(status) {
  return {
    APPROVED: "Apto",
    PENDING: "Pendiente",
    IN_REVIEW: "En revisión",
    REWORK: "Requiere arreglos",
    REJECTED: "Rechazado",
    ASSIGNED: "Asignado",
  }[status] || status || "Pendiente";
}

function translateReportLabel(label) {
  return {
    APPROVED: "Apto",
    REWORK: "Requiere arreglos",
    REJECTED: "No apto / rechazado",
  }[label] || label;
}

async function filesToDataUrls(files) {
  const results = [];
  for (const file of files) {
    results.push(await fileToDataUrl(file));
  }
  return results;
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("No se pudo leer una imagen de evidencia."));
    reader.readAsDataURL(file);
  });
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method || "GET",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Ocurrió un error en el servidor.");
  return data;
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-CO", { dateStyle: "short", timeStyle: "short" }).format(date);
}

function formatNumber(value) {
  if (value === null || value === undefined || value === "") return "";
  return new Intl.NumberFormat("es-CO", { maximumFractionDigits: 1 }).format(Number(value));
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
