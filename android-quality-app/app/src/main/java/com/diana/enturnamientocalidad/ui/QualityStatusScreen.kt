package com.diana.enturnamientocalidad.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Construction
import androidx.compose.material.icons.outlined.LocalShipping
import androidx.compose.material.icons.outlined.ReportProblem
import androidx.compose.material.icons.outlined.Schedule
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.diana.enturnamientocalidad.data.model.VehicleDto

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun QualityStatusScreen(
    padding: PaddingValues,
    title: String,
    subtitle: String,
    vehicles: List<VehicleDto>,
    allowReview: Boolean,
    onBack: () -> Unit,
    onOpenInspection: (VehicleDto) -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(padding)
            .background(MaterialTheme.colorScheme.background),
    ) {
        TopAppBar(
            title = { Text(title) },
            navigationIcon = {
                IconButton(onClick = onBack) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Outlined.ArrowBack,
                        contentDescription = "Volver",
                    )
                }
            },
        )
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            item {
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
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
                                    .clip(CircleShape)
                                    .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.10f))
                                    .padding(10.dp),
                                contentAlignment = Alignment.Center,
                            ) {
                                Icon(Icons.Outlined.LocalShipping, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                            }
                            Text("No hay vehículos en esta vista.")
                        }
                    }
                }
            } else {
                items(vehicles, key = { it.id }) { vehicle ->
                    VehicleStatusCard(
                        vehicle = vehicle,
                        allowReview = allowReview,
                        onOpenInspection = { onOpenInspection(vehicle) },
                    )
                }
            }
        }
    }
}

@Composable
private fun VehicleStatusCard(
    vehicle: VehicleDto,
    allowReview: Boolean,
    onOpenInspection: () -> Unit,
) {
    Card(
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 6.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(18.dp),
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
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                MetaChip(Modifier.weight(1f), "Turno", vehicle.turnPosition?.toString() ?: "-")
                MetaChip(Modifier.weight(1f), "Transportadora", vehicle.carrier)
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                MetaChip(Modifier.weight(1f), "Destino", "${vehicle.city} - ${vehicle.zone}")
                MetaChip(Modifier.weight(1f), "Celular", vehicle.driverPhone ?: "-")
            }
            Surface(
                shape = RoundedCornerShape(18.dp),
                color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.38f),
            ) {
                Text(
                    text = vehicle.latestInspection?.findingsSummary ?: "Sin hallazgos registrados todavía.",
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            if (allowReview) {
                Button(
                    onClick = onOpenInspection,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(18.dp),
                ) {
                    Text("Abrir revisión")
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
  val icon: ImageVector = when (status) {
      "APPROVED" -> Icons.Outlined.CheckCircle
      "REWORK" -> Icons.Outlined.Construction
      "REJECTED" -> Icons.Outlined.ReportProblem
      else -> Icons.Outlined.Schedule
  }
  Surface(
      shape = RoundedCornerShape(999.dp),
      color = color.copy(alpha = 0.14f),
  ) {
      Row(
          modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
          horizontalArrangement = Arrangement.spacedBy(6.dp),
          verticalAlignment = Alignment.CenterVertically,
      ) {
          Icon(icon, contentDescription = null, tint = color)
          Text(
              text = translateQualityStatus(status),
              color = color,
              style = MaterialTheme.typography.labelLarge,
              fontWeight = FontWeight.Bold,
          )
      }
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
private fun MetaChip(
    modifier: Modifier = Modifier,
    label: String,
    value: String,
) {
    Surface(
        modifier = modifier,
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
