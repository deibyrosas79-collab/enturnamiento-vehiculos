package com.diana.enturnamientocalidad.ui

import android.content.Context
import android.net.Uri
import android.util.Base64
import android.webkit.MimeTypeMap
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.Arrangement
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
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.Checklist
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.diana.enturnamientocalidad.data.model.ChecklistSubmissionItem
import com.diana.enturnamientocalidad.data.model.VehicleDto
import androidx.compose.runtime.snapshots.SnapshotStateList
import java.io.IOException

private data class ChecklistDefinition(
    val key: String,
    val label: String,
    val requiresEvidence: Boolean,
)

private val inspectionChecklist = listOf(
    ChecklistDefinition("foodLegend", "Leyenda visible Transporte de alimentos", true),
    ChecklistDefinition("cleanliness", "Libre de suciedad", true),
    ChecklistDefinition("strangeSmells", "Libre de olores extranos", false),
    ChecklistDefinition("stains", "Libre de manchas", true),
    ChecklistDefinition("damage", "Libre de orificios y averias", true),
    ChecklistDefinition("humidity", "Libre de humedad", true),
    ChecklistDefinition("infestation", "Libre de infestacion", true),
    ChecklistDefinition("bulkWallsFloor", "Paredes y piso limpios y en buen estado", true),
    ChecklistDefinition("containerHoles", "Trompos limpios y con proteccion", true),
    ChecklistDefinition("fumigationIn", "Fumigacion ingreso", true),
    ChecklistDefinition("fumigationOut", "Fumigacion salida", true),
)

private val suitabilityOptions = listOf(
    "Cadenas",
    "Mayoristas",
    "Bodegas y operadores",
    "Subproductos",
)

@OptIn(ExperimentalLayoutApi::class, ExperimentalMaterial3Api::class)
@Composable
fun InspectionScreen(
    padding: PaddingValues,
    vehicle: VehicleDto?,
    loading: Boolean,
    onBack: () -> Unit,
    onSave: (String, String, List<String>, Map<String, ChecklistSubmissionItem>) -> Unit,
) {
    val context = LocalContext.current
    val inspection = vehicle?.latestInspection
    val evidenceUris = remember(vehicle?.id) {
        mutableStateMapOf<String, SnapshotStateList<Uri>>().apply {
            inspectionChecklist.forEach { definition ->
                put(definition.key, mutableStateListOf())
            }
        }
    }
    val statusMap = remember(vehicle?.id) {
        mutableStateMapOf<String, String>().apply {
            inspectionChecklist.forEach { definition ->
                put(
                    definition.key,
                    inspection?.checklist?.get(definition.key)?.status ?: "CUMPLE",
                )
            }
        }
    }
    val selectedSuitability = remember(vehicle?.id) {
        mutableStateListOf<String>().apply {
            addAll(inspection?.suitability.orEmpty())
        }
    }
    var observations by rememberSaveable(vehicle?.id) {
        mutableStateOf(inspection?.observationsText.orEmpty())
    }
    var finalDecision by rememberSaveable(vehicle?.id) {
        mutableStateOf(
            inspection?.finalDecision ?: if (vehicle?.qualityStatus == "REWORK") "REWORK" else "APPROVED",
        )
    }
    var pickerTarget by remember { mutableStateOf<String?>(null) }
    val picker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.PickMultipleVisualMedia(maxItems = 5),
    ) { uris ->
        val key = pickerTarget ?: return@rememberLauncherForActivityResult
        evidenceUris[key]?.apply {
            clear()
            addAll(uris)
        }
        pickerTarget = null
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(padding),
    ) {
        TopAppBar(
            title = { Text(vehicle?.plate ?: "Inspeccion") },
            navigationIcon = {
                IconButton(onClick = onBack) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Outlined.ArrowBack,
                        contentDescription = "Volver",
                    )
                }
            },
        )
        if (vehicle == null) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(20.dp),
                verticalArrangement = Arrangement.Center,
            ) {
                Text("No se encontro el vehiculo para revisar.")
                Button(
                    onClick = onBack,
                    modifier = Modifier.padding(top = 12.dp),
                ) {
                    Text("Volver")
                }
            }
            return
        }

        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            item {
                Card(
                    shape = androidx.compose.foundation.shape.RoundedCornerShape(26.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                    ),
                ) {
                    Column(
                        modifier = Modifier.padding(18.dp),
                        verticalArrangement = Arrangement.spacedBy(14.dp),
                    ) {
                        Row(
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
                        ) {
                            Surface(
                                shape = androidx.compose.foundation.shape.RoundedCornerShape(18.dp),
                                color = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.14f),
                            ) {
                                Icon(
                                    imageVector = Icons.Outlined.Checklist,
                                    contentDescription = null,
                                    tint = androidx.compose.ui.graphics.Color.White,
                                    modifier = Modifier.padding(12.dp),
                                )
                            }
                            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Text(
                                    text = "Checklist de calidad",
                                    style = MaterialTheme.typography.headlineSmall,
                                    color = androidx.compose.ui.graphics.Color.White,
                                    fontWeight = FontWeight.ExtraBold,
                                )
                                Text(
                                    text = "Vehiculo ${vehicle.plate} listo para inspeccion.",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.85f),
                                )
                            }
                        }
                        FlowRow(
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            InspectionMetaChip("Conductor", vehicle.driverName)
                            InspectionMetaChip("Transportadora", vehicle.carrier)
                            InspectionMetaChip("Destino", "${vehicle.city} - ${vehicle.zone}")
                            InspectionMetaChip("Turno", vehicle.turnPosition?.toString() ?: "-")
                        }
                    }
                }
            }

            items(inspectionChecklist, key = { it.key }) { definition ->
                val existingEvidenceCount = inspection?.checklist
                    ?.get(definition.key)
                    ?.evidences
                    ?.size
                    ?: 0
                ChecklistCard(
                    definition = definition,
                    status = statusMap[definition.key] ?: "CUMPLE",
                    existingEvidenceCount = existingEvidenceCount,
                    selectedEvidenceCount = evidenceUris[definition.key]?.size ?: 0,
                    onStatusChange = { statusMap[definition.key] = it },
                    onPickEvidence = {
                        pickerTarget = definition.key
                        picker.launch(
                            PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly),
                        )
                    },
                )
            }

            item {
                Card(
                    shape = androidx.compose.foundation.shape.RoundedCornerShape(24.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surface,
                    ),
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(16.dp),
                    ) {
                        Text(
                            text = "Uso permitido del vehiculo",
                            style = MaterialTheme.typography.titleMedium,
                        )
                        FlowRow(
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            suitabilityOptions.forEach { option ->
                                FilterChip(
                                    selected = option in selectedSuitability,
                                    onClick = {
                                        if (option in selectedSuitability) {
                                            selectedSuitability.remove(option)
                                        } else {
                                            selectedSuitability.add(option)
                                        }
                                    },
                                    label = { Text(option) },
                                )
                            }
                        }
                        OutlinedTextField(
                            value = observations,
                            onValueChange = { observations = it },
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text("Observaciones 2") },
                            minLines = 3,
                        )
                        Column(
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            Text(
                                text = "Decision final",
                                style = MaterialTheme.typography.titleMedium,
                            )
                            FlowRow(
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                                verticalArrangement = Arrangement.spacedBy(8.dp),
                            ) {
                                listOf(
                                    "APPROVED" to "Apto",
                                    "REWORK" to "Requiere arreglos",
                                    "REJECTED" to "No apto",
                                ).forEach { (value, label) ->
                                    FilterChip(
                                        selected = finalDecision == value,
                                        onClick = { finalDecision = value },
                                        label = { Text(label) },
                                    )
                                }
                            }
                        }
                    }
                }
            }

            item {
                Button(
                    onClick = {
                        val checklist = inspectionChecklist.associate { definition ->
                            val evidences = evidenceUris[definition.key]
                                ?.map { uri -> uriToDataUrl(context, uri) }
                                .orEmpty()
                            definition.key to ChecklistSubmissionItem(
                                label = definition.label,
                                status = statusMap[definition.key] ?: "CUMPLE",
                                evidences = evidences,
                            )
                        }
                        onSave(
                            finalDecision,
                            observations.trim(),
                            selectedSuitability.toList(),
                            checklist,
                        )
                    },
                    enabled = !loading,
                    modifier = Modifier.fillMaxWidth(),
                    shape = androidx.compose.foundation.shape.RoundedCornerShape(18.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                    ),
                ) {
                    Text(if (loading) "Guardando..." else "Guardar inspeccion")
                }
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun ChecklistCard(
    definition: ChecklistDefinition,
    status: String,
    existingEvidenceCount: Int,
    selectedEvidenceCount: Int,
    onStatusChange: (String) -> Unit,
    onPickEvidence: () -> Unit,
) {
    Card(
        shape = androidx.compose.foundation.shape.RoundedCornerShape(22.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                text = definition.label,
                style = MaterialTheme.typography.titleMedium,
            )
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                FilterChip(
                    selected = status == "CUMPLE",
                    onClick = { onStatusChange("CUMPLE") },
                    label = { Text("Cumple") },
                )
                FilterChip(
                    selected = status == "NO_CUMPLE",
                    onClick = { onStatusChange("NO_CUMPLE") },
                    label = { Text("No cumple") },
                )
            }
            if (definition.requiresEvidence) {
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant,
                    ),
                ) {
                    Column(
                        modifier = Modifier.padding(12.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Text(
                            text = "Evidencias previas: $existingEvidenceCount | Nuevas seleccionadas: $selectedEvidenceCount",
                            style = MaterialTheme.typography.bodySmall,
                        )
                        Button(onClick = onPickEvidence) {
                            Text("Adjuntar fotos")
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun InspectionMetaChip(label: String, value: String) {
    Surface(
        shape = androidx.compose.foundation.shape.RoundedCornerShape(16.dp),
        color = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.14f),
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 9.dp),
            verticalArrangement = Arrangement.spacedBy(2.dp),
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.labelSmall,
                color = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.72f),
            )
            Text(
                text = value,
                style = MaterialTheme.typography.bodySmall,
                color = androidx.compose.ui.graphics.Color.White,
                fontWeight = FontWeight.Bold,
            )
        }
    }
}

private fun uriToDataUrl(context: Context, uri: Uri): String {
    val resolver = context.contentResolver
    val mimeType = resolver.getType(uri) ?: "image/jpeg"
    val bytes = try {
        resolver.openInputStream(uri)?.use { it.readBytes() }
    } catch (error: IOException) {
        null
    } ?: error("No se pudo leer una imagen seleccionada.")
    val encoded = Base64.encodeToString(bytes, Base64.NO_WRAP)
    val normalizedMime = if (mimeType.startsWith("image/")) {
        mimeType
    } else {
        val extension = MimeTypeMap.getFileExtensionFromUrl(uri.toString())
        "image/${extension.ifBlank { "jpeg" }}"
    }
    return "data:$normalizedMime;base64,$encoded"
}
