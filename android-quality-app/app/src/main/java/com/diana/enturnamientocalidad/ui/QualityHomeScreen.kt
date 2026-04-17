package com.diana.enturnamientocalidad.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Construction
import androidx.compose.material.icons.outlined.ExitToApp
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.ReportProblem
import androidx.compose.material.icons.outlined.Schedule
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.diana.enturnamientocalidad.data.model.VehicleDto

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun QualityHomeScreen(
    padding: PaddingValues,
    uiState: QualityUiState,
    onRefresh: () -> Unit,
    onLogout: () -> Unit,
    onOpenInspection: (VehicleDto) -> Unit,
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(padding),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            Card {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Text(
                        text = "Hola, ${uiState.userName}",
                        style = MaterialTheme.typography.headlineSmall,
                    )
                    Text(
                        text = "Panel movil del equipo de calidad. Aqui ves pendientes, aptos, arreglos y rechazos.",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    FlowRow(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        SummaryChip("Pendientes", uiState.pending.size, Icons.Outlined.Schedule)
                        SummaryChip("Arreglos", uiState.rework.size, Icons.Outlined.Construction)
                        SummaryChip("Aptos", uiState.approved.size, Icons.Outlined.CheckCircle)
                        SummaryChip("Rechazados", uiState.rejected.size, Icons.Outlined.ReportProblem)
                    }
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Button(
                            onClick = onRefresh,
                            enabled = !uiState.loading,
                        ) {
                            Icon(Icons.Outlined.Refresh, contentDescription = null)
                            Text(
                                text = "Actualizar",
                                modifier = Modifier.padding(start = 8.dp),
                            )
                        }
                        OutlinedButton(onClick = onLogout) {
                            Icon(Icons.Outlined.ExitToApp, contentDescription = null)
                            Text(
                                text = "Salir",
                                modifier = Modifier.padding(start = 8.dp),
                            )
                        }
                    }
                }
            }
        }

        qualitySection(
            title = "Pendientes por revisar",
            vehicles = uiState.pending,
            emptyText = "No hay vehiculos pendientes.",
            actionLabel = "Revisar",
            onAction = onOpenInspection,
        )
        qualitySection(
            title = "Vehiculos en arreglos",
            vehicles = uiState.rework,
            emptyText = "No hay vehiculos en arreglos.",
            actionLabel = "Revisar de nuevo",
            onAction = onOpenInspection,
        )
        qualitySection(
            title = "Vehiculos aptos",
            vehicles = uiState.approved,
            emptyText = "Todavia no hay vehiculos aptos.",
            actionLabel = null,
            onAction = onOpenInspection,
        )
        qualitySection(
            title = "Vehiculos rechazados",
            vehicles = uiState.rejected,
            emptyText = "Todavia no hay vehiculos rechazados.",
            actionLabel = null,
            onAction = onOpenInspection,
        )
    }
}

private fun androidx.compose.foundation.lazy.LazyListScope.qualitySection(
    title: String,
    vehicles: List<VehicleDto>,
    emptyText: String,
    actionLabel: String?,
    onAction: (VehicleDto) -> Unit,
) {
    item {
        Text(
            text = title,
            style = MaterialTheme.typography.titleLarge,
        )
    }
    if (vehicles.isEmpty()) {
        item {
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant,
                ),
            ) {
                Text(
                    text = emptyText,
                    modifier = Modifier.padding(16.dp),
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    } else {
        items(vehicles, key = { it.id }) { vehicle ->
            VehicleCard(
                vehicle = vehicle,
                actionLabel = actionLabel,
                onAction = if (actionLabel != null) {
                    { onAction(vehicle) }
                } else {
                    null
                },
            )
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun SummaryChip(
    label: String,
    count: Int,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
) {
    AssistChip(
        onClick = {},
        label = { Text("$label: $count") },
        leadingIcon = { Icon(icon, contentDescription = null) },
    )
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun VehicleCard(
    vehicle: VehicleDto,
    actionLabel: String?,
    onAction: (() -> Unit)?,
) {
    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = vehicle.plate,
                    style = MaterialTheme.typography.titleMedium,
                )
                StatusPill(vehicle.qualityStatus)
            }
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                MetaChip("Turno", vehicle.turnPosition?.toString() ?: "-")
                MetaChip("Transportadora", vehicle.carrier)
                MetaChip("Destino", "${vehicle.city} - ${vehicle.zone}")
                MetaChip("Conductor", vehicle.driverName)
                MetaChip("Celular", vehicle.driverPhone ?: "-")
                MetaChip("P. vacio", vehicle.emptyWeightKg?.toString() ?: "-")
            }
            Text(
                text = vehicle.latestInspection?.findingsSummary ?: "Sin hallazgos registrados todavia.",
                style = MaterialTheme.typography.bodyMedium,
            )
            if (actionLabel != null && onAction != null) {
                Button(
                    onClick = onAction,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(actionLabel)
                }
            }
        }
    }
}

@Composable
private fun StatusPill(status: String) {
    val color = when (status) {
        "APPROVED" -> Color(0xFF2E7D32)
        "REWORK" -> Color(0xFFF9A825)
        "REJECTED" -> Color(0xFFC62828)
        else -> Color(0xFF1565C0)
    }
    Card(
        colors = CardDefaults.cardColors(
            containerColor = color.copy(alpha = 0.14f),
        ),
    ) {
        Text(
            text = status,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
            color = color,
            style = MaterialTheme.typography.labelLarge,
        )
    }
}

@Composable
private fun MetaChip(label: String, value: String) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
        ),
    ) {
        Text(
            text = "$label: $value",
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
            style = MaterialTheme.typography.bodySmall,
        )
    }
}
