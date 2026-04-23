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
        sessionStore.saveAppState(response)
        return response
    }

    suspend fun getAppState(): AppStateDto =
        api.getAppState().also(sessionStore::saveAppState)

    suspend fun saveInspection(vehicleId: String, request: InspectionRequest): AppStateDto =
        api.inspectVehicle(vehicleId, request).also(sessionStore::saveAppState)

    fun getSavedToken(): String? = sessionStore.getToken()

    fun getSavedAppState(): AppStateDto? = sessionStore.getSavedAppState()

    suspend fun registerFcmToken(token: String) {
        api.registerFcmToken(mapOf("token" to token))
        sessionStore.saveFcmToken(token)
    }

    fun getSavedFcmToken(): String? = sessionStore.getSavedFcmToken()

    fun clearSession() = sessionStore.clear()
}
