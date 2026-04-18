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
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.time.OffsetDateTime
import java.time.ZoneId

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
) : ViewModel() {
    private val _uiState = MutableStateFlow(QualityUiState())
    val uiState: StateFlow<QualityUiState> = _uiState.asStateFlow()

    init {
        if (!repository.getSavedToken().isNullOrBlank()) {
            refresh()
        }
    }

    fun login(username: String, password: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, errorMessage = null)
            runCatching { repository.login(username, password) }
                .onSuccess { applyState(it, repository::clearSession) }
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
                .onSuccess { applyState(it, repository::clearSession) }
                .onFailure {
                    repository.clearSession()
                    _uiState.value = QualityUiState(errorMessage = humanizeError(it))
                }
        }
    }

    fun logout() {
        repository.clearSession()
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
                applyState(it, repository::clearSession)
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

    private fun applyState(state: AppStateDto, onInvalidRole: () -> Unit) {
        if (state.user.role != "CALIDAD") {
            onInvalidRole()
            _uiState.value = QualityUiState(
                errorMessage = "Esta app movil es solo para usuarios con rol CALIDAD.",
            )
            return
        }
        val approvedToday = state.quality.approved.filter {
            it.latestInspection?.reviewedAt?.let(::isTodayInBogota) == true
        }
        val rejectedToday = state.quality.rejected.filter {
            it.latestInspection?.reviewedAt?.let(::isTodayInBogota) == true
        }
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
                .toLocalDate() == java.time.LocalDate.now(ZoneId.of("America/Bogota"))
        }.getOrDefault(false)
    }

    private fun humanizeError(error: Throwable): String {
        val message = error.message.orEmpty()
        return when {
            message.contains("Unable to resolve host", ignoreCase = true) ->
                "No fue posible conectar la app con el programa principal."
            message.contains("Failed to connect", ignoreCase = true) ->
                "No fue posible conectar la app con el programa principal."
            message.contains("timeout", ignoreCase = true) ->
                "El servidor tardo demasiado en responder. Intenta nuevamente."
            message.isBlank() ->
                "Ocurrio un problema al sincronizar la informacion de calidad."
            else -> message
        }
    }

    companion object {
        fun factory(context: Context): ViewModelProvider.Factory = object : ViewModelProvider.Factory {
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                val sessionStore = SessionStore(context.applicationContext)
                val logger = HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC }
                val okHttp = OkHttpClient.Builder()
                    .addInterceptor(AuthInterceptor { sessionStore.getToken() })
                    .addInterceptor(logger)
                    .build()
                val retrofit = Retrofit.Builder()
                    .baseUrl(BuildConfig.BASE_URL)
                    .addConverterFactory(GsonConverterFactory.create())
                    .client(okHttp)
                    .build()
                val api = retrofit.create(ApiService::class.java)
                return QualityViewModel(QualityRepository(api, sessionStore)) as T
            }
        }
    }
}
