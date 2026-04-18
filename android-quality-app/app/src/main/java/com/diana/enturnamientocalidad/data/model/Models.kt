package com.diana.enturnamientocalidad.data.model

data class LoginRequest(
    val username: String,
    val password: String,
)

data class UserDto(
    val id: String,
    val username: String,
    val fullName: String,
    val role: String,
)

data class InspectionDto(
    val id: String,
    val vehicleId: String,
    val inspectorUserId: String,
    val inspectorName: String,
    val reviewedAt: String,
    val finalDecision: String,
    val suitability: List<String>,
    val observationsText: String,
    val checklist: Map<String, ChecklistItemDto>,
    val findingsSummary: String,
)

data class ChecklistItemDto(
    val label: String,
    val status: String,
    val evidences: List<String> = emptyList(),
)

data class VehicleDto(
    val id: String,
    val plate: String,
    val carrier: String,
    val carrierCode: String?,
    val driverName: String,
    val driverId: String,
    val driverPhone: String?,
    val emptyWeightKg: Double?,
    val city: String,
    val zone: String,
    val qualityStatus: String,
    val turnPosition: Int?,
    val latestInspection: InspectionDto?,
)

data class QualityStateDto(
    val pending: List<VehicleDto>,
    val rework: List<VehicleDto>,
    val approved: List<VehicleDto>,
    val rejected: List<VehicleDto>,
    val inspections: List<InspectionDto>,
    val dailyApprovedCount: Int = 0,
    val dailyRejectedCount: Int = 0,
)

data class AppStateDto(
    val user: UserDto,
    val quality: QualityStateDto,
    val sessionToken: String? = null,
)

data class ChecklistSubmissionItem(
    val label: String,
    val status: String,
    val evidences: List<String>,
)

data class InspectionRequest(
    val finalDecision: String,
    val observationsText: String,
    val suitability: List<String>,
    val checklist: Map<String, ChecklistSubmissionItem>,
)
