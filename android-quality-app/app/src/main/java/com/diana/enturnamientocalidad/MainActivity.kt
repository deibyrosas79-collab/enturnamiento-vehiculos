package com.diana.enturnamientocalidad

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.material3.Surface
import androidx.lifecycle.viewmodel.compose.viewModel
import com.diana.enturnamientocalidad.ui.QualityApp
import com.diana.enturnamientocalidad.ui.QualityViewModel
import com.diana.enturnamientocalidad.ui.theme.ControlCalidadTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            ControlCalidadTheme {
                Surface {
                    val viewModel: QualityViewModel = viewModel(factory = QualityViewModel.factory(this))
                    QualityApp(viewModel)
                }
            }
        }
    }
}
