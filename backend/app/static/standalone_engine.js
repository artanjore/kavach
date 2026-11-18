/*
 * Kavach in-browser engine for the hosted demo (docs/demo/index.html).
 *
 * A JavaScript port of the backend's risk engine and the API routes the demo page
 * uses. It replaces window.fetch for /v1/... and /webhooks/... paths, so demo.html
 * runs unchanged with no server. All rule DATA (scam patterns, weights, URL lists,
 * Hindi/Marathi/English text, seed numbers) is exported from the Python code by
 * scripts/build_static_demo.py, and scripts/parity_check.mjs verifies this file
 * gives the same verdicts as the Python engine on the eval set.
 *
 * Production uses the Python backend. This file is for demos only.
 */
(function (root) {
  "use strict";
  const D = root.KAVACH_DATA;

  // ------------------------------------------------------------ text
  const LANGS = ["en", "hi", "mr"];
  const langOf = (l) => (LANGS.includes(l) ? l : "hi");
  const fmt = (s, kw) => (kw ? s.replace(/\{(\w+)\}/g, (_, k) => (k in kw ? String(kw[k]) : `{${k}}`)) : s);
  const t = (key, lang, kw) => { const e = D.T[key]; return fmt(e[langOf(lang)] || e.en, kw); };
  const reason = (code, lang) => { const e = D.REASONS[code]; return e ? e[langOf(lang)] || e.en : code; };

  // ------------------------------------------------------------ phone
  function normalize(raw) {
    raw = (raw || "").trim();
    const plus = raw.startsWith("+");
    const d = raw.replace(/\D/g, "");
    if (!d) return "";
    if (plus) return "+" + d;
    if (d.startsWith("00")) return "+" + d.slice(2);
    if (d.length === 10 && "6789".includes(d[0])) return "+91" + d;
    if (d.length === 11 && d[0] === "0" && "6789".includes(d[1])) return "+91" + d.slice(1);
    if (d.length === 12 && d.startsWith("91") && "6789".includes(d[2])) return "+" + d;
    return d;
  }
  function shapeSignals(number) {
    const n = normalize(number);
    const s = [];
    if (!n) return ["hidden_number"];
    if (n.startsWith("+") && !n.startsWith("+91")) s.push("international");
    if (n.startsWith("+91")) {
      const rest = n.slice(3);
      if (!(rest.length === 10 && "6789".includes(rest[0])) && !rest.startsWith("1600") && !rest.startsWith("140")) s.push("malformed_indian");
    }
    const bare = n.startsWith("+91") ? n.slice(3) : n;
    if (bare.startsWith("140")) s.push("telemarketing_series");
    if (bare.startsWith("1600")) s.push("trai_1600_series");
    return s;
  }

  // ------------------------------------------------------------ URLs
  const U = D.URLS;
  // Parsed by hand like Python's urlparse: the browser's URL() rejects some malformed
  // hosts (e.g. bad punycode) that scammers use, and we still want to inspect them.
  function hostOf(url) {
    const m = url.replace(/^https?:\/\//i, "").match(/^([^/?#]*)/);
    const host = (m ? m[1] : "").replace(/^.*@/, "").replace(/:\d*$/, "");
    return host.toLowerCase().replace(/\.$/, "");
  }
  function registrable(host) {
    const p = host.split(".");
    if (p.length >= 3 && ["co", "gov", "nic", "org", "bank", "net", "ac"].includes(p[p.length - 2]) && p[p.length - 1] === "in") return p.slice(-3).join(".");
    return p.slice(-2).join(".");
  }
  function urlSignals(url) {
    const host = hostOf(url);
    if (!host) return ["bad_url"];
    let s = [];
    if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host) || host.startsWith("[")) s.push("ip_url");
    if (host.startsWith("xn--") || host.includes(".xn--")) s.push("punycode");
    if (U.shorteners.includes(host)) s.push("shortener");
    if (U.risky_tlds.includes(host.split(".").pop())) s.push("risky_tld");
    if (url.toLowerCase().split("?")[0].endsWith(".apk")) s.push("apk_download");
    const reg = registrable(host);
    const compact = host.replace(/[-.]/g, "");
    for (const [brand, legit] of Object.entries(U.brands)) {
      if (compact.includes(brand) && !legit.includes(reg) && !legit.some((d) => host === d || host.endsWith("." + d))) { s.push("brand_lookalike"); break; }
    }
    if (U.official_suffixes.some((suf) => host.endsWith(suf))) { s = s.filter((x) => x !== "brand_lookalike"); s.push("official_domain"); }
    return s;
  }

  // ------------------------------------------------------------ rules
  const CATS = D.CATEGORIES.map((c) => ({
    key: c.key, weight: c.weight,
    patterns: c.patterns.map((p) => new RegExp(p, "i")),
    negatives: c.negatives.map((p) => new RegExp(p, "i")),
  }));
  const URL_RE = new RegExp(D.URL_RE, "gi");
  const PHONE_RE = new RegExp(D.PHONE_RE, "g");

  // ------------------------------------------------------------ in-memory database
  const db = { users: [], tokens: {}, pairings: [], scam: {}, reports: [], calls: [], alerts: [], outbox: [], holds: [], checks: [], audit: [], codes: {} };
  const ids = {};
  const nextId = (k) => (ids[k] = (ids[k] || 0) + 1);
  const iso = (d = new Date()) => d.toISOString().replace("Z", "");
  const nowMs = () => Date.now();
  for (const n of D.SEED_NUMBERS) db.scam[n.number] = { number: n.number, category: n.category, source: "seed", scam_reports: 0, genuine_reports: 0 };

  function reputation(number) {
    const r = db.scam[number];
    if (!r) return [false, []];
    if ((r.source === "seed" || r.source === "partner") && r.genuine_reports < D.SETTINGS.report_threshold) return [true, ["scam_list"]];
    if (r.scam_reports - r.genuine_reports >= D.SETTINGS.report_threshold) return [true, ["user_reports"]];
    return [false, []];
  }

  function assessCall(seniorId, raw) {
    const number = normalize(raw);
    const [isScam, reasons] = reputation(number);
    if (isScam) return { number, level: "warn", reasons };
    const shape = shapeSignals(raw);
    if (shape.includes("trai_1600_series")) return { number, level: "safe", reasons: [] };
    const caution = shape.filter((s) => ["international", "malformed_indian", "hidden_number"].includes(s));
    const since = nowMs() - 24 * 3600e3;
    const recent = db.calls.filter((c) => c.senior_id === seniorId && c.number === number && c.ts >= since).length;
    if (recent + 1 >= D.SETTINGS.repeat_call_threshold) caution.push("repeat_unknown");
    if (caution.includes("malformed_indian") && (caution.includes("international") || caution.includes("repeat_unknown"))) return { number, level: "warn", reasons: caution };
    return { number, level: caution.length ? "caution" : "safe", reasons: caution };
  }

  function rulesScore(text) {
    let score = 0;
    const codes = [];
    for (const c of CATS) {
      if (c.patterns.some((p) => p.test(text)) && !c.negatives.some((n) => n.test(text))) { score += c.weight; codes.push(c.key); }
    }
    const urls = [...text.matchAll(URL_RE)].map((m) => m[1].replace(/[.,)]+$/, ""));
    for (const u of urls) for (const sig of urlSignals(u)) {
      score += U.weights[sig] || 0;
      if (sig !== "official_domain" && !codes.includes(sig)) codes.push(sig);
    }
    const numbers = [];
    for (const m of text.match(PHONE_RE) || []) {
      const n = normalize(m);
      if (n.replace(/^\+/, "").length >= 10) {
        numbers.push(n);
        const [isScam, r] = reputation(n);
        if (isScam) { score += 5; for (const c of r) if (!codes.includes(c)) codes.push(c); }
      }
    }
    return { score, codes, urls, numbers };
  }

  function assessMessage(text, lang) {
    text = (text || "").trim();
    let { score, codes, urls, numbers } = text ? rulesScore(text) : { score: 0, codes: [], urls: [], numbers: [] };
    if (text && !urls.length && numbers.length && text.replace(PHONE_RE, "").trim().length < 4) {
      let verdict;
      if (codes.includes("scam_list") || codes.includes("user_reports")) verdict = "scam";
      else { codes = shapeSignals(numbers[0]).filter((s) => s === "international" || s === "malformed_indian"); verdict = codes.length ? "suspicious" : "safe"; }
      const primary = codes[0] || "no_signals";
      return { verdict, category: primary, reason_codes: codes, reason: reason(primary, lang), engine: "rules" };
    }
    const verdict = score >= 6 ? "scam" : score >= 3 ? "suspicious" : "safe";
    return {
      verdict, category: codes[0] || "none", reason_codes: codes, engine: "rules",
      reason: codes.length ? codes.slice(0, 2).map((c) => reason(c, lang)).join("; ") : reason("no_signals", lang),
    };
  }

  // ------------------------------------------------------------ alerts & messaging
  const PERMISSION = { call_warning: "see_call_warnings", long_call: "see_call_warnings", help_pressed: "see_help_presses", checklist_yes: "see_help_presses", message_scam: "see_message_checks", transfer_hold: "approve_transfers" };
  const user = (id) => db.users.find((u) => u.id === id);
  function sendWhatsapp(to, body) { db.outbox.push({ id: nextId("outbox"), channel: "whatsapp", to, body, at: iso() }); }
  function notifyGuardians(senior, kind, refId, guardians, kw = {}) {
    const targets = guardians || db.pairings.filter((p) => p.senior_id === senior.id && p.status === "active" && p[PERMISSION[kind]]).map((p) => user(p.guardian_id));
    for (const g of targets) {
      const text = t("alert." + kind, g.language, { senior: senior.name || senior.phone, ...kw });
      db.alerts.push({ id: nextId("alert"), senior_id: senior.id, guardian_id: g.id, kind, detail: text, ref_id: refId, created_at: iso(), acknowledged_at: null, called_back_at: null });
      if (g.whatsapp_opt_in) sendWhatsapp(g.phone, `[template:kavach_guardian_alert] ${text} Call: ${senior.phone}`);
    }
  }
  const formatVerdict = (a, lang) => [t("verdict." + a.verdict, lang), t("verdict.why", lang, { reason: a.reason }), "", t("disclaimer", lang)].join("\n");
  function runCheck(u, text, channel, lang) {
    const a = assessMessage(text, lang);
    const id = nextId("check");
    db.checks.push({ id, user_id: u ? u.id : null, channel, verdict: a.verdict, at: nowMs() });
    if (u && a.verdict === "scam" && u.role === "senior") notifyGuardians(u, "message_scam", id, null, { detail: a.category ? reason(a.category, "en") : "" });
    return [id, a];
  }

  // ------------------------------------------------------------ holds (bank v2)
  const holdJson = (h) => ({ hold_id: h.id, event_id: h.bank_event_id, status: h.status, amount_paise: h.amount_paise, payee_label: h.payee_label, expires_at: h.expires_at, decided_at: h.decided_at });
  function expire(h) { if (h.status === "pending" && new Date(h.expires_at + "Z").getTime() < nowMs()) { h.status = "expired"; db.audit.push({ actor: "system", action: "hold_expired", target: "hold:" + h.id, at: iso() }); } }
  function trustedGuardians(seniorId) {
    return db.pairings.filter((p) => p.senior_id === seniorId && p.status === "active" && p.approve_transfers && p.approve_transfers_effective_at && new Date(p.approve_transfers_effective_at + "Z").getTime() <= nowMs()).map((p) => user(p.guardian_id));
  }
  const pairingJson = (p) => {
    const s = user(p.senior_id), g = user(p.guardian_id);
    return { id: p.id, status: p.status, senior: { id: s.id, name: s.name, phone: s.phone }, guardian: { id: g.id, name: g.name, phone: g.phone },
      permissions: { see_call_warnings: p.see_call_warnings, see_help_presses: p.see_help_presses, see_message_checks: p.see_message_checks, approve_transfers: p.approve_transfers },
      approve_transfers_effective_at: p.approve_transfers_effective_at };
  };

  // ------------------------------------------------------------ router
  class HttpError extends Error { constructor(status, detail) { super(detail); this.status = status; } }
  const need = (u) => { if (!u) throw new HttpError(401, "invalid token"); return u; };
  const senior = (u) => { need(u); if (u.role !== "senior") throw new HttpError(403, "senior only"); return u; };
  const bankAuth = (h) => { if (h["x-api-key"] !== "dev-bank-key") throw new HttpError(401, "invalid bank api key"); return "DEVBANK"; };

  const routes = [
    ["POST", /^\/v1\/demo\/setup$/, ({ q }) => {
      const tag = Math.floor(Math.random() * 1e6).toString().padStart(6, "0");
      const lang = q.get("senior_lang") || "hi";
      const s = { id: nextId("user"), phone: "+9170" + tag + "00", name: "Kamla-ji", role: "senior", language: lang, bank_code: "DEVBANK", bank_customer_ref: "DEMO-" + tag, whatsapp_opt_in: true };
      const g = { id: nextId("user"), phone: "+9180" + tag + "00", name: "Rohit", role: "guardian", language: "en", whatsapp_opt_in: true };
      db.users.push(s, g);
      db.pairings.push({ id: nextId("pairing"), senior_id: s.id, guardian_id: g.id, status: "active", see_call_warnings: true, see_help_presses: true, see_message_checks: true, approve_transfers: true, approve_transfers_effective_at: iso(new Date(nowMs() - 60e3)) });
      const tok = (u) => { const k = "tok-" + u.id + "-" + tag; db.tokens[k] = u.id; return k; };
      return { senior: { token: tok(s), phone: s.phone, name: s.name, customer_ref: s.bank_customer_ref, language: lang }, guardian: { token: tok(g), phone: g.phone, name: g.name }, bank: { code: "DEVBANK", api_key: "dev-bank-key" } };
    }],
    ["GET", /^\/v1\/demo\/outbox$/, ({ q }) => {
      const to = q.get("to"), after = Number(q.get("after_id") || 0);
      return db.outbox.filter((m) => m.to === to && m.id > after);
    }],
    ["POST", /^\/v1\/calls\/screen$/, ({ u, body }) => {
      const s = senior(u);
      const a = assessCall(s.id, body.number);
      const ev = { id: nextId("call"), senior_id: s.id, number: a.number, level: a.level, outcome: "", ts: nowMs() };
      db.calls.push(ev);
      if (a.level === "warn") notifyGuardians(s, "call_warning", ev.id, null, { number: a.number });
      return { call_id: ev.id, level: a.level, reasons: a.reasons, speak: t("call." + a.level, s.language), reason_text: a.reasons.map((r) => reason(r, s.language)).join("; "), cnap_name: null };
    }],
    ["POST", /^\/v1\/calls\/(\d+)\/outcome$/, ({ u, body, m }) => {
      const ev = db.calls.find((c) => c.id === Number(m[1]));
      if (!ev || ev.senior_id !== need(u).id) throw new HttpError(404, "call not found");
      ev.outcome = body.outcome;
      const row = db.scam[ev.number] || (db.scam[ev.number] = { number: ev.number, source: "reports", scam_reports: 0, genuine_reports: 0 });
      if (body.outcome === "scam") row.scam_reports++; else row.genuine_reports++;
      return { ok: true };
    }],
    ["POST", /^\/v1\/calls\/long-call$/, ({ u, body }) => {
      const s = senior(u);
      if (body.duration_s < D.SETTINGS.long_call_seconds) return { nudge: false };
      notifyGuardians(s, "long_call", body.call_id || null, null, { number: normalize(body.number), minutes: Math.floor(body.duration_s / 60) });
      return { nudge: true, speak: t("long_call.nudge", s.language) };
    }],
    ["POST", /^\/v1\/help\/pressed$/, ({ u }) => {
      const s = senior(u);
      const before = db.alerts.length;
      notifyGuardians(s, "help_pressed");
      return { guardians_alerted: db.alerts.length - before, questions: ["stay_on_call", "secret", "pay", "authority", "app"].map((q) => ({ id: q, text: t("check.q." + q, s.language) })) };
    }],
    ["POST", /^\/v1\/help\/checklist$/, ({ u, body }) => {
      const s = senior(u);
      const yes = Object.entries(body.answers).filter(([, v]) => v).map(([k]) => k);
      if (!yes.length) return { risk: false, speak: t("check.ok", s.language) };
      notifyGuardians(s, "checklist_yes", null, null, { detail: yes.filter((q) => D.T["check.q." + q]).map((q) => t("check.q." + q, "en").replace(/\?$/, "")).join(", ") });
      const guardians = db.pairings.filter((p) => p.senior_id === s.id && p.status === "active").map((p) => user(p.guardian_id));
      return { risk: true, speak: t("check.stop", s.language), call_guardians: guardians.map((g) => ({ name: g.name, phone: g.phone })), helplines: helplines(s) };
    }],
    ["POST", /^\/v1\/check$/, ({ u, body }) => {
      need(u);
      const [id, a] = runCheck(u, body.text, "app", u.language);
      return { check_id: id, verdict: a.verdict, category: a.category, reason: a.reason, engine: a.engine, message: formatVerdict(a, u.language) };
    }],
    ["GET", /^\/v1\/recover$/, ({ u }) => ({ helplines: helplines(need(u)), steps: D.RECOVER_STEPS })],
    ["GET", /^\/v1\/alerts$/, ({ u }) => {
      need(u);
      return db.alerts.filter((a) => a.guardian_id === u.id).slice().reverse().slice(0, 100).map((a) => {
        const s = user(a.senior_id);
        return { id: a.id, kind: a.kind, detail: a.detail, ref_id: a.ref_id, created_at: a.created_at, acknowledged: !!a.acknowledged_at, senior: { name: s.name, phone: s.phone } };
      });
    }],
    ["POST", /^\/v1\/alerts\/(\d+)\/ack$/, ({ u, body, m }) => {
      const a = db.alerts.find((x) => x.id === Number(m[1]));
      if (!a || a.guardian_id !== need(u).id) throw new HttpError(404, "not found");
      a.acknowledged_at = a.acknowledged_at || iso();
      if (body.called_back) a.called_back_at = a.called_back_at || iso();
      return { ok: true };
    }],
    ["GET", /^\/v1\/pairing$/, ({ u }) => {
      need(u);
      const col = u.role === "senior" ? "senior_id" : "guardian_id";
      return db.pairings.filter((p) => p[col] === u.id && p.status === "active").map(pairingJson);
    }],
    ["PATCH", /^\/v1\/pairing\/(\d+)$/, ({ u, body, m }) => {
      const p = db.pairings.find((x) => x.id === Number(m[1]));
      if (!p || p.senior_id !== need(u).id) throw new HttpError(404, "pairing not found");
      if (body.approve_transfers && !p.approve_transfers) p.approve_transfers_effective_at = iso(new Date(nowMs() + D.SETTINGS.guardian_cooloff_hours * 3600e3));
      if (body.approve_transfers === false) p.approve_transfers_effective_at = null;
      Object.assign(p, body);
      return pairingJson(p);
    }],
    ["POST", /^\/v1\/pairing\/code$/, ({ u }) => {
      senior(u);
      db.codes[D.DEMO_QR.code] = u.id;
      return { code: D.DEMO_QR.code, expires_in_s: 900, join_url: D.DEMO_QR.join_url };
    }],
    ["GET", /^\/v1\/pairing\/qr\.png$/, () => new Blob([D.DEMO_QR.svg], { type: "image/svg+xml" })],
    ["POST", /^\/webhooks\/whatsapp$/, ({ body }) => {
      for (const e of body.entry || []) for (const c of e.changes || []) for (const msg of c.value?.messages || []) {
        const sender = "+" + String(msg.from || "").replace(/^\+/, "");
        const u = db.users.find((x) => x.phone === sender);
        const text = msg.type === "text" ? msg.text?.body || "" : "";
        const lang = u ? u.language : /[ऀ-ॿ]/.test(text) ? (/(आहे|नाही|तुम्ही|आम्ही|करा|झाले)/.test(text) ? "mr" : "hi") : "en";
        if (!text) { sendWhatsapp(sender, t("wa.unsupported", lang)); continue; }
        if (/^\s*(hi|hello|hey|namaste|namaskar|start|नमस्ते|नमस्कार)\s*[!.]*\s*$/i.test(text)) { sendWhatsapp(sender, t("wa.welcome", lang)); continue; }
        const [, a] = runCheck(u, text, "whatsapp", lang);
        sendWhatsapp(sender, formatVerdict(a, lang));
      }
      return { ok: true };
    }],
    ["POST", /^\/v1\/bank\/risk-events$/, ({ h, body }) => {
      const bank = bankAuth(h);
      const existing = db.holds.find((x) => x.bank_code === bank && x.bank_event_id === body.event_id);
      if (existing) { expire(existing); return holdJson(existing); }
      const s = db.users.find((x) => x.bank_code === bank && x.bank_customer_ref === body.customer_ref);
      if (!s) throw new HttpError(404, "customer not enrolled");
      const guardians = trustedGuardians(s.id);
      if (!guardians.length) return { status: "no_trusted_person", event_id: body.event_id };
      const hold = { id: nextId("hold"), bank_code: bank, bank_event_id: body.event_id, senior_id: s.id, amount_paise: body.amount_paise, payee_label: body.payee_label || "", status: "pending", decided_at: null,
        expires_at: iso(new Date(nowMs() + D.SETTINGS.hold_decision_minutes * 60e3)) };
      db.holds.push(hold);
      db.audit.push({ actor: "bank:" + bank, action: "risk_event", target: "hold:" + hold.id, at: iso() });
      notifyGuardians(s, "transfer_hold", hold.id, guardians, { bank, amount: Math.round(body.amount_paise / 100).toLocaleString("en-US"), payee: body.payee_label || "a new payee", minutes: D.SETTINGS.hold_decision_minutes });
      return holdJson(hold);
    }],
    ["GET", /^\/v1\/bank\/holds\/(.+)$/, ({ h, m }) => {
      const bank = bankAuth(h);
      const hold = db.holds.find((x) => x.bank_code === bank && x.bank_event_id === decodeURIComponent(m[1]));
      if (!hold) throw new HttpError(404, "not found");
      expire(hold);
      return holdJson(hold);
    }],
    ["GET", /^\/v1\/bank\/dashboard$/, ({ h }) => {
      const bank = bankAuth(h);
      const seniors = db.users.filter((x) => x.bank_code === bank);
      const ids = new Set(seniors.map((x) => x.id));
      const holds = db.holds.filter((x) => x.bank_code === bank);
      holds.forEach(expire);
      const count = (arr, key) => arr.reduce((o, x) => ((o[x[key]] = (o[x[key]] || 0) + 1), o), {});
      return { enrolled_seniors: seniors.length, recent_holds: holds.slice().reverse().slice(0, 25).map(holdJson), holds_by_status: count(holds, "status"),
        alerts_by_kind: count(db.alerts.filter((a) => ids.has(a.senior_id)), "kind"),
        declined_amount_rupees: holds.filter((x) => x.status === "declined").reduce((a, x) => a + x.amount_paise, 0) / 100,
        audit: db.audit.filter((a) => a.actor === "bank:" + bank).slice().reverse().slice(0, 50) };
    }],
    ["GET", /^\/v1\/holds$/, ({ u }) => {
      need(u);
      const seniors = db.pairings.filter((p) => p.guardian_id === u.id && p.status === "active").map((p) => p.senior_id);
      const rows = db.holds.filter((x) => seniors.includes(x.senior_id)).slice().reverse().slice(0, 50);
      rows.forEach(expire);
      return rows.map((x) => ({ ...holdJson(x), senior: user(x.senior_id).name, bank: x.bank_code }));
    }],
    ["POST", /^\/v1\/holds\/(\d+)\/decision$/, ({ u, body, m }) => {
      need(u);
      const hold = db.holds.find((x) => x.id === Number(m[1]));
      if (!hold) throw new HttpError(404, "not found");
      if (!trustedGuardians(hold.senior_id).some((g) => g.id === u.id)) throw new HttpError(403, "you are not a trusted person for this account");
      expire(hold);
      if (hold.status !== "pending") throw new HttpError(409, "already " + hold.status);
      hold.status = body.decision === "approve" ? "approved" : "declined";
      hold.decided_at = iso();
      db.audit.push({ actor: "user:" + u.id, action: "hold_" + hold.status, target: "hold:" + hold.id, at: iso() });
      return holdJson(hold);
    }],
    ["GET", /^\/v1\/admin\/metrics$/, () => {
      const week = nowMs() - 7 * 24 * 3600e3;
      const pairs = db.pairings.filter((p) => p.status === "active");
      const seniors = new Set(pairs.map((p) => p.senior_id));
      const active = new Set([...db.calls.filter((c) => c.ts >= week).map((c) => c.senior_id), ...db.checks.filter((c) => c.at >= week).map((c) => c.user_id),
        ...db.alerts.filter((a) => ["help_pressed", "checklist_yes"].includes(a.kind)).map((a) => a.senior_id)]);
      const wa = [...seniors].filter((s) => active.has(s)).length;
      const warned = db.calls.filter((c) => c.level === "warn");
      const labelled = warned.filter((c) => c.outcome);
      const resp = db.alerts.filter((a) => a.called_back_at).map((a) => (new Date(a.called_back_at + "Z") - new Date(a.created_at + "Z")) / 60000).sort((a, b) => a - b);
      const median = resp.length ? (resp.length % 2 ? resp[(resp.length - 1) / 2] : (resp[resp.length / 2 - 1] + resp[resp.length / 2]) / 2) : null;
      return { activated_pairs: pairs.length, weekly_active_seniors: wa, weekly_active_share: seniors.size ? wa / seniors.size : null, call_warnings: warned.length,
        alert_precision: labelled.length ? labelled.filter((c) => c.outcome === "scam").length / labelled.length : null,
        false_alarm_rate: warned.length ? warned.filter((c) => c.outcome === "genuine").length / warned.length : null,
        median_guardian_response_min: median, message_checks: db.checks.length, seniors: db.users.filter((x) => x.role === "senior").length };
    }],
  ];
  function helplines(u) {
    return { cyber_fraud_helpline: "1930", cybercrime_portal: "https://cybercrime.gov.in", chakshu: "https://sancharsaathi.gov.in/sfc/", bank: D.BANK_BLOCK_LINES[u.bank_code] || null };
  }

  function handle(method, url, headers, body) {
    const parsed = new URL(url, "http://kavach.local");
    const h = {};
    for (const [k, v] of Object.entries(headers || {})) h[k.toLowerCase()] = v;
    const tok = (h.authorization || "").replace(/^Bearer\s+/i, "");
    const u = tok && db.tokens[tok] ? user(db.tokens[tok]) : null;
    for (const [m, re, fn] of routes) {
      const match = m === method && parsed.pathname.match(re);
      if (match) return fn({ u, h, q: parsed.searchParams, body: body ? JSON.parse(body) : {}, m: match });
    }
    throw new HttpError(404, "Not Found");
  }

  // ------------------------------------------------------------ fetch shim (browser only)
  if (typeof window !== "undefined" && window.fetch) {
    const realFetch = window.fetch.bind(window);
    window.fetch = async (input, init = {}) => {
      const url = typeof input === "string" ? input : input.url;
      if (!/^\/(v1|webhooks)\//.test(url)) return realFetch(input, init);
      await new Promise((r) => setTimeout(r, 60 + Math.random() * 90)); // feel like a network
      try {
        const out = handle((init.method || "GET").toUpperCase(), url, init.headers, init.body);
        if (out instanceof Blob) return new Response(out, { status: 200, headers: { "Content-Type": out.type } });
        return new Response(JSON.stringify(out), { status: 200, headers: { "Content-Type": "application/json" } });
      } catch (e) {
        const status = e.status || 500;
        if (status === 500) console.error(e);
        return new Response(JSON.stringify({ detail: e.message }), { status, headers: { "Content-Type": "application/json" } });
      }
    };
  }

  root.KavachEngine = { normalize, shapeSignals, urlSignals, assessMessage, assessCall, handle };
})(typeof window !== "undefined" ? window : globalThis);
