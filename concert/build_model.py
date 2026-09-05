# -*- coding: utf-8 -*-
"""
Финансовая модель концерта (клубный формат, 150-400 мест).
Схема сделки: раздел прибыли 50/50 с площадкой, налоговая нагрузка УСН 6% + взносы 1% + банк 1%
на двух уровнях (валовой сбор и выплата организатору).
Все расчётные ячейки — формулы Excel, файл пересчитывается при изменении вводных.
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, NamedStyle
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule, FormulaRule
from openpyxl.worksheet.datavalidation import DataValidation

# ---------------------------------------------------------------- стиль
FONT = 'Arial'
RUB   = '#,##0" ₽";[Red](#,##0" ₽");"—"'
RUB2  = '#,##0.00" ₽";[Red](#,##0.00" ₽");"—"'
PCT   = '0.0%'
INT   = '#,##0;[Red](#,##0);"—"'

C_INPUT  = '0000FF'      # синий  — вводные
C_CALC   = '000000'      # чёрный — формулы
C_LINK   = '008000'      # зелёный — ссылка на другой лист
C_MUTED  = '808080'

F_HEAD   = PatternFill('solid', fgColor='1F3864')   # тёмно-синяя шапка
F_SUB    = PatternFill('solid', fgColor='D9E2F3')   # подзаголовок блока
F_KEY    = PatternFill('solid', fgColor='FFF2CC')   # ключевое допущение (жёлтый)
F_TOTAL  = PatternFill('solid', fgColor='E2EFDA')   # итог
F_RESULT = PatternFill('solid', fgColor='FCE4D6')   # финальный результат
F_ZEBRA  = PatternFill('solid', fgColor='F7F9FC')

THIN = Side(style='thin', color='BFBFBF')
MED  = Side(style='medium', color='1F3864')
BOX  = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
TOPLINE = Border(top=Side(style='thin', color='1F3864'))

wb = openpyxl.Workbook()

def title(ws, text, sub=None, width=8):
    ws['A1'] = text
    ws['A1'].font = Font(name=FONT, size=15, bold=True, color='FFFFFF')
    ws['A1'].fill = F_HEAD
    ws['A1'].alignment = Alignment(vertical='center')
    ws.row_dimensions[1].height = 30
    for c in range(1, width + 1):
        ws.cell(1, c).fill = F_HEAD
    if sub:
        ws['A2'] = sub
        ws['A2'].font = Font(name=FONT, size=9, italic=True, color=C_MUTED)

def block(ws, row, text, width=8):
    ws.cell(row, 1, text).font = Font(name=FONT, size=11, bold=True, color='1F3864')
    for c in range(1, width + 1):
        ws.cell(row, c).fill = F_SUB
        ws.cell(row, c).border = Border(bottom=Side(style='thin', color='1F3864'))
    ws.row_dimensions[row].height = 20

def hdr(ws, row, headers, start=1):
    for i, h in enumerate(headers):
        c = ws.cell(row, start + i, h)
        c.font = Font(name=FONT, size=9, bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='4472C4')
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = BOX
    ws.row_dimensions[row].height = 30

def widths(ws, spec):
    for col, w in spec.items():
        ws.column_dimensions[col].width = w

def put(ws, row, label_text, value, fmt=None, kind='calc', note=None, col=2, indent=0):
    """kind: input | calc | link | text"""
    lc = ws.cell(row, 1, label_text)
    lc.font = Font(name=FONT, size=10)
    lc.alignment = Alignment(indent=indent)
    c = ws.cell(row, col, value)
    color = {'input': C_INPUT, 'calc': C_CALC, 'link': C_LINK, 'text': C_INPUT}[kind]
    c.font = Font(name=FONT, size=10, color=color, bold=(kind == 'calc' and fmt == RUB))
    if fmt:
        c.number_format = fmt
    if kind in ('input', 'text'):
        c.fill = F_KEY
    c.border = BOX
    if note:
        ws.cell(row, col + 1, note).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
    return c

# ================================================================ 1. ВВОДНЫЕ
ws = wb.active
ws.title = 'Вводные'
V = {}
title(ws, 'ВВОДНЫЕ ДАННЫЕ И ДОПУЩЕНИЯ',
      'Синие ячейки на жёлтом фоне — вводные, их можно и нужно менять. Чёрные — формулы, их менять не нужно. Зелёные — ссылки на другие листы.')
widths(ws, {'A': 52, 'B': 18, 'C': 64})

r = 4
block(ws, 4, '1. ПАРАМЕТРЫ СОБЫТИЯ')
r = 5
for lab, val, key in [
    ('Название концерта', '— укажите название —', 'name'),
    ('Артист / состав', '— укажите —', 'artist'),
    ('Дата и время', '— ДД.ММ.ГГГГ, 20:00 —', 'date'),
    ('Площадка', '— клуб —', 'venue'),
    ('Город', '— город —', 'city'),
]:
    put(ws, r, lab, val, kind='text'); V[key] = f"Вводные!$B${r}"; r += 1

r += 1
block(ws, r, '2. ЗАЛ И ПОСЕЩАЕМОСТЬ'); r += 1
put(ws, r, 'Вместимость зала, чел.', 300, INT, 'input',
    'Клубный формат. Поставьте реальную вместимость по договору с площадкой')
V['cap'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'Заполняемость — пессимистичный сценарий', 0.40, PCT, 'input',
    'Слабый промо, плохая погода, конкурирующее событие в городе')
V['fill_pess'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'Заполняемость — оптимистичный сценарий', 0.90, PCT, 'input')
V['fill_opt'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'Заполняемость — аншлаг', 1.00, PCT, 'input',
    'Базовый сценарий берётся с листа «Билеты» — там задана покатегорийная продажа')
V['fill_full'] = f"Вводные!$B${r}"; r += 1

r += 1
block(ws, r, '3. БИЛЕТНАЯ ПРОДАЖА'); r += 1
c = put(ws, r, 'Схема сервисного сбора (1 или 2)', 2, INT, 'input',
    '1 = сбор платит покупатель сверх цены (вам — полная цена) · 2 = комиссия удерживается из цены (расход организатора)')
c.comment = Comment('Схема 1 выгоднее организатору, но повышает итоговую цену для зрителя и снижает конверсию.\nСхема 2 — чаще встречается в договорах с билетными операторами.', 'model', width=380, height=90)
V['mode'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'Комиссия билетного оператора, %', 0.10, PCT, 'input',
    'Рынок: 5–12% от номинала. Уточните в договоре с оператором')
V['comm'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'Доля продаж на входе / напрямую, %', 0.15, PCT, 'input',
    'На эту часть комиссия оператора не начисляется')
V['offline'] = f"Вводные!$B${r}"; r += 1

r += 1
block(ws, r, '4. НАЛОГИ, СБОРЫ И ОТЧИСЛЕНИЯ'); r += 1
ws.cell(r, 1, 'УРОВЕНЬ 1 — с валового сбора (до раздела прибыли)').font = Font(name=FONT, size=10, bold=True, color='1F3864'); r += 1
c = put(ws, r, 'УСН «доходы», %', 0.06, PCT, 'input',
    'На первом уровне удерживается только УСН 6%', indent=1)
c.comment = Comment('По условиям сделки на уровне валового сбора удерживается только УСН 6%.\nСтраховые взносы и банковские комиссии учитываются на втором уровне — при выплате доли организатору.', 'model', width=400, height=90)
V['usn1'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'ИТОГО фискальная нагрузка, уровень 1', f"={V['usn1']}", PCT, 'calc',
    'Удерживается с валового сбора до вычета расходов и раздела прибыли', indent=1)
ws.cell(r, 1).font = Font(name=FONT, size=10, bold=True)
ws.cell(r, 2).fill = F_TOTAL
V['t1'] = f"Вводные!$B${r}"; r += 1
c = put(ws, r, 'Отчисления в РАО, %', 0.05, PCT, 'input',
    'Стандартная ставка для концертов — 5% от валового сбора', indent=1)
c.comment = Comment('РАО взимает ставку с валового сбора от продажи билетов за публичное исполнение произведений.\nЕсли исполняются только собственные произведения или произведения в общественном достоянии, ставку можно снизить или обнулить — см. лист «Варианты».\nСтавку нужно подтвердить в договоре с РАО.', 'model', width=400, height=130)
V['rao'] = f"Вводные!$B${r}"; r += 2

ws.cell(r, 1, 'УРОВЕНЬ 2 — с выплаты доли прибыли организатору').font = Font(name=FONT, size=10, bold=True, color='1F3864'); r += 1
put(ws, r, 'УСН «доходы» с выплаты, %', 0.06, PCT, 'input', indent=1); V['usn2'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'Страховые взносы (1% с дохода), %', 0.01, PCT, 'input', indent=1); V['vzn'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'Банковские комиссии / эквайринг, %', 0.01, PCT, 'input', indent=1); V['bank'] = f"Вводные!$B${r}"; r += 1
c = ws.cell(r, 2, f"={V['usn2']}+{V['vzn']}+{V['bank']}")
lc = ws.cell(r, 1, 'ИТОГО фискальная нагрузка, уровень 2')
lc.font = Font(name=FONT, size=10, bold=True); lc.alignment = Alignment(indent=1)
c.number_format = PCT; c.font = Font(name=FONT, size=10, bold=True); c.fill = F_TOTAL; c.border = BOX
ws.cell(r, 3, '6% + 1% + 1% = 8% — удерживается с выплаты прибыли по договору с площадкой').font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
V['t2'] = f"Вводные!$B${r}"; r += 1

r += 1
block(ws, r, '5. РАЗДЕЛ ПРИБЫЛИ С ПЛОЩАДКОЙ'); r += 1
put(ws, r, 'Доля организатора в прибыли, %', 0.50, PCT, 'input')
V['share'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'Доля площадки в прибыли, %', f"=1-{V['share']}", PCT, 'calc')
V['share_v'] = f"Вводные!$B${r}"; r += 1
c = put(ws, r, 'Убыток делится с площадкой? (Да/Нет)', 'Нет', None, 'text',
    'КРИТИЧНО: если «Нет» — весь убыток на вас. Пропишите это в договоре явно')
c.comment = Comment('Самая частая ловушка в сделках 50/50: прибыль делится пополам, а убыток — нет.\nЕсли площадка не делит убыток, ваш риск асимметричен: выше точки безубыточности вы получаете 50%, ниже — теряете 100%.', 'model', width=420, height=110)
V['loss'] = f"Вводные!$B${r}"
dv = DataValidation(type='list', formula1='"Да,Нет"', allow_blank=False)
ws.add_data_validation(dv); dv.add(ws.cell(r, 2)); r += 1
c = put(ws, r, 'Доп. доходы участвуют в разделе? (Да/Нет)', 'Нет', None, 'text',
    'Мерч, спонсорство, донаты — обычно остаются у организатора целиком')
V['extra_split'] = f"Вводные!$B${r}"
dv2 = DataValidation(type='list', formula1='"Да,Нет"', allow_blank=False)
ws.add_data_validation(dv2); dv2.add(ws.cell(r, 2)); r += 1

r += 1
block(ws, r, '6. ПРОЧЕЕ'); r += 1
put(ws, r, 'Переменные расходы на гостя, ₽', 60, RUB, 'input',
    'Браслет, печать билета, гардеробный номерок, вода')
V['perguest'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'Резерв на непредвиденное, % от сметы', 0.10, PCT, 'input',
    'Ниже 10% ставить не рекомендую — всегда вылезает что-то неучтённое')
V['reserve'] = f"Вводные!$B${r}"; r += 1

ws.freeze_panes = 'A4'

# ================================================================ 2. БИЛЕТЫ
ws = wb.create_sheet('Билеты')
B = {}
title(ws, 'БИЛЕТНАЯ МАТРИЦА И ДОПОЛНИТЕЛЬНЫЕ ДОХОДЫ',
      'Базовый сценарий строится именно здесь: задайте цены, квоты мест и ожидаемый процент продажи по каждой категории.')
widths(ws, {'A': 40, 'B': 13, 'C': 12, 'D': 14, 'E': 12, 'F': 16, 'G': 11, 'H': 56})

block(ws, 4, 'СТРУКТУРА БИЛЕТОВ')
hdr(ws, 5, ['Категория билета', 'Цена, ₽', 'Квота, мест', 'Ожид. продажа, %',
            'Продано, шт', 'Валовой сбор, ₽', 'Доля в сборе', 'Комментарий'])

tickets = [
    ('Ранняя пташка (early bird)',            1800,  60, 0.95, 'Первые 2 недели, ограниченная квота. Даёт ранний денежный поток на маркетинг'),
    ('Стандарт (предпродажа)',                2500, 150, 0.60, 'Основная квота зала'),
    ('Стандарт (на входе, в день концерта)',  2800,  40, 0.50, 'Цена на входе выше — это стимул покупать заранее'),
    ('Фан-зона у сцены / VIP',                4000,  30, 0.60, 'Первые ряды, отдельный вход, мерч в подарок'),
    ('Льготный (студенты)',                   1500,  10, 0.70, 'Заполняет зал и даёт социальный охват'),
    ('Промо, пресс, гости артиста',              0,  10, 1.00, 'Денег не приносят, но занимают места и создают переменные расходы'),
]
R0 = 6
for i, (name, price, quota, sell, note) in enumerate(tickets):
    r = R0 + i
    ws.cell(r, 1, name).font = Font(name=FONT, size=10)
    for col, val, fmt in ((2, price, RUB), (3, quota, INT), (4, sell, PCT)):
        c = ws.cell(r, col, val); c.number_format = fmt
        c.font = Font(name=FONT, size=10, color=C_INPUT); c.fill = F_KEY
    ws.cell(r, 5, f'=ROUND(C{r}*D{r},0)').number_format = INT
    ws.cell(r, 6, f'=B{r}*E{r}').number_format = RUB
    ws.cell(r, 7, f'=IFERROR(F{r}/$F${R0+len(tickets)},0)').number_format = PCT
    ws.cell(r, 8, note).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
    for col in range(1, 9):
        ws.cell(r, col).border = BOX
        if col in (5, 6, 7):
            ws.cell(r, col).font = Font(name=FONT, size=10)
RT = R0 + len(tickets)
ws.cell(RT, 1, 'ИТОГО').font = Font(name=FONT, size=10, bold=True)
for col, f in ((3, f'=SUM(C{R0}:C{RT-1})'), (5, f'=SUM(E{R0}:E{RT-1})'),
               (6, f'=SUM(F{R0}:F{RT-1})'), (7, f'=SUM(G{R0}:G{RT-1})')):
    c = ws.cell(RT, col, f)
    c.number_format = {3: INT, 5: INT, 6: RUB, 7: PCT}[col]
    c.font = Font(name=FONT, size=10, bold=True)
for col in range(1, 9):
    ws.cell(RT, col).fill = F_TOTAL; ws.cell(RT, col).border = BOX

B['gross']  = f"Билеты!$F${RT}"
B['sold']   = f"Билеты!$E${RT}"
B['quotas'] = f"Билеты!$C${RT}"

r = RT + 2
block(ws, r, 'КОНТРОЛЬНЫЕ ПОКАЗАТЕЛИ'); r += 1
put(ws, r, 'Проверка: сумма квот = вместимость зала?',
    f'=IF({B["quotas"]}={V["cap"]},"OK — квоты сходятся с залом","ВНИМАНИЕ: квоты ("&{B["quotas"]}&") ≠ вместимость ("&{V["cap"]}&")")',
    None, 'calc'); ws.cell(r, 2).font = Font(name=FONT, size=10, bold=True); r += 1
put(ws, r, 'Продано билетов всего, шт', f'={B["sold"]}', INT, 'link'); r += 1
put(ws, r, '   в т.ч. платных, шт', f'=SUMIF(B{R0}:B{RT-1},">0",E{R0}:E{RT-1})', INT)
B['paid'] = f"Билеты!$B${r}"; r += 1
put(ws, r, '   в т.ч. бесплатных (промо, пресс), шт', f'={B["sold"]}-{B["paid"]}', INT); r += 1
put(ws, r, 'Валовой сбор (box office), ₽', f'={B["gross"]}', RUB, 'link'); r += 1
put(ws, r, 'Средняя цена платного билета, ₽', f'=IFERROR({B["gross"]}/{B["paid"]},0)', RUB)
B['avg'] = f"Билеты!$B${r}"; r += 1
put(ws, r, 'Доход на одно место зала (yield), ₽', f'=IFERROR({B["gross"]}/{V["cap"]},0)', RUB,
    note='Ключевая метрика для сравнения площадок и форматов'); r += 1
put(ws, r, 'Фактическая заполняемость зала, %', f'=IFERROR({B["sold"]}/{V["cap"]},0)', PCT)
B['fill_base'] = f"Билеты!$B${r}"; r += 1
put(ws, r, 'Доля платных билетов от всех проходов, %', f'=IFERROR({B["paid"]}/{B["sold"]},0)', PCT)
B['paid_share'] = f"Билеты!$B${r}"; r += 1

r += 1
block(ws, r, 'ДОПОЛНИТЕЛЬНЫЕ ДОХОДЫ (не билетные)'); r += 1
hdr(ws, r, ['Источник дохода', 'База (шт / ₽)', 'Ставка, чек, ₽', 'Маржа / доля, %',
            'Доход, ₽', '', '', 'Комментарий'])
E0 = r + 1
extras = [
    ('Мерч: футболки, винил, значки',   30,   2000, 0.55, 'Конверсия в мерч 10–20% зала. Продаётся до концерта и на выходе'),
    ('Доля от выручки бара',             1, 250000, 0.10, 'Часто 10–20% бара. Обязательно прописать в договоре с площадкой'),
    ('Спонсорский пакет / партнёр',      1,      0, 1.00, 'Поставьте сумму, если есть партнёр. Самый недооценённый источник — см. лист «Варианты»'),
    ('Донаты, краудфандинг, предзаказ',  1,      0, 1.00, 'Сбор до концерта закрывает кассовый разрыв на предоплаты'),
    ('Съёмка концерта: релиз, стриминг', 1,      0, 1.00, 'Доход приходит после события — учитывайте отдельно по срокам'),
]
for i, (name, base, rate, marg, note) in enumerate(extras):
    rr = E0 + i
    ws.cell(rr, 1, name).font = Font(name=FONT, size=10)
    for col, val, fmt in ((2, base, INT), (3, rate, RUB), (4, marg, PCT)):
        c = ws.cell(rr, col, val); c.number_format = fmt
        c.font = Font(name=FONT, size=10, color=C_INPUT); c.fill = F_KEY
    ws.cell(rr, 5, f'=B{rr}*C{rr}*D{rr}').number_format = RUB
    ws.cell(rr, 8, note).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
    for col in range(1, 9):
        ws.cell(rr, col).border = BOX
ET = E0 + len(extras)
ws.cell(ET, 1, 'ИТОГО дополнительных доходов').font = Font(name=FONT, size=10, bold=True)
c = ws.cell(ET, 5, f'=SUM(E{E0}:E{ET-1})'); c.number_format = RUB
c.font = Font(name=FONT, size=10, bold=True)
for col in range(1, 9):
    ws.cell(ET, col).fill = F_TOTAL; ws.cell(ET, col).border = BOX
B['extra'] = f"Билеты!$E${ET}"
ws.freeze_panes = 'A6'

# ================================================================ 3. МАРКЕТИНГ И PR
ws = wb.create_sheet('Маркетинг')
M = {}
title(ws, 'МАРКЕТИНГ И PR: БЮДЖЕТ, ВОРОНКА, СТОИМОСТЬ БИЛЕТА',
      'Каждый канал считается до билета: охват → отклик → покупка. Так видно, какой канал реально продаёт, а какой только тратит.')
widths(ws, {'A': 40, 'B': 14, 'C': 14, 'D': 13, 'E': 14, 'F': 14, 'G': 14, 'H': 54})

block(ws, 4, 'КАНАЛЫ ПРОДВИЖЕНИЯ')
hdr(ws, 5, ['Канал', 'Бюджет, ₽', 'Прогноз охвата, чел.', 'Отклик (CTR), %',
            'Конверсия в покупку, %', 'Прогноз билетов, шт', 'CPA, ₽ за билет', 'Комментарий'])
MR0 = 6
channels = [
    ('Таргетированная реклама VK',            25000, 120000, 0.012, 0.030, 'Основной платный канал в РФ. Гео + интересы + look-alike по базе'),
    ('Посевы в Telegram-каналах',             20000,  60000, 0.020, 0.040, 'Городские и жанровые каналы. Просите статистику охватов до оплаты'),
    ('Блогеры и лидеры мнений',               15000,  40000, 0.025, 0.035, 'Часть работает по бартеру за билеты — снижает бюджет'),
    ('Наружная реклама и расклейка афиш',     10000,  30000, 0.005, 0.050, 'Работает на узнавание, плохо атрибутируется. Отдельный промокод обязателен'),
    ('Городские афиши: Яндекс.Афиша, KudaGo',     0,  25000, 0.010, 0.040, 'Бесплатное размещение. Подавать за 3–4 недели'),
    ('PR: пресс-релиз, СМИ, интервью',         8000,  20000, 0.010, 0.030, 'Даёт доверие и вторичные перепечатки, а не прямые продажи'),
    ('Email и база подписчиков',               2000,   5000, 0.120, 0.080, 'Самый дешёвый билет. Базу надо собирать с прошлых концертов'),
    ('Продакшн контента: дизайн, тизер, фото',10000,      0, 0.000, 0.000, 'Не продаёт напрямую, но без него не работают все каналы выше'),
]
for i, (name, budget, reach, ctr, conv, note) in enumerate(channels):
    r = MR0 + i
    ws.cell(r, 1, name).font = Font(name=FONT, size=10)
    for col, val, fmt in ((2, budget, RUB), (3, reach, INT), (4, ctr, '0.00%'), (5, conv, '0.00%')):
        c = ws.cell(r, col, val); c.number_format = fmt
        c.font = Font(name=FONT, size=10, color=C_INPUT); c.fill = F_KEY
    ws.cell(r, 6, f'=ROUND(C{r}*D{r}*E{r},0)').number_format = INT
    ws.cell(r, 7, f'=IFERROR(B{r}/F{r},0)').number_format = RUB
    ws.cell(r, 8, note).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
    for col in range(1, 9):
        ws.cell(r, col).border = BOX
MT = MR0 + len(channels)
ws.cell(MT, 1, 'ИТОГО МАРКЕТИНГ И PR').font = Font(name=FONT, size=11, bold=True)
for col, f, fmt in ((2, f'=SUM(B{MR0}:B{MT-1})', RUB), (3, f'=SUM(C{MR0}:C{MT-1})', INT),
                    (6, f'=SUM(F{MR0}:F{MT-1})', INT), (7, f'=IFERROR(B{MT}/F{MT},0)', RUB)):
    c = ws.cell(MT, col, f); c.number_format = fmt
    c.font = Font(name=FONT, size=11, bold=True)
for col in range(1, 9):
    ws.cell(MT, col).fill = F_TOTAL; ws.cell(MT, col).border = BOX
M['budget']  = f"Маркетинг!$B${MT}"
M['tickets'] = f"Маркетинг!$F${MT}"
M['cpa']     = f"Маркетинг!$G${MT}"

r = MT + 2
block(ws, r, 'ПРОВЕРКА ЗДОРОВЬЯ МАРКЕТИНГА'); r += 1
put(ws, r, 'Бюджет маркетинга и PR, ₽', f'={M["budget"]}', RUB, 'link'); r += 1
put(ws, r, 'Прогноз билетов от маркетинга, шт', f'={M["tickets"]}', INT, 'link'); r += 1
put(ws, r, 'План продаж по билетной матрице, шт', f'={B["paid"]}', INT, 'link'); r += 1
put(ws, r, 'Покрытие плана продаж маркетингом, %', f'=IFERROR({M["tickets"]}/{B["paid"]},0)', PCT,
    note='Ниже 100% — план продаж ничем не обеспечен. Выше 130% — можно снять часть бюджета')
COV = f"Маркетинг!$B${r}"; r += 1
put(ws, r, 'Средний CPA (стоимость привлечения билета), ₽', f'={M["cpa"]}', RUB, 'link'); r += 1
put(ws, r, 'Средняя цена платного билета, ₽', f'={B["avg"]}', RUB, 'link'); r += 1
put(ws, r, 'CPA к цене билета, %', f'=IFERROR({M["cpa"]}/{B["avg"]},0)', PCT,
    note='Здоровый диапазон — до 25%. Выше 35% — канальная модель не сходится'); r += 1
put(ws, r, 'Доля маркетинга в валовом сборе, %', f'=IFERROR({M["budget"]}/{B["gross"]},0)', PCT,
    note='Ориентир для клубного концерта — 10–15%. Выше 20% — бюджет съедает прибыль')
MSHARE = f"Маркетинг!$B${r}"; r += 1
put(ws, r, 'Вердикт', 
    f'=IF({MSHARE}>0.2,"ПЕРЕРАСХОД: маркетинг забирает больше 20% сбора",'
    f'IF({COV}<1,"РИСК: маркетинг не покрывает план продаж","Норма: бюджет и план продаж сбалансированы"))',
    None, 'calc')
ws.cell(r, 2).font = Font(name=FONT, size=10, bold=True)
ws.conditional_formatting.add(f'B{r}', FormulaRule(
    formula=[f'$B${r}<>"Норма: бюджет и план продаж сбалансированы"'],
    fill=PatternFill('solid', fgColor='FFC7CE'), font=Font(color='9C0006', bold=True)))
ws.freeze_panes = 'A6'

# ================================================================ 4. РАСХОДЫ (СМЕТА)
ws = wb.create_sheet('Расходы')
X = {}
title(ws, 'СМЕТА РАСХОДОВ',
      'Столбец «Оплачивает» решает всё: строки со значением «Площадка» показаны по рыночной цене, но в ваши расходы не попадают. Так видно реальный вклад площадки в сделку 50/50.')
widths(ws, {'A': 44, 'B': 9, 'C': 10, 'D': 15, 'E': 16, 'F': 15, 'G': 58})

dv_pay = DataValidation(type='list', formula1='"Организатор,Площадка"', allow_blank=False)
ws.add_data_validation(dv_pay)

blocks = [
    ('1. ПЛОЩАДКА И ТЕХНИЧЕСКОЕ ОБЕСПЕЧЕНИЕ', [
        ('Аренда зала (смена)',                     1, 'смена',  60000, 'Площадка',   'При сделке 50/50 аренда не выставляется — это вклад площадки'),
        ('Доп. часы: монтаж и саундчек',            4, 'час',     5000, 'Площадка',   'Обычно входит в смену. Обязательно уточните в договоре'),
        ('Звуковой комплект PA',                    1, 'компл.', 45000, 'Площадка',   'Штатный аппарат клуба'),
        ('Доп. микрофоны, радиосистемы, стойки',    1, 'компл.', 12000, 'Организатор','Под конкретный состав почти всегда докупается в аренду'),
        ('Мониторная линия / in-ear',               1, 'компл.', 15000, 'Организатор','Критично для качества исполнения на сцене'),
        ('Звукорежиссёр FOH (свой)',                1, 'смена',  20000, 'Организатор','Свой инженер — предсказуемый звук. Клубный — лотерея'),
        ('Мониторный инженер',                      1, 'смена',  12000, 'Площадка',   'В клубе часто совмещается с FOH'),
        ('Световое оборудование',                   1, 'компл.', 25000, 'Площадка',   'Штатный свет клуба'),
        ('Художник по свету / оператор',            1, 'смена',  12000, 'Организатор','Свет под программу, а не «дискотека по кнопке»'),
        ('Бэклайн: барабаны, усилители, клавиши',   1, 'компл.', 20000, 'Организатор','По техническому райдеру'),
        ('Экран, проекция, видеоконтент',           0, 'компл.', 18000, 'Организатор','Поставьте количество 1, если в программе есть видеоряд'),
        ('Электрика, кабели, распределение',        1, 'компл.',  5000, 'Площадка',   ''),
        ('Монтаж, демонтаж, погрузка',              3, 'чел.',    4000, 'Организатор','Разгрузка и погрузка бэклайна'),
    ]),
    ('2. ПЕРСОНАЛ И ОБСЛУЖИВАНИЕ', [
        ('Администратор площадки',                  1, 'смена',  10000, 'Площадка',   ''),
        ('Билетный контроль',                       2, 'чел.',    4000, 'Площадка',   ''),
        ('Гардероб',                                2, 'чел.',    3500, 'Площадка',   ''),
        ('Охрана',                                  4, 'чел.',    5000, 'Площадка',   'Ориентир — 1 человек на 75–100 гостей'),
        ('Уборка до и после',                       2, 'чел.',    3500, 'Площадка',   ''),
        ('Дежурный медик',                          1, 'смена',   6000, 'Площадка',   'Требование для массовых мероприятий'),
        ('Фотограф',                                1, 'смена',  15000, 'Организатор','Контент окупается в промо следующего концерта'),
        ('Видеосъёмка концерта (2 камеры)',         1, 'смена',  25000, 'Организатор','Материал для клипов, отчётного видео и питчей площадкам'),
        ('Продюсер / директор проекта',             0, 'проект', 30000, 'Организатор','Поставьте 1, если проект ведёт наёмный человек, а не вы'),
    ]),
    ('3. ПРОДАКШН И ЛОГИСТИКА', [
        ('Репетиции и прогон программы',            2, 'смена',   6000, 'Организатор','Аренда репетиционной базы'),
        ('Транспорт оборудования',                  2, 'рейс',    8000, 'Организатор','Туда и обратно'),
        ('Трансфер и проживание команды',           0, 'компл.', 25000, 'Организатор','Заполните, если команда не из этого города'),
        ('Кейтеринг и райдер бэкстейджа',          15, 'чел.',     800, 'Организатор','По числу людей на площадке, включая техников'),
        ('Вода, расходники, хозтовары',             1, 'компл.',  3000, 'Организатор',''),
        ('Полиграфия: афиши, флаеры',               1, 'тираж',  12000, 'Организатор','Печать. Размещение — в бюджете маркетинга'),
        ('Бейджи, браслеты, программки',            1, 'тираж',   6000, 'Организатор',''),
        ('Оформление сцены и зала, декор',          1, 'компл.', 15000, 'Организатор','Сильно влияет на восприятие и на качество контента'),
    ]),
    ('5. ЮРИДИЧЕСКОЕ, ФИНАНСОВОЕ, ПРОЧЕЕ', [
        ('Страхование мероприятия',                 0, 'полис',  12000, 'Организатор','Рекомендую при бюджете свыше 500 000 ₽ — покрывает срыв и отмену'),
        ('Юридическое сопровождение, договоры',     1, 'проект',  8000, 'Организатор','Договор с площадкой, артистами, лицензия РАО'),
        ('Согласования и уведомления',              1, 'проект',  5000, 'Организатор',''),
        ('Онлайн-касса, ОФД, кассовое обслуживание',1, 'проект',  3000, 'Организатор','Если часть билетов продаёте сами'),
    ]),
]

hdr(ws, 4, ['Статья расхода', 'Кол-во', 'Ед.', 'Цена за ед., ₽',
            'Сумма организатора, ₽', 'Оплачивает', 'Комментарий'])
r = 5
subtotal_rows = []
venue_ranges = []
for bname, items in blocks:
    ws.cell(r, 1, bname).font = Font(name=FONT, size=10, bold=True, color='1F3864')
    for col in range(1, 8):
        ws.cell(r, col).fill = F_SUB
    bstart = r + 1
    r += 1
    for name, qty, unit, price, payer, note in items:
        ws.cell(r, 1, name).font = Font(name=FONT, size=10)
        ws.cell(r, 1).alignment = Alignment(indent=1)
        for col, val, fmt in ((2, qty, INT), (4, price, RUB)):
            c = ws.cell(r, col, val); c.number_format = fmt
            c.font = Font(name=FONT, size=10, color=C_INPUT); c.fill = F_KEY
        ws.cell(r, 3, unit).font = Font(name=FONT, size=9, color=C_MUTED)
        ws.cell(r, 3).alignment = Alignment(horizontal='center')
        c = ws.cell(r, 5, f'=IF($F{r}="Площадка",0,B{r}*D{r})')
        c.number_format = RUB; c.font = Font(name=FONT, size=10)
        c = ws.cell(r, 6, payer)
        c.font = Font(name=FONT, size=10, color=C_INPUT); c.fill = F_KEY
        c.alignment = Alignment(horizontal='center')
        dv_pay.add(c)
        ws.cell(r, 7, note).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
        for col in range(1, 8):
            ws.cell(r, col).border = BOX
        r += 1
    bend = r - 1
    ws.cell(r, 1, f'Итого по блоку: {bname.split(". ")[1].capitalize()}').font = Font(name=FONT, size=10, bold=True)
    c = ws.cell(r, 5, f'=SUM(E{bstart}:E{bend})')
    c.number_format = RUB; c.font = Font(name=FONT, size=10, bold=True)
    for col in range(1, 8):
        ws.cell(r, col).fill = F_TOTAL; ws.cell(r, col).border = BOX
    subtotal_rows.append(r)
    venue_ranges.append((bstart, bend))
    r += 2

# блок 4 — маркетинг, ссылкой
ws.cell(r, 1, '4. МАРКЕТИНГ И PR').font = Font(name=FONT, size=10, bold=True, color='1F3864')
for col in range(1, 8):
    ws.cell(r, col).fill = F_SUB
r += 1
ws.cell(r, 1, 'Бюджет маркетинга и PR (детализация — на листе «Маркетинг»)').font = Font(name=FONT, size=10)
ws.cell(r, 1).alignment = Alignment(indent=1)
c = ws.cell(r, 5, f'={M["budget"]}')
c.number_format = RUB; c.font = Font(name=FONT, size=10, bold=True, color=C_LINK)
ws.cell(r, 6, 'Организатор').font = Font(name=FONT, size=10, color=C_MUTED)
ws.cell(r, 6).alignment = Alignment(horizontal='center')
ws.cell(r, 7, 'Меняется на листе «Маркетинг» — здесь только итог').font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
for col in range(1, 8):
    ws.cell(r, col).border = BOX
mkt_row = r
r += 1
ws.cell(r, 1, 'Итого по блоку: Маркетинг и PR').font = Font(name=FONT, size=10, bold=True)
c = ws.cell(r, 5, f'=E{mkt_row}'); c.number_format = RUB; c.font = Font(name=FONT, size=10, bold=True)
for col in range(1, 8):
    ws.cell(r, col).fill = F_TOTAL; ws.cell(r, col).border = BOX
subtotal_rows.append(r)
r += 2

# ---- итоги сметы
block(ws, r, 'ИТОГИ СМЕТЫ'); r += 1
sub_sum = '+'.join(f'E{x}' for x in subtotal_rows)
ws.cell(r, 1, 'Прямые расходы организатора (блоки 1–5)').font = Font(name=FONT, size=10, bold=True)
c = ws.cell(r, 5, f'={sub_sum}'); c.number_format = RUB; c.font = Font(name=FONT, size=10, bold=True); c.border = BOX
direct_row = r; r += 1
ws.cell(r, 1, 'Резерв на непредвиденное').font = Font(name=FONT, size=10)
c = ws.cell(r, 5, f'=E{direct_row}*{V["reserve"]}'); c.number_format = RUB; c.font = Font(name=FONT, size=10); c.border = BOX
ws.cell(r, 7, f'Ставка резерва задаётся на листе «Вводные»').font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
res_row = r; r += 1
ws.cell(r, 1, 'ИТОГО ПОСТОЯННЫЕ РАСХОДЫ ОРГАНИЗАТОРА').font = Font(name=FONT, size=12, bold=True)
c = ws.cell(r, 5, f'=E{direct_row}+E{res_row}')
c.number_format = RUB; c.font = Font(name=FONT, size=12, bold=True)
for col in range(1, 8):
    ws.cell(r, col).fill = F_RESULT; ws.cell(r, col).border = Border(top=MED, bottom=MED)
ws.row_dimensions[r].height = 22
X['fixed'] = f"Расходы!$E${r}"
r += 2

venue_terms = '+'.join(
    f'SUMPRODUCT(($F${a}:$F${b}="Площадка")*$B${a}:$B${b}*$D${a}:$D${b})' for a, b in venue_ranges)
ws.cell(r, 1, 'Справочно: рыночная стоимость услуг, которые берёт на себя площадка').font = Font(name=FONT, size=10, bold=True, color='1F3864')
c = ws.cell(r, 5, f'={venue_terms}'); c.number_format = RUB
c.font = Font(name=FONT, size=10, bold=True, color='1F3864'); c.border = BOX
ws.cell(r, 7, 'Это ваш реальный аргумент в переговорах о доле: сравните с половиной прибыли, которую отдаёте').font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
X['venue_value'] = f"Расходы!$E${r}"
ws.freeze_panes = 'A5'

SUB = [f"Расходы!$E${x}" for x in subtotal_rows]   # 1 площадка/техника, 2 персонал, 3 продакшн, 4 юр/прочее, 5 маркетинг

# ================================================================ 5. ЭКОНОМИКА (P&L)
ws = wb.create_sheet('Экономика')
P = {}
title(ws, 'ЭКОНОМИКА КОНЦЕРТА: ОТ КАССЫ ДО ДЕНЕГ В КАРМАНЕ',
      'Водопад по вашей схеме: УСН 6% с валового сбора → расходы → раздел прибыли с площадкой → 8% (6+1+1) с выплаты вам.')
widths(ws, {'A': 56, 'B': 18, 'C': 12, 'D': 62})
hdr(ws, 4, ['Показатель', 'Сумма, ₽', '% от сбора', 'Комментарий'])

pr = 5
def pl(label, formula, fmt=RUB, kind='calc', pct=True, note=None,
       bold=False, fill=None, size=10, indent=1):
    global pr
    lc = ws.cell(pr, 1, label)
    lc.font = Font(name=FONT, size=size, bold=bold)
    lc.alignment = Alignment(indent=indent)
    c = ws.cell(pr, 2, formula)
    if fmt: c.number_format = fmt
    c.font = Font(name=FONT, size=size, bold=bold, color=(C_LINK if kind == 'link' else C_CALC))
    if pct and fmt == RUB:
        pc = ws.cell(pr, 3, f'=IFERROR(B{pr}/$B${GROSS_ROW},0)')
        pc.number_format = PCT; pc.font = Font(name=FONT, size=9, color=C_MUTED, bold=bold)
        pc.alignment = Alignment(horizontal='center')
    if note:
        ws.cell(pr, 4, note).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
    for col in range(1, 5):
        ws.cell(pr, col).border = BOX
        if fill:
            ws.cell(pr, col).fill = fill
    addr = f"Экономика!$B${pr}"
    pr += 1
    return addr

def sect(text):
    global pr
    block(ws, pr, text, width=4); pr += 1

GROSS_ROW = 9   # заранее известная строка валового сбора

sect('ДОХОДНАЯ ЧАСТЬ')
P['sold'] = pl('Продано билетов всего, шт', f'={B["sold"]}', INT, 'link', pct=False)
P['paid'] = pl('   в том числе платных, шт', f'={B["paid"]}', INT, 'link', pct=False)
P['avg']  = pl('Средняя цена платного билета, ₽', f'={B["avg"]}', RUB, 'link', pct=False)
assert pr == GROSS_ROW, f'GROSS_ROW рассинхронизирован: {pr}'
P['gross'] = pl('ВАЛОВОЙ СБОР (BOX OFFICE)', f'={B["gross"]}', RUB, 'link',
                note='Вся сумма, которую платят зрители за номинал билета', bold=True, fill=F_TOTAL, indent=0)
GR = P['gross']
P['svc'] = pl('Сервисный сбор с покупателя (справочно)',
    f'=IF({V["mode"]}=1,{GR}*(1-{V["offline"]})*{V["comm"]},0)', RUB, 'calc',
    note='При схеме 1 это деньги оператора сверх цены — в вашу выручку не входят')

sect('ВЫЧЕТЫ ИЗ ВАЛОВОГО СБОРА — УРОВЕНЬ 1')
P['comm'] = pl('Комиссия билетного оператора',
    f'=IF({V["mode"]}=2,{GR}*(1-{V["offline"]})*{V["comm"]},0)', RUB, 'calc',
    note='При схеме 2 удерживается из цены билета. На продажи «на входе» не начисляется')
P['rao'] = pl('Отчисления в РАО', f'={GR}*{V["rao"]}', RUB, 'calc',
    note='5% от валового сбора за публичное исполнение произведений')
P['usn1'] = pl('УСН 6% с валового сбора', f'={GR}*{V["t1"]}', RUB, 'calc',
    note='Уровень 1: только УСН, без взносов и банковской комиссии')
P['ded'] = pl('ИТОГО ВЫЧЕТОВ', f'={P["comm"]}+{P["rao"]}+{P["usn1"]}', RUB, 'calc', bold=True)
P['net_gross'] = pl('СБОР ПОСЛЕ ВЫЧЕТОВ', f'={GR}-{P["ded"]}', RUB, 'calc',
    bold=True, fill=F_TOTAL, indent=0)

sect('РАСХОДЫ')
P['c1'] = pl('Площадка и техническое обеспечение', f'={SUB[0]}', RUB, 'link')
P['c2'] = pl('Персонал и обслуживание', f'={SUB[1]}', RUB, 'link')
P['c3'] = pl('Продакшн и логистика', f'={SUB[2]}', RUB, 'link')
P['c5'] = pl('Маркетинг и PR', f'={SUB[4]}', RUB, 'link',
             note='Детализация по каналам и стоимость привлечения — на листе «Маркетинг»')
P['c4'] = pl('Юридическое, финансовое, прочее', f'={SUB[3]}', RUB, 'link')
P['res'] = pl('Резерв на непредвиденное', f'={X["fixed"]}-({SUB[0]}+{SUB[1]}+{SUB[2]}+{SUB[3]}+{SUB[4]})', RUB, 'link')
P['fixed'] = pl('Итого постоянных расходов', f'={X["fixed"]}', RUB, 'link', bold=True)
P['var'] = pl('Переменные расходы на гостей', f'={P["sold"]}*{V["perguest"]}', RUB, 'calc',
    note='Браслеты, печать билетов, вода, гардеробные номерки — растут вместе с залом')
P['costs'] = pl('ИТОГО РАСХОДЫ', f'={P["fixed"]}+{P["var"]}', RUB, 'calc',
    bold=True, fill=F_TOTAL, indent=0)

sect('РАЗДЕЛ ПРИБЫЛИ С ПЛОЩАДКОЙ')
P['extra_in'] = pl('Доп. доходы, участвующие в разделе (за вычетом УСН 6%)',
    f'=IF({V["extra_split"]}="Да",{B["extra"]}*(1-{V["t1"]}),0)', RUB, 'calc',
    note='Переключатель «Доп. доходы участвуют в разделе» — на листе «Вводные»')
P['profit'] = pl('ПРИБЫЛЬ К РАЗДЕЛУ',
    f'={P["net_gross"]}-{P["costs"]}+{P["extra_in"]}', RUB, 'calc',
    bold=True, fill=F_TOTAL, indent=0, size=11)
P['v_share'] = pl('Доля площадки',
    f'=IF({P["profit"]}>=0,{P["profit"]}*{V["share_v"]},IF({V["loss"]}="Да",{P["profit"]}*{V["share_v"]},0))',
    RUB, 'calc', note='Если убыток не делится, площадка не несёт ничего — весь минус ваш')
P['payout'] = pl('Доля организатора — выплата по договору',
    f'={P["profit"]}-{P["v_share"]}', RUB, 'calc', bold=True)
P['t2'] = pl('Налог и комиссии с выплаты (уровень 2: 6%+1%+1%)',
    f'=-MAX(0,{P["payout"]})*{V["t2"]}', RUB, 'calc',
    note='Выплата от площадки — второй доход, облагается повторно')
P['net_tickets'] = pl('ЧИСТЫЙ ДОХОД ОРГАНИЗАТОРА ОТ БИЛЕТОВ',
    f'={P["payout"]}+{P["t2"]}', RUB, 'calc', bold=True, fill=F_TOTAL, indent=0, size=11)

sect('ДОПОЛНИТЕЛЬНЫЕ ДОХОДЫ И ИТОГ')
P['extra_out'] = pl('Доп. доходы, остающиеся у организатора',
    f'=IF({V["extra_split"]}="Да",0,{B["extra"]})', RUB, 'link')
P['extra_tax'] = pl('Налоги и комиссии с доп. доходов (8%)',
    f'=-{P["extra_out"]}*{V["t2"]}', RUB, 'calc')
P['net'] = pl('ИТОГО ЧИСТЫЙ ДОХОД ОРГАНИЗАТОРА',
    f'={P["net_tickets"]}+{P["extra_out"]}+{P["extra_tax"]}', RUB, 'calc',
    bold=True, indent=0, size=13)
for col in range(1, 5):
    ws.cell(pr - 1, col).fill = F_RESULT
    ws.cell(pr - 1, col).border = Border(top=MED, bottom=MED)
ws.row_dimensions[pr - 1].height = 26

pr += 1
sect('КЛЮЧЕВЫЕ МЕТРИКИ И ТОЧКА БЕЗУБЫТОЧНОСТИ')
COMM_EFF = f'IF({V["mode"]}=2,{V["comm"]}*(1-{V["offline"]}),0)'
P['cm'] = pl('Маржинальный доход с одного платного билета, ₽',
    f'={P["avg"]}*(1-{COMM_EFF}-{V["rao"]}-{V["t1"]})-IFERROR({V["perguest"]}/{B["paid_share"]},{V["perguest"]})',
    RUB, 'calc', pct=False,
    note='Сколько остаётся с билета до постоянных расходов. Это «скорость», с которой окупается смета')
P['be'] = pl('Точка безубыточности, платных билетов',
    f'=IF({P["cm"]}<=0,"н/д — билет не покрывает переменные расходы",ROUNDUP({P["fixed"]}/{P["cm"]},0))',
    INT, 'calc', pct=False, bold=True,
    note='Сколько платных билетов надо продать, чтобы выйти в ноль до раздела прибыли')
P['be_fill'] = pl('Точка безубыточности, % заполнения зала',
    f'=IFERROR({P["be"]}/{B["paid_share"]}/{V["cap"]},0)', PCT, 'calc', pct=False, bold=True)
P['margin_safety'] = pl('Запас прочности (насколько план выше нуля), %',
    f'=IFERROR(({P["paid"]}-{P["be"]})/{P["paid"]},0)', PCT, 'calc', pct=False,
    note='Меньше 15% — проект висит на волоске: одна отмена промо и вы в минусе')
P['roi'] = pl('Рентабельность к валовому сбору, %',
    f'=IFERROR({P["net"]}/{GR},0)', PCT, 'calc', pct=False)
P['per_ticket'] = pl('Чистый доход на один проданный билет, ₽',
    f'=IFERROR({P["net"]}/{P["sold"]},0)', RUB, 'calc', pct=False)
P['venue_val'] = pl('Справочно: рыночная стоимость услуг площадки, ₽', f'={X["venue_value"]}', RUB, 'link', pct=False,
    note='Сравните с долей площадки в прибыли — это база для торга о проценте')
P['verdict'] = pl('ВЕРДИКТ ПО ПРОЕКТУ',
    f'=IF({P["profit"]}<0,"УБЫТОК. Нужно резать смету, поднимать цену или менять условия сделки",'
    f'IF({P["margin_safety"]}<0.15,"НА ГРАНИ. Запас прочности меньше 15% — риск высокий",'
    f'IF({P["roi"]}<0.1,"СЛАБО. Прибыль есть, но рентабельность ниже 10% от сбора",'
    f'"ЗДОРОВО. Проект окупается с приемлемым запасом")))',
    None, 'calc', pct=False, bold=True)
ws.conditional_formatting.add(f'B{pr-1}', FormulaRule(formula=[f'LEFT($B${pr-1},6)="УБЫТОК"'],
    fill=PatternFill('solid', fgColor='FFC7CE'), font=Font(color='9C0006', bold=True)))
ws.conditional_formatting.add(f'B{pr-1}', FormulaRule(formula=[f'LEFT($B${pr-1},7)="ЗДОРОВО"'],
    fill=PatternFill('solid', fgColor='C6EFCE'), font=Font(color='006100', bold=True)))
ws.freeze_panes = 'A5'

# ================================================================ 6. СЦЕНАРИИ
ws = wb.create_sheet('Сценарии')
title(ws, 'СЦЕНАРИИ: ОТ ПРОВАЛА ДО АНШЛАГА',
      'Структура цен и смета во всех сценариях одинаковые — меняется только заполняемость зала. Последний столбец показывает, где проходит граница нуля.')
widths(ws, {'A': 50, 'B': 17, 'C': 17, 'D': 17, 'E': 17, 'F': 19, 'G': 50})

hdr(ws, 4, ['Показатель', 'Пессимистичный', 'БАЗОВЫЙ', 'Оптимистичный', 'Аншлаг', 'Точка безубыточности', 'Комментарий'])
cols = ['B', 'C', 'D', 'E', 'F']
fills_ref = [V['fill_pess'], B['fill_base'], V['fill_opt'], V['fill_full'], P['be_fill']]

rows_def = [
    ('Заполняемость зала, %',                        PCT, 'fill'),
    ('Продано билетов всего, шт',                    INT, 'sold'),
    ('   в том числе платных, шт',                   INT, 'paid'),
    ('Средняя цена платного билета, ₽',              RUB, 'avg'),
    ('ВАЛОВОЙ СБОР',                                 RUB, 'gross'),
    ('   − комиссия билетного оператора',            RUB, 'comm'),
    ('   − отчисления в РАО',                        RUB, 'rao'),
    ('   − УСН 6% с валового сбора',                 RUB, 'usn'),
    ('СБОР ПОСЛЕ ВЫЧЕТОВ',                           RUB, 'netgross'),
    ('   − постоянные расходы (смета)',              RUB, 'fixed'),
    ('   − переменные расходы на гостей',            RUB, 'var'),
    ('   + доп. доходы, участвующие в разделе',      RUB, 'extrain'),
    ('ПРИБЫЛЬ К РАЗДЕЛУ',                            RUB, 'profit'),
    ('   доля площадки',                             RUB, 'vshare'),
    ('   доля организатора (выплата по договору)',   RUB, 'payout'),
    ('   − налог и комиссии с выплаты (8%)',         RUB, 'tax2'),
    ('Чистый доход от билетов',                      RUB, 'nettick'),
    ('   + доп. доходы вне раздела (за вычетом 8%)', RUB, 'extraout'),
    ('ИТОГО ЧИСТЫЙ ДОХОД ОРГАНИЗАТОРА',              RUB, 'net'),
    ('Рентабельность к валовому сбору, %',           PCT, 'roi'),
    ('Отклонение от базового сценария, ₽',           RUB, 'delta'),
]
SR = {k: 5 + i for i, (_, _, k) in enumerate(rows_def)}
notes = {
    'fill':     'Пессимистичный и оптимистичный задаются на листе «Вводные»',
    'profit':   'Именно эта строка делится с площадкой пополам',
    'vshare':   'При убытке площадка не участвует, если в договоре не сказано иное',
    'net':      'Деньги, которые реально останутся у вас после всех налогов',
    'delta':    'Цена риска: разброс между сценариями',
}
for lab, fmt, key in rows_def:
    r = SR[key]
    strong = key in ('gross', 'netgross', 'profit', 'net')
    lc = ws.cell(r, 1, lab)
    lc.font = Font(name=FONT, size=10, bold=strong)
    lc.alignment = Alignment(indent=0 if strong else 1)
    if key in notes:
        ws.cell(r, 7, notes[key]).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
    for ci, col in enumerate(cols):
        base = (ci == 1)
        f = {
          'fill':     f'={fills_ref[ci]}',
          'sold':     (f'={B["sold"]}' if base else f'=ROUND({V["cap"]}*{col}{SR["fill"]},0)'),
          'paid':     (f'={B["paid"]}' if base else f'=ROUND({col}{SR["sold"]}*{B["paid_share"]},0)'),
          'avg':      f'={B["avg"]}',
          'gross':    (f'={B["gross"]}' if base else f'={col}{SR["paid"]}*{col}{SR["avg"]}'),
          'comm':     f'=-IF({V["mode"]}=2,{col}{SR["gross"]}*(1-{V["offline"]})*{V["comm"]},0)',
          'rao':      f'=-{col}{SR["gross"]}*{V["rao"]}',
          'usn':      f'=-{col}{SR["gross"]}*{V["t1"]}',
          'netgross': f'=SUM({col}{SR["gross"]}:{col}{SR["usn"]})',
          'fixed':    f'=-{X["fixed"]}',
          'var':      f'=-{col}{SR["sold"]}*{V["perguest"]}',
          'extrain':  f'=IF({V["extra_split"]}="Да",{B["extra"]}*(1-{V["t1"]}),0)',
          'profit':   f'=SUM({col}{SR["netgross"]}:{col}{SR["extrain"]})',
          'vshare':   f'=IF({col}{SR["profit"]}>=0,{col}{SR["profit"]}*{V["share_v"]},IF({V["loss"]}="Да",{col}{SR["profit"]}*{V["share_v"]},0))',
          'payout':   f'={col}{SR["profit"]}-{col}{SR["vshare"]}',
          'tax2':     f'=-MAX(0,{col}{SR["payout"]})*{V["t2"]}',
          'nettick':  f'={col}{SR["payout"]}+{col}{SR["tax2"]}',
          'extraout': f'=IF({V["extra_split"]}="Да",0,{B["extra"]})*(1-{V["t2"]})',
          'net':      f'={col}{SR["nettick"]}+{col}{SR["extraout"]}',
          'roi':      f'=IFERROR({col}{SR["net"]}/{col}{SR["gross"]},0)',
          'delta':    f'={col}{SR["net"]}-$C${SR["net"]}',
        }[key]
        c = ws.cell(r, ci + 2, f)
        c.number_format = fmt
        c.font = Font(name=FONT, size=10, bold=strong)
        c.border = BOX
        if key in ('gross', 'netgross', 'profit'):
            c.fill = F_TOTAL
        if key == 'net':
            c.fill = F_RESULT
        if base and key != 'delta':
            c.border = Border(left=MED, right=MED, top=THIN, bottom=THIN)
    if key == 'net':
        ws.row_dimensions[r].height = 22
ws.conditional_formatting.add(f'B{SR["net"]}:F{SR["net"]}',
    CellIsRule(operator='lessThan', formula=['0'],
               fill=PatternFill('solid', fgColor='FFC7CE'), font=Font(color='9C0006', bold=True)))
ws.conditional_formatting.add(f'B{SR["profit"]}:F{SR["profit"]}',
    CellIsRule(operator='lessThan', formula=['0'],
               fill=PatternFill('solid', fgColor='FFC7CE'), font=Font(color='9C0006', bold=True)))
ws.freeze_panes = 'B5'

# ================================================================ 7. ЧУВСТВИТЕЛЬНОСТЬ
ws = wb.create_sheet('Чувствительность')
title(ws, 'ЧУВСТВИТЕЛЬНОСТЬ: ЦЕНА ПРОТИВ ЗАПОЛНЯЕМОСТИ',
      'Что будет с вашим чистым доходом при разной средней цене билета и разной заполняемости зала. Зелёное — прибыль, красное — убыток.')
widths(ws, {'A': 20})
for col in range(2, 9):
    ws.column_dimensions[get_column_letter(col)].width = 15

prices = [1500, 2000, 2500, 3000, 3500, 4000, 4500]
fillsv = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]

ws.cell(4, 1, 'ПРИБЫЛЬ К РАЗДЕЛУ С ПЛОЩАДКОЙ (до сплита и налога уровня 2), ₽').font = Font(name=FONT, size=11, bold=True, color='1F3864')
HR = 5
ws.cell(HR, 1, 'Заполняемость \\ Средняя цена').font = Font(name=FONT, size=9, bold=True, color='FFFFFF')
ws.cell(HR, 1).fill = PatternFill('solid', fgColor='4472C4')
ws.cell(HR, 1).alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
ws.cell(HR, 1).border = BOX
ws.row_dimensions[HR].height = 32
for j, p_ in enumerate(prices):
    c = ws.cell(HR, 2 + j, p_)
    c.number_format = RUB
    c.font = Font(name=FONT, size=10, bold=True, color='FFFFFF')
    c.fill = PatternFill('solid', fgColor='4472C4')
    c.alignment = Alignment(horizontal='center'); c.border = BOX

CAP, PS, PG = V['cap'], B['paid_share'], V['perguest']
for i, fv in enumerate(fillsv):
    r = HR + 1 + i
    c = ws.cell(r, 1, fv); c.number_format = PCT
    c.font = Font(name=FONT, size=10, bold=True, color='FFFFFF')
    c.fill = PatternFill('solid', fgColor='4472C4')
    c.alignment = Alignment(horizontal='center'); c.border = BOX
    for j in range(len(prices)):
        col = get_column_letter(2 + j)
        sold = f'({CAP}*$A{r})'
        paid = f'({CAP}*$A{r}*{PS})'
        g    = f'({paid}*{col}${HR})'
        comm = f'IF({V["mode"]}=2,{g}*(1-{V["offline"]})*{V["comm"]},0)'
        prof = (f'={g}-{comm}-{g}*{V["rao"]}-{g}*{V["t1"]}-{sold}*{PG}-{X["fixed"]}'
                f'+IF({V["extra_split"]}="Да",{B["extra"]}*(1-{V["t1"]}),0)')
        cc = ws.cell(r, 2 + j, prof)
        cc.number_format = RUB; cc.font = Font(name=FONT, size=10); cc.border = BOX
last = HR + len(fillsv)
LASTCOL = get_column_letter(1 + len(prices))
rng = f'B{HR+1}:{LASTCOL}{last}'
ws.conditional_formatting.add(rng, ColorScaleRule(
    start_type='num', start_value=-300000, start_color='F8696B',
    mid_type='num',   mid_value=0,         mid_color='FFEB84',
    end_type='num',   end_value=500000,    end_color='63BE7B'))

# --- таблица 2: чистый доход организатора (ссылается на таблицу 1)
T2H = last + 3
ws.cell(T2H - 1, 1, 'ИТОГО чистый доход организатора после раздела и всех налогов, ₽').font = Font(
    name=FONT, size=11, bold=True, color='1F3864')
ws.cell(T2H, 1, 'Заполняемость \\ Средняя цена').font = Font(name=FONT, size=9, bold=True, color='FFFFFF')
ws.cell(T2H, 1).fill = PatternFill('solid', fgColor='4472C4')
ws.cell(T2H, 1).alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
ws.cell(T2H, 1).border = BOX
ws.row_dimensions[T2H].height = 32
for j, p_ in enumerate(prices):
    c = ws.cell(T2H, 2 + j, p_); c.number_format = RUB
    c.font = Font(name=FONT, size=10, bold=True, color='FFFFFF')
    c.fill = PatternFill('solid', fgColor='4472C4')
    c.alignment = Alignment(horizontal='center'); c.border = BOX
for i, fv in enumerate(fillsv):
    r = T2H + 1 + i
    src = HR + 1 + i
    c = ws.cell(r, 1, fv); c.number_format = PCT
    c.font = Font(name=FONT, size=10, bold=True, color='FFFFFF')
    c.fill = PatternFill('solid', fgColor='4472C4')
    c.alignment = Alignment(horizontal='center'); c.border = BOX
    for j in range(len(prices)):
        col = get_column_letter(2 + j)
        pf  = f'{col}{src}'
        pay = f'IF({pf}>=0,{pf}*{V["share"]},IF({V["loss"]}="Да",{pf}*{V["share"]},{pf}))'
        f = (f'={pay}-MAX(0,{pay})*{V["t2"]}'
             f'+IF({V["extra_split"]}="Да",0,{B["extra"]})*(1-{V["t2"]})')
        cc = ws.cell(r, 2 + j, f)
        cc.number_format = RUB; cc.font = Font(name=FONT, size=10); cc.border = BOX
last2 = T2H + len(fillsv)
ws.conditional_formatting.add(f'B{T2H+1}:{LASTCOL}{last2}', ColorScaleRule(
    start_type='num', start_value=-300000, start_color='F8696B',
    mid_type='num',   mid_value=0,         mid_color='FFEB84',
    end_type='num',   end_value=500000,    end_color='63BE7B'))
last = last2

r2 = last + 3
ws.cell(r2, 1, 'Точка безубыточности при разной средней цене билета').font = Font(name=FONT, size=11, bold=True, color='1F3864')
r2 += 1
ws.cell(r2, 1, 'Средняя цена, ₽').font = Font(name=FONT, size=9, bold=True, color='FFFFFF')
ws.cell(r2, 1).fill = PatternFill('solid', fgColor='4472C4'); ws.cell(r2, 1).border = BOX
for j, p_ in enumerate(prices):
    c = ws.cell(r2, 2 + j, p_); c.number_format = RUB
    c.font = Font(name=FONT, size=10, bold=True, color='FFFFFF')
    c.fill = PatternFill('solid', fgColor='4472C4')
    c.alignment = Alignment(horizontal='center'); c.border = BOX
COMM_EFF = f'IF({V["mode"]}=2,{V["comm"]}*(1-{V["offline"]}),0)'
for off, lab, fmt in ((1, 'Нужно продать платных билетов, шт', INT),
                      (2, 'Это заполняемость зала, %', PCT)):
    rr = r2 + off
    ws.cell(rr, 1, lab).font = Font(name=FONT, size=10, bold=(off == 2))
    for j in range(len(prices)):
        col = get_column_letter(2 + j)
        cmv = f'({col}${r2}*(1-{COMM_EFF}-{V["rao"]}-{V["t1"]})-IFERROR({PG}/{PS},{PG}))'
        if off == 1:
            f = f'=IF({cmv}<=0,"н/д",ROUNDUP({X["fixed"]}/{cmv},0))'
        else:
            f = f'=IFERROR({col}{r2+1}/{PS}/{CAP},"н/д")'
        c = ws.cell(rr, 2 + j, f); c.number_format = fmt
        c.font = Font(name=FONT, size=10, bold=(off == 2)); c.border = BOX
        c.alignment = Alignment(horizontal='center')
ws.conditional_formatting.add(f'B{r2+2}:{LASTCOL}{r2+2}',
    CellIsRule(operator='greaterThan', formula=['1'],
               fill=PatternFill('solid', fgColor='FFC7CE'), font=Font(color='9C0006', bold=True)))
ws.freeze_panes = 'B6'

# ================================================================ 8. ДАШБОРД
ws = wb.create_sheet('Дашборд')
wb.move_sheet('Дашборд', offset=-(len(wb.sheetnames) - 1))
title(ws, 'КОНЦЕРТ: ИТОГОВАЯ ЭКОНОМИКА', None, width=6)
widths(ws, {'A': 3, 'B': 40, 'C': 22, 'D': 4, 'E': 40, 'F': 22})
ws['A2'] = ('Один экран с главными цифрами. Все они пересчитываются автоматически — '
            'меняйте вводные на листах «Вводные», «Билеты», «Расходы» и «Маркетинг».')
ws['A2'].font = Font(name=FONT, size=9, italic=True, color=C_MUTED)

r = 4
ws.cell(r, 2, 'Проект').font = Font(name=FONT, size=10, bold=True, color='1F3864')
ws.cell(r, 3, f'={V["name"]}').font = Font(name=FONT, size=10, bold=True)
ws.cell(r, 5, 'Дата / площадка').font = Font(name=FONT, size=10, bold=True, color='1F3864')
ws.cell(r, 6, f'={V["date"]}&" · "&{V["venue"]}').font = Font(name=FONT, size=10)
r += 2

def tile(row, col, label, formula, fmt, big=False, accent=False):
    lc = ws.cell(row, col, label)
    lc.font = Font(name=FONT, size=9, bold=True, color='44546A')
    lc.alignment = Alignment(vertical='center')
    c = ws.cell(row, col + 1, formula)
    c.number_format = fmt
    c.font = Font(name=FONT, size=14 if big else 11, bold=True,
                  color='1F3864' if not accent else 'C00000')
    c.alignment = Alignment(horizontal='right', vertical='center')
    for cc in (lc, c):
        cc.fill = F_RESULT if big else F_ZEBRA
        cc.border = BOX
    ws.row_dimensions[row].height = 24 if big else 20

block(ws, r, 'ГЛАВНЫЕ ЦИФРЫ', width=6); r += 1
tiles = [
    ('Валовой сбор (box office)',          f'={P["gross"]}',        RUB, False),
    ('Продано билетов, шт',                f'={P["sold"]}',         INT, False),
    ('Итого расходы (смета + переменные)', f'={P["costs"]}',        RUB, False),
    ('Средняя цена платного билета',       f'={P["avg"]}',          RUB, False),
    ('Налоги, РАО и комиссии, всего',      f'={P["ded"]}-{P["t2"]}-{P["extra_tax"]}', RUB, False),
    ('Дополнительные доходы',              f'={B["extra"]}',        RUB, False),
    ('ПРИБЫЛЬ К РАЗДЕЛУ С ПЛОЩАДКОЙ',      f'={P["profit"]}',       RUB, True),
    ('ЧИСТЫЙ ДОХОД ОРГАНИЗАТОРА',          f'={P["net"]}',          RUB, True),
]
for i, (lab, f, fmt, big) in enumerate(tiles):
    tile(r + i // 2, 2 + (i % 2) * 3, lab, f, fmt, big)
r += (len(tiles) + 1) // 2 + 1

block(ws, r, 'УСТОЙЧИВОСТЬ ПРОЕКТА', width=6); r += 1
tiles2 = [
    ('Точка безубыточности, платных билетов', f'={P["be"]}',            INT),
    ('Точка безубыточности, % зала',          f'={P["be_fill"]}',       PCT),
    ('Запас прочности',                       f'={P["margin_safety"]}', PCT),
    ('Рентабельность к валовому сбору',       f'={P["roi"]}',           PCT),
    ('Маржинальный доход с билета',           f'={P["cm"]}',            RUB),
    ('Чистый доход на один билет',            f'={P["per_ticket"]}',    RUB),
]
for i, (lab, f, fmt) in enumerate(tiles2):
    tile(r + i // 2, 2 + (i % 2) * 3, lab, f, fmt)
r += (len(tiles2) + 1) // 2 + 1

ws.cell(r, 2, 'ВЕРДИКТ').font = Font(name=FONT, size=11, bold=True, color='1F3864')
c = ws.cell(r, 3, f'={P["verdict"]}')
c.font = Font(name=FONT, size=11, bold=True)
ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=6)
for col in range(2, 7):
    ws.cell(r, col).border = BOX
ws.conditional_formatting.add(f'C{r}', FormulaRule(formula=[f'LEFT($C${r},6)="УБЫТОК"'],
    fill=PatternFill('solid', fgColor='FFC7CE'), font=Font(color='9C0006', bold=True)))
ws.conditional_formatting.add(f'C{r}', FormulaRule(formula=[f'LEFT($C${r},7)="ЗДОРОВО"'],
    fill=PatternFill('solid', fgColor='C6EFCE'), font=Font(color='006100', bold=True)))
ws.row_dimensions[r].height = 24
r += 2

block(ws, r, 'СЦЕНАРИИ — ЧИСТЫЙ ДОХОД ОРГАНИЗАТОРА', width=6); r += 1
sc_labels = ['Пессимистичный', 'Базовый', 'Оптимистичный', 'Аншлаг']
for i, lab in enumerate(sc_labels):
    col = 2 + i
    hc = ws.cell(r, col, lab)
    hc.font = Font(name=FONT, size=9, bold=True, color='FFFFFF')
    hc.fill = PatternFill('solid', fgColor='4472C4')
    hc.alignment = Alignment(horizontal='center', wrap_text=True); hc.border = BOX
    fc = ws.cell(r + 1, col, f"=Сценарии!{get_column_letter(2+i)}{SR['net']}")
    fc.number_format = RUB; fc.font = Font(name=FONT, size=11, bold=True)
    fc.alignment = Alignment(horizontal='center'); fc.border = BOX
    pc = ws.cell(r + 2, col, f"=Сценарии!{get_column_letter(2+i)}{SR['fill']}")
    pc.number_format = PCT; pc.font = Font(name=FONT, size=9, color=C_MUTED)
    pc.alignment = Alignment(horizontal='center'); pc.border = BOX
ws.conditional_formatting.add(f'B{r+1}:E{r+1}', CellIsRule(operator='lessThan', formula=['0'],
    fill=PatternFill('solid', fgColor='FFC7CE'), font=Font(color='9C0006', bold=True)))
ws.cell(r + 2, 6, '← заполняемость зала в сценарии').font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
r += 4

block(ws, r, 'ЧТО ОБЯЗАТЕЛЬНО УТОЧНИТЬ ПЕРЕД ЗАПУСКОМ', width=6); r += 1
checks = [
    'Договор с площадкой: что именно входит в её вклад (звук, свет, персонал, охрана, уборка) — впишите это в столбец «Оплачивает» на листе «Расходы».',
    'Договор с площадкой: делится ли убыток. Если нет — весь минус ваш, а плюс только наполовину.',
    'Договор с площадкой: из какой базы считается «прибыль к разделу» и кто подтверждает смету расходов.',
    'Билетный оператор: ставка комиссии и чья это комиссия — покупателя или ваша (схема 1 или 2 на листе «Вводные»).',
    'Билетный оператор: агентская схема или прямая продажа — от этого зависит, вся ли касса попадает в базу УСН.',
    'РАО: ставка по договору и перечень исполняемых произведений (собственные и общественное достояние считаются иначе).',
    'Кто получает деньги от билетов физически — вы или площадка. От этого зависит, у кого возникает доход и на каком уровне удерживается УСН.',
    'Технический райдер артиста — пришлите файл, и я перенесу его построчно в смету с реальными ценами аренды.',
]
for i, t in enumerate(checks):
    cc = ws.cell(r + i, 2, f'{i+1}. {t}')
    cc.font = Font(name=FONT, size=9)
    cc.alignment = Alignment(wrap_text=True, vertical='top')
    ws.merge_cells(start_row=r + i, start_column=2, end_row=r + i, end_column=6)
    ws.row_dimensions[r + i].height = 26
ws.sheet_view.showGridLines = False

# ================================================================ 9. ВАРИАНТЫ УЛУЧШЕНИЙ
ws = wb.create_sheet('Варианты')
title(ws, 'ВАРИАНТЫ УЛУЧШЕНИЯ ЭКОНОМИКИ',
      'Каждый вариант привязан к конкретной ячейке модели — можно проверить эффект прямо в файле. Оценки эффекта ориентировочные, для клубного концерта на 300 мест.')
widths(ws, {'A': 5, 'B': 22, 'C': 52, 'D': 34, 'E': 20, 'F': 52})
hdr(ws, 4, ['№', 'Направление', 'Что конкретно сделать', 'Где в модели', 'Оценка эффекта', 'Что учесть / риск'])

options = [
 ('Цена', 'Волновое ценообразование: early bird → предпродажа → цена на входе. Ранняя квота даёт деньги на маркетинг ещё до концерта.',
  'Лист «Билеты», категории 1–3', '+5–10% к сбору', 'Уже заложено в модель. Не делайте разрыв больше 40% — обесценивает раннюю цену'),
 ('Цена', 'Поднять цену фан-зоны и вложить в неё мерч и ранний вход. Люди платят за статус, а не за метры.',
  'Лист «Билеты», строка «Фан-зона / VIP»', '+3–7% к сбору', 'Квота VIP выше 15% зала обычно не продаётся'),
 ('Цена', 'Пакеты: «билет + футболка», «два билета со скидкой 10%». Растёт средний чек и конверсия.',
  'Лист «Билеты», доп. категория', '+5% к сбору', 'Нужен учёт себестоимости мерча в смете'),
 ('Сделка', 'Пересмотреть долю: показать площадке рыночную стоимость её услуг и сравнить с половиной прибыли.',
  'Расходы: «Рыночная стоимость услуг площадки»', '±10 п.п. доли', 'Сильнее всего работает, если вы приводите свою аудиторию'),
 ('Сделка', 'Прописать в договоре раздел убытка, а не только прибыли. Сейчас риск асимметричен.',
  'Вводные: «Убыток делится с площадкой»', 'Снижает риск вдвое', 'Площадки соглашаются редко — но просить нужно всегда'),
 ('Сделка', 'Договориться о доле от выручки бара. Ваша публика приносит площадке бар, а вы этого не видите.',
  'Билеты: «Доля от выручки бара»', '+20–60 тыс ₽', 'Просите фиксированный процент и доступ к отчёту по кассе'),
 ('Налоги', 'Убрать второй уровень налога: оформить отношения так, чтобы вашим доходом была сразу ваша доля, а не выплата от площадки.',
  'Вводные: «Уровень 2»', 'До 8% от вашей доли', 'ОБЯЗАТЕЛЬНО обсудить с бухгалтером — схема зависит от формы договора'),
 ('Налоги', 'Проверить, что попадает в базу УСН при агентской продаже билетов: по агентскому договору доходом может признаваться вся сумма от покупателей, включая удержанную комиссию.',
  'Вводные: «УСН», лист «Экономика»', 'До 1–2% от сбора', 'Частая и дорогая ошибка. Уточните формулировки в договоре с оператором'),
 ('РАО', 'Декларировать точный репертуар: собственные произведения возвращаются автору через РАО, произведения в общественном достоянии не облагаются.',
  'Вводные: «Отчисления в РАО»', 'До 5% от сбора', 'Нужна корректная рапортичка. Не платить вообще — нельзя'),
 ('Билеты', 'Перевести сервисный сбор на покупателя (схема 1) или продавать часть билетов напрямую через свою страницу.',
  'Вводные: «Схема сервисного сбора», «Доля продаж на входе»', '+3–8% к сбору', 'Схема 1 повышает итоговую цену для зрителя и может просадить конверсию'),
 ('Маркетинг', 'Перераспределить бюджет в каналы с низким CPA: собственная база и Telegram обычно дешевле таргета в разы.',
  'Лист «Маркетинг», столбцы «Бюджет» и «CPA»', '−20–30% бюджета', 'Требует заранее собранной базы. Начинайте собирать на этом концерте'),
 ('Маркетинг', 'Кросс-промо: обмен рассылками и сторис с площадками и артистами смежной аудитории вместо платного охвата.',
  'Лист «Маркетинг», новая строка с бюджетом 0', '−10–15 тыс ₽', 'Договариваться нужно за 4–6 недель'),
 ('Маркетинг', 'Реферальные промокоды: скидка тому, кто привёл, и тому, кого привели. Считается по коду, а не по ощущениям.',
  'Лист «Маркетинг», новая строка', '+5–10% продаж', 'Скидка уменьшает среднюю цену — заведите отдельную категорию билета'),
 ('Доходы', 'Спонсорский или партнёрский пакет: логотип, стенд, семплинг, упоминания. Для клуба на 300 мест это 50–150 тыс ₽.',
  'Билеты: «Спонсорский пакет»', '+50–150 тыс ₽', 'Самый недооценённый источник. Нужна презентация и охваты за 2 месяца'),
 ('Доходы', 'Мерч на предзаказ до концерта: печать по факту заказов, без остатков и замороженных денег.',
  'Билеты: «Мерч»', '+20–40 тыс ₽', 'Срок печати 10–14 дней — закрывать предзаказ заранее'),
 ('Доходы', 'Снять концерт на 2 камеры и выпустить релиз или стрим. Материал работает и как промо следующего события.',
  'Билеты: «Съёмка концерта»', 'Отложенный доход', 'Права на запись нужно закрыть в договорах с музыкантами'),
 ('Риск', 'Предпродажа с порогом: анонсировать, но подтверждать концерт только при N проданных билетов.',
  'Экономика: «Точка безубыточности»', 'Убирает риск убытка', 'Требует честной коммуникации и возможности вернуть деньги'),
 ('Риск', 'Страхование отмены при бюджете свыше 500 тыс ₽.',
  'Расходы: «Страхование мероприятия»', 'Стоит 1–3% бюджета', 'Читайте исключения: болезнь артиста покрывается не всегда'),
 ('Риск', 'Свести график платежей: предоплаты за аренду, технику и рекламу уходят до того, как придут деньги за билеты.',
  'Нужен отдельный лист платёжного календаря', 'Убирает кассовый разрыв', 'Скажите — добавлю платёжный календарь по неделям'),
]
r = 5
for i, (dirn, what, where, eff, risk) in enumerate(options):
    ws.cell(r, 1, i + 1).font = Font(name=FONT, size=10, bold=True)
    ws.cell(r, 1).alignment = Alignment(horizontal='center', vertical='top')
    ws.cell(r, 2, dirn).font = Font(name=FONT, size=10, bold=True, color='1F3864')
    ws.cell(r, 3, what).font = Font(name=FONT, size=10)
    ws.cell(r, 4, where).font = Font(name=FONT, size=9, color=C_LINK)
    ws.cell(r, 5, eff).font = Font(name=FONT, size=10, bold=True)
    ws.cell(r, 6, risk).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
    for col in range(1, 7):
        ws.cell(r, col).border = BOX
        ws.cell(r, col).alignment = Alignment(wrap_text=True, vertical='top',
                                              horizontal='center' if col == 1 else 'left')
        if i % 2:
            ws.cell(r, col).fill = F_ZEBRA
    ws.row_dimensions[r].height = 46
    r += 1
ws.freeze_panes = 'A5'

# ---------------------------------------------------------------- финальная отделка
for sh in wb.worksheets:
    for row in sh.iter_rows():
        for c in row:
            if c.font and c.font.name != FONT:
                c.font = Font(name=FONT, size=c.font.size, bold=c.font.bold,
                              italic=c.font.italic, color=c.font.color)
    sh.page_setup.orientation = 'landscape'
    sh.page_setup.fitToWidth = 1
    sh.sheet_properties.pageSetUpPr.fitToPage = True

wb.save('Бюджет_концерта.xlsx')
print('saved: Бюджет_концерта.xlsx')
print('sheets:', wb.sheetnames)
