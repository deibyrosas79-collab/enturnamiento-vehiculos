package com.diana.enturnamientocalidad.ui

import android.content.ContentValues
import android.content.Context
import android.net.Uri
import android.os.Build
import android.provider.MediaStore
import android.util.Base64
import android.webkit.MimeTypeMap
import androidx.activity.compose.rememberLauncherForActivityResult
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
    val options: List<Pair<String, String>>,
    val requiresPoison: Boolean = false,
)

private val inspectionChecklist = listOf(
    ChecklistDefinition("foodLegend", "Cuenta con leyenda visible \"Transporte de alimentos\"", true, listOf("CUMPLE" to "Cumple", "NO_CUMPLE" to "No cumple", "NO_APLICA" to "No aplica")),
    ChecklistDefinition("cleanliness", "Libre de suciedad", true, listOf("CUMPLE" to "Cumple", "NO_CUMPLE" to "No cumple", "NO_APLICA" to "No aplica")),
    ChecklistDefinition("strangeSmells", "Libre de olores extraños", false, listOf("CUMPLE" to "Cumple", "NO_CUMPLE" to "No cumple", "NO_APLICA" to "No aplica")),
    ChecklistDefinition("stains", "Libre de manchas", true, listOf("CUMPLE" to "Cumple", "NO_CUMPLE" to "No cumple", "NO_APLICA" to "No aplica")),
    ChecklistDefinition("damage", "Libre de orificios y averías", true, listOf("CUMPLE" to "Cumple", "NO_CUMPLE" to "No cumple", "NO_APLICA" to "No aplica")),
    ChecklistDefinition("humidity", "Libre de humedad", true, listOf("CUMPLE" to "Cumple", "NO_CUMPLE" to "No cumple", "NO_APLICA" to "No aplica")),
    ChecklistDefinition("infestation", "Libre de infestación (plagas, roedores y/o contaminación biológica)", true, listOf("CUMPLE" to "Cumple", "NO_CUMPLE" to "No cumple", "NO_APLICA" to "No aplica")),
    ChecklistDefinition("bulkWallsFloor", "Granel en paredes y piso limpio y en buen estado", true, listOf("CUMPLE" to "Cumple", "NO_CUMPLE" to "No cumple", "NO_APLICA" to "No aplica")),
    ChecklistDefinition("containerHoles", "Trompos (agujeros de ensamble del contenedor) limpios y con la debida protección de parche", true, listOf("CUMPLE" to "Cumple", "NO_CUMPLE" to "No cumple", "NO_APLICA" to "No aplica")),
    ChecklistDefinition("woodenStakesPestFree", "Estacas de madera del vehículo libres de plagas (paredes y pisos)", true, listOf("CUMPLE" to "Cumple", "NO_CUMPLE" to "No cumple", "NO_APLICA" to "No aplica")),
    ChecklistDefinition("fumigationIn", "Fumigación ingreso", true, listOf("SI" to "Sí", "NO" to "No"), requiresPoison = true),
    ChecklistDefinition("fumigationOut", "Fumigación salida", true, listOf("SI" to "Sí", "NO" to "No"), requiresPoison = true),
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
                    inspection?.checklist?.get(definition.key)?.status.orEmpty(),
                )
            }
        }
    }
    val poisonMap = remember(vehicle?.id) {
        mutableStateMapOf<String, String>().apply {
            inspectionChecklist.forEach { definition ->
                put(
                    definition.key,
                    inspection?.checklist?.get(definition.key)?.poison.orEmpty(),
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
    var localValidationError by rememberSaveable(vehicle?.id) {
        mutableStateOf<String?>(null)
    }
    var finalDecision by rememberSaveable(vehicle?.id) {
        mutableStateOf(
            inspection?.finalDecision ?: if (vehicle?.qualityStatus == "REWORK") "REWORK" else "APPROVED",
        )
    }
    var captureTarget by remember { mutableStateOf<String?>(null) }
    var pendingCaptureUri by remember { mutableStateOf<Uri?>(null) }
    val cameraLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicture(),
    ) { success ->
        val target = captureTarget
        val uri = pendingCaptureUri
        if (success && target != null && uri != null) {
            evidenceUris[target]?.add(uri)
        } else if (uri != null) {
            context.contentResolver.delete(uri, null, null)
        }
        captureTarget = null
        pendingCaptureUri = null
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
                    status = statusMap[definition.key].orEmpty(),
                    poison = poisonMap[definition.key].orEmpty(),
                    existingEvidenceCount = existingEvidenceCount,
                    selectedEvidenceCount = evidenceUris[definition.key]?.size ?: 0,
                    onStatusChange = {
                        statusMap[definition.key] = it
                        localValidationError = null
                    },
                    onPoisonChange = {
                        poisonMap[definition.key] = it
                        localValidationError = null
                    },
                    onPickEvidence = {
                        val captureUri = createChecklistCameraUri(context, vehicle.plate, definition.key)
                        if (captureUri == null) {
                            localValidationError = "No se pudo abrir la cámara para ${definition.label}."
                        } else {
                            localValidationError = null
                            captureTarget = definition.key
                            pendingCaptureUri = captureUri
                            cameraLauncher.launch(captureUri)
                        }
                    },
                )
            }

            if (!localValidationError.isNullOrBlank()) {
                item {
                    Text(
                        text = localValidationError.orEmpty(),
                        color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
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
                        val missingDefinition = inspectionChecklist.firstOrNull { definition ->
                            statusMap[definition.key].isNullOrBlank()
                        }
                        if (missingDefinition != null) {
                            localValidationError = "Debes seleccionar el resultado en: ${missingDefinition.label}."
                            return@Button
                        }
                        val missingPoisonDefinition = inspectionChecklist.firstOrNull { definition ->
                            definition.requiresPoison &&
                                statusMap[definition.key] == "SI" &&
                                poisonMap[definition.key].isNullOrBlank()
                        }
                        if (missingPoisonDefinition != null) {
                            localValidationError = "Debes escribir el veneno utilizado en: ${missingPoisonDefinition.label}."
                            return@Button
                        }
                        localValidationError = null
                        val checklist = inspectionChecklist.associate { definition ->
                            val evidences = evidenceUris[definition.key]
                                ?.map { uri -> uriToDataUrl(context, uri) }
                                .orEmpty()
                            definition.key to ChecklistSubmissionItem(
                                label = definition.label,
                                status = statusMap[definition.key].orEmpty(),
                                poison = poisonMap[definition.key].orEmpty().ifBlank { null },
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
    poison: String,
    existingEvidenceCount: Int,
    selectedEvidenceCount: Int,
    onStatusChange: (String) -> Unit,
    onPoisonChange: (String) -> Unit,
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
                definition.options.forEach { (value, label) ->
                    FilterChip(
                        selected = status == value,
                        onClick = { onStatusChange(value) },
                        label = { Text(label) },
                    )
                }
            }
            if (definition.requiresPoison && status == "SI") {
                OutlinedTextField(
                    value = poison,
                    onValueChange = onPoisonChange,
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Veneno utilizado") },
                    placeholder = { Text("Ej: Atonit") },
                    singleLine = true,
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
                            text = "Evidencias previas: $existingEvidenceCount | Nuevas tomadas: $selectedEvidenceCount",
                            style = MaterialTheme.typography.bodySmall,
                        )
                        Button(onClick = onPickEvidence) {
                            Text(if (selectedEvidenceCount > 0) "Tomar otra foto" else "Abrir cámara")
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

private fun createChecklistCameraUri(context: Context, plate: String, checklistKey: String): Uri? {
    val safePlate = plate.trim().ifBlank { "vehiculo" }.replace(Regex("[^A-Za-z0-9]+"), "_").trim('_')
    val safeKey = checklistKey.trim().ifBlank { "evidencia" }.replace(Regex("[^A-Za-z0-9]+"), "_").trim('_')
    val timestamp = System.currentTimeMillis()
    val values = ContentValues().apply {
        put(MediaStore.Images.Media.DISPLAY_NAME, "control_calidad_${safePlate}_${safeKey}_$timestamp.jpg")
        put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            put(MediaStore.Images.Media.RELATIVE_PATH, "DCIM/ControlCalidad")
        }
    }
    return context.contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
}
