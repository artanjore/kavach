package com.kavach.app.ui

import android.graphics.BitmapFactory
import android.widget.ImageView
import android.widget.LinearLayout
import com.kavach.app.KavachApp
import com.kavach.app.data.Api

/** Shows the pairing QR (rendered by the server, so the app needs no QR library). */
object QrView {
    fun create(a: BaseActivity, code: String): ImageView {
        val size = Ui.dp(a, 240)
        val img = ImageView(a).apply {
            layoutParams = LinearLayout.LayoutParams(size, size).apply { gravity = android.view.Gravity.CENTER_HORIZONTAL }
            scaleType = ImageView.ScaleType.FIT_CENTER
        }
        Api.async({ (a.application as KavachApp).api.bytes("/v1/pairing/qr.png?code=$code") }) { r ->
            r.onSuccess { bytes -> img.setImageBitmap(BitmapFactory.decodeByteArray(bytes, 0, bytes.size)) }
        }
        return img
    }
}
