// ar-conjugation browsing page: loads data/json/verbs.json and errata.json, lets the
// reader search and filter the 462 paradigms, and shows one as the book prints it.
(function () {
  "use strict";
  var $ = function (s) { return document.querySelector(s); };
  var PERSONS = ["3ms", "3md", "3mp", "3fs", "3fd", "3fp", "2ms", "2d", "2mp", "2fs", "2fp", "1s", "1p"];
  var PERSON_AR = { "3ms": "هو", "3md": "هما", "3mp": "هم", "3fs": "هي", "3fd": "هما (مؤ)", "3fp": "هنّ",
    "2ms": "أنتَ", "2d": "أنتما", "2mp": "أنتم", "2fs": "أنتِ", "2fp": "أنتنّ", "1s": "أنا", "1p": "نحن" };
  var COLS = [["past", "الماضي", false], ["past_pass", "الماضي المجهول", true], ["ind", "المضارع", false],
    ["ind_pass", "المضارع المجهول", true], ["imp", "الأمر", false]];
  var FORMS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "Iq", "IIq", "IIIq", "IVq"];
  var CLASSES = [["سالم", "sound"], ["مهموز", "hamza"], ["مضاعف", "gem"], ["مثال", "assim"], ["أجوف", "hollow"],
    ["ناقص", "defective"], ["لفيف", "doubly"], ["رباعي", "quad"]];
  var MARKS = /[ً-ْٰ]/g;

  function classesOf(v) {
    var r = v.root, out = [];
    if (v.form.slice(-1) === "q") return ["quad"];
    var r1 = r[0], r2 = r[1], r3 = r[2];
    var w = function (c) { return c === "و" || c === "ي"; };
    if (r.indexOf("ء") >= 0) out.push("hamza");
    if (r2 === r3 && !w(r2)) out.push("gem");
    var weak = [w(r1), w(r2), w(r3)];
    var n = weak.filter(Boolean).length;
    if (n >= 2) out.push("doubly");
    else if (weak[0]) out.push("assim");
    else if (weak[1]) out.push("hollow");
    else if (weak[2]) out.push("defective");
    if (!out.length) out.push("sound");
    return out;
  }

  function bare(s) { return (s || "").replace(MARKS, "").replace(/ـ/g, ""); }
  function forms(cell) { return Array.isArray(cell) ? cell : [cell]; }

  var state = { q: "", form: null, cls: null, sel: null, verbs: [], errata: null };

  function chips(el, items, key) {
    el.innerHTML = "";
    items.forEach(function (it) {
      var b = document.createElement("button");
      b.type = "button"; b.className = "chip"; b.textContent = it[0]; b.dataset.v = it[1];
      b.addEventListener("click", function () {
        state[key] = state[key] === it[1] ? null : it[1];
        render();
      });
      el.appendChild(b);
    });
  }

  function matches(v) {
    if (state.form && v.form !== state.form) return false;
    if (state.cls && classesOf(v).indexOf(state.cls) < 0) return false;
    if (!state.q) return true;
    var q = bare(state.q).replace(/\s+/g, "");
    return bare(v.root) === q || bare(v.lemma).indexOf(q) >= 0 || bare(v.wazn).replace(/\s+/g, "").indexOf(q) >= 0 ||
      v.form.toLowerCase() === state.q.trim().toLowerCase();
  }

  function render() {
    document.querySelectorAll("#forms .chip").forEach(function (b) { b.classList.toggle("on", b.dataset.v === state.form); });
    document.querySelectorAll("#classes .chip").forEach(function (b) { b.classList.toggle("on", b.dataset.v === state.cls); });
    var list = $("#list"); list.innerHTML = "";
    var hits = state.verbs.filter(matches);
    $("#count").textContent = hits.length === state.verbs.length ? "كلّ النماذج: " + hits.length : "النتائج: " + hits.length;
    hits.forEach(function (v) {
      var li = document.createElement("li");
      li.innerHTML = '<span class="lemma"></span><span class="meta"></span>';
      li.querySelector(".lemma").textContent = v.lemma;
      li.querySelector(".meta").textContent = v.wazn + " · " + v.root;
      li.classList.toggle("on", state.sel === v.id);
      li.addEventListener("click", function () { location.hash = v.id; });
      list.appendChild(li);
    });
  }

  function td(cell, pass) {
    var t = document.createElement("td");
    if (cell === undefined || cell === null) { t.className = "empty"; t.textContent = "—"; return t; }
    var fs = forms(cell);
    t.textContent = fs[0];
    for (var i = 1; i < fs.length; i++) { var a = document.createElement("span"); a.className = "alt"; a.textContent = fs[i]; t.appendChild(a); }
    if (pass) t.className = "pass";
    return t;
  }

  function badge(text, warn) { var b = document.createElement("span"); b.className = "badge" + (warn ? " warn" : ""); b.textContent = text; return b; }

  function show(v) {
    var d = $("#detail"); d.innerHTML = "";
    var h = document.createElement("h2"); h.textContent = v.lemma; d.appendChild(h);
    var f = document.createElement("div"); f.className = "facts";
    var facts = [["الجذر", v.root], ["الوزن", v.wazn], ["الصيغة", v.form + (v.vowels ? " (" + v.vowels.past + "~" + v.vowels.nonpast + ")" : "")],
      ["نموذج الكتاب", String(v.source.model)],
      ["الصفحة", v.source.printed_page ? "ص " + v.source.printed_page : (v.source.page ? "مسح " + v.source.page : "—")],
      ["التصنيف", v.classification.verb_type + " · جذر " + v.classification.root_type]];
    facts.forEach(function (p) { var s = document.createElement("span"); s.innerHTML = p[0] + ": <b></b>"; s.querySelector("b").textContent = p[1]; f.appendChild(s); });
    if (v.flags.reduced) f.appendChild(badge("مدغم"));
    if (v.flags.full_passive) f.appendChild(badge("مبني للمجهول كاملًا"));
    d.appendChild(f);

    var cols = COLS.filter(function (c) { return v.conjugation[c[0]] !== null; });
    var wrap = document.createElement("div"); wrap.className = "tablewrap";
    var t = document.createElement("table"); t.className = "conj";
    var thead = t.createTHead(); var hr = thead.insertRow();
    var th0 = document.createElement("th"); hr.appendChild(th0);
    cols.forEach(function (c) { var th = document.createElement("th"); th.textContent = c[1]; hr.appendChild(th); });
    var tb = t.createTBody();
    PERSONS.forEach(function (p) {
      var tr = tb.insertRow();
      var th = document.createElement("th"); th.className = "person"; th.textContent = PERSON_AR[p]; tr.appendChild(th);
      cols.forEach(function (c) {
        var block = v.conjugation[c[0]];
        var applicable = c[0] !== "imp" || p.charAt(0) === "2";
        tr.appendChild(applicable ? td(block[p], c[2]) : td(null));
      });
    });
    wrap.appendChild(t); d.appendChild(wrap);

    if (v.derived) {
      var g = document.createElement("div"); g.className = "derived";
      var items = [["المصدر", v.derived.masdar.join(" ، "), null, false],
        ["اسم الفاعل", v.derived.active_participle, v.derived.status.active_participle, v.derived.read_from_page.active_participle],
        ["اسم المفعول", v.derived.passive_participle, v.derived.status.passive_participle, v.derived.read_from_page.passive_participle]];
      items.forEach(function (it) {
        var box = document.createElement("div");
        var k = document.createElement("div"); k.className = "k"; k.textContent = it[0];
        if (it[2] === "differs-from-module") k.appendChild(badge("يخالف المولِّد", true));
        if (it[2] === "book-only") k.appendChild(badge("في الكتاب فقط"));
        if (it[3]) k.appendChild(badge("قُرئ من الصفحة"));
        var val = document.createElement("div"); val.className = "v"; val.textContent = it[1] || "—";
        box.appendChild(k); box.appendChild(val); g.appendChild(box);
      });
      d.appendChild(g);
    }

    if (state.errata) {
      var notes = [];
      state.errata.deliberately_empty_cells.forEach(function (e) { if (e.id === v.id) notes.push("خانة " + e.column + "/" + e.person + " متروكة عمدًا: " + e.reason); });
      state.errata.corrected_misprints.forEach(function (e) { if (e.id === v.id) notes.push("تصحيح: " + e.column + "/" + e.persons + " المطبوع «" + e.printed + "» والصواب «" + e.corrected + "» — " + e.reason); });
      if (notes.length) { var n = document.createElement("div"); n.className = "errata"; n.innerHTML = "<b>ملاحظات</b><br>" + notes.map(function (s) { return "· " + s.replace(/</g, "&lt;"); }).join("<br>"); d.appendChild(n); }
    }
  }

  function route() {
    var id = decodeURIComponent(location.hash.slice(1));
    var v = state.verbs.filter(function (x) { return x.id === id; })[0];
    state.sel = v ? v.id : null;
    if (v) show(v);
    render();
    var on = document.querySelector("#list li.on"); if (on) on.scrollIntoView({ block: "nearest" });
  }

  function theme(set) {
    var cur = document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    var next = set || (cur === "dark" ? "light" : "dark");
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("ar-conjugation-theme", next); } catch (e) { /* ignore */ }
  }
  try { var saved = localStorage.getItem("ar-conjugation-theme"); if (saved) theme(saved); else if (matchMedia("(prefers-color-scheme: dark)").matches) theme("dark"); } catch (e) { /* ignore */ }
  $("#theme").addEventListener("click", function () { theme(); });

  chips($("#forms"), FORMS.map(function (f) { return [f, f]; }), "form");
  chips($("#classes"), CLASSES, "cls");
  $("#q").addEventListener("input", function (e) { state.q = e.target.value; render(); });
  window.addEventListener("hashchange", route);

  Promise.all([fetch("data/json/verbs.json").then(function (r) { return r.json(); }),
    fetch("data/json/errata.json").then(function (r) { return r.json(); }).catch(function () { return null; })])
    .then(function (res) {
      state.verbs = res[0]; state.errata = res[1];
      $("#n-paradigms").textContent = state.verbs.length;
      route();
    })
    .catch(function (e) { $("#detail").textContent = "تعذّر تحميل البيانات: " + e; });
})();
