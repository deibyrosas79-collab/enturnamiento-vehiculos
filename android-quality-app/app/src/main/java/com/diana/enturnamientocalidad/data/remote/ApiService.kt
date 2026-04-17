package com.diana.enturnamientocalidad.data.remote

import com.diana.enturnamientocalidad.data.model.AppStateDto
import com.diana.enturnamientocalidad.data.model.InspectionRequest
import com.diana.enturnamientocalidad.data.model.LoginRequest
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface ApiService {
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): AppStateDto

    @GET("app-state")
    suspend fun getAppState(): AppStateDto

    @POST("quality/{vehicleId}/inspect")
    suspend fun inspectVehicle(
        @Path("vehicleId") vehicleId: String,
        @Body request: InspectionRequest,
    ): AppStateDto
}
