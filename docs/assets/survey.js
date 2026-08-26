(function () {
  "use strict";

  var cfg = window.SURVEY_CONFIG || {};
  var form = document.getElementById("form");
  var note = document.getElementById("note");
  var send = document.getElementById("send");
  var cardForm = document.getElementById("card-form");
  var cardThanks = document.getElementById("card-thanks");
  var DEFAULT_NOTE = "Ответ анонимный — сохраняем только две оценки и время.";

  /* шкалы */
  function buildScale(el, name, from, to) {
    var html = "";
    for (var v = from; v <= to; v++) {
      html += '<label class="opt"><input type="radio" name="' + name + '" value="' + v + '">'
        + '<span>' + v + '</span></label>';
    }
    el.innerHTML = html;
  }
  buildScale(document.getElementById("scale1"), "q1", 1, 5);
  buildScale(document.getElementById("scale2"), "q2", 0, 10);

  function picked(name) {
    var el = form.querySelector('input[name="' + name + '"]:checked');
    return el ? Number(el.value) : null;
  }
  function say(text, bad) {
    note.textContent = text;
    note.className = bad ? "note warn" : "note";
  }
  function uid() {
    return Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 9);
  }

  form.addEventListener("change", function () {
    if (note.classList.contains("warn")) say(DEFAULT_NOTE, false);
  });

  document.getElementById("again").addEventListener("click", function () {
    form.reset();
    cardThanks.classList.add("hidden");
    cardForm.classList.remove("hidden");
    say(DEFAULT_NOTE, false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (send.disabled) return;

    var q1 = picked("q1"), q2 = picked("q2");
    if (q1 === null) { say("Выберите оценку в первом вопросе.", true); return; }
    if (q2 === null) { say("Выберите оценку во втором вопросе.", true); return; }

    if (!cfg.endpoint) {
      say("Опрос ещё не подключён к таблице: заполните endpoint в assets/config.js.", true);
      return;
    }

    send.disabled = true;
    send.textContent = "Отправляем…";
    say(DEFAULT_NOTE, false);

    var payload = { id: uid(), q1: q1, q2: q2 };

    fetch(cfg.endpoint, {
      method: "POST",
      /* text/plain — чтобы браузер не слал preflight, который Apps Script не принимает */
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify(payload)
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data || !data.ok) throw new Error((data && data.error) || "save_failed");
        cardForm.classList.add("hidden");
        cardThanks.classList.remove("hidden");
        window.scrollTo({ top: 0, behavior: "smooth" });
      })
      .catch(function () {
        say("Не получилось отправить ответ. Проверьте связь и нажмите ещё раз.", true);
      })
      .then(function () {
        send.disabled = false;
        send.textContent = "Отправить отзыв";
      });
  });
})();
