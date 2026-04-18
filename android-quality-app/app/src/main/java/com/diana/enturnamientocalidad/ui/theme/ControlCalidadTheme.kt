package com.diana.enturnamientocalidad.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

private val BrandBlue       = Color(0xFF1B58E8)
private val BrandBlueDark   = Color(0xFF1038B2)
private val BrandBlueDeep   = Color(0xFF0A1E4A)
private val BrandNavy       = Color(0xFF0D1E3A)
private val BrandSky        = Color(0xFFE4EFFE)
private val BrandEmerald    = Color(0xFF0FA872)
private val BrandAmber      = Color(0xFFF59E0B)
private val BrandRed        = Color(0xFFDC2626)
private val BrandSurface    = Color(0xFFF0F6FF)
private val BrandSurfaceDark= Color(0xFF0A1427)
private val BrandWhite      = Color(0xFFFFFFFF)
private val BrandOutline    = Color(0xFFCBD9EE)

private val LightColors = lightColorScheme(
    primary              = BrandBlue,
    onPrimary            = BrandWhite,
    primaryContainer     = BrandSky,
    onPrimaryContainer   = BrandBlueDeep,
    secondary            = BrandEmerald,
    onSecondary          = BrandWhite,
    secondaryContainer   = Color(0xFFD0F5E8),
    onSecondaryContainer = Color(0xFF054030),
    tertiary             = BrandAmber,
    onTertiary           = BrandWhite,
    background           = BrandSurface,
    onBackground         = BrandNavy,
    surface              = BrandWhite,
    onSurface            = BrandNavy,
    surfaceVariant       = BrandSky,
    onSurfaceVariant     = Color(0xFF3D5070),
    outline              = BrandOutline,
    outlineVariant       = Color(0xFFE2EAF7),
    error                = BrandRed,
    onError              = BrandWhite,
    errorContainer       = Color(0xFFFFE4E4),
    onErrorContainer     = Color(0xFF7A0000),
)

private val DarkColors = darkColorScheme(
    primary              = Color(0xFF7EB0FF),
    onPrimary            = Color(0xFF082869),
    primaryContainer     = BrandBlueDark,
    onPrimaryContainer   = Color(0xFFDDE8FF),
    secondary            = Color(0xFF50D4A8),
    onSecondary          = Color(0xFF03382A),
    secondaryContainer   = Color(0xFF054F3C),
    onSecondaryContainer = Color(0xFFB0F0D8),
    tertiary             = Color(0xFFFFCB70),
    onTertiary           = Color(0xFF402900),
    background           = BrandSurfaceDark,
    onBackground         = Color(0xFFE4EEFE),
    surface              = Color(0xFF101E38),
    onSurface            = Color(0xFFE4EEFE),
    surfaceVariant       = Color(0xFF182840),
    onSurfaceVariant     = Color(0xFFAABDD5),
    outline              = Color(0xFF2D4060),
    outlineVariant       = Color(0xFF1A2E4A),
    error                = Color(0xFFFF8A8A),
    onError              = Color(0xFF690000),
    errorContainer       = Color(0xFF930000),
    onErrorContainer     = Color(0xFFFFDAD6),
)

private val AppTypography = Typography(
    displayLarge  = TextStyle(fontWeight = FontWeight.Black,  fontSize = 57.sp, letterSpacing = (-0.25).sp),
    displayMedium = TextStyle(fontWeight = FontWeight.ExtraBold, fontSize = 45.sp),
    displaySmall  = TextStyle(fontWeight = FontWeight.Bold,   fontSize = 36.sp),
    headlineLarge = TextStyle(fontWeight = FontWeight.ExtraBold, fontSize = 32.sp, letterSpacing = (-0.5).sp),
    headlineMedium= TextStyle(fontWeight = FontWeight.Bold,   fontSize = 28.sp, letterSpacing = (-0.3).sp),
    headlineSmall = TextStyle(fontWeight = FontWeight.Bold,   fontSize = 24.sp),
    titleLarge    = TextStyle(fontWeight = FontWeight.Bold,   fontSize = 22.sp),
    titleMedium   = TextStyle(fontWeight = FontWeight.SemiBold, fontSize = 16.sp, letterSpacing = 0.15.sp),
    titleSmall    = TextStyle(fontWeight = FontWeight.SemiBold, fontSize = 14.sp, letterSpacing = 0.1.sp),
    bodyLarge     = TextStyle(fontWeight = FontWeight.Normal, fontSize = 16.sp, lineHeight = 24.sp),
    bodyMedium    = TextStyle(fontWeight = FontWeight.Normal, fontSize = 14.sp, lineHeight = 20.sp),
    bodySmall     = TextStyle(fontWeight = FontWeight.Normal, fontSize = 12.sp, lineHeight = 16.sp),
    labelLarge    = TextStyle(fontWeight = FontWeight.SemiBold, fontSize = 14.sp, letterSpacing = 0.1.sp),
    labelMedium   = TextStyle(fontWeight = FontWeight.SemiBold, fontSize = 12.sp, letterSpacing = 0.5.sp),
    labelSmall    = TextStyle(fontWeight = FontWeight.Medium, fontSize = 11.sp, letterSpacing = 0.5.sp),
)

@Composable
fun ControlCalidadTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        typography  = AppTypography,
        content     = content,
    )
}
