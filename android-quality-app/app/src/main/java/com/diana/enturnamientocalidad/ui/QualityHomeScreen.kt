package com.diana.enturnamientocalidad.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Construction
import androidx.compose.material.icons.outlined.ExitToApp
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

@Composable
fun QualityHomeScreen(
    padding: PaddingValues,
    uiState: QualityUiState,
    onRefresh: () -> Unit,
    onLogout: () -> Unit,
    onOpenPending: () -> Unit,
    onOpenRework: () -> Unit,
    onOpenApproved: () -> Unit,
    onOpenRejected: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(padding)
            .background(MaterialTheme.colorScheme.background)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 18.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        Card(
            shape = RoundedCornerShape(28.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primary),
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
                            text = "Consulta cada estado por pantalla separada y sincroniza el checklist con el sistema principal.",
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
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
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
                        Text(text = "Actualizar", modifier = Modifier.padding(start = 8.dp))
                    }
                    OutlinedButton(
                        onClick = onLogout,
                        shape = RoundedCornerShape(18.dp),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.45f)),
                    ) {
                        Icon(Icons.Outlined.ExitToApp, contentDescription = null, tint = Color.White)
                        Text(text = "Salir", modifier = Modifier.padding(start = 8.dp), color = Color.White)
                    }
                }
            }
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            StatTile(
                modifier = Modifier.weight(1f),
                label = "Pendientes",
                count = uiState.pending.size,
                icon = Icons.Outlined.Schedule,
                tint = Color(0xFF1565C0),
            )
            StatTile(
                modifier = Modifier.weight(1f),
                label = "Arreglos",
                count = uiState.rework.size,
                icon = Icons.Outlined.Construction,
                tint = Color(0xFFF9A825),
            )
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            StatTile(
                modifier = Modifier.weight(1f),
                label = "Aptos del dia",
                count = uiState.dailyApprovedCount,
                icon = Icons.Outlined.CheckCircle,
                tint = Color(0xFF2E7D32),
            )
            StatTile(
                modifier = Modifier.weight(1f),
                label = "Rechazados del dia",
                count = uiState.dailyRejectedCount,
                icon = Icons.Outlined.ReportProblem,
                tint = Color(0xFFC62828),
            )
        }

        StatusActionCard(
            title = "Pendientes por revisar",
            subtitle = "Vehiculos recien enturnados que aun no tienen checklist completo.",
            countLabel = "${uiState.pending.size} pendientes",
            buttonLabel = "Abrir pendientes",
            icon = Icons.Outlined.Schedule,
            tint = Color(0xFF1565C0),
            onClick = onOpenPending,
        )
        StatusActionCard(
            title = "Vehiculos en arreglos",
            subtitle = "Unidades revisadas que requieren ajustes antes de aprobarse.",
            countLabel = "${uiState.rework.size} en arreglos",
            buttonLabel = "Abrir arreglos",
            icon = Icons.Outlined.Construction,
            tint = Color(0xFFF9A825),
            onClick = onOpenRework,
        )
        StatusActionCard(
            title = "Vehiculos aptos",
            subtitle = "Consulta los vehiculos aprobados hoy y su informacion consolidada.",
            countLabel = "${uiState.dailyApprovedCount} aptos hoy",
            buttonLabel = "Abrir aptos",
            icon = Icons.Outlined.CheckCircle,
            tint = Color(0xFF2E7D32),
            onClick = onOpenApproved,
        )
        StatusActionCard(
            title = "Vehiculos rechazados",
            subtitle = "Revisa los rechazados del dia y las observaciones registradas.",
            countLabel = "${uiState.dailyRejectedCount} rechazados hoy",
            buttonLabel = "Abrir rechazados",
            icon = Icons.Outlined.ReportProblem,
            tint = Color(0xFFC62828),
            onClick = onOpenRejected,
        )
    }
}

@Composable
private fun StatTile(
    modifier: Modifier = Modifier,
    label: String,
    count: Int,
    icon: ImageVector,
    tint: Color,
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(24.dp),
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 6.dp,
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Box(
                modifier = Modifier
                    .size(44.dp)
                    .clip(CircleShape)
                    .background(tint.copy(alpha = 0.12f)),
                contentAlignment = Alignment.Center,
            ) {
                Icon(icon, contentDescription = null, tint = tint)
            }
            Text(
                text = count.toString(),
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.ExtraBold,
            )
            Text(
                text = label,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun StatusActionCard(
    title: String,
    subtitle: String,
    countLabel: String,
    buttonLabel: String,
    icon: ImageVector,
    tint: Color,
    onClick: () -> Unit,
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
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Box(
                    modifier = Modifier
                        .size(52.dp)
                        .clip(CircleShape)
                        .background(tint.copy(alpha = 0.12f)),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(icon, contentDescription = null, tint = tint)
                }
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(text = title, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    Text(text = subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            Surface(
                shape = RoundedCornerShape(16.dp),
                color = tint.copy(alpha = 0.10f),
            ) {
                Text(
                    text = countLabel,
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
                    color = tint,
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.Bold,
                )
            }
            Button(
                onClick = onClick,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = RoundedCornerShape(18.dp),
                colors = ButtonDefaults.buttonColors(containerColor = tint),
            ) {
                Text(buttonLabel)
            }
        }
    }
}
