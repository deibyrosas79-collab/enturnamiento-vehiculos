package com.diana.enturnamientocalidad.data.repository

import com.diana.enturnamientocalidad.data.model.AppStateDto
import com.diana.enturnamientocalidad.data.model.InspectionRequest
import com.diana.enturnamientocalidad.data.model.LoginRequest
import com.diana.enturnamientocalidad.data.remote.ApiService
import com.diana.enturnamientocalidad.data.session.SessionStore

class QualityRepository(
    private val api: ApiService,
    private val sessionStore: SessionStore,
) {
    suspend fun login(username: String, password: String): AppStateDto {
        val response = api.login(LoginRequest(username = username, password = password))
        response.sessionToken?.let(sessionStore::saveToken)
        return response
    }

    suspend fun getAppState(): AppStateDto = api.getAppState()

    suspend fun saveInspection(vehicleId: String, request: InspectionRequest): AppStateDto =
        api.inspectVehicle(vehicleId, request)

    fun getSavedToken(): String? = sessionStore.getToken()

    fun clearSession() = sessionStore.clear()
}
