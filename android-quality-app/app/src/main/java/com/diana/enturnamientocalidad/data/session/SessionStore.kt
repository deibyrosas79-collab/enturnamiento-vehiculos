package com.diana.enturnamientocalidad.data.session

import android.content.Context
import com.diana.enturnamientocalidad.data.model.AppStateDto
import com.google.gson.Gson

class SessionStore(context: Context) {
    private val prefs = context.getSharedPreferences("quality_session", Context.MODE_PRIVATE)
    private val gson = Gson()

    fun saveToken(token: String) {
        prefs.edit().putString("token", token).apply()
    }

    fun getToken(): String? = prefs.getString("token", null)

    fun saveAppState(state: AppStateDto) {
        prefs.edit().putString("app_state_json", gson.toJson(state)).apply()
    }

    fun getSavedAppState(): AppStateDto? {
        val json = prefs.getString("app_state_json", null) ?: return null
        return runCatching { gson.fromJson(json, AppStateDto::class.java) }.getOrNull()
    }

    fun saveFcmToken(token: String) {
        prefs.edit().putString("fcm_token", token).apply()
    }

    fun getSavedFcmToken(): String? = prefs.getString("fcm_token", null)

    fun clear() {
        prefs.edit()
            .remove("token")
            .remove("app_state_json")
            .remove("fcm_token")
            .apply()
    }
}
