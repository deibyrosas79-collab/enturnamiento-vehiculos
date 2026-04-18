
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
  refreshButton: document.querySelector("#refreshButton"),
  welcomeText: document.querySelector("#welcomeText"),
  roleText: document.querySelector("#roleText"),
  navTabs: document.querySelectorAll(".nav-tab"),
  appViews: document.querySelectorAll(".app-view"),
  vehicleForm: document.querySelector("#vehicleForm"),
  carrierSelect: document.querySelector("#carrierId"),
  destinationSelect: document.querySelector("#destinationId"),
  searchInput: document.querySelector("#searchInput"),
  historySearchInput: document.querySelector("#historySearchInput"),
  queueTables: document.querySelector("#queueTables"),
  cityQueueTables: document.querySelector("#cityQueueTables"),
  historyTable: document.querySelector("#historyTable"),
  queueTabs: document.querySelectorAll("[data-queue-tab]"),
  destinationForm: document.querySelector("#destinationForm"),
  carrierForm: document.querySelector("#carrierForm"),
  userForm: document.querySelector("#userForm"),
  siteForm: document.querySelector("#siteForm"),
  destinationsTable: document.querySelector("#destinationsTable"),
  carriersTable: document.querySelector("#carriersTable"),
  usersTable: document.querySelector("#usersTable"),
  usersSection: document.querySelector("#usersSection"),
  catalogsSection: document.querySelector("#catalogsSection"),
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
  elements.openPublicPageButton.addEventListener("click", () => {
    const url = state.appState?.publicRegistrationUrl || "/driver.html";
    window.open(url, "_blank", "noopener");
  });
  elements.refreshButton.addEventListener("click", async () => {
    try {
      await refreshAppState();
      showToast("Información actualizada.");
    } catch (error) {
      showToast(error.message);
    }
  });
  elements.vehicleForm.addEventListener("submit", submitVehicle);
  elements.destinationForm.addEventListener("submit", submitDestination);
  elements.carrierForm.addEventListener("submit", submitCarrier);
  elements.userForm.addEventListener("submit", submitUser);
  elements.siteForm.addEventListener("submit", submitSiteConfig);
  elements.searchInput.addEventListener("input", () => {
    renderQueueTables();
    renderCityQueues();
  });
  elements.historySearchInput.addEventListener("input", renderHistoryTable);
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
  const {
    user,
    queued,
    quality,
    settings,
    destinations,
    carriers,
    users,
    analytics,
    permissions,
  } = state.appState;
  elements.welcomeText.textContent = `Hola, ${user.fullName}`;
  elements.roleText.textContent = `Rol activo: ${translateRole(user.role)}`;
  applyRoleVisibility(permissions);
  switchView(getFirstAllowedView(user.role === "CALIDAD" ? "quality" : state.currentView, permissions));
  populateSelect(elements.carrierSelect, carriers, "Selecciona transportadora", (item) => `${item.code} - ${item.name}`);
  populateMultiSelect(elements.destinationSelect, destinations, (item) => `${item.city} - ${item.zone}`);
  elements.publicRegistrationUrl.value = state.appState.publicRegistrationUrl;
  elements.publicQrImage.src = state.appState.publicQrUrl;
  elements.countQueued.textContent = analytics.queuedCount ?? queued.length;
  elements.countQualityPending.textContent = analytics.qualityPendingCount ?? quality.pending.length;
  elements.countQualityApproved.textContent = analytics.dailyApprovedCount ?? quality.dailyApprovedCount ?? 0;
  elements.countRejected.textContent = analytics.dailyRejectedCount ?? quality.dailyRejectedCount ?? 0;
  elements.qualityPendingCount.textContent = quality.pending.length;
  elements.qualityReworkCount.textContent = quality.rework.length;
  elements.qualityApprovedCount.textContent = quality.dailyApprovedCount ?? 0;
  elements.qualityRejectedCount.textContent = quality.dailyRejectedCount ?? 0;
  elements.siteName.value = settings.siteName || "Planta principal";
  elements.siteLat.value = settings.siteLat || "5.286142";
  elements.siteLng.value = settings.siteLng || "-72.402228";
  elements.siteRadiusM.value = settings.siteRadiusM || "180";
  elements.geofenceEnabled.checked = settings.geofenceEnabled;

  renderQueueTables();
  renderCityQueues();
  renderMastersTables(destinations, carriers, users, permissions);
  renderQualityLists();
  renderHistoryTable();
  renderReport(elements.carrierRejectReport, analytics.rejectedByCarrier, "No hay rechazos por transportadora.");
  renderReport(elements.reasonReport, analytics.topRejectionReasons, "No hay motivos registrados.");
  renderReport(elements.suitabilityReport, analytics.suitabilityCounts, "Sin datos de compatibilidad.");
  renderReport(elements.qualityDecisionReport, analytics.qualityDecisionCounts, "Sin decisiones de calidad.");
}

function applyRoleVisibility(permissions) {
  const visibleMap = {
    dashboard: Boolean(permissions?.canOperateLogistics),
    quality: Boolean(permissions?.canOperateQuality),
    history: true,
    masters: Boolean(permissions?.canManageCatalogs || permissions?.canManageUsers),
    reports: true,
    settings: Boolean(permissions?.canConfigureSite),
  };
  elements.navTabs.forEach((button) => {
    button.classList.toggle("hidden", !visibleMap[button.dataset.view]);
  });
  elements.vehicleForm.closest(".panel")?.classList.toggle("hidden", !permissions?.canOperateLogistics);
  elements.catalogsSection?.classList.toggle("hidden", !permissions?.canManageCatalogs);
  elements.usersSection?.classList.toggle("hidden", !permissions?.canManageUsers);
  elements.siteForm.closest(".panel")?.classList.toggle("hidden", !permissions?.canConfigureSite);
}

function getFirstAllowedView(preferredView, permissions) {
  const allowedViews = [
    { view: "dashboard", ok: Boolean(permissions?.canOperateLogistics) },
    { view: "quality", ok: Boolean(permissions?.canOperateQuality) },
    { view: "history", ok: true },
    { view: "reports", ok: true },
    { view: "masters", ok: Boolean(permissions?.canManageCatalogs || permissions?.canManageUsers) },
    { view: "settings", ok: Boolean(permissions?.canConfigureSite) },
  ].filter((item) => item.ok);
  return allowedViews.find((item) => item.view === preferredView)?.view || allowedViews[0]?.view || "history";
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

function populateMultiSelect(select, rows, formatter) {
  const selectedValues = new Set(Array.from(select.selectedOptions || []).map((option) => option.value));
  select.innerHTML = "";
  rows.forEach((row) => {
    const option = new Option(formatter(row), row.id);
    option.selected = selectedValues.has(row.id);
    select.append(option);
  });
}

function renderQueueTables() {
  if (!state.appState) return;
  if (state.queueTab === "queued") {
    const generalRows = filterVehicles(state.appState.queueGroups?.general || []);
    const dianaRows = filterVehicles(state.appState.queueGroups?.dianaAgricola || []);
    const columns = [
      ["Turno", (item) => item.turnPosition ? `<span class="turn">${item.turnPosition}</span>` : "-"],
      ["Cola", (item) => escapeHtml(item.queueGroupLabel || "-")],
      ["Placa", (item) => escapeHtml(item.plate)],
      ["Transportadora", (item) => escapeHtml(`${item.carrierCode || ""} - ${item.carrier}`.replace(/^ - /, ""))],
      ["Conductor", (item) => escapeHtml(item.driverName)],
      ["Celular", (item) => escapeHtml(item.driverPhone || "")],
      ["P. vacío (kg)", (item) => formatNumber(item.emptyWeightKg)],
      ["Destinos", renderDestinations],
      ["Turnos por ciudad", renderCityTurns],
      ["Calidad", (item) => qualityBadge(item.qualityStatus)],
      ["Canal", (item) => `<span class="badge channel">${escapeHtml(item.registrationChannel || "DESK")}</span>`],
      ["Soportes", renderVehicleSupports],
      ["Ingreso", (item) => formatDate(item.createdAt)],
      ["Espera a calidad", (item) => escapeHtml(item.reviewLeadLabel || "Pendiente")],
      ["Acciones", renderQueueActions],
    ];
    elements.queueTables.innerHTML = [
      renderNamedTable(
        "Fila general de transportadoras",
        "Aquí continúan todas las transportadoras diferentes de 4000801 - DIANA AGRICOLA S.A.S.",
        renderTable(columns, generalRows, "No hay vehículos en la fila general."),
      ),
      renderNamedTable(
        "Fila paralela DIANA AGRICOLA S.A.S",
        "Esta fila es exclusiva para la transportadora 4000801 - DIANA AGRICOLA S.A.S.",
        renderTable(columns, dianaRows, "No hay vehículos en la fila paralela de Diana Agrícola."),
      ),
    ].join("");
    bindQueueActions();
    return;
  }

  const rows = filterVehicles(state.appState[state.queueTab]);
  const columns = state.queueTab === "assigned"
    ? [
        ["#", (_item, index) => index + 1],
        ["Placa", (item) => escapeHtml(item.plate)],
        ["Transportadora", (item) => escapeHtml(item.carrier)],
        ["Conductor", (item) => escapeHtml(item.driverName)],
        ["Celular", (item) => escapeHtml(item.driverPhone || "")],
        ["Destinos", renderDestinations],
        ["Inspector", (item) => escapeHtml(item.latestInspection?.inspectorName || "-")],
        ["Revisión", (item) => formatDate(item.latestInspection?.reviewedAt)],
        ["Ingreso", (item) => formatDate(item.createdAt)],
        ["Asignado", (item) => formatDate(item.assignedAt)],
        ["Soportes", renderVehicleSupports],
      ]
    : [
        ["#", (_item, index) => index + 1],
        ["Placa", (item) => escapeHtml(item.plate)],
        ["Cola", (item) => escapeHtml(item.queueGroupLabel || "-")],
        ["Transportadora", (item) => escapeHtml(item.carrier)],
        ["Conductor", (item) => escapeHtml(item.driverName)],
        ["Destinos", renderDestinations],
        ["Calidad", (item) => qualityBadge(item.qualityStatus)],
        ["Inspector", (item) => escapeHtml(item.latestInspection?.inspectorName || "-")],
        ["Motivo", (item) => escapeHtml(item.rejectionReason || item.latestInspection?.findingsSummary || "No informado")],
        ["Rechazado", (item) => formatDate(item.rejectedAt)],
        ["Soportes", renderVehicleSupports],
      ];

  elements.queueTables.innerHTML = renderTable(
    columns,
    rows,
    state.queueTab === "assigned" ? "No hay viajes asignados." : "No hay vehículos rechazados.",
  );
  bindQueueActions();
}

function renderQueueActions(item) {
  if (!state.appState?.permissions?.canOperateLogistics || item.status !== "QUEUED") {
    return `<span class="muted-text">Solo lectura</span>`;
  }
  return `
    <div class="actions">
      <button class="primary small-action" type="button" data-action="assign" data-id="${item.id}" ${item.qualityStatus !== "APPROVED" ? "disabled" : ""}>Asignar</button>
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

function renderNamedTable(title, subtitle, content) {
  return `
    <section class="panel soft">
      <div class="panel-heading">
        <div>
          <h3>${escapeHtml(title)}</h3>
          <p>${escapeHtml(subtitle)}</p>
        </div>
      </div>
      ${content}
    </section>
  `;
}

function renderCityQueues() {
  if (!state.appState) return;
  const blocks = (state.appState.cityQueues || []).map((group) => {
    const rows = filterVehicles(group.vehicles || []);
    return renderNamedTable(
      group.city,
      `${rows.length} vehículo(s) visible(s) en esta ciudad.`,
      renderTable(
        [
          ["Turno", (item) => item.cityTurns?.[group.city] ? `<span class="turn">${item.cityTurns[group.city]}</span>` : "-"],
          ["Placa", (item) => escapeHtml(item.plate)],
          ["Transportadora", (item) => escapeHtml(item.carrier)],
          ["Cola", (item) => escapeHtml(item.queueGroupLabel || "-")],
          ["Conductor", (item) => escapeHtml(item.driverName)],
          ["Calidad", (item) => qualityBadge(item.qualityStatus)],
        ],
        rows,
        `No hay vehículos visibles para ${group.city}.`,
      ),
    );
  });
  elements.cityQueueTables.innerHTML = blocks.join("") || `<div class="empty">No hay ciudades configuradas.</div>`;
}

function renderMastersTables(destinations, carriers, users, permissions) {
  if (permissions?.canManageCatalogs) {
    elements.destinationsTable.innerHTML = renderTable(
      [["Ciudad", (item) => escapeHtml(item.city)], ["Zona", (item) => escapeHtml(item.zone)], ["Acción", (item) => `<button class="danger small-action" data-destination-delete="${item.id}" type="button">Eliminar</button>`]],
      destinations,
      "No hay destinos."
    );
    elements.carriersTable.innerHTML = renderTable(
      [["Código", (item) => escapeHtml(item.code)], ["Transportadora", (item) => escapeHtml(item.name)], ["Tipo de cola", (item) => item.code === "4000801" ? "Fila paralela Diana Agrícola" : "Fila general"], ["Acción", (item) => `<button class="danger small-action" data-carrier-delete="${item.id}" type="button">Eliminar</button>`]],
      carriers,
      "No hay transportadoras."
    );
  } else {
    elements.destinationsTable.innerHTML = `<div class="empty">Solo el administrador puede modificar destinos.</div>`;
    elements.carriersTable.innerHTML = `<div class="empty">Solo el administrador puede modificar transportadoras.</div>`;
  }

  if (permissions?.canManageUsers) {
    elements.usersTable.innerHTML = renderTable(
      [["Usuario", (item) => escapeHtml(item.username)], ["Nombre", (item) => escapeHtml(item.fullName)], ["Rol", (item) => translateRole(item.role)], ["Estado", (item) => item.active ? "Activo" : "Inactivo"]],
      users,
      "No hay usuarios."
    );
  } else {
    elements.usersTable.innerHTML = `<div class="empty">Solo el administrador general puede ver y crear usuarios.</div>`;
  }
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
        <span><strong>Cola:</strong> ${escapeHtml(item.queueGroupLabel || "-")}</span>
        <span><strong>Turno:</strong> ${item.turnPosition || "-"}</span>
        <span><strong>Conductor:</strong> ${escapeHtml(item.driverName)}</span>
        <span><strong>Celular:</strong> ${escapeHtml(item.driverPhone || "")}</span>
        <span><strong>Destinos:</strong> ${renderDestinations(item)}</span>
        <span><strong>Responsable última:</strong> ${escapeHtml(item.latestInspection?.inspectorName || "-")}</span>
        <span><strong>Revisado:</strong> ${escapeHtml(formatDate(item.latestInspection?.reviewedAt) || "Pendiente")}</span>
      </div>
      ${renderVehicleSupports(item)}
      <p class="muted-text">${escapeHtml(item.latestInspection?.findingsSummary || "Pendiente de checklist")}</p>
      ${allowInspect && state.appState.permissions?.canOperateQuality ? `<div class="actions"><button class="primary" type="button" data-quality-review="${item.id}">Revisar vehículo</button></div>` : ""}
    </article>
  `).join("");
  container.querySelectorAll("[data-quality-review]").forEach((button) => {
    const vehicle = rows.find((item) => item.id === button.dataset.qualityReview);
    button.addEventListener("click", () => openQualityModal(vehicle));
  });
}

function renderHistoryTable() {
  if (!state.appState) return;
  const rows = filterHistoryRows(state.appState.history || []);
  elements.historyTable.innerHTML = renderTable(
    [
      ["Fecha enturnamiento", (item) => escapeHtml(formatDateOnly(item.createdAt))],
      ["Hora enturnamiento", (item) => escapeHtml(formatTimeOnly(item.createdAt))],
      ["Placa", (item) => escapeHtml(item.plate)],
      ["Cola", (item) => escapeHtml(item.queueGroupLabel || "-")],
      ["Transportadora", (item) => escapeHtml(item.carrierLabel || item.carrier || "-")],
      ["Conductor", (item) => escapeHtml(item.driverName || "-")],
      ["Cédula", (item) => escapeHtml(item.driverId || "-")],
      ["Celular", (item) => escapeHtml(item.driverPhone || "-")],
      ["Destinos", (item) => escapeHtml(item.destinationSummary || "-")],
      ["Estado logística", (item) => escapeHtml(translateLogisticsStatus(item.status))],
      ["Estado calidad", (item) => qualityBadge(item.qualityStatus)],
      ["Selfie", (item) => renderSupportLink(item.driverSelfieUrl, "Ver selfie")],
      ["Firma", (item) => renderSupportLink(item.driverSignatureUrl, "Ver firma")],
      ["Inspector", (item) => escapeHtml(item.inspectorName || "-")],
      ["Fecha revisión", (item) => escapeHtml(formatDateOnly(item.reviewedAt))],
      ["Hora revisión", (item) => escapeHtml(formatTimeOnly(item.reviewedAt))],
      ["Tiempo enturnamiento vs calidad", (item) => escapeHtml(item.reviewLeadLabel || "Pendiente")],
      ["Hallazgos / motivo", (item) => escapeHtml(item.findingsSummary || item.rejectionReason || "-")],
    ],
    rows,
    "No hay historial registrado todavía.",
  );
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
  const destinationIds = Array.from(elements.destinationSelect.selectedOptions).map((option) => option.value).filter(Boolean);
  if (!destinationIds.length) {
    showToast("Debes seleccionar al menos un destino.");
    return;
  }
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
        destinationId: destinationIds[0],
        destinationIds,
      },
    });
    elements.vehicleForm.reset();
    Array.from(elements.destinationSelect.options).forEach((option) => { option.selected = false; });
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
  elements.qualityMeta.textContent = `Conductor: ${vehicle.driverName} | Cola: ${vehicle.queueGroupLabel || "-"} | Turno: ${vehicle.turnPosition || "-"} | Responsable: ${state.user.fullName}`;
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
    [row.plate, row.carrier, row.carrierCode, row.driverName, row.driverId, row.driverPhone, row.city, row.zone, row.queueGroupLabel, row.rejectionReason, renderDestinationsText(row)]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(query))
  );
}

function filterHistoryRows(rows) {
  const query = elements.historySearchInput.value.trim().toLowerCase();
  if (!query) return rows || [];
  return (rows || []).filter((row) =>
    [row.plate, row.carrier, row.carrierLabel, row.driverName, row.driverId, row.driverPhone, row.destinationSummary, row.queueGroupLabel, row.inspectorName, row.findingsSummary, row.rejectionReason]
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
    links.push(renderSupportLink(item.driverSelfieUrl, "Ver selfie"));
  }
  if (item.driverSignatureUrl) {
    links.push(renderSupportLink(item.driverSignatureUrl, "Ver firma"));
  }
  return links.length ? `<div class="support-links">${links.join("")}</div>` : `<span class="muted-text">Sin soportes visuales.</span>`;
}

function renderSupportLink(url, label) {
  if (!url) return `<span class="muted-text">Sin archivo</span>`;
  return `<a class="support-link" href="${encodeURI(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
}

function renderDestinations(item) {
  return escapeHtml(renderDestinationsText(item));
}

function renderDestinationsText(item) {
  const options = Array.isArray(item.destinationOptions) && item.destinationOptions.length
    ? item.destinationOptions.map((option) => `${option.city} - ${option.zone}`)
    : [`${item.city || ""}${item.zone ? ` - ${item.zone}` : ""}`.trim()];
  return options.filter(Boolean).join(", ");
}

function renderCityTurns(item) {
  const turns = item.cityTurns || {};
  const entries = Object.entries(turns);
  if (!entries.length) return "-";
  return entries.map(([city, turn]) => `${city}: ${turn}`).join(" | ");
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

function translateLogisticsStatus(status) {
  return {
    QUEUED: "En turno",
    ASSIGNED: "Viaje asignado",
    REJECTED: "Rechazado",
  }[status] || status || "-";
}

function translateRole(role) {
  return {
    ADMIN: "Administrador general",
    LOGISTICA: "Logística",
    CALIDAD: "Calidad",
  }[role] || role;
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

function formatDateOnly(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-CO", { dateStyle: "short" }).format(date);
}

function formatTimeOnly(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-CO", { timeStyle: "short" }).format(date);
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


