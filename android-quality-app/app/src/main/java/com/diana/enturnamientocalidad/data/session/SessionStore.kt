package com.diana.enturnamientocalidad.data.session

import android.content.Context

class SessionStore(context: Context) {
    private val prefs = context.getSharedPreferences("quality_session", Context.MODE_PRIVATE)

    fun saveToken(token: String) {
        prefs.edit().putString("token", token).apply()
    }

    fun getToken(): String? = prefs.getString("token", null)

    fun clear() {
        prefs.edit().remove("token").apply()
    }
}
