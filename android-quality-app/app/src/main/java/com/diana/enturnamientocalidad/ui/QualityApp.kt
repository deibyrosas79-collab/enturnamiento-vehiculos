package com.diana.enturnamientocalidad.ui

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay

@Composable
fun QualityApp(viewModel: QualityViewModel) {
    val navController = rememberNavController()
    val uiState by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    val currentBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = currentBackStackEntry?.destination?.route

    LaunchedEffect(uiState.loggedIn) {
        if (uiState.loggedIn) {
            navController.navigate("home") {
                popUpTo("login") { inclusive = true }
            }
        } else {
            navController.navigate("login") {
                popUpTo(navController.graph.startDestinationId) { inclusive = true }
            }
        }
    }

    LaunchedEffect(uiState.errorMessage) {
        uiState.errorMessage?.let {
            snackbarHostState.showSnackbar(it)
            viewModel.clearError()
        }
    }

    LaunchedEffect(uiState.loggedIn, currentRoute) {
        if (uiState.loggedIn && currentRoute != "login") {
            while (true) {
                delay(30000)
                viewModel.refresh()
            }
        }
    }

    Scaffold(
        modifier = androidx.compose.ui.Modifier.fillMaxSize(),
        containerColor = MaterialTheme.colorScheme.background,
        snackbarHost = {
            SnackbarHost(snackbarHostState) { data ->
                Surface(
                    color = MaterialTheme.colorScheme.inverseSurface,
                    contentColor = MaterialTheme.colorScheme.inverseOnSurface,
                    shape = MaterialTheme.shapes.large,
                    shadowElevation = 10.dp,
                ) {
                    Text(
                        text = data.visuals.message,
                        modifier = androidx.compose.ui.Modifier.padding(
                            horizontal = 18.dp,
                            vertical = 14.dp,
                        ),
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
        },
    ) { padding ->
        NavHost(navController = navController, startDestination = "login") {
            composable("login") {
                LoginScreen(
                    padding = padding,
                    loading = uiState.loading,
                    onLogin = viewModel::login,
                )
            }
            composable("home") {
                QualityHomeScreen(
                    padding = padding,
                    uiState = uiState,
                    onRefresh = viewModel::refresh,
                    onLogout = viewModel::logout,
                    onOpenPending = { navController.navigate("status/pending") },
                    onOpenRework = { navController.navigate("status/rework") },
                    onOpenApproved = { navController.navigate("status/approved") },
                    onOpenRejected = { navController.navigate("status/rejected") },
                )
            }
            composable("status/pending") {
                QualityStatusScreen(
                    padding = padding,
                    title = "Pendientes por revisar",
                    subtitle = "Vehiculos recien enturnados que aun no tienen checklist completo.",
                    vehicles = uiState.pending,
                    allowReview = true,
                    onBack = { navController.popBackStack() },
                    onOpenInspection = { vehicle ->
                        InspectionRoutesHolder.vehicle = vehicle
                        navController.navigate("inspection")
                    },
                )
            }
            composable("status/rework") {
                QualityStatusScreen(
                    padding = padding,
                    title = "Vehiculos en arreglos",
                    subtitle = "Unidades revisadas que requieren ajustes antes de aprobarse.",
                    vehicles = uiState.rework,
                    allowReview = true,
                    onBack = { navController.popBackStack() },
                    onOpenInspection = { vehicle ->
                        InspectionRoutesHolder.vehicle = vehicle
                        navController.navigate("inspection")
                    },
                )
            }
            composable("status/approved") {
                QualityStatusScreen(
                    padding = padding,
                    title = "Vehiculos aptos",
                    subtitle = "Consulta los vehiculos aptos del dia con su informacion consolidada.",
                    vehicles = uiState.approved,
                    allowReview = false,
                    onBack = { navController.popBackStack() },
                    onOpenInspection = {},
                )
            }
            composable("status/rejected") {
                QualityStatusScreen(
                    padding = padding,
                    title = "Vehiculos rechazados",
                    subtitle = "Consulta los rechazados del dia y sus observaciones.",
                    vehicles = uiState.rejected,
                    allowReview = false,
                    onBack = { navController.popBackStack() },
                    onOpenInspection = {},
                )
            }
            composable("inspection") {
                InspectionScreen(
                    padding = padding,
                    vehicle = InspectionRoutesHolder.vehicle,
                    loading = uiState.loading,
                    onBack = { navController.popBackStack() },
                    onSave = { decision, observations, suitability, checklist ->
                        InspectionRoutesHolder.vehicle?.let { vehicle ->
                            viewModel.saveInspection(
                                vehicleId = vehicle.id,
                                finalDecision = decision,
                                observationsText = observations,
                                suitability = suitability,
                                checklist = checklist,
                            ) { success ->
                                if (success) {
                                    navController.popBackStack()
                                }
                            }
                        }
                    },
                )
            }
        }
    }
}

object InspectionRoutesHolder {
    var vehicle: com.diana.enturnamientocalidad.data.model.VehicleDto? = null
}
