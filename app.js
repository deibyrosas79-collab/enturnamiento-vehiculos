
const API_BASE = window.location.protocol === "file:" ? "http://localhost:8000/api" : "/api";

const CHECKLIST_ITEMS = [
  { key: "foodLegend", label: "Cuenta con leyenda visible Transporte de alimentos", evidence: true },
  { key: "cleanliness", label: "Libre de suciedad", evidence: true },
  { key: "strangeSmells", label: "Libre de olores extraños", evidence: false },
  { key: "stains", label: "Libre de manchas", evidence: true },
  { key: "damage", label: "Libre de orificios y averías", evidence: true },
  { key: "humidity", label: "Libre de humedad", evidence: true },
  { key: "infestation", label: "Libre de infestación", evidence: true },
  { key: "woodenStakesPestFree", label: "Estacas de madera del vehículo libres de plagas (paredes y pisos)", evidence: true },
  { key: "bulkWallsFloor", label: "Granel en paredes y piso limpio y en buen estado", evidence: true },
  { key: "containerHoles", label: "Trompos limpios y protegidos", evidence: true },
  { key: "fumigationIn", label: "Fumigación ingreso", evidence: true },
  { key: "fumigationOut", label: "Fumigación salida", evidence: true },
];

const HISTORY_CHECKLIST_COLUMNS = [
  { key: "foodLegend", title: "Leyenda visible transporte de alimentos" },
  { key: "cleanliness", title: "Libre de suciedad" },
  { key: "strangeSmells", title: "Libre de olores extraños" },
  { key: "stains", title: "Libre de manchas" },
  { key: "damage", title: "Libre de orificios y averías" },
  { key: "humidity", title: "Libre de humedad" },
  { key: "infestation", title: "Libre de infestación" },
  { key: "woodenStakesPestFree", title: "Estacas de madera libres de plagas" },
  { key: "bulkWallsFloor", title: "Granel en paredes y piso" },
  { key: "containerHoles", title: "Trompos limpios y protegidos" },
  { key: "fumigationIn", title: "Fumigación ingreso" },
  { key: "fumigationOut", title: "Fumigación salida" },
];

const SUITABILITY_OPTIONS = ["Cadenas", "Mayoristas", "Bodegas y operadores", "Subproductos"];

const state = {
  user: null,
  appState: null,
  currentView: "dashboard",
  queueTab: "queued",
  rejectVehicle: null,
  qualityVehicle: null,
  suitabilityInsights: null,
  editVehicle: null,
  editingDestinationId: null,
  editingCarrierId: null,
  editingUserId: null,
  mediaPreviewMap: {},
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
  dashboardDestinationPicker: document.querySelector("#dashboardDestinationPicker"),
  dashboardDestinationToggle: document.querySelector("#dashboardDestinationToggle"),
  dashboardDestinationMenu: document.querySelector("#dashboardDestinationMenu"),
  dashboardDestinationHint: document.querySelector("#dashboardDestinationHint"),
  editCarrierSelect: document.querySelector("#editCarrierId"),
  editDestinationSelect: document.querySelector("#editDestinationIds"),
  editCenterSelect: document.querySelector("#editCenterId"),
  searchInput: document.querySelector("#searchInput"),
  historySearchInput: document.querySelector("#historySearchInput"),
  exportHistoryButton: document.querySelector("#exportHistoryButton"),
  queueTables: document.querySelector("#queueTables"),
  cityQueueTables: document.querySelector("#cityQueueTables"),
  historyTable: document.querySelector("#historyTable"),
  queueTabs: document.querySelectorAll("[data-queue-tab]"),
  destinationForm: document.querySelector("#destinationForm"),
  carrierForm: document.querySelector("#carrierForm"),
  userForm: document.querySelector("#userForm"),
  newCenterSelect: document.querySelector("#newCenterId"),
  destinationSubmitButton: document.querySelector("#destinationSubmitButton"),
  cancelDestinationEditButton: document.querySelector("#cancelDestinationEditButton"),
  carrierSubmitButton: document.querySelector("#carrierSubmitButton"),
  cancelCarrierEditButton: document.querySelector("#cancelCarrierEditButton"),
  userSubmitButton: document.querySelector("#userSubmitButton"),
  cancelUserEditButton: document.querySelector("#cancelUserEditButton"),
  siteForm: document.querySelector("#siteForm"),
  siteCenterSelect: document.querySelector("#siteCenterId"),
  destinationsTable: document.querySelector("#destinationsTable"),
  carriersTable: document.querySelector("#carriersTable"),
  usersTable: document.querySelector("#usersTable"),
  usersSection: document.querySelector("#usersSection"),
  newPassword: document.querySelector("#newPassword"),
  newUserActive: document.querySelector("#newUserActive"),
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
  suitabilityHistoryModal: document.querySelector("#suitabilityHistoryModal"),
  suitabilityHistoryTitle: document.querySelector("#suitabilityHistoryTitle"),
  suitabilityHistoryDescription: document.querySelector("#suitabilityHistoryDescription"),
  suitabilityHistoryTable: document.querySelector("#suitabilityHistoryTable"),
  closeSuitabilityHistoryButton: document.querySelector("#closeSuitabilityHistoryButton"),
  vehicleEditModal: document.querySelector("#vehicleEditModal"),
  vehicleEditForm: document.querySelector("#vehicleEditForm"),
  vehicleEditTitle: document.querySelector("#vehicleEditTitle"),
  vehicleEditMeta: document.querySelector("#vehicleEditMeta"),
  cancelVehicleEditButton: document.querySelector("#cancelVehicleEditButton"),
  editPlate: document.querySelector("#editPlate"),
  editDriverName: document.querySelector("#editDriverName"),
  editDriverId: document.querySelector("#editDriverId"),
  editDriverPhone: document.querySelector("#editDriverPhone"),
  editEmptyWeightKg: document.querySelector("#editEmptyWeightKg"),
  editVehicleStatus: document.querySelector("#editVehicleStatus"),
  editQualityStatus: document.querySelector("#editQualityStatus"),
  editRejectionReason: document.querySelector("#editRejectionReason"),
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
  mediaPreviewModal: document.querySelector("#mediaPreviewModal"),
  mediaPreviewTitle: document.querySelector("#mediaPreviewTitle"),
  mediaPreviewBody: document.querySelector("#mediaPreviewBody"),
  closeMediaPreviewButton: document.querySelector("#closeMediaPreviewButton"),
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
  elements.dashboardDestinationToggle?.addEventListener("click", toggleDashboardDestinationMenu);
  elements.destinationForm.addEventListener("submit", submitDestination);
  elements.carrierForm.addEventListener("submit", submitCarrier);
  elements.userForm.addEventListener("submit", submitUser);
  elements.cancelDestinationEditButton?.addEventListener("click", resetDestinationForm);
  elements.cancelCarrierEditButton?.addEventListener("click", resetCarrierForm);
  elements.cancelUserEditButton?.addEventListener("click", resetUserForm);
  elements.siteForm.addEventListener("submit", submitSiteConfig);
  elements.siteCenterSelect?.addEventListener("change", () => applySiteSettingsFromCenter(elements.siteCenterSelect.value));
  elements.searchInput.addEventListener("input", () => {
    renderQueueTables();
    renderCityQueues();
  });
  elements.historySearchInput.addEventListener("input", renderHistoryTable);
  elements.exportHistoryButton?.addEventListener("click", exportHistoryToExcel);
  elements.rejectForm.addEventListener("submit", submitRejectVehicle);
  elements.cancelRejectButton.addEventListener("click", closeRejectModal);
  elements.qualityForm.addEventListener("submit", submitQualityInspection);
  elements.cancelQualityButton.addEventListener("click", closeQualityModal);
  elements.closeSuitabilityHistoryButton?.addEventListener("click", closeSuitabilityHistoryModal);
  elements.vehicleEditForm?.addEventListener("submit", submitVehicleEdit);
  elements.cancelVehicleEditButton?.addEventListener("click", closeVehicleEditModal);
  elements.navTabs.forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view)));
  elements.queueTabs.forEach((button) => button.addEventListener("click", () => switchQueueTab(button.dataset.queueTab)));
  elements.rejectModal.addEventListener("click", (event) => {
    if (event.target === elements.rejectModal) closeRejectModal();
  });
  elements.qualityModal.addEventListener("click", (event) => {
    if (event.target === elements.qualityModal) closeQualityModal();
  });
  elements.suitabilityHistoryModal?.addEventListener("click", (event) => {
    if (event.target === elements.suitabilityHistoryModal) closeSuitabilityHistoryModal();
  });
  elements.vehicleEditModal?.addEventListener("click", (event) => {
    if (event.target === elements.vehicleEditModal) closeVehicleEditModal();
  });
  elements.mediaPreviewModal?.addEventListener("click", (event) => {
    if (event.target === elements.mediaPreviewModal) closeMediaPreviewModal();
  });
  elements.closeMediaPreviewButton?.addEventListener("click", closeMediaPreviewModal);
  document.addEventListener("click", handleMediaPreviewClick);
  document.addEventListener("click", handleDashboardDestinationDocumentClick);
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
  state.mediaPreviewMap = {};
  const {
    user,
    queued,
    quality,
    settings,
    destinations,
    carriers,
    centers,
    users,
    analytics,
    permissions,
  } = state.appState;
  elements.welcomeText.textContent = `Hola, ${user.fullName}`;
  elements.roleText.textContent = `Rol activo: ${translateRole(user.role)}${user.centerName ? ` · ${user.centerName}` : ""}`;
  applyRoleVisibility(permissions);
  switchView(getFirstAllowedView(user.role === "CALIDAD" ? "quality" : state.currentView, permissions));
  populateSelect(elements.carrierSelect, carriers, "Selecciona transportadora", (item) => `${item.code} - ${item.name}`);
  populateMultiSelect(elements.destinationSelect, destinations, (item) => `${item.city} - ${item.zone}`);
  renderDashboardDestinationMenu(destinations);
  populateSelect(elements.editCarrierSelect, carriers, "Selecciona transportadora", (item) => `${item.code} - ${item.name}`);
  populateSelect(elements.editDestinationSelect, destinations, "Selecciona destino", (item) => `${item.city} - ${item.zone}`);
  populateSelect(elements.newCenterSelect, centers || [], "Selecciona centro / CEDI", (item) => `${item.code} - ${item.name}`);
  populateSelect(elements.editCenterSelect, centers || [], "Selecciona centro / CEDI", (item) => `${item.code} - ${item.name}`);
  populateSelect(elements.siteCenterSelect, centers || [], "Selecciona centro / CEDI", (item) => `${item.code} - ${item.name}`);
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
  if (elements.siteCenterSelect) {
    elements.siteCenterSelect.value = settings.centerId || user.centerId || centers?.[0]?.id || "";
    applySiteSettingsFromCenter(elements.siteCenterSelect.value);
  } else {
    elements.siteName.value = settings.siteName || "Planta principal";
    elements.siteLat.value = settings.siteLat || "5.286142";
    elements.siteLng.value = settings.siteLng || "-72.402228";
    elements.siteRadiusM.value = settings.siteRadiusM || "180";
    elements.geofenceEnabled.checked = settings.geofenceEnabled;
  }
  state.suitabilityInsights = buildSuitabilityInsights(state.appState.history || []);

  renderQueueTables();
  renderCityQueues();
  renderMastersTables(destinations, carriers, users, permissions);
  renderQualityLists();
  renderHistoryTable();
  renderReport(elements.carrierRejectReport, analytics.rejectedByCarrier, "No hay rechazos por transportadora.");
  renderReport(elements.reasonReport, analytics.topRejectionReasons, "No hay motivos registrados.");
  renderSuitabilityReport();
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

function renderDashboardDestinationMenu(rows) {
  if (!elements.dashboardDestinationMenu) return;
  const selectedValues = new Set(Array.from(elements.destinationSelect.selectedOptions || []).map((option) => option.value));
  elements.dashboardDestinationMenu.innerHTML = rows.map((row) => `
    <label class="multi-select-option">
      <input type="checkbox" value="${escapeHtml(row.id)}" ${selectedValues.has(row.id) ? "checked" : ""} />
      <span class="multi-select-copy">
        <strong>${escapeHtml(row.city)}</strong>
        <small>${escapeHtml(row.zone)}</small>
      </span>
    </label>
  `).join("");
  elements.dashboardDestinationMenu.querySelectorAll("input[type='checkbox']").forEach((checkbox) => {
    checkbox.addEventListener("change", syncDashboardDestinationSelection);
  });
  syncDashboardDestinationSummary();
}

function syncDashboardDestinationSelection() {
  const checkedValues = new Set(
    Array.from(elements.dashboardDestinationMenu.querySelectorAll("input[type='checkbox']:checked"))
      .map((input) => input.value)
      .filter(Boolean),
  );
  Array.from(elements.destinationSelect.options).forEach((option) => {
    option.selected = checkedValues.has(option.value);
  });
  syncDashboardDestinationSummary();
}

function syncDashboardDestinationSummary() {
  if (!elements.dashboardDestinationToggle || !elements.dashboardDestinationHint) return;
  const selectedRows = Array.from(elements.destinationSelect.selectedOptions || [])
    .map((option) => state.appState?.destinations?.find((item) => item.id === option.value))
    .filter(Boolean);
  const labels = selectedRows.map((item) => `${item.city} - ${item.zone}`);
  if (!labels.length) {
    elements.dashboardDestinationToggle.textContent = "Selecciona uno o mas destinos";
    elements.dashboardDestinationHint.textContent = "Selecciona al menos un destino.";
    return;
  }
  elements.dashboardDestinationToggle.textContent = labels.length === 1 ? labels[0] : `${labels.length} destinos seleccionados`;
  elements.dashboardDestinationHint.textContent = `Seleccionados: ${labels.join(" | ")}`;
}

function toggleDashboardDestinationMenu(event) {
  event?.preventDefault();
  if (!elements.dashboardDestinationMenu) return;
  const willOpen = elements.dashboardDestinationMenu.classList.contains("hidden");
  elements.dashboardDestinationMenu.classList.toggle("hidden", !willOpen);
  elements.dashboardDestinationToggle?.setAttribute("aria-expanded", willOpen ? "true" : "false");
  elements.dashboardDestinationPicker?.closest(".panel")?.classList.toggle("dropdown-open", willOpen);
}

function closeDashboardDestinationMenu() {
  elements.dashboardDestinationMenu?.classList.add("hidden");
  elements.dashboardDestinationToggle?.setAttribute("aria-expanded", "false");
  elements.dashboardDestinationPicker?.closest(".panel")?.classList.remove("dropdown-open");
}

function handleDashboardDestinationDocumentClick(event) {
  if (!elements.dashboardDestinationPicker || !elements.dashboardDestinationMenu || elements.dashboardDestinationMenu.classList.contains("hidden")) {
    return;
  }
  if (!event.target.closest("#dashboardDestinationPicker")) {
    closeDashboardDestinationMenu();
  }
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
      ["Alerta historial", renderSuitabilityAlertCell],
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

  if (state.appState?.permissions?.isAdmin) {
    columns.push(["Acciones", renderRecordActions]);
  }

  elements.queueTables.innerHTML = renderTable(
    columns,
    rows,
    state.queueTab === "assigned" ? "No hay viajes asignados." : "No hay vehículos rechazados.",
  );
  bindQueueActions();
}

function renderQueueActions(item) {
  const actions = [];
  if (state.appState?.permissions?.canOperateLogistics && item.status === "QUEUED") {
    actions.push(`<button class="primary small-action" type="button" data-action="assign" data-id="${item.id}" ${item.qualityStatus !== "APPROVED" ? "disabled" : ""}>Asignar</button>`);
    actions.push(`<button class="danger small-action" type="button" data-action="reject" data-id="${item.id}">Rechazar</button>`);
  }
  if (state.appState?.permissions?.isAdmin) {
    actions.push(`<button class="ghost small-action" type="button" data-action="edit-record" data-id="${item.id}">Editar</button>`);
    actions.push(`<button class="danger small-action" type="button" data-action="delete-record" data-id="${item.id}">Eliminar</button>`);
  }
  if (!actions.length) return `<span class="muted-text">Solo lectura</span>`;
  return `<div class="actions">${actions.join("")}</div>`;
}

function bindQueueActions() {
  elements.queueTables.querySelectorAll("[data-action='assign']").forEach((button) => {
    button.addEventListener("click", () => assignVehicle(button.dataset.id));
  });
  elements.queueTables.querySelectorAll("[data-action='reject']").forEach((button) => {
    const vehicle = state.appState.queued.find((item) => item.id === button.dataset.id);
    button.addEventListener("click", () => openRejectModal(vehicle));
  });
  bindRecordActions(elements.queueTables);
}

function bindRecordActions(container) {
  if (!container) return;
  container.querySelectorAll("[data-action='edit-record']").forEach((button) => {
    button.addEventListener("click", () => openVehicleEditModal(findVehicleById(button.dataset.id)));
  });
  container.querySelectorAll("[data-action='delete-record']").forEach((button) => {
    button.addEventListener("click", () => deleteVehicleRecord(button.dataset.id));
  });
}

function renderRecordActions(item) {
  if (!state.appState?.permissions?.isAdmin) return `<span class="muted-text">Solo lectura</span>`;
  return `
    <div class="actions">
      <button class="ghost small-action" type="button" data-action="edit-record" data-id="${item.id}">Editar</button>
      <button class="danger small-action" type="button" data-action="delete-record" data-id="${item.id}">Eliminar</button>
    </div>
  `;
}

function findVehicleById(vehicleId) {
  const allVehicles = [
    ...(state.appState?.queued || []),
    ...(state.appState?.assigned || []),
    ...(state.appState?.rejected || []),
  ];
  return allVehicles.find((item) => item.id === vehicleId) || null;
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
          ["Turno", (item) => item.turnPosition ? `<span class="turn">${item.turnPosition}</span>` : "-"],
          ["Placa", (item) => escapeHtml(item.plate)],
          ["Transportadora", (item) => escapeHtml(item.carrier)],
          ["Cola", (item) => escapeHtml(item.queueGroupLabel || "-")],
          ["Conductor", (item) => escapeHtml(item.driverName)],
          ["Calidad", (item) => qualityBadge(item.qualityStatus || "PENDING")],
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
      [
        ["Ciudad", (item) => escapeHtml(item.city)],
        ["Zona", (item) => escapeHtml(item.zone)],
        ["Acción", (item) => renderCatalogActions("destination", item.id, permissions)],
      ],
      destinations,
      "No hay destinos."
    );
    elements.carriersTable.innerHTML = renderTable(
      [
        ["Código", (item) => escapeHtml(item.code)],
        ["Transportadora", (item) => escapeHtml(item.name)],
        ["Tipo de cola", (item) => item.code === "4000801" ? "Fila paralela Diana Agrícola" : "Fila general"],
        ["Acción", (item) => renderCatalogActions("carrier", item.id, permissions)],
      ],
      carriers,
      "No hay transportadoras."
    );
  } else {
    elements.destinationsTable.innerHTML = `<div class="empty">Solo el administrador puede modificar destinos.</div>`;
    elements.carriersTable.innerHTML = `<div class="empty">Solo el administrador puede modificar transportadoras.</div>`;
  }

  if (permissions?.canManageUsers) {
    elements.usersTable.innerHTML = renderTable(
      [["Usuario", (item) => escapeHtml(item.username)], ["Nombre", (item) => escapeHtml(item.fullName)], ["Rol", (item) => translateRole(item.role)], ["Centro", (item) => escapeHtml(`${item.centerCode || ""} - ${item.centerName || ""}`.replace(/^ - /, ""))], ["Estado", (item) => item.active ? "Activo" : "Inactivo"], ["Acción", (item) => `<div class="actions"><button class="ghost small-action" data-user-edit="${item.id}" type="button">Editar</button></div>`]],
      users,
      "No hay usuarios."
    );
  } else {
    elements.usersTable.innerHTML = `<div class="empty">Solo el administrador general puede ver y crear usuarios.</div>`;
  }
  bindMasterActions();
}

function renderCatalogActions(entityType, entityId, permissions) {
  if (!permissions?.canEditCatalogs && !permissions?.canDeleteCatalogs) {
    return `<span class="muted-text">Solo agregar</span>`;
  }
  const buttons = [];
  if (permissions?.canEditCatalogs) {
    buttons.push(
      entityType === "destination"
        ? `<button class="ghost small-action" data-destination-edit="${entityId}" type="button">Editar</button>`
        : `<button class="ghost small-action" data-carrier-edit="${entityId}" type="button">Editar</button>`,
    );
  }
  if (permissions?.canDeleteCatalogs) {
    buttons.push(
      entityType === "destination"
        ? `<button class="danger small-action" data-destination-delete="${entityId}" type="button">Eliminar</button>`
        : `<button class="danger small-action" data-carrier-delete="${entityId}" type="button">Eliminar</button>`,
    );
  }
  return buttons.length ? `<div class="actions">${buttons.join("")}</div>` : `<span class="muted-text">Solo agregar</span>`;
}

function applySiteSettingsFromCenter(centerId) {
  const center = (state.appState?.centers || []).find((item) => item.id === centerId);
  const fallback = state.appState?.settings || {};
  elements.siteName.value = center?.name || fallback.siteName || "Planta principal";
  elements.siteLat.value = center?.siteLat || fallback.siteLat || "5.286142";
  elements.siteLng.value = center?.siteLng || fallback.siteLng || "-72.402228";
  elements.siteRadiusM.value = center?.siteRadiusM || fallback.siteRadiusM || "180";
  elements.geofenceEnabled.checked = center ? Boolean(center.geofenceEnabled) : Boolean(fallback.geofenceEnabled);
}

function bindMasterActions() {
  document.querySelectorAll("[data-destination-edit]").forEach((button) => {
    button.addEventListener("click", () => startDestinationEdit(button.dataset.destinationEdit));
  });
  document.querySelectorAll("[data-destination-delete]").forEach((button) => {
    button.addEventListener("click", () => deleteEntity("destinations", button.dataset.destinationDelete));
  });
  document.querySelectorAll("[data-carrier-edit]").forEach((button) => {
    button.addEventListener("click", () => startCarrierEdit(button.dataset.carrierEdit));
  });
  document.querySelectorAll("[data-carrier-delete]").forEach((button) => {
    button.addEventListener("click", () => deleteEntity("carriers", button.dataset.carrierDelete));
  });
  document.querySelectorAll("[data-user-edit]").forEach((button) => {
    button.addEventListener("click", () => startUserEdit(button.dataset.userEdit));
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
        <span><strong>Historial útil:</strong> ${renderSuitabilityAlertInline(item)}</span>
        <span><strong>Responsable última:</strong> ${escapeHtml(item.latestInspection?.inspectorName || "-")}</span>
        <span><strong>Revisado:</strong> ${escapeHtml(formatDate(item.latestInspection?.reviewedAt) || "Pendiente")}</span>
      </div>
      ${renderVehicleSupports(item)}
      <p class="muted-text">${escapeHtml(item.latestInspection?.findingsSummary || "Pendiente de checklist")}</p>
      ${(allowInspect && state.appState.permissions?.canOperateQuality) || state.appState.permissions?.isAdmin ? `
        <div class="actions">
          ${allowInspect && state.appState.permissions?.canOperateQuality ? `<button class="primary" type="button" data-quality-review="${item.id}">Revisar vehículo</button>` : ""}
          ${state.appState.permissions?.isAdmin ? `<button class="ghost" type="button" data-quality-edit="${item.id}">Editar registro</button><button class="danger" type="button" data-quality-delete="${item.id}">Eliminar</button>` : ""}
        </div>
      ` : ""}
    </article>
  `).join("");
  container.querySelectorAll("[data-quality-review]").forEach((button) => {
    const vehicle = rows.find((item) => item.id === button.dataset.qualityReview);
    button.addEventListener("click", () => openQualityModal(vehicle));
  });
  container.querySelectorAll("[data-quality-edit]").forEach((button) => {
    const vehicle = rows.find((item) => item.id === button.dataset.qualityEdit);
    button.addEventListener("click", () => openVehicleEditModal(vehicle));
  });
  container.querySelectorAll("[data-quality-delete]").forEach((button) => {
    button.addEventListener("click", () => deleteVehicleRecord(button.dataset.qualityDelete));
  });
}

function renderHistoryTable() {
  if (!state.appState) return;
  const rows = filterHistoryRows(state.appState.history || []);
  elements.historyTable.innerHTML = renderTable(getHistoryColumns(false), rows, "No hay historial registrado todavía.");
  bindRecordActions(elements.historyTable);
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

function renderSuitabilityReport() {
  const categories = state.suitabilityInsights?.categories || [];
  if (!categories.length || categories.every((item) => !item.rows.length)) {
    elements.suitabilityReport.innerHTML = `<div class="empty">Sin datos de compatibilidad.</div>`;
    return;
  }
  elements.suitabilityReport.innerHTML = renderTable(
    [
      [
        "Concepto",
        (item) => item.rows.length
          ? `<button class="report-link" type="button" data-suitability-history="${encodeURIComponent(item.label)}">${escapeHtml(item.label)}</button>`
          : `<span class="muted-text">${escapeHtml(item.label)}</span>`,
      ],
      ["Cantidad", (item) => item.rows.length],
    ],
    categories,
    "Sin datos de compatibilidad.",
  );
  elements.suitabilityReport.querySelectorAll("[data-suitability-history]").forEach((button) => {
    button.addEventListener("click", () => openSuitabilityHistoryModal(decodeURIComponent(button.dataset.suitabilityHistory)));
  });
}

function openSuitabilityHistoryModal(category) {
  const categoryData = state.suitabilityInsights?.categories.find((item) => item.label === category);
  const rows = categoryData?.rows || [];
  elements.suitabilityHistoryTitle.textContent = `Historial de vehículos aptos para ${category}`;
  elements.suitabilityHistoryDescription.textContent = rows.length
    ? `Aquí ves las placas que ya han servido para ${category}. Esta información también aparecerá como alerta cuando esa placa vuelva a enturnarse.`
    : `Todavía no hay placas con historial apto para ${category}.`;
  elements.suitabilityHistoryTable.innerHTML = renderTable(
    [
      ["Placa", (item) => escapeHtml(item.plate)],
      ["Transportadora más reciente", (item) => escapeHtml(item.carrier || "-")],
      ["Último conductor", (item) => escapeHtml(item.driverName || "-")],
      ["Veces apto", (item) => escapeHtml(String(item.approvalCount || 0))],
      ["Última revisión", (item) => escapeHtml(formatDate(item.lastReviewedAt) || "-")],
      ["Inspector última", (item) => escapeHtml(item.inspectorName || "-")],
      ["Destinos", (item) => escapeHtml(item.destinationsText || "-")],
    ],
    rows,
    `No hay historial disponible para ${category}.`,
  );
  elements.suitabilityHistoryModal.classList.remove("hidden");
}

function closeSuitabilityHistoryModal() {
  elements.suitabilityHistoryModal.classList.add("hidden");
}

function openVehicleEditModal(vehicle) {
  if (!vehicle) {
    showToast("No se encontró el registro que deseas editar.");
    return;
  }
  state.editVehicle = vehicle;
  elements.vehicleEditTitle.textContent = `Editar registro ${vehicle.plate}`;
  elements.vehicleEditMeta.textContent = `Administrador: puedes corregir cualquier dato del registro y volver a guardarlo.`;
  elements.editPlate.value = vehicle.plate || "";
  elements.editCarrierSelect.value = vehicle.carrierId || "";
  elements.editDriverName.value = vehicle.driverName || "";
  elements.editDriverId.value = vehicle.driverId || "";
  elements.editDriverPhone.value = vehicle.driverPhone || "";
  elements.editEmptyWeightKg.value = vehicle.emptyWeightKg ?? "";
  elements.editCenterSelect.value = vehicle.centerId || "1010";
  const selectedDestinations = vehicle.destinationIds || (vehicle.destinationId ? [vehicle.destinationId] : []);
  elements.editDestinationSelect.value = selectedDestinations[0] || "";
  elements.editVehicleStatus.value = vehicle.status || "QUEUED";
  elements.editQualityStatus.value = vehicle.qualityStatus || "PENDING";
  elements.editRejectionReason.value = vehicle.rejectionReason || "";
  elements.vehicleEditModal.classList.remove("hidden");
}

function closeVehicleEditModal() {
  state.editVehicle = null;
  elements.vehicleEditForm?.reset();
  elements.vehicleEditModal.classList.add("hidden");
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
  const registeredPlate = normalizePlateClient(form.get("plate"));
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
    renderDashboardDestinationMenu(state.appState?.destinations || []);
    closeDashboardDestinationMenu();
    await refreshAppState();
    const suitabilityHistory = getPlateSuitabilityHistory(registeredPlate);
    showToast(
      suitabilityHistory.length
        ? `Vehículo enturnado. Historial útil detectado: ${suitabilityHistory.join(", ")}.`
        : "Vehículo enturnado correctamente.",
    );
  } catch (error) {
    showToast(error.message);
  }
}

async function submitDestination(event) {
  event.preventDefault();
  const form = new FormData(elements.destinationForm);
  const isEditing = Boolean(state.editingDestinationId);
  try {
    const path = isEditing ? `/destinations/${encodeURIComponent(state.editingDestinationId)}` : "/destinations";
    const method = isEditing ? "PUT" : "POST";
    await request(path, { method, body: { city: form.get("destinationCity"), zone: form.get("destinationZone") } });
    resetDestinationForm();
    await refreshAppState();
    showToast(isEditing ? "Destino actualizado." : "Destino guardado.");
  } catch (error) {
    showToast(error.message);
  }
}

async function submitCarrier(event) {
  event.preventDefault();
  const form = new FormData(elements.carrierForm);
  const isEditing = Boolean(state.editingCarrierId);
  try {
    const path = isEditing ? `/carriers/${encodeURIComponent(state.editingCarrierId)}` : "/carriers";
    const method = isEditing ? "PUT" : "POST";
    await request(path, { method, body: { code: form.get("carrierCode"), name: form.get("carrierName") } });
    resetCarrierForm();
    await refreshAppState();
    showToast(isEditing ? "Transportadora actualizada." : "Transportadora guardada.");
  } catch (error) {
    showToast(error.message);
  }
}

async function submitUser(event) {
  event.preventDefault();
  const form = new FormData(elements.userForm);
  const isEditing = Boolean(state.editingUserId);
  if (!isEditing && !String(form.get("newPassword") || "").trim()) {
    showToast("La clave es obligatoria para crear el usuario.");
    return;
  }
  try {
    await request(isEditing ? `/users/${encodeURIComponent(state.editingUserId)}` : "/users", {
      method: isEditing ? "PUT" : "POST",
      body: {
        username: form.get("newUsername"),
        fullName: form.get("newFullName"),
        role: form.get("newRole"),
        centerId: form.get("newCenterId"),
        password: form.get("newPassword"),
        active: elements.newUserActive.checked,
      },
    });
    resetUserForm();
    await refreshAppState();
    showToast(isEditing ? "Usuario actualizado." : "Usuario creado.");
  } catch (error) {
    showToast(error.message);
  }
}

function startDestinationEdit(destinationId) {
  const destination = (state.appState?.destinations || []).find((item) => item.id === destinationId);
  if (!destination) return;
  state.editingDestinationId = destination.id;
  document.querySelector("#destinationCity").value = destination.city || "";
  document.querySelector("#destinationZone").value = destination.zone || "";
  elements.destinationSubmitButton.textContent = "Guardar cambios";
  elements.cancelDestinationEditButton.classList.remove("hidden");
}

function resetDestinationForm() {
  state.editingDestinationId = null;
  elements.destinationForm.reset();
  elements.destinationSubmitButton.textContent = "Guardar destino";
  elements.cancelDestinationEditButton.classList.add("hidden");
}

function startCarrierEdit(carrierId) {
  const carrier = (state.appState?.carriers || []).find((item) => item.id === carrierId);
  if (!carrier) return;
  state.editingCarrierId = carrier.id;
  document.querySelector("#carrierCode").value = carrier.code || "";
  document.querySelector("#carrierName").value = carrier.name || "";
  elements.carrierSubmitButton.textContent = "Guardar cambios";
  elements.cancelCarrierEditButton.classList.remove("hidden");
}

function resetCarrierForm() {
  state.editingCarrierId = null;
  elements.carrierForm.reset();
  elements.carrierSubmitButton.textContent = "Guardar transportadora";
  elements.cancelCarrierEditButton.classList.add("hidden");
}

function startUserEdit(userId) {
  const user = (state.appState?.users || []).find((item) => item.id === userId);
  if (!user) return;
  state.editingUserId = user.id;
  document.querySelector("#newUsername").value = user.username || "";
  document.querySelector("#newFullName").value = user.fullName || "";
  document.querySelector("#newRole").value = user.role || "LOGISTICA";
  elements.newCenterSelect.value = user.centerId || "1010";
  elements.newPassword.value = "";
  elements.newUserActive.checked = Boolean(user.active);
  elements.userSubmitButton.textContent = "Guardar cambios";
  elements.cancelUserEditButton.classList.remove("hidden");
}

function resetUserForm() {
  state.editingUserId = null;
  elements.userForm.reset();
  document.querySelector("#newRole").value = "LOGISTICA";
  if (elements.newCenterSelect.options.length) {
    elements.newCenterSelect.selectedIndex = 0;
  }
  elements.newUserActive.checked = true;
  elements.userSubmitButton.textContent = "Crear usuario";
  elements.cancelUserEditButton.classList.add("hidden");
}

async function submitSiteConfig(event) {
  event.preventDefault();
  const selectedCenterId = elements.siteCenterSelect?.value || state.appState?.settings?.centerId || state.user?.centerId || "1010";
  try {
    await request("/settings/site", {
      method: "POST",
      body: {
        centerId: selectedCenterId,
        siteName: elements.siteName.value,
        siteLat: elements.siteLat.value,
        siteLng: elements.siteLng.value,
        siteRadiusM: elements.siteRadiusM.value,
        geofenceEnabled: elements.geofenceEnabled.checked,
      },
    });
    await refreshAppState();
    if (elements.siteCenterSelect) {
      elements.siteCenterSelect.value = selectedCenterId;
      applySiteSettingsFromCenter(selectedCenterId);
    }
    showToast("Geocerca actualizada.");
  } catch (error) {
    showToast(error.message);
  }
}

async function submitVehicleEdit(event) {
  event.preventDefault();
  if (!state.editVehicle) return;
  const destinationIds = Array.from(elements.editDestinationSelect.selectedOptions).map((option) => option.value).filter(Boolean);
  if (!destinationIds.length) {
    showToast("Debes seleccionar al menos un destino para el registro.");
    return;
  }
  try {
    await request(`/vehicles/${encodeURIComponent(state.editVehicle.id)}`, {
      method: "PUT",
      body: {
        plate: elements.editPlate.value,
        carrierId: elements.editCarrierSelect.value,
        driverName: elements.editDriverName.value,
        driverId: elements.editDriverId.value,
        driverPhone: elements.editDriverPhone.value,
        emptyWeightKg: elements.editEmptyWeightKg.value,
        centerId: elements.editCenterSelect.value,
        destinationId: destinationIds[0],
        destinationIds,
        status: elements.editVehicleStatus.value,
        qualityStatus: elements.editQualityStatus.value,
        rejectionReason: elements.editRejectionReason.value,
      },
    });
    closeVehicleEditModal();
    await refreshAppState();
    showToast("Registro corregido por administrador.");
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

async function deleteVehicleRecord(vehicleId) {
  if (!confirm("¿Seguro que deseas eliminar definitivamente este registro del vehículo?")) return;
  try {
    await request(`/vehicles/${encodeURIComponent(vehicleId)}`, { method: "DELETE" });
    closeVehicleEditModal();
    await refreshAppState();
    showToast("Registro eliminado por administrador.");
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
    [row.plate, row.carrier, row.carrierCode, row.driverName, row.driverId, row.driverPhone, row.city, row.zone, row.queueGroupLabel, row.rejectionReason, renderDestinationsText(row), getPlateSuitabilityHistory(row.plate).join(", ")]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(query))
  );
}

function filterHistoryRows(rows) {
  const query = elements.historySearchInput.value.trim().toLowerCase();
  if (!query) return rows || [];
  return (rows || []).filter((row) =>
    [
      row.plate,
      getHistoryCarrierLabel(row),
      row.driverName,
      row.driverId,
      row.driverPhone,
      getHistoryDestinationSummary(row),
      row.queueGroupLabel,
      getHistoryInspectorName(row),
      getHistoryFindings(row),
      row.rejectionReason,
      ...HISTORY_CHECKLIST_COLUMNS.map((column) => `${column.title} ${getChecklistHistoryResult(row, column.key)}`),
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(query))
  );
}

function getHistoryColumns(forExport = false) {
  const columns = [
    ["Fecha enturnamiento", (item) => formatDateOnly(item.createdAt)],
    ["Hora enturnamiento", (item) => formatTimeOnly(item.createdAt)],
    ["Placa", (item) => item.plate || "-"],
    ["Cola", (item) => item.queueGroupLabel || "-"],
    ["Transportadora", (item) => getHistoryCarrierLabel(item)],
    ["Conductor", (item) => item.driverName || "-"],
    ["Cédula", (item) => item.driverId || "-"],
    ["Celular", (item) => item.driverPhone || "-"],
    ["P. vacío (kg)", (item) => formatNumber(item.emptyWeightKg) || "-"],
    ["Destinos", (item) => getHistoryDestinationSummary(item)],
    ["Turnos por ciudad", (item) => getHistoryCityTurns(item)],
    ["Estado logística", (item) => translateLogisticsStatus(item.status)],
    ["Estado calidad", (item) => forExport ? translateQualityStatus(item.qualityStatus || "PENDING") : qualityBadge(item.qualityStatus)],
    ["Selfie", (item) => forExport ? getSupportText(item.driverSelfieUrl, "Selfie registrada") : renderSupportLink(item.driverSelfieUrl, "Ver selfie")],
    ["Firma", (item) => forExport ? getSupportText(item.driverSignatureUrl, "Firma registrada") : renderSupportLink(item.driverSignatureUrl, "Ver firma")],
    ["Inspector", (item) => getHistoryInspectorName(item)],
    ["Fecha revisión", (item) => formatDateOnly(getHistoryReviewedAt(item)) || "-"],
    ["Hora revisión", (item) => formatTimeOnly(getHistoryReviewedAt(item)) || "-"],
    ["Tiempo enturnamiento vs calidad", (item) => item.reviewLeadLabel || "Pendiente"],
    ["Hallazgos / motivo", (item) => getHistoryFindings(item)],
  ];
  HISTORY_CHECKLIST_COLUMNS.forEach((column) => {
    columns.push([column.title, (item) => getChecklistHistoryResult(item, column.key)]);
  });
  if (!forExport && state.appState?.permissions?.isAdmin) {
    columns.push(["Acciones", renderRecordActions]);
  }
  const htmlColumns = new Set(["Estado calidad", "Selfie", "Firma", "Acciones"]);
  return forExport
    ? columns
    : columns.map(([title, renderer]) => [
        title,
        (item, index) => htmlColumns.has(title) ? (renderer(item, index) ?? "") : escapeHtml(renderer(item, index)),
      ]);
}

function exportHistoryToExcel() {
  const rows = filterHistoryRows(state.appState?.history || []);
  if (!rows.length) {
    showToast("No hay registros para exportar en este informe.");
    return;
  }
  const columns = getHistoryColumns(true);
  const tableHtml = `
    <table>
      <thead>
        <tr>${columns.map(([title]) => `<th>${escapeHtml(title)}</th>`).join("")}</tr>
      </thead>
      <tbody>
        ${rows.map((row, index) => `
          <tr>
            ${columns.map(([, renderer]) => `<td>${escapeHtml(renderer(row, index) ?? "")}</td>`).join("")}
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
  const workbook = `
    <html xmlns:o="urn:schemas-microsoft-com:office:office"
          xmlns:x="urn:schemas-microsoft-com:office:excel"
          xmlns="http://www.w3.org/TR/REC-html40">
      <head>
        <meta charset="utf-8" />
        <style>
          table { border-collapse: collapse; }
          th, td { border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; }
          th { background: #dbeafe; font-weight: 700; }
        </style>
      </head>
      <body>${tableHtml}</body>
    </html>
  `;
  const blob = new Blob([`\ufeff${workbook}`], { type: "application/vnd.ms-excel;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `historial-enturnamiento-${new Date().toISOString().slice(0, 10)}.xls`;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  showToast("Informe exportado en Excel.");
}

function getHistoryCarrierLabel(item) {
  if (item.carrierLabel) return item.carrierLabel;
  const code = item.carrierCode ? `${item.carrierCode} - ` : "";
  return `${code}${item.carrier || ""}`.trim() || "-";
}

function getHistoryDestinationSummary(item) {
  if (item.destinationSummary) return item.destinationSummary;
  if (Array.isArray(item.destinations) && item.destinations.length) {
    return item.destinations.map((destination) => `${destination.city} - ${destination.zone}`).join(", ");
  }
  return renderDestinationsText(item) || "-";
}

function getHistoryCityTurns(item) {
  const entries = Object.entries(item.cityTurns || {});
  if (!entries.length) return "-";
  return entries.map(([city, turn]) => `${city}: ${turn}`).join(" | ");
}

function getHistoryInspectorName(item) {
  return item.qualityInspectorName || item.inspectorName || "-";
}

function getHistoryReviewedAt(item) {
  return item.qualityReviewedAt || item.reviewedAt || "";
}

function getHistoryFindings(item) {
  return item.qualityFindingsSummary || item.findingsSummary || item.qualityObservations || item.rejectionReason || "-";
}

function getChecklistHistoryResult(item, checklistKey) {
  const checklist = item.qualityChecklist || item.checklist || {};
  const status = checklist?.[checklistKey]?.status;
  if (status === "CUMPLE") return "Apto";
  if (status === "NO_CUMPLE") return "No apto";
  return "Pendiente";
}

function getSupportText(url, labelWhenPresent) {
  return url ? labelWhenPresent : "Sin archivo";
}

function buildSuitabilityInsights(historyRows) {
  const categoryBuckets = Object.fromEntries(SUITABILITY_OPTIONS.map((label) => [label, new Map()]));
  const plateAlerts = {};
  (historyRows || []).forEach((row) => {
    const plate = normalizePlateClient(row.plate);
    if (!plate) return;
    const inspections = Array.isArray(row.inspectionHistory) ? row.inspectionHistory : [];
    inspections.forEach((inspection) => {
      if (inspection.finalDecision !== "APPROVED") return;
      const suitability = Array.isArray(inspection.suitability) ? inspection.suitability : [];
      suitability.forEach((category) => {
        if (!categoryBuckets[category]) return;
        const existing = categoryBuckets[category].get(plate) || {
          plate,
          carrier: row.carrierLabel || row.carrier || "-",
          driverName: row.driverName || "-",
          approvalCount: 0,
          lastReviewedAt: inspection.reviewedAt || "",
          inspectorName: inspection.inspectorName || "-",
          destinationsText: getHistoryDestinationSummary(row),
        };
        existing.approvalCount += 1;
        const existingTime = new Date(existing.lastReviewedAt || 0).getTime();
        const candidateTime = new Date(inspection.reviewedAt || 0).getTime();
        if (!existing.lastReviewedAt || candidateTime >= existingTime) {
          existing.carrier = row.carrierLabel || row.carrier || "-";
          existing.driverName = row.driverName || "-";
          existing.lastReviewedAt = inspection.reviewedAt || "";
          existing.inspectorName = inspection.inspectorName || "-";
          existing.destinationsText = getHistoryDestinationSummary(row);
        }
        categoryBuckets[category].set(plate, existing);
        plateAlerts[plate] = plateAlerts[plate] || new Set();
        plateAlerts[plate].add(category);
      });
    });
  });
  return {
    categories: SUITABILITY_OPTIONS.map((label) => ({
      label,
      rows: Array.from(categoryBuckets[label].values()).sort((a, b) => {
        const dateA = new Date(a.lastReviewedAt || 0).getTime();
        const dateB = new Date(b.lastReviewedAt || 0).getTime();
        return dateB - dateA || a.plate.localeCompare(b.plate);
      }),
    })),
    plateAlerts: Object.fromEntries(
      Object.entries(plateAlerts).map(([plate, categories]) => [plate, Array.from(categories).sort((a, b) => a.localeCompare(b))]),
    ),
  };
}

function renderSuitabilityAlertCell(item) {
  const categories = getPlateSuitabilityHistory(item.plate);
  if (!categories.length) return `<span class="muted-text">Sin historial</span>`;
  return `<div class="suitability-alerts">${categories.map((category) => `<span class="badge suitability">${escapeHtml(category)}</span>`).join("")}</div>`;
}

function renderSuitabilityAlertInline(item) {
  const categories = getPlateSuitabilityHistory(item.plate);
  if (!categories.length) return `<span class="muted-text">Sin historial</span>`;
  return categories.map((category) => `<span class="badge suitability">${escapeHtml(category)}</span>`).join(" ");
}

function getPlateSuitabilityHistory(plate) {
  return state.suitabilityInsights?.plateAlerts?.[normalizePlateClient(plate)] || [];
}

function normalizePlateClient(value) {
  return String(value || "").trim().toUpperCase().replace(/[\s-]+/g, "");
}

function qualityBadge(status) {
  return `<span class="badge ${badgeClass(status)}">${escapeHtml(translateQualityStatus(status || "PENDING"))}</span>`;
}

function renderVehicleSupports(item) {
  const links = [];
  if (item.driverSelfieUrl) {
    links.push(renderSupportLink(item.driverSelfieUrl, "Ver selfie"));
    links.push(renderDownloadLink(item.driverSelfieUrl, `selfie-${item.plate || "vehiculo"}.png`, "Descargar selfie"));
  }
  if (item.driverSignatureUrl) {
    links.push(renderSupportLink(item.driverSignatureUrl, "Ver firma"));
    links.push(renderDownloadLink(item.driverSignatureUrl, `firma-${item.plate || "vehiculo"}.png`, "Descargar firma"));
  }
  const evidenceCount = getChecklistEvidenceCount(item.latestInspection?.checklist);
  if (evidenceCount > 0) {
    links.push(`<button class="support-link" type="button" data-evidence-preview-id="${item.id}">Ver evidencias (${evidenceCount})</button>`);
  }
  return links.length ? `<div class="support-links">${links.join("")}</div>` : `<span class="muted-text">Sin soportes visuales.</span>`;
}

function renderSupportLink(url, label) {
  if (!url) return `<span class="muted-text">Sin archivo</span>`;
  const mediaKey = registerPreviewMedia(url, label);
  return `<button class="support-link" type="button" data-media-preview-key="${mediaKey}">${escapeHtml(label)}</button>`;
}

function renderDownloadLink(url, fileName, label) {
  if (!url) return "";
  return `<a class="support-link download" href="${url}" download="${escapeHtml(fileName)}">${escapeHtml(label)}</a>`;
}

function getChecklistEvidenceCount(checklist) {
  if (!checklist || typeof checklist !== "object") return 0;
  return Object.values(checklist).reduce((total, item) => total + ((item?.evidences || []).filter(Boolean).length), 0);
}

function handleMediaPreviewClick(event) {
  const mediaButton = event.target.closest("[data-media-preview-key]");
  if (mediaButton) {
    const mediaEntry = state.mediaPreviewMap[mediaButton.dataset.mediaPreviewKey];
    openMediaPreview(mediaEntry?.url || "", mediaEntry?.label || "Vista previa");
    return;
  }
  const evidenceButton = event.target.closest("[data-evidence-preview-id]");
  if (evidenceButton) {
    const vehicle = findVehicleById(evidenceButton.dataset.evidencePreviewId);
    openChecklistEvidencePreview(vehicle);
  }
}

function openMediaPreview(url, label) {
  if (!url) {
    showToast("No hay archivo disponible para visualizar.");
    return;
  }
  const fileName = buildEvidenceFileName(label || "imagen");
  elements.mediaPreviewTitle.textContent = label || "Vista previa";
  elements.mediaPreviewBody.innerHTML = `
    <div class="media-preview-single">
      <img src="${url}" alt="${escapeHtml(label || "Vista previa")}" />
      <div class="media-preview-actions">
        <a class="support-link download" href="${url}" download="${escapeHtml(fileName)}">Descargar imagen</a>
      </div>
    </div>
  `;
  elements.mediaPreviewModal.classList.remove("hidden");
}

function openChecklistEvidencePreview(vehicle) {
  const checklist = vehicle?.latestInspection?.checklist || {};
  const evidences = [];
  Object.values(checklist).forEach((item) => {
    (item?.evidences || []).filter(Boolean).forEach((url, index) => {
      evidences.push({
        url,
        label: `${item.label || "Evidencia"} ${index + 1}`,
      });
    });
  });
  if (!evidences.length) {
    showToast("Ese vehículo no tiene evidencias fotográficas en el checklist.");
    return;
  }
  elements.mediaPreviewTitle.textContent = `Evidencias checklist ${vehicle?.plate || ""}`.trim();
  elements.mediaPreviewBody.innerHTML = `
    <div class="media-preview-grid">
      ${evidences.map((item) => `
        <figure class="media-preview-figure">
          <img src="${item.url}" alt="${escapeHtml(item.label)}" />
          <figcaption>${escapeHtml(item.label)}</figcaption>
          <div class="media-preview-actions">
            <a class="support-link download" href="${item.url}" download="${escapeHtml(buildEvidenceFileName(`${vehicle?.plate || "vehiculo"}-${item.label}`))}">Descargar evidencia</a>
          </div>
        </figure>
      `).join("")}
    </div>
  `;
  elements.mediaPreviewModal.classList.remove("hidden");
}

function closeMediaPreviewModal() {
  elements.mediaPreviewModal.classList.add("hidden");
  elements.mediaPreviewBody.innerHTML = "";
}

function registerPreviewMedia(url, label) {
  const key = `media-${Object.keys(state.mediaPreviewMap).length + 1}`;
  state.mediaPreviewMap[key] = { url, label };
  return key;
}

function buildEvidenceFileName(label) {
  return `${String(label || "evidencia")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "evidencia"}.png`;
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


