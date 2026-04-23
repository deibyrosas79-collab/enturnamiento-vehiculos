package com.diana.enturnamientocalidad.ui

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.diana.enturnamientocalidad.BuildConfig
import com.diana.enturnamientocalidad.data.model.AppStateDto
import com.diana.enturnamientocalidad.data.model.ChecklistSubmissionItem
import com.diana.enturnamientocalidad.data.model.InspectionRequest
import com.diana.enturnamientocalidad.data.model.VehicleDto
import com.diana.enturnamientocalidad.data.remote.ApiService
import com.diana.enturnamientocalidad.data.remote.AuthInterceptor
import com.diana.enturnamientocalidad.data.repository.QualityRepository
import com.diana.enturnamientocalidad.data.session.SessionStore
import com.google.firebase.FirebaseApp
import com.google.firebase.messaging.FirebaseMessaging
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.ZoneId
import java.util.concurrent.TimeUnit

data class QualityUiState(
    val loading: Boolean = false,
    val loggedIn: Boolean = false,
    val userName: String = "",
    val role: String = "",
    val pending: List<VehicleDto> = emptyList(),
    val rework: List<VehicleDto> = emptyList(),
    val approved: List<VehicleDto> = emptyList(),
    val rejected: List<VehicleDto> = emptyList(),
    val dailyApprovedCount: Int = 0,
    val dailyRejectedCount: Int = 0,
    val errorMessage: String? = null,
)

class QualityViewModel(
    private val repository: QualityRepository,
    private val appContext: Context,
) : ViewModel() {
    private val _uiState = MutableStateFlow(QualityUiState())
    val uiState: StateFlow<QualityUiState> = _uiState.asStateFlow()
    private var lastPendingVehicleIds: Set<String> = emptySet()
    private var hasLoadedState = false

    init {
        repository.getSavedAppState()?.let { cached ->
            applyState(cached, repository::clearSession, allowNotifications = false)
        }
        syncFcmToken()
        if (!repository.getSavedToken().isNullOrBlank()) {
            refresh()
        }
    }

    fun login(username: String, password: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, errorMessage = null)
            runCatching { repository.login(username, password) }
                .onSuccess {
                    applyState(it, repository::clearSession, allowNotifications = false)
                    syncFcmToken()
                }
                .onFailure {
                    _uiState.value = _uiState.value.copy(
                        loading = false,
                        errorMessage = humanizeError(it),
                    )
                }
        }
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, errorMessage = null)
            runCatching { repository.getAppState() }
                .onSuccess {
                    applyState(it, repository::clearSession, allowNotifications = hasLoadedState)
                    syncFcmToken()
                }
                .onFailure {
                    _uiState.value = _uiState.value.copy(
                        loading = false,
                        errorMessage = humanizeError(it),
                    )
                }
        }
    }

    fun logout() {
        repository.clearSession()
        lastPendingVehicleIds = emptySet()
        hasLoadedState = false
        _uiState.value = QualityUiState()
    }

    fun saveInspection(
        vehicleId: String,
        finalDecision: String,
        observationsText: String,
        suitability: List<String>,
        checklist: Map<String, ChecklistSubmissionItem>,
        onComplete: (Boolean) -> Unit,
    ) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, errorMessage = null)
            runCatching {
                repository.saveInspection(
                    vehicleId,
                    InspectionRequest(
                        finalDecision = finalDecision,
                        observationsText = observationsText,
                        suitability = suitability,
                        checklist = checklist,
                    ),
                )
            }.onSuccess {
                applyState(it, repository::clearSession, allowNotifications = false)
                syncFcmToken()
                onComplete(true)
            }.onFailure {
                _uiState.value = _uiState.value.copy(
                    loading = false,
                    errorMessage = humanizeError(it),
                )
                onComplete(false)
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(errorMessage = null)
    }

    private fun syncFcmToken() {
        runCatching {
            val existingApps = FirebaseApp.getApps(appContext)
            if (existingApps.isEmpty()) {
                FirebaseApp.initializeApp(appContext) ?: return
            }
            FirebaseMessaging.getInstance().token
                .addOnSuccessListener { token ->
                    if (token.isNullOrBlank()) return@addOnSuccessListener
                    if (token == repository.getSavedFcmToken()) return@addOnSuccessListener
                    viewModelScope.launch {
                        runCatching { repository.registerFcmToken(token) }
                    }
                }
                .addOnFailureListener {
                    // Si Firebase no esta configurado todavia, mantenemos la app operativa sin romper la sesion.
                }
        }.onFailure {
            // Si falta google-services.json o Firebase no esta inicializado, la app sigue funcionando sin push.
        }
    }

    private fun applyState(state: AppStateDto, onInvalidRole: () -> Unit, allowNotifications: Boolean) {
        if (state.user.role != "CALIDAD") {
            onInvalidRole()
            _uiState.value = QualityUiState(
                errorMessage = "Esta app m\u00f3vil es solo para usuarios con rol CALIDAD.",
            )
            return
        }
        val approvedToday = state.quality.approved.filter {
            it.latestInspection?.reviewedAt?.let(::isTodayInBogota) == true
        }
        val rejectedToday = state.quality.rejected.filter {
            it.latestInspection?.reviewedAt?.let(::isTodayInBogota) == true
        }
        val newPendingIds = state.quality.pending.map { it.id }.toSet()
        if (allowNotifications) {
            val freshVehicles = state.quality.pending.filter { it.id !in lastPendingVehicleIds }
            freshVehicles.forEachIndexed { index, vehicle ->
                AppNotificationHelper.showLocalNotification(
                    context = appContext,
                    title = "Nuevo veh\u00edculo por revisar",
                    body = "Placa ${vehicle.plate} \u00b7 ${vehicle.driverName}",
                    notificationId = 4000 + index + vehicle.id.hashCode(),
                )
            }
        }
        lastPendingVehicleIds = newPendingIds
        hasLoadedState = true
        _uiState.value = QualityUiState(
            loading = false,
            loggedIn = true,
            userName = state.user.fullName,
            role = state.user.role,
            pending = state.quality.pending,
            rework = state.quality.rework,
            approved = approvedToday,
            rejected = rejectedToday,
            dailyApprovedCount = state.quality.dailyApprovedCount,
            dailyRejectedCount = state.quality.dailyRejectedCount,
        )
    }

    private fun isTodayInBogota(value: String): Boolean {
        return runCatching {
            OffsetDateTime.parse(value)
                .atZoneSameInstant(ZoneId.of("America/Bogota"))
                .toLocalDate() == LocalDate.now(ZoneId.of("America/Bogota"))
        }.getOrDefault(false)
    }

    private fun humanizeError(error: Throwable): String {
        val message = error.message.orEmpty()
        return when {
            message.contains("401", ignoreCase = true) ||
                message.contains("403", ignoreCase = true) ||
                message.contains("usuario o clave", ignoreCase = true) ||
                message.contains("credenciales", ignoreCase = true) ->
                "Usuario o contrase\u00f1a incorrectos. Verifica la informaci\u00f3n e intenta nuevamente."
            message.contains("Unable to resolve host", ignoreCase = true) ->
                "No fue posible conectar la app con el programa principal."
            message.contains("Failed to connect", ignoreCase = true) ->
                "No fue posible conectar la app con el programa principal."
            message.contains("timeout", ignoreCase = true) ->
                "El servidor tard\u00f3 demasiado en responder. Intenta nuevamente."
            message.isBlank() ->
                "Ocurri\u00f3 un problema al sincronizar la informaci\u00f3n de calidad."
            else -> message
        }
    }

    companion object {
        fun factory(context: Context): ViewModelProvider.Factory = object : ViewModelProvider.Factory {
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                val sessionStore = SessionStore(context.applicationContext)
                val logger = HttpLoggingInterceptor().apply {
                    level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BASIC else HttpLoggingInterceptor.Level.NONE
                }
                val okHttp = OkHttpClient.Builder()
                    .addInterceptor(AuthInterceptor { sessionStore.getToken() })
                    .addInterceptor(logger)
                    .connectTimeout(10, TimeUnit.SECONDS)
                    .readTimeout(20, TimeUnit.SECONDS)
                    .writeTimeout(20, TimeUnit.SECONDS)
                    .retryOnConnectionFailure(true)
                    .build()
                val retrofit = Retrofit.Builder()
                    .baseUrl(BuildConfig.BASE_URL)
                    .addConverterFactory(GsonConverterFactory.create())
                    .client(okHttp)
                    .build()
                val api = retrofit.create(ApiService::class.java)
                return QualityViewModel(
                    repository = QualityRepository(api, sessionStore),
                    appContext = context.applicationContext,
                ) as T
            }
        }
    }
}
