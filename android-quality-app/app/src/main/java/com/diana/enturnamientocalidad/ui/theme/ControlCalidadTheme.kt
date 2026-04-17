package com.diana.enturnamientocalidad.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val BrandBlue = Color(0xFF1C5EE8)
private val BrandBlueDark = Color(0xFF0D3FAF)
private val BrandNavy = Color(0xFF11203D)
private val BrandSky = Color(0xFFEAF2FF)
private val BrandEmerald = Color(0xFF139B72)
private val BrandAmber = Color(0xFFF59E0B)
private val BrandRed = Color(0xFFDC2626)
private val BrandSurface = Color(0xFFF6F9FD)
private val BrandSurfaceDark = Color(0xFF0C1427)

private val LightColors = lightColorScheme(
    primary = BrandBlue,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFDDE8FF),
    onPrimaryContainer = BrandNavy,
    secondary = BrandEmerald,
    onSecondary = Color.White,
    tertiary = BrandAmber,
    background = BrandSurface,
    onBackground = BrandNavy,
    surface = Color.White,
    onSurface = BrandNavy,
    surfaceVariant = BrandSky,
    onSurfaceVariant = Color(0xFF4B5B7A),
    outline = Color(0xFFD6DEEA),
    error = BrandRed,
)

private val DarkColors = darkColorScheme(
    primary = Color(0xFF8EB2FF),
    onPrimary = Color(0xFF082869),
    primaryContainer = BrandBlueDark,
    onPrimaryContainer = Color(0xFFDDE8FF),
    secondary = Color(0xFF56D4AB),
    onSecondary = Color(0xFF053829),
    tertiary = Color(0xFFFFC766),
    background = BrandSurfaceDark,
    onBackground = Color(0xFFE7EEFA),
    surface = Color(0xFF13203A),
    onSurface = Color(0xFFE7EEFA),
    surfaceVariant = Color(0xFF1A2947),
    onSurfaceVariant = Color(0xFFB5C2D9),
    outline = Color(0xFF30425F),
    error = Color(0xFFFF8A8A),
)

@Composable
fun ControlCalidadTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        content = content,
    )
}
