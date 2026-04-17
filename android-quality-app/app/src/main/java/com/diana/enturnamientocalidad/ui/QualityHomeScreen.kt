package com.diana.enturnamientocalidad.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Construction
import androidx.compose.material.icons.outlined.ExitToApp
import androidx.compose.material.icons.outlined.LocalShipping
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.ReportProblem
import androidx.compose.material.icons.outlined.Schedule
import androidx.compose.material.icons.outlined.VerifiedUser
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
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
            .padding(padding)
            .background(MaterialTheme.colorScheme.background),
        contentPadding = PaddingValues(horizontal = 18.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        item {
            Card(
                shape = RoundedCornerShape(28.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                ),
                elevation = CardDefaults.cardElevation(defaultElevation = 10.dp),
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 20.dp, vertical = 22.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.Top,
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Column(
                            modifier = Modifier.weight(1f),
                            verticalArrangement = Arrangement.spacedBy(6.dp),
                        ) {
                            Text(
                                text = "Panel Control Calidad",
                                style = MaterialTheme.typography.headlineMedium,
                                color = Color.White,
                                fontWeight = FontWeight.ExtraBold,
                            )
                            Text(
                                text = "Hola, ${uiState.userName}",
                                style = MaterialTheme.typography.titleMedium,
                                color = Color.White.copy(alpha = 0.92f),
                            )
                            Text(
                                text = "Revisa vehiculos en turno, registra evidencias y toma decisiones con sincronizacion en tiempo real.",
                                style = MaterialTheme.typography.bodyMedium,
                                color = Color.White.copy(alpha = 0.82f),
                            )
                        }
                        Surface(
                            shape = RoundedCornerShape(22.dp),
                            color = Color.White.copy(alpha = 0.14f),
                        ) {
                            Icon(
                                imageVector = Icons.Outlined.VerifiedUser,
                                contentDescription = null,
                                tint = Color.White,
                                modifier = Modifier
                                    .padding(16.dp)
                                    .size(28.dp),
                            )
                        }
                    }
                    Row(
                        modifier = Modifier.horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        StatTile("Pendientes", uiState.pending.size, Icons.Outlined.Schedule)
                        StatTile("Arreglos", uiState.rework.size, Icons.Outlined.Construction)
                        StatTile("Aptos", uiState.approved.size, Icons.Outlined.CheckCircle)
                        StatTile("Rechazados", uiState.rejected.size, Icons.Outlined.ReportProblem)
                    }
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Button(
                            onClick = onRefresh,
                            shape = RoundedCornerShape(18.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = Color.White,
                                contentColor = MaterialTheme.colorScheme.primary,
                            ),
                            enabled = !uiState.loading,
                        ) {
                            Icon(Icons.Outlined.Refresh, contentDescription = null)
                            Text(
                                text = "Actualizar",
                                modifier = Modifier.padding(start = 8.dp),
                            )
                        }
                        OutlinedButton(
                            onClick = onLogout,
                            shape = RoundedCornerShape(18.dp),
                            border = androidx.compose.foundation.BorderStroke(
                                1.dp,
                                Color.White.copy(alpha = 0.45f),
                            ),
                        ) {
                            Icon(
                                Icons.Outlined.ExitToApp,
                                contentDescription = null,
                                tint = Color.White,
                            )
                            Text(
                                text = "Salir",
                                modifier = Modifier.padding(start = 8.dp),
                                color = Color.White,
                            )
                        }
                    }
                }
            }
        }

        qualitySection(
            title = "Pendientes por revisar",
            subtitle = "Vehiculos recien enturnados que aun no tienen checklist completo.",
            vehicles = uiState.pending,
            emptyText = "No hay vehiculos pendientes.",
            actionLabel = "Revisar",
            onAction = onOpenInspection,
        )
        qualitySection(
            title = "Vehiculos en arreglos",
            subtitle = "Ya fueron inspeccionados y requieren ajustes antes de aprobarse.",
            vehicles = uiState.rework,
            emptyText = "No hay vehiculos en arreglos.",
            actionLabel = "Revisar de nuevo",
            onAction = onOpenInspection,
        )
        qualitySection(
            title = "Vehiculos aptos",
            subtitle = "Unidades aprobadas por calidad y listas para continuar el proceso.",
            vehicles = uiState.approved,
            emptyText = "Todavia no hay vehiculos aptos.",
            actionLabel = null,
            onAction = onOpenInspection,
        )
        qualitySection(
            title = "Vehiculos rechazados",
            subtitle = "Inspecciones no aptas o rechazadas en la revision.",
            vehicles = uiState.rejected,
            emptyText = "Todavia no hay vehiculos rechazados.",
            actionLabel = null,
            onAction = onOpenInspection,
        )
        item {
            Spacer(modifier = Modifier.height(10.dp))
        }
    }
}

private fun androidx.compose.foundation.lazy.LazyListScope.qualitySection(
    title: String,
    subtitle: String,
    vehicles: List<VehicleDto>,
    emptyText: String,
    actionLabel: String?,
    onAction: (VehicleDto) -> Unit,
) {
    item {
        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
            )
            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
    if (vehicles.isEmpty()) {
        item {
            Surface(
                shape = RoundedCornerShape(22.dp),
                color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.45f),
            ) {
                Row(
                    modifier = Modifier.padding(18.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Box(
                        modifier = Modifier
                            .size(44.dp)
                            .clip(CircleShape)
                            .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.10f)),
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(
                            imageVector = Icons.Outlined.LocalShipping,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary,
                        )
                    }
                    Text(
                        text = emptyText,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
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

@Composable
private fun StatTile(
    label: String,
    count: Int,
    icon: ImageVector,
) {
    Surface(
        modifier = Modifier.width(132.dp),
        shape = RoundedCornerShape(22.dp),
        color = Color.White.copy(alpha = 0.16f),
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Surface(
                shape = CircleShape,
                color = Color.White.copy(alpha = 0.14f),
            ) {
                Icon(
                    icon,
                    contentDescription = null,
                    tint = Color.White,
                    modifier = Modifier.padding(9.dp),
                )
            }
            Text(
                text = count.toString(),
                style = MaterialTheme.typography.headlineMedium,
                color = Color.White,
                fontWeight = FontWeight.ExtraBold,
            )
            Text(
                text = label,
                style = MaterialTheme.typography.bodySmall,
                color = Color.White.copy(alpha = 0.82f),
            )
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun VehicleCard(
    vehicle: VehicleDto,
    actionLabel: String?,
    onAction: (() -> Unit)?,
) {
    Card(
        shape = RoundedCornerShape(26.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 6.dp),
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(
                        text = vehicle.plate,
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.ExtraBold,
                    )
                    Text(
                        text = vehicle.driverName,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                StatusPill(vehicle.qualityStatus)
            }
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                MetaChip("Turno", vehicle.turnPosition?.toString() ?: "-")
                MetaChip("Transportadora", vehicle.carrier)
                MetaChip("Destino", "${vehicle.city} - ${vehicle.zone}")
                MetaChip("Celular", vehicle.driverPhone ?: "-")
                MetaChip("P. vacio", vehicle.emptyWeightKg?.toString() ?: "-")
            }
            Surface(
                shape = RoundedCornerShape(18.dp),
                color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.38f),
            ) {
                Text(
                    text = vehicle.latestInspection?.findingsSummary ?: "Sin hallazgos registrados todavia.",
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            if (actionLabel != null && onAction != null) {
                Button(
                    onClick = onAction,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    shape = RoundedCornerShape(18.dp),
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
    Surface(
        shape = RoundedCornerShape(999.dp),
        color = color.copy(alpha = 0.14f),
    ) {
        Text(
            text = translateQualityStatus(status),
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
            color = color,
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.Bold,
        )
    }
}

private fun translateQualityStatus(status: String): String = when (status) {
    "APPROVED" -> "Apto"
    "REWORK" -> "Requiere arreglos"
    "REJECTED" -> "Rechazado"
    "IN_REVIEW" -> "En revision"
    else -> "Pendiente"
}

@Composable
private fun MetaChip(label: String, value: String) {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = MaterialTheme.colorScheme.secondaryContainer.copy(alpha = 0.48f),
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 9.dp),
            verticalArrangement = Arrangement.spacedBy(2.dp),
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Bold,
            )
            Text(
                text = value,
                style = MaterialTheme.typography.bodySmall,
            )
        }
    }
}
