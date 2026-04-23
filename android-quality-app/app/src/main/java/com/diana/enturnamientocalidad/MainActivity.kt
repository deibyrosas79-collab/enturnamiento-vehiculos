package com.diana.enturnamientocalidad

import android.Manifest
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.compose.material3.Surface
import androidx.lifecycle.viewmodel.compose.viewModel
import com.diana.enturnamientocalidad.ui.QualityApp
import com.diana.enturnamientocalidad.ui.QualityViewModel
import com.diana.enturnamientocalidad.ui.theme.ControlCalidadTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        requestNotificationPermissionIfNeeded()
        setContent {
            ControlCalidadTheme {
                Surface {
                    val viewModel: QualityViewModel = viewModel(factory = QualityViewModel.factory(this))
                    QualityApp(viewModel)
                }
            }
        }
    }

    private fun requestNotificationPermissionIfNeeded() {
        if (android.os.Build.VERSION.SDK_INT < android.os.Build.VERSION_CODES.TIRAMISU) return
        val granted = ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.POST_NOTIFICATIONS,
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        if (!granted) {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1201)
        }
    }
}
