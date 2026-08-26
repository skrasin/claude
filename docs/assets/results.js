(function () {
  "use strict";

  var cfg = window.SURVEY_CONFIG || {};
  var out = document.getElementById("out");
  var tip = document.getElementById("tip");
  var KEY_STORE = "massage_results_key";
  var responses = [];

  /* ---------- ключ доступа ---------- */
  function storedKey() {
    var m = /(?:^|[#?&])key=([^&]+)/.exec(location.hash + "&" + location.search);
    if (m) {
      var fromUrl = decodeURIComponent(m[1]);
      try { localStorage.setItem(KEY_STORE, fromUrl); } catch (e) {}
      history.replaceState(null, "", location.pathname);
      return fromUrl;
    }
    try { return localStorage.getItem(KEY_STORE) || ""; } catch (e) { return ""; }
  }

  function askKey(message) {
    out.innerHTML = '<div class="card">'
      + '<div class="sec-head"><h3>Ключ доступа</h3></div>'
      + '<p class="note">' + (message || "Введите слово, которое вы вписали в строку RESULTS_KEY в Apps Script. Оно сохранится в этом браузере.") + '</p>'
      + '<form class="keyform" id="keyform"><input type="password" id="keyinput" autocomplete="current-password" placeholder="Ключ"><button class="btn-ghost" type="submit">Показать результаты</button></form>'
      + '</div>';
    document.getElementById("keyform").addEventListener("submit", function (e) {
      e.preventDefault();
      var v = document.getElementById("keyinput").value.trim();
      if (!v) return;
      try { localStorage.setItem(KEY_STORE, v); } catch (err) {}
      load(v);
    });
  }

  /* ---------- загрузка ---------- */
  function load(key) {
    out.innerHTML = '<div class="card"><p class="loading">Загружаем ответы…</p></div>';
    var url = cfg.endpoint + (cfg.endpoint.indexOf("?") === -1 ? "?" : "&") + "key=" + encodeURIComponent(key);
    fetch(url)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data && data.error === "forbidden") {
          try { localStorage.removeItem(KEY_STORE); } catch (e) {}
          askKey("Ключ не подошёл. Проверьте строку RESULTS_KEY в Apps Script и попробуйте снова.");
          return;
        }
        if (!data || !data.ok) throw new Error("bad_response");
        responses = (data.responses || []).filter(function (r) {
          return r && isFinite(r.q1) && isFinite(r.q2);
        }).sort(function (a, b) { return a.ts - b.ts; });
        render();
      })
      .catch(function () {
        out.innerHTML = '<div class="card"><p class="note warn">Не удалось получить ответы. '
          + 'Проверьте, что веб-приложение Apps Script развёрнуто с доступом «Все» и адрес в assets/config.js верный.</p></div>';
      });
  }

  /* ---------- статистика ---------- */
  function stats() {
    var n = responses.length, d1 = [0, 0, 0, 0, 0], d2 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    var sum = 0, det = 0, pas = 0, pro = 0;
    for (var i = 0; i < n; i++) {
      var a = responses[i];
      if (a.q1 >= 1 && a.q1 <= 5) { d1[a.q1 - 1]++; sum += a.q1; }
      if (a.q2 >= 0 && a.q2 <= 10) {
        d2[a.q2]++;
        if (a.q2 <= 6) det++; else if (a.q2 <= 8) pas++; else pro++;
      }
    }
    var withQ2 = det + pas + pro;
    return {
      n: n, d1: d1, d2: d2, det: det, pas: pas, pro: pro, withQ2: withQ2,
      avg: n ? sum / n : 0,
      nps: withQ2 ? Math.round((pro - det) / withQ2 * 100) : 0
    };
  }
  function pct(part, total) { return total ? Math.round(part / total * 1000) / 10 : 0; }
  function fmtPct(x) { return String(x).replace(".", ",") + "%"; }
  function fmtAvg(x) { return x.toFixed(1).replace(".", ","); }
  function fmtDate(ts) {
    try {
      return new Date(ts).toLocaleString("ru-RU", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
    } catch (e) { return ""; }
  }
  function plural(n, one, few, many) {
    var a = Math.abs(n) % 100, b = a % 10;
    if (a > 10 && a < 20) return many;
    if (b > 1 && b < 5) return few;
    if (b === 1) return one;
    return many;
  }

  /* ---------- отрисовка ---------- */
  function render() {
    var s = stats();
    if (!s.n) {
      out.innerHTML = '<div class="card"><p class="empty">Пока нет ни одного ответа. '
        + 'Как только кто-то заполнит опрос, здесь появятся средняя оценка, распределение и NPS.</p></div>';
      return;
    }

    var maxQ1 = Math.max.apply(null, s.d1.concat([1]));
    var maxQ2 = Math.max.apply(null, s.d2.concat([1]));

    var h = '<div class="stats">'
      + '<div class="stat"><small>Ответов</small><b>' + s.n + '</b><i>всего собрано</i></div>'
      + '<div class="stat"><small>Средняя</small><b>' + fmtAvg(s.avg) + '</b><i>из 5 баллов</i></div>'
      + '<div class="stat"><small>NPS</small><b>' + (s.nps > 0 ? "+" : "") + s.nps + '</b><i>'
      + fmtPct(pct(s.pro, s.withQ2)) + ' промоутеров</i></div></div>';

    var rows = "";
    for (var i = 4; i >= 0; i--) {
      var c = s.d1[i], p = pct(c, s.n);
      rows += '<div class="row">'
        + '<span class="lbl">' + (i + 1) + ' ' + plural(i + 1, "балл", "балла", "баллов") + '</span>'
        + '<div class="track"><div class="fill" style="width:' + (c / maxQ1 * 100) + '%;background:var(--r' + (i + 1) + ')" '
        + 'data-tip="Оценка ' + (i + 1) + ': ' + c + ' — ' + fmtPct(p) + '"></div></div>'
        + '<span class="val">' + c + ' · ' + fmtPct(p) + '</span></div>';
    }
    h += '<div class="card"><div class="sec-head"><h3>Удовлетворённость</h3><span>'
      + s.n + ' ' + plural(s.n, "ответ", "ответа", "ответов") + '</span></div>'
      + '<div class="rows">' + rows + '</div>'
      + '<div class="ends"><span>1 — совсем не понравилось</span><span>5 — всё было прекрасно</span></div></div>';

    var segs = [
      { c: s.det, color: "var(--det)", name: "Критики 0–6" },
      { c: s.pas, color: "var(--pas)", name: "Нейтральные 7–8" },
      { c: s.pro, color: "var(--pro)", name: "Промоутеры 9–10" }
    ];
    var bar = "", leg = "";
    for (var j = 0; j < segs.length; j++) {
      var g = segs[j], gp = pct(g.c, s.withQ2);
      if (g.c) {
        bar += '<div class="nps-seg" style="width:' + (g.c / s.withQ2 * 100) + '%;background:' + g.color + '" '
          + 'data-tip="' + g.name + ': ' + g.c + ' — ' + fmtPct(gp) + '">' + (gp >= 12 ? fmtPct(gp) : "") + '</div>';
      }
      leg += '<span><i style="background:' + g.color + '"></i>' + g.name + ' — ' + g.c + ' (' + fmtPct(gp) + ')</span>';
    }
    var cols = "";
    for (var k = 0; k < 11; k++) {
      var cc = s.d2[k];
      var col = k <= 6 ? "var(--det)" : (k <= 8 ? "var(--pas)" : "var(--pro)");
      cols += '<div class="col"><div class="bar" style="height:' + (cc / maxQ2 * 100) + '%;background:' + col
        + ';opacity:' + (cc ? 1 : .22) + '" data-tip="Оценка ' + k + ': ' + cc + ' ' + plural(cc, "ответ", "ответа", "ответов") + '"></div>'
        + '<span class="tick">' + k + '</span></div>';
    }
    h += '<div class="card"><div class="sec-head"><h3>Готовность рекомендовать</h3><span>NPS '
      + (s.nps > 0 ? "+" : "") + s.nps + '</span></div>'
      + '<div class="nps-bar">' + bar + '</div><div class="legend">' + leg + '</div>'
      + '<div class="cols">' + cols + '</div></div>';

    var last = responses.slice(-25).reverse(), trs = "";
    for (var m = 0; m < last.length; m++) {
      var a = last[m];
      var grp = a.q2 <= 6 ? ["var(--det)", "критик"] : (a.q2 <= 8 ? ["var(--pas)", "нейтрал"] : ["var(--pro)", "промоутер"]);
      trs += '<tr><td class="num">' + fmtDate(a.ts) + '</td><td class="num">' + a.q1 + ' / 5</td>'
        + '<td class="num">' + a.q2 + ' / 10</td>'
        + '<td><span class="chip" title="' + grp[1] + '"><i style="background:' + grp[0] + '"></i>' + grp[1] + '</span></td></tr>';
    }
    h += '<div class="card"><div class="sec-head"><h3>Последние ответы</h3><span>' + last.length + ' из ' + s.n + '</span></div>'
      + '<div class="tablewrap"><table><thead><tr><th>Когда</th><th>Оценка</th><th>Реком.</th><th></th></tr></thead>'
      + '<tbody>' + trs + '</tbody></table></div>'
      + '<div class="actions"><button class="btn-ghost" id="csv">Скачать все ответы (CSV)</button></div></div>';

    out.innerHTML = h;
    document.getElementById("csv").addEventListener("click", downloadCsv);
  }

  function downloadCsv() {
    var lines = ["Дата;Удовлетворённость (1-5);Готовность рекомендовать (0-10)"];
    for (var i = 0; i < responses.length; i++) {
      var a = responses[i];
      lines.push([new Date(a.ts).toISOString(), a.q1, a.q2].join(";"));
    }
    var blob = new Blob(["﻿" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "massage-survey.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  /* ---------- подсказки на графиках ---------- */
  document.addEventListener("mouseover", function (e) {
    var el = e.target.closest("[data-tip]");
    if (!el) return;
    tip.textContent = el.getAttribute("data-tip");
    tip.classList.add("on");
    moveTip(e);
  });
  document.addEventListener("mousemove", function (e) { if (tip.classList.contains("on")) moveTip(e); });
  document.addEventListener("mouseout", function (e) { if (e.target.closest("[data-tip]")) tip.classList.remove("on"); });
  function moveTip(e) {
    tip.style.left = Math.min(e.clientX + 14, window.innerWidth - tip.offsetWidth - 8) + "px";
    tip.style.top = Math.max(e.clientY - tip.offsetHeight - 12, 8) + "px";
  }

  /* ---------- старт ---------- */
  if (!cfg.endpoint) {
    out.innerHTML = '<div class="card"><div class="setup">Опрос ещё не подключён к таблице. '
      + 'Впишите адрес веб-приложения Apps Script в <code>assets/config.js</code> — как его получить, '
      + 'написано в <code>SURVEY-SETUP.md</code>.</div></div>';
  } else {
    var k = storedKey();
    if (k) load(k); else askKey();
  }
})();
