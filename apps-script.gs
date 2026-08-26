/**
 * Приём ответов опроса «Как прошёл массаж» и выдача их странице результатов.
 *
 * Куда вставлять: откройте Google-таблицу с ответами →
 * Расширения → Apps Script → замените всё содержимое Code.gs на этот файл.
 * Пошаговая инструкция — в SURVEY-SETUP.md.
 *
 * После правки кода обязательно выпустите новую версию:
 * Начать развёртывание → Управление развёртываниями → Изменить (карандаш) →
 * Версия: Новая версия → Развернуть. Адрес /exec при этом не меняется.
 */

/** Слово-ключ для страницы результатов. Замените на своё. */
var RESULTS_KEY = 'ЗАМЕНИТЕ-НА-СВОЁ-СЛОВО';

/** Максимальная длина комментария, символов. */
var MAX_COMMENT = 2000;

var HEADER = ['Дата', 'Удовлетворённость (1-5)', 'Готовность рекомендовать (0-10)', 'ID', 'Комментарий'];

/** Приём одного ответа из формы опроса. */
function doPost(e) {
  try {
    var body = JSON.parse(e.postData.contents);
    var q1 = Number(body.q1);
    var q2 = Number(body.q2);

    var ok1 = q1 >= 1 && q1 <= 5 && q1 === Math.round(q1);
    var ok2 = q2 >= 0 && q2 <= 10 && q2 === Math.round(q2);
    if (!ok1 || !ok2) return json({ ok: false, error: 'bad_values' });

    var comment = body.comment == null ? '' : String(body.comment).slice(0, MAX_COMMENT);

    var lock = LockService.getScriptLock();
    lock.waitLock(15000);
    try {
      var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
      ensureHeader(sheet);
      sheet.appendRow([new Date(), q1, q2, String(body.id || ''), comment]);
    } finally {
      lock.releaseLock();
    }
    return json({ ok: true });
  } catch (err) {
    return json({ ok: false, error: String(err) });
  }
}

/** Выдача всех ответов странице результатов — только по ключу. */
function doGet(e) {
  var key = e && e.parameter ? e.parameter.key : '';
  if (key !== RESULTS_KEY) return json({ ok: false, error: 'forbidden' });

  var values = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0].getDataRange().getValues();
  var rows = [];
  for (var i = 1; i < values.length; i++) {
    var r = values[i];
    if (r[1] === '' || r[1] === null) continue;
    var when = r[0] instanceof Date ? r[0].getTime() : new Date(r[0]).getTime();
    rows.push({
      ts: when,
      q1: Number(r[1]),
      q2: Number(r[2]),
      comment: r[4] == null ? '' : String(r[4])
    });
  }
  return json({ ok: true, responses: rows });
}

/** Шапка таблицы: дописываем колонку «Комментарий», если её ещё нет. */
function ensureHeader(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADER);
    return;
  }
  if (!sheet.getRange(1, 5).getValue()) {
    sheet.getRange(1, 5).setValue(HEADER[4]);
  }
}

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
