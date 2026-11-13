package com.kavach.app.ui

import android.app.Activity
import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.text.InputType
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast

/**
 * Senior-first UI kit, built in code: very large text, very large buttons,
 * high contrast, one column. Every screen is at most two taps from any action.
 */
object Ui {
    const val RED = 0xFFC62828.toInt()
    const val GREEN = 0xFF2E7D32.toInt()
    const val BLUE = 0xFF1565C0.toInt()
    const val GREY = 0xFF455A64.toInt()
    const val AMBER = 0xFFEF6C00.toInt()
    const val INK = 0xFF111111.toInt()

    fun dp(ctx: Context, v: Int) = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v.toFloat(), ctx.resources.displayMetrics).toInt()

    /** A scrolling single-column screen. Returns the column to add views to. */
    fun screen(a: Activity, background: Int = Color.WHITE): LinearLayout {
        val col = LinearLayout(a).apply {
            orientation = LinearLayout.VERTICAL
            val p = dp(a, 20)
            setPadding(p, p, p, p)
        }
        val scroll = ScrollView(a).apply { setBackgroundColor(background); isFillViewport = true; addView(col) }
        a.setContentView(scroll)
        return col
    }

    fun title(ctx: Context, text: String, color: Int = INK) = TextView(ctx).apply {
        this.text = text
        setTextSize(TypedValue.COMPLEX_UNIT_SP, 32f)
        setTypeface(typeface, Typeface.BOLD)
        setTextColor(color)
        setPadding(0, dp(ctx, 8), 0, dp(ctx, 16))
    }

    fun body(ctx: Context, text: String, color: Int = INK, sizeSp: Float = 22f) = TextView(ctx).apply {
        this.text = text
        setTextSize(TypedValue.COMPLEX_UNIT_SP, sizeSp)
        setTextColor(color)
        setLineSpacing(0f, 1.2f)
        setPadding(0, dp(ctx, 6), 0, dp(ctx, 10))
    }

    fun button(ctx: Context, text: String, color: Int = BLUE, heightDp: Int = 88, onClick: () -> Unit) = Button(ctx).apply {
        this.text = text
        isAllCaps = false
        setTextSize(TypedValue.COMPLEX_UNIT_SP, 24f)
        setTypeface(typeface, Typeface.BOLD)
        setTextColor(Color.WHITE)
        background = GradientDrawable().apply { setColor(color); cornerRadius = dp(ctx, 18).toFloat() }
        minHeight = dp(ctx, heightDp)
        layoutParams = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT)
            .apply { setMargins(0, dp(ctx, 8), 0, dp(ctx, 8)) }
        setOnClickListener { onClick() }
    }

    fun input(ctx: Context, hint: String, type: Int = InputType.TYPE_CLASS_TEXT, lines: Int = 1) = EditText(ctx).apply {
        this.hint = hint
        inputType = type
        setTextSize(TypedValue.COMPLEX_UNIT_SP, 24f)
        minLines = lines
        gravity = Gravity.TOP or Gravity.START
        setPadding(dp(ctx, 12), dp(ctx, 12), dp(ctx, 12), dp(ctx, 12))
    }

    fun spacer(ctx: Context, h: Int = 16) = View(ctx).apply { layoutParams = LinearLayout.LayoutParams(1, dp(ctx, h)) }

    fun dial(ctx: Context, number: String) =
        ctx.startActivity(Intent(Intent.ACTION_DIAL, Uri.parse("tel:$number")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))

    fun open(ctx: Context, url: String) =
        ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))

    fun toast(ctx: Context, text: String) = Toast.makeText(ctx, text, Toast.LENGTH_LONG).show()

    fun confirm(a: Activity, lang: String, message: String, onYes: () -> Unit) {
        AlertDialog.Builder(a).setMessage(message)
            .setPositiveButton(S.get("yes", lang)) { _, _ -> onYes() }
            .setNegativeButton(S.get("no", lang), null).show()
    }
}
