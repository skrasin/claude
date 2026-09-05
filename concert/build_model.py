# -*- coding: utf-8 -*-
"""
Финансовая модель концерта.

Этап 1 (до раздела прибыли с площадкой):
    Валовой сбор − УСН 6% − РАО 8% − технические расходы = ПРИБЫЛЬ
Раздел:
    Прибыль делится пополам, половина = прибыль организатора
Этап 2 (из прибыли организатора):
    − налоги 7% − банковские комиссии 1% − гонорары − маркетинг и PR − прочие расходы
    = ЧИСТЫЙ ДОХОД ОРГАНИЗАТОРА
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule, FormulaRule
from openpyxl.worksheet.datavalidation import DataValidation

FONT = 'Arial'
RUB  = '#,##0" ₽";[Red](#,##0" ₽");"—"'
PCT  = '0.0%'
INT  = '#,##0;[Red](#,##0);"—"'

C_IN, C_CALC, C_LINK, C_MUTED = '0000FF', '000000', '008000', '808080'
F_HEAD   = PatternFill('solid', fgColor='1F3864')
F_SUB    = PatternFill('solid', fgColor='D9E2F3')
F_KEY    = PatternFill('solid', fgColor='FFF2CC')
F_TOTAL  = PatternFill('solid', fgColor='E2EFDA')
F_RESULT = PatternFill('solid', fgColor='FCE4D6')
F_STAGE  = PatternFill('solid', fgColor='DDEBF7')
F_ZEBRA  = PatternFill('solid', fgColor='F7F9FC')

THIN = Side(style='thin', color='BFBFBF')
MED  = Side(style='medium', color='1F3864')
BOX  = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

wb = openpyxl.Workbook()

def title(ws, text, sub=None, width=8):
    ws['A1'] = text
    ws['A1'].font = Font(name=FONT, size=15, bold=True, color='FFFFFF')
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

def hdr(ws, row, headers):
    for i, h in enumerate(headers):
        c = ws.cell(row, 1 + i, h)
        c.font = Font(name=FONT, size=9, bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='4472C4')
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = BOX
    ws.row_dimensions[row].height = 30

def widths(ws, spec):
    for col, w in spec.items():
        ws.column_dimensions[col].width = w

def put(ws, row, label, value, fmt=None, kind='calc', note=None, indent=0):
    lc = ws.cell(row, 1, label)
    lc.font = Font(name=FONT, size=10)
    lc.alignment = Alignment(indent=indent)
    c = ws.cell(row, 2, value)
    c.font = Font(name=FONT, size=10,
                  color={'input': C_IN, 'calc': C_CALC, 'link': C_LINK, 'text': C_IN}[kind])
    if fmt:
        c.number_format = fmt
    if kind in ('input', 'text'):
        c.fill = F_KEY
    c.border = BOX
    if note:
        ws.cell(row, 3, note).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
    return c

# ================================================================ ВВОДНЫЕ
ws = wb.active
ws.title = 'Вводные'
V = {}
title(ws, 'ВВОДНЫЕ ДАННЫЕ И СТАВКИ',
      'Синие ячейки на жёлтом фоне — вводные, их можно менять. Чёрные — формулы. Зелёные — ссылки на другие листы.')
widths(ws, {'A': 54, 'B': 18, 'C': 70})

r = 4
block(ws, r, '1. ПАРАМЕТРЫ СОБЫТИЯ'); r += 1
for lab, val, key in [('Название концерта', '— укажите название —', 'name'),
                      ('Артист / состав', '— укажите —', 'artist'),
                      ('Дата и время', '— ДД.ММ.ГГГГ, 20:00 —', 'date'),
                      ('Площадка', '— клуб —', 'venue'),
                      ('Город', '— город —', 'city')]:
    put(ws, r, lab, val, kind='text'); V[key] = f"Вводные!$B${r}"; r += 1

r += 1
block(ws, r, '2. ЗАЛ И ПОСЕЩАЕМОСТЬ'); r += 1
put(ws, r, 'Вместимость зала, чел.', 300, INT, 'input'); V['cap'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'Заполняемость — пессимистичный сценарий', 0.40, PCT, 'input',
    'Базовый сценарий берётся с листа «Билеты» — там задана продажа по категориям')
V['fill_pess'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'Заполняемость — оптимистичный сценарий', 0.90, PCT, 'input')
V['fill_opt'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'Заполняемость — аншлаг', 1.00, PCT, 'input')
V['fill_full'] = f"Вводные!$B${r}"; r += 1

r += 1
block(ws, r, '3. СТАВКИ ЭТАПА 1 — С ВАЛОВОГО СБОРА'); r += 1
put(ws, r, 'Налоги УСН, %', 0.06, PCT, 'input', 'Начисляется на весь валовой сбор', indent=1)
V['usn'] = f"Вводные!$B${r}"; r += 1
c = put(ws, r, 'Комиссия за продажу билетов, %', 0.05, PCT, 'input',
        'Вычитается сразу после УСН', indent=1)
V['comm'] = f"Вводные!$B${r}"; r += 1
c2 = put(ws, r, 'База для комиссии', 'Валовой сбор', None, 'text',
         'Операторы обычно берут процент от номинала билета, то есть от валового сбора', indent=1)
c2.comment = Comment('«Валовой сбор» — 5% считается со всей кассы.\n'
                     '«Сбор после вычета УСН» — 5% считается с того, что осталось после УСН 6%.\n'
                     'На базовых цифрах разница около 1 400 ₽. Проверьте формулировку в договоре с оператором.',
                     'model', width=420, height=110)
V['comm_base'] = f"Вводные!$B${r}"
dv_cb = DataValidation(type='list', formula1='"Валовой сбор,Сбор после вычета УСН"', allow_blank=False)
ws.add_data_validation(dv_cb); dv_cb.add(c2); r += 1
c = put(ws, r, 'Отчисления в РАО, %', 0.08, PCT, 'input', 'Начисляется на весь валовой сбор', indent=1)
c.comment = Comment('Ставка 8% — по вашим условиям. Базовый тариф РАО для концертов обычно 5%; '
                    'если в вашем договоре 8%, значит в него, вероятно, входят смежные права (ВОИС) '
                    'или это согласованная повышенная ставка. Стоит проверить в договоре — разница в 3 п.п. '
                    'от валового сбора это заметные деньги.', 'model', width=430, height=140)
V['rao'] = f"Вводные!$B${r}"; r += 1

r += 1
block(ws, r, '4. ТЕХНИЧЕСКИЕ РАСХОДЫ (АРЕНДА ЗВУКА И ОБЕСПЕЧЕНИЕ ПЛОЩАДКИ)'); r += 1
c = put(ws, r, 'Как считать: «Из сметы» или «Фиксированной суммой»', 'Из сметы', None, 'text',
        'Пока нет точных цифр — поставьте «Фиксированной суммой» и впишите её ниже', indent=1)
V['tech_mode'] = f"Вводные!$B${r}"
dv_t = DataValidation(type='list', formula1='"Из сметы,Фиксированной суммой"', allow_blank=False)
ws.add_data_validation(dv_t); dv_t.add(c); r += 1
put(ws, r, 'Фиксированная сумма технических расходов, ₽', 150000, RUB, 'input',
    'Используется, только если выбран режим «Фиксированной суммой»', indent=1)
V['tech_fixed'] = f"Вводные!$B${r}"; r += 1

r += 1
block(ws, r, '5. РАЗДЕЛ ПРИБЫЛИ С ПЛОЩАДКОЙ'); r += 1
put(ws, r, 'Доля организатора в прибыли, %', 0.50, PCT, 'input', indent=1)
V['share'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'Доля площадки в прибыли, %', f"=1-{V['share']}", PCT, 'calc', indent=1)
V['share_v'] = f"Вводные!$B${r}"; r += 1
c = put(ws, r, 'Убыток делится с площадкой? (Да/Нет)', 'Нет', None, 'text',
        'Если «Нет» — весь убыток ваш, а прибыль только наполовину', indent=1)
V['loss'] = f"Вводные!$B${r}"
dv_l = DataValidation(type='list', formula1='"Да,Нет"', allow_blank=False)
ws.add_data_validation(dv_l); dv_l.add(c); r += 1

r += 1
block(ws, r, '6. СТАВКИ ЭТАПА 2 — С ПРИБЫЛИ ОРГАНИЗАТОРА'); r += 1
put(ws, r, 'Налоги, %', 0.07, PCT, 'input', 'С половины прибыли, полученной от площадки', indent=1)
V['tax2'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'Банковские комиссии, %', 0.01, PCT, 'input', indent=1)
V['bank'] = f"Вводные!$B${r}"; r += 1
put(ws, r, 'ИТОГО ставка этапа 2, %', f"={V['tax2']}+{V['bank']}", PCT, 'calc', indent=1)
ws.cell(r, 2).fill = F_TOTAL; ws.cell(r, 1).font = Font(name=FONT, size=10, bold=True)
V['t2'] = f"Вводные!$B${r}"; r += 1

r += 1
block(ws, r, '7. ЧТО ВЫЧИТАТЬ ДО РАЗДЕЛА ПРИБЫЛИ (переговорный рычаг)'); r += 1
ws.cell(r, 1, 'По вашей схеме всё это вычитается ПОСЛЕ раздела, из вашей половины. '
              'Переключите на «Да», чтобы увидеть, как изменится экономика, если договориться '
              'вычитать эти расходы до раздела.').font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
ws.cell(r, 1).alignment = Alignment(wrap_text=True, vertical='top')
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
ws.row_dimensions[r].height = 30; r += 1
dv_p = DataValidation(type='list', formula1='"Да,Нет"', allow_blank=False)
ws.add_data_validation(dv_p)
for lab, key in [('Гонорары артистам вычитать до раздела?', 'fee_pre'),
                 ('Маркетинг и PR вычитать до раздела?', 'mkt_pre'),
                 ('Прочие расходы вычитать до раздела?', 'oth_pre')]:
    c = put(ws, r, lab, 'Нет', None, 'text', indent=1)
    dv_p.add(c); V[key] = f"Вводные!$B${r}"; r += 1

r += 1
block(ws, r, '8. ПРОЧЕЕ'); r += 1
put(ws, r, 'Резерв на непредвиденное, % от прочих расходов', 0.10, PCT, 'input', indent=1)
V['reserve'] = f"Вводные!$B${r}"; r += 1
ws.freeze_panes = 'A4'

# ================================================================ БИЛЕТЫ
ws = wb.create_sheet('Билеты')
B = {}
title(ws, 'БИЛЕТНАЯ МАТРИЦА',
      'Базовый сценарий строится здесь: цена, квота мест и ожидаемый процент продажи по каждой категории.')
widths(ws, {'A': 40, 'B': 13, 'C': 12, 'D': 14, 'E': 12, 'F': 16, 'G': 11, 'H': 56})
block(ws, 4, 'СТРУКТУРА БИЛЕТОВ')
hdr(ws, 5, ['Категория билета', 'Цена, ₽', 'Квота, мест', 'Ожид. продажа, %',
            'Продано, шт', 'Валовой сбор, ₽', 'Доля в сборе', 'Комментарий'])
tickets = [
    ('Ранняя пташка (early bird)',           1800,  60, 0.95, 'Первые 2 недели, ограниченная квота. Ранние деньги на маркетинг'),
    ('Стандарт (предпродажа)',               2500, 150, 0.60, 'Основная квота зала'),
    ('Стандарт (на входе, в день концерта)', 2800,  40, 0.50, 'Цена на входе выше — стимул покупать заранее'),
    ('Фан-зона у сцены / VIP',               4000,  30, 0.60, 'Первые ряды, отдельный вход'),
    ('Льготный (студенты)',                  1500,  10, 0.70, 'Заполняет зал в будни'),
    ('Промо, пресс, гости артиста',             0,  10, 1.00, 'Денег не приносят, но занимают места'),
]
R0 = 6
for i, (name, price, quota, sell, note) in enumerate(tickets):
    r = R0 + i
    ws.cell(r, 1, name).font = Font(name=FONT, size=10)
    for col, val, fmt in ((2, price, RUB), (3, quota, INT), (4, sell, PCT)):
        c = ws.cell(r, col, val); c.number_format = fmt
        c.font = Font(name=FONT, size=10, color=C_IN); c.fill = F_KEY
    ws.cell(r, 5, f'=ROUND(C{r}*D{r},0)').number_format = INT
    ws.cell(r, 6, f'=B{r}*E{r}').number_format = RUB
    ws.cell(r, 7, f'=IFERROR(F{r}/$F${R0+len(tickets)},0)').number_format = PCT
    ws.cell(r, 8, note).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
    for col in range(1, 9):
        ws.cell(r, col).border = BOX
RT = R0 + len(tickets)
ws.cell(RT, 1, 'ИТОГО').font = Font(name=FONT, size=10, bold=True)
for col, f, fmt in ((3, f'=SUM(C{R0}:C{RT-1})', INT), (5, f'=SUM(E{R0}:E{RT-1})', INT),
                    (6, f'=SUM(F{R0}:F{RT-1})', RUB), (7, f'=SUM(G{R0}:G{RT-1})', PCT)):
    c = ws.cell(RT, col, f); c.number_format = fmt; c.font = Font(name=FONT, size=10, bold=True)
for col in range(1, 9):
    ws.cell(RT, col).fill = F_TOTAL; ws.cell(RT, col).border = BOX
B['gross'], B['sold'], B['quotas'] = f"Билеты!$F${RT}", f"Билеты!$E${RT}", f"Билеты!$C${RT}"

r = RT + 2
block(ws, r, 'КОНТРОЛЬНЫЕ ПОКАЗАТЕЛИ'); r += 1
put(ws, r, 'Проверка: сумма квот = вместимость зала?',
    f'=IF({B["quotas"]}={V["cap"]},"OK — квоты сходятся с залом",'
    f'"ВНИМАНИЕ: квоты ("&{B["quotas"]}&") ≠ вместимость ("&{V["cap"]}&")")', None, 'calc')
ws.cell(r, 2).font = Font(name=FONT, size=10, bold=True); r += 1
put(ws, r, 'Продано билетов всего, шт', f'={B["sold"]}', INT, 'link'); r += 1
put(ws, r, '   в том числе платных, шт', f'=SUMIF(B{R0}:B{RT-1},">0",E{R0}:E{RT-1})', INT)
B['paid'] = f"Билеты!$B${r}"; r += 1
put(ws, r, 'Валовой сбор (box office), ₽', f'={B["gross"]}', RUB, 'link'); r += 1
put(ws, r, 'Средняя цена платного билета, ₽', f'=IFERROR({B["gross"]}/{B["paid"]},0)', RUB)
B['avg'] = f"Билеты!$B${r}"; r += 1
put(ws, r, 'Доход на одно место зала (yield), ₽', f'=IFERROR({B["gross"]}/{V["cap"]},0)', RUB); r += 1
put(ws, r, 'Фактическая заполняемость зала, %', f'=IFERROR({B["sold"]}/{V["cap"]},0)', PCT)
B['fill_base'] = f"Билеты!$B${r}"; r += 1
put(ws, r, 'Доля платных билетов от всех проходов, %', f'=IFERROR({B["paid"]}/{B["sold"]},0)', PCT)
B['paid_share'] = f"Билеты!$B${r}"; r += 1
ws.freeze_panes = 'A6'

# ================================================================ детальные листы расходов
def detail_sheet(name, head, sub, items, reserve=False):
    """Лист сметы: Статья | Кол-во | Ед. | Цена | Сумма | Комментарий. Возвращает карту строк."""
    s = wb.create_sheet(name)
    title(s, head, sub, width=6)
    widths(s, {'A': 46, 'B': 9, 'C': 10, 'D': 16, 'E': 16, 'F': 62})
    hdr(s, 4, ['Статья расхода', 'Кол-во', 'Ед.', 'Цена за ед., ₽', 'Сумма, ₽', 'Комментарий'])
    first = 5
    rr = first
    for art, qty, unit, price, note in items:
        s.cell(rr, 1, art).font = Font(name=FONT, size=10)
        for col, val, fmt in ((2, qty, INT), (4, price, RUB)):
            c = s.cell(rr, col, val); c.number_format = fmt
            c.font = Font(name=FONT, size=10, color=C_IN); c.fill = F_KEY
        c = s.cell(rr, 3, unit); c.font = Font(name=FONT, size=9, color=C_MUTED)
        c.alignment = Alignment(horizontal='center')
        c = s.cell(rr, 5, f'=B{rr}*D{rr}'); c.number_format = RUB; c.font = Font(name=FONT, size=10)
        s.cell(rr, 6, note).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
        for col in range(1, 7):
            s.cell(rr, col).border = BOX
        rr += 1
    last = rr - 1
    detail_rows = list(range(first, last + 1))
    if reserve:
        s.cell(rr, 1, 'Резерв на непредвиденное').font = Font(name=FONT, size=10)
        c = s.cell(rr, 5, f'=SUM(E{first}:E{last})*{V["reserve"]}')
        c.number_format = RUB; c.font = Font(name=FONT, size=10)
        s.cell(rr, 6, 'Ставка резерва задаётся на листе «Вводные»').font = Font(
            name=FONT, size=9, italic=True, color=C_MUTED)
        for col in range(1, 7):
            s.cell(rr, col).border = BOX
        detail_rows.append(rr)
        last = rr
        rr += 1
    s.cell(rr, 1, 'ИТОГО').font = Font(name=FONT, size=12, bold=True)
    c = s.cell(rr, 5, f'=SUM(E{first}:E{last})')
    c.number_format = RUB; c.font = Font(name=FONT, size=12, bold=True)
    for col in range(1, 7):
        s.cell(rr, col).fill = F_RESULT
        s.cell(rr, col).border = Border(top=MED, bottom=MED)
    s.row_dimensions[rr].height = 22
    s.freeze_panes = 'A5'
    return {'sheet': name, 'rows': detail_rows, 'total': f"{name}!$E${rr}", 'sumcol': 'E'}

TECH = detail_sheet('Технические',
    'ТЕХНИЧЕСКИЕ РАСХОДЫ: АРЕНДА ЗВУКА И ОБЕСПЕЧЕНИЕ ПЛОЩАДКИ',
    'Этап 1 — вычитается из валового сбора ДО раздела прибыли с площадкой. '
    'Пришлёте технический райдер — заменю строки на реальные позиции и цены.',
    [('Аренда зала (смена)',                    1, 'смена',  20000, 'При сделке 50/50 часто не выставляется — уточните в договоре'),
     ('Аренда звукового комплекта PA',          1, 'компл.', 25000, 'Основная позиция технической сметы'),
     ('Микрофоны, радиосистемы, стойки',        1, 'компл.',  8000, 'Под конкретный состав почти всегда докупается'),
     ('Мониторная линия / in-ear',              1, 'компл.', 10000, 'Критично для качества исполнения на сцене'),
     ('Звукорежиссёр FOH',                      1, 'смена',  15000, 'Свой инженер — предсказуемый звук'),
     ('Мониторный инженер',                     0, 'смена',  12000, 'В клубе часто совмещается с FOH'),
     ('Световое оборудование',                  1, 'компл.', 15000, ''),
     ('Художник по свету / оператор',           1, 'смена',   8000, 'Свет под программу, а не «дискотека по кнопке»'),
     ('Бэклайн: барабаны, усилители, клавиши',  0, 'компл.', 20000, 'Поставьте 1, если бэклайн привозной'),
     ('Экран, проекция, видеоконтент',          0, 'компл.', 18000, 'Поставьте 1, если в программе есть видеоряд'),
     ('Электрика, кабели, распределение',       1, 'компл.',  3000, ''),
     ('Монтаж, демонтаж, погрузка',             3, 'чел.',    3500, 'Разгрузка и погрузка оборудования'),
     ('Охрана',                                 3, 'чел.',    4000, 'Ориентир — 1 человек на 75–100 гостей'),
     ('Билетный контроль и гардероб',           3, 'чел.',    3000, ''),
     ('Уборка до и после',                      2, 'чел.',    3000, ''),
     ('Дежурный медик',                         1, 'смена',   5000, 'Требование для массовых мероприятий'),
     ('Администратор площадки',                 1, 'смена',   8000, '')])

FEES = detail_sheet('Гонорары',
    'ГОНОРАРЫ АРТИСТАМ',
    'Этап 2 — по вашей схеме вычитается из половины прибыли, уже полученной организатором. '
    'Переключатель «вычитать до раздела» — на листе «Вводные».',
    [('Артист / хедлайнер',              1, 'выступл.', 25000, 'Основной гонорар по договору'),
     ('Музыкант: гитара',                1, 'выступл.',  8000, ''),
     ('Музыкант: бас',                   1, 'выступл.',  8000, ''),
     ('Музыкант: барабаны',              1, 'выступл.',  8000, ''),
     ('Музыкант: клавиши',               0, 'выступл.',  8000, 'Поставьте 1, если есть в составе'),
     ('Разогрев / support act',          0, 'выступл.', 10000, 'Часто выступает за билеты и промо'),
     ('Ведущий / конферансье',           0, 'выступл.',  8000, ''),
     ('Налоги и взносы с гонораров',     0, 'компл.',   15000, 'Если музыканты не самозанятые — нагрузка ложится на вас')])

OTHER = detail_sheet('Прочие',
    'ПРОЧИЕ РАСХОДЫ',
    'Этап 2 — вычитается из половины прибыли организатора. Резерв считается процентом от суммы строк выше.',
    [('Полиграфия: афиши, флаеры',       1, 'тираж',    12000, 'Печать. Размещение — в бюджете маркетинга'),
     ('Бейджи, браслеты, программки',    1, 'тираж',     5000, ''),
     ('Оформление сцены и зала, декор',  0, 'компл.',   15000, 'Сильно влияет на восприятие и качество контента'),
     ('Репетиции, аренда репбазы',       2, 'смена',     6000, ''),
     ('Транспорт оборудования',          2, 'рейс',      6000, 'Туда и обратно'),
     ('Трансфер и проживание команды',   0, 'компл.',   25000, 'Заполните, если команда не из этого города'),
     ('Кейтеринг и райдер бэкстейджа',  15, 'чел.',       700, 'По числу людей на площадке, включая техников'),
     ('Фотограф',                        1, 'смена',    12000, 'Контент окупается в промо следующего концерта'),
     ('Видеосъёмка концерта',            0, 'смена',    25000, 'Материал для клипов и питчей площадкам'),
     ('Юридическое сопровождение',       1, 'проект',    6000, 'Договоры с площадкой, артистами, лицензия РАО'),
     ('Онлайн-касса, ОФД',               0, 'проект',    3000, 'Если часть билетов продаёте сами'),
     ('Страхование мероприятия',         0, 'полис',    12000, 'Рекомендую при бюджете свыше 500 000 ₽')],
    reserve=True)

# ================================================================ МАРКЕТИНГ
ws = wb.create_sheet('Маркетинг')
title(ws, 'МАРКЕТИНГ И PR: БЮДЖЕТ, ВОРОНКА, СТОИМОСТЬ БИЛЕТА',
      'Этап 2 — вычитается из половины прибыли организатора. Каждый канал считается до билета: '
      'охват → отклик → покупка.')
widths(ws, {'A': 40, 'B': 14, 'C': 15, 'D': 13, 'E': 15, 'F': 14, 'G': 15, 'H': 54})
block(ws, 4, 'КАНАЛЫ ПРОДВИЖЕНИЯ')
hdr(ws, 5, ['Канал', 'Бюджет, ₽', 'Прогноз охвата, чел.', 'Отклик (CTR), %',
            'Конверсия в покупку, %', 'Прогноз билетов, шт', 'CPA, ₽ за билет', 'Комментарий'])
MR0 = 6
channels = [
    ('Таргетированная реклама VK',             20000, 120000, 0.012, 0.030, 'Основной платный канал. Гео + интересы + look-alike'),
    ('Посевы в Telegram-каналах',              15000,  55000, 0.020, 0.040, 'Городские и жанровые каналы. Просите статистику до оплаты'),
    ('Блогеры и лидеры мнений',                10000,  35000, 0.025, 0.035, 'Часть работает по бартеру за билеты'),
    ('Наружная реклама и расклейка афиш',       5000,  20000, 0.005, 0.050, 'Плохо атрибутируется — нужен отдельный промокод'),
    ('Городские афиши: Яндекс.Афиша, KudaGo',      0,  25000, 0.010, 0.040, 'Бесплатно. Подавать за 3–4 недели'),
    ('PR: пресс-релиз, СМИ, интервью',          3000,  15000, 0.010, 0.030, 'Даёт доверие и перепечатки, а не прямые продажи'),
    ('Email и база подписчиков',                1000,   6000, 0.120, 0.080, 'Самый дешёвый билет. Базу надо собирать заранее'),
    ('Продакшн контента: дизайн, тизер, фото',  6000,      0, 0.000, 0.000, 'Не продаёт напрямую, но без него не работают каналы выше'),
]
for i, (name, budget, reach, ctr, conv, note) in enumerate(channels):
    r = MR0 + i
    ws.cell(r, 1, name).font = Font(name=FONT, size=10)
    for col, val, fmt in ((2, budget, RUB), (3, reach, INT), (4, ctr, '0.00%'), (5, conv, '0.00%')):
        c = ws.cell(r, col, val); c.number_format = fmt
        c.font = Font(name=FONT, size=10, color=C_IN); c.fill = F_KEY
    ws.cell(r, 6, f'=ROUND(C{r}*D{r}*E{r},0)').number_format = INT
    ws.cell(r, 7, f'=IFERROR(B{r}/F{r},0)').number_format = RUB
    ws.cell(r, 8, note).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
    for col in range(1, 9):
        ws.cell(r, col).border = BOX
MT = MR0 + len(channels)
ws.cell(MT, 1, 'ИТОГО МАРКЕТИНГ И PR').font = Font(name=FONT, size=12, bold=True)
for col, f, fmt in ((2, f'=SUM(B{MR0}:B{MT-1})', RUB), (3, f'=SUM(C{MR0}:C{MT-1})', INT),
                    (6, f'=SUM(F{MR0}:F{MT-1})', INT), (7, f'=IFERROR(B{MT}/F{MT},0)', RUB)):
    c = ws.cell(MT, col, f); c.number_format = fmt; c.font = Font(name=FONT, size=12, bold=True)
for col in range(1, 9):
    ws.cell(MT, col).fill = F_RESULT
    ws.cell(MT, col).border = Border(top=MED, bottom=MED)
ws.row_dimensions[MT].height = 22
MKT = {'sheet': 'Маркетинг', 'rows': list(range(MR0, MT)),
       'total': f"Маркетинг!$B${MT}", 'sumcol': 'B'}

r = MT + 2
block(ws, r, 'ПРОВЕРКА ЗДОРОВЬЯ МАРКЕТИНГА'); r += 1
put(ws, r, 'Бюджет маркетинга и PR, ₽', f'={MKT["total"]}', RUB, 'link'); r += 1
put(ws, r, 'Прогноз билетов от маркетинга, шт', f'=Маркетинг!$F${MT}', INT, 'link'); r += 1
put(ws, r, 'План продаж по билетной матрице, шт', f'={B["paid"]}', INT, 'link'); r += 1
put(ws, r, 'Покрытие плана продаж маркетингом, %', f'=IFERROR(Маркетинг!$F${MT}/{B["paid"]},0)', PCT,
    note='Ниже 100% — план продаж ничем не обеспечен')
COV = f"Маркетинг!$B${r}"; r += 1
put(ws, r, 'CPA к средней цене билета, %', f'=IFERROR(Маркетинг!$G${MT}/{B["avg"]},0)', PCT,
    note='Здоровый диапазон — до 25%'); r += 1
put(ws, r, 'Доля маркетинга в валовом сборе, %', f'=IFERROR({MKT["total"]}/{B["gross"]},0)', PCT,
    note='Ориентир для клубного концерта — 10–15%')
MSH = f"Маркетинг!$B${r}"; r += 1
put(ws, r, 'Вердикт',
    f'=IF({MSH}>0.2,"ПЕРЕРАСХОД: маркетинг забирает больше 20% сбора",'
    f'IF({COV}<1,"РИСК: маркетинг не покрывает план продаж",'
    f'"Норма: бюджет и план продаж сбалансированы"))', None, 'calc')
ws.cell(r, 2).font = Font(name=FONT, size=10, bold=True)
ws.conditional_formatting.add(f'B{r}', FormulaRule(
    formula=[f'$B${r}<>"Норма: бюджет и план продаж сбалансированы"'],
    fill=PatternFill('solid', fgColor='FFC7CE'), font=Font(color='9C0006', bold=True)))
ws.freeze_panes = 'A6'

# ================================================================ ЭКОНОМИКА
ws = wb.create_sheet('Экономика')
P = {}
title(ws, 'ЭКОНОМИКА КОНЦЕРТА',
      'Этап 1: валовой сбор − УСН − РАО − технические расходы = прибыль. Прибыль делится пополам. '
      'Этап 2: из половины организатора вычитаются налоги 7%, банк 1%, гонорары, маркетинг и прочие расходы.')
widths(ws, {'A': 54, 'B': 16, 'C': 18, 'D': 11, 'E': 60})
hdr(ws, 4, ['Показатель', 'Расшифровка, ₽', 'Сумма, ₽', '% от сбора', 'Комментарий'])
ws.sheet_properties.outlinePr.summaryBelow = False

TECH_TOTAL = (f'IF({V["tech_mode"]}="Фиксированной суммой",{V["tech_fixed"]},{TECH["total"]})')
COMM_BASE = f'IF({V["comm_base"]}="Валовой сбор",{B["gross"]},{B["gross"]}*(1-{V["usn"]}))'
# доля валового сбора, доживающая до строки «Прибыль» (до вычета расходов)
A_RATE = (f'(1-{V["usn"]}-{V["rao"]}-{V["comm"]}*IF({V["comm_base"]}="Валовой сбор",1,1-{V["usn"]}))')
pr = 5
GROSS_ROW = 6

def line(label, formula, fmt=RUB, bold=False, fill=None, size=10, indent=1,
         note=None, pct=True, kind='calc'):
    """Строка водопада: сумма в столбце C."""
    global pr
    lc = ws.cell(pr, 1, label)
    lc.font = Font(name=FONT, size=size, bold=bold)
    lc.alignment = Alignment(indent=indent)
    c = ws.cell(pr, 3, formula)
    if fmt: c.number_format = fmt
    c.font = Font(name=FONT, size=size, bold=bold, color=(C_LINK if kind == 'link' else C_CALC))
    if pct and fmt == RUB:
        p = ws.cell(pr, 4, f'=IFERROR(C{pr}/$C${GROSS_ROW},0)')
        p.number_format = PCT; p.font = Font(name=FONT, size=9, color=C_MUTED)
        p.alignment = Alignment(horizontal='center')
    if note:
        ws.cell(pr, 5, note).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
    for col in range(1, 6):
        ws.cell(pr, col).border = BOX
        if fill: ws.cell(pr, col).fill = fill
    addr = f"Экономика!$C${pr}"
    pr += 1
    return addr

def breakdown(src, sign='-'):
    """Расшифровка: каждая строка сметы отдельной строкой, сумма в столбце B."""
    global pr
    sh, col = src['sheet'], src['sumcol']
    for dr in src['rows']:
        a = ws.cell(pr, 1, f"={sh}!$A${dr}")
        a.font = Font(name=FONT, size=9, color=C_MUTED)
        a.alignment = Alignment(indent=3)
        c = ws.cell(pr, 2, f"={sign}{sh}!${col}${dr}")
        c.number_format = RUB; c.font = Font(name=FONT, size=9, color=C_MUTED)
        for cc in range(1, 6):
            ws.cell(pr, cc).border = BOX
            ws.cell(pr, cc).fill = F_ZEBRA
        ws.row_dimensions[pr].outlineLevel = 1
        pr += 1

def stage(text):
    global pr
    block(ws, pr, text, width=5); pr += 1

stage('ЭТАП 1 — ДО РАЗДЕЛА ПРИБЫЛИ С ПЛОЩАДКОЙ')
assert pr == GROSS_ROW, pr
P['gross'] = line('1. ВАЛОВОЙ СБОР', f'={B["gross"]}', bold=True, fill=F_TOTAL, indent=0,
                  size=11, kind='link', note='Вся выручка от продажи билетов — лист «Билеты»')
G = P['gross']
P['usn'] = line('2. Налоги УСН 6%', f'=-{G}*{V["usn"]}', note='Ставка — на листе «Вводные»')
P['comm'] = line('3. Комиссия за продажу билетов 5%', f'=-{COMM_BASE}*{V["comm"]}',
                 note='База — валовой сбор или сбор после вычета УСН, переключатель на листе «Вводные»')
P['rao'] = line('4. Отчисления в РАО 8%', f'=-{G}*{V["rao"]}',
                note='Ставка 8% по вашим условиям. Базовый тариф РАО для концертов обычно 5% — стоит сверить с договором')
P['tech'] = line('5. Технические расходы: аренда звука и обеспечение площадки',
                 f'=-{TECH_TOTAL}', bold=True,
                 note='Режим «из сметы» или «фиксированной суммой» — на листе «Вводные»')
breakdown(TECH)
P['fee_pre'] = line('Гонорары артистам — если вычитаются до раздела',
                    f'=-IF({V["fee_pre"]}="Да",{FEES["total"]},0)',
                    note='По вашей схеме = 0. Переключатель на листе «Вводные»')
P['mkt_pre'] = line('Маркетинг и PR — если вычитается до раздела',
                    f'=-IF({V["mkt_pre"]}="Да",{MKT["total"]},0)')
P['oth_pre'] = line('Прочие расходы — если вычитаются до раздела',
                    f'=-IF({V["oth_pre"]}="Да",{OTHER["total"]},0)')
P['profit'] = line('6. ПРИБЫЛЬ',
                   f'={G}+{P["usn"]}+{P["comm"]}+{P["rao"]}+{P["tech"]}'
                   f'+{P["fee_pre"]}+{P["mkt_pre"]}+{P["oth_pre"]}',
                   bold=True, fill=F_TOTAL, indent=0, size=12)
ws.row_dimensions[pr - 1].height = 22

pr += 1
stage('РАЗДЕЛ ПРИБЫЛИ ПОПОЛАМ')
P['v_share'] = line('Доля площадки',
    f'=-IF({P["profit"]}>=0,{P["profit"]}*{V["share_v"]},IF({V["loss"]}="Да",{P["profit"]}*{V["share_v"]},0))',
    note='При убытке площадка не участвует, если в договоре не сказано иное')
P['org_profit'] = line('ПРИБЫЛЬ ОРГАНИЗАТОРА', f'={P["profit"]}+{P["v_share"]}',
                       bold=True, fill=F_STAGE, indent=0, size=12,
                       note='Это база, из которой дальше вычитается всё на этапе 2')
ws.row_dimensions[pr - 1].height = 22

pr += 1
stage('ЭТАП 2 — РАСХОДЫ ИЗ ПРИБЫЛИ ОРГАНИЗАТОРА')
P['tax2'] = line('Налоги 7%', f'=-MAX(0,{P["org_profit"]})*{V["tax2"]}',
                 note='С прибыли организатора, полученной от площадки')
P['bank'] = line('Банковские комиссии 1%', f'=-MAX(0,{P["org_profit"]})*{V["bank"]}')
P['fees'] = line('Гонорары артистам', f'=-IF({V["fee_pre"]}="Нет",{FEES["total"]},0)', bold=True)
breakdown(FEES)
P['mkt'] = line('Маркетинг и PR', f'=-IF({V["mkt_pre"]}="Нет",{MKT["total"]},0)', bold=True)
breakdown(MKT)
P['other'] = line('Прочие расходы', f'=-IF({V["oth_pre"]}="Нет",{OTHER["total"]},0)', bold=True)
breakdown(OTHER)
P['net'] = line('ЧИСТЫЙ ДОХОД ОРГАНИЗАТОРА',
                f'={P["org_profit"]}+{P["tax2"]}+{P["bank"]}+{P["fees"]}+{P["mkt"]}+{P["other"]}',
                bold=True, indent=0, size=14)
for col in range(1, 6):
    ws.cell(pr - 1, col).fill = F_RESULT
    ws.cell(pr - 1, col).border = Border(top=MED, bottom=MED)
ws.row_dimensions[pr - 1].height = 28

pr += 1
stage('КЛЮЧЕВЫЕ МЕТРИКИ И ТОЧКА БЕЗУБЫТОЧНОСТИ')
PRE  = (f'({TECH_TOTAL}+IF({V["fee_pre"]}="Да",{FEES["total"]},0)'
        f'+IF({V["mkt_pre"]}="Да",{MKT["total"]},0)+IF({V["oth_pre"]}="Да",{OTHER["total"]},0))')
POST = (f'(IF({V["fee_pre"]}="Нет",{FEES["total"]},0)+IF({V["mkt_pre"]}="Нет",{MKT["total"]},0)'
        f'+IF({V["oth_pre"]}="Нет",{OTHER["total"]},0))')
P['pre']  = line('Расходы, вычитаемые до раздела (этап 1)', f'={PRE}', pct=False)
P['post'] = line('Расходы, вычитаемые после раздела (этап 2)', f'={POST}', pct=False)
P['be_gross'] = line('Валовой сбор в точке безубыточности, ₽',
    f'=IFERROR(({PRE}+{POST}/((1-{V["t2"]})*{V["share"]}))/{A_RATE},0)', pct=False, bold=True,
    note='Сколько нужно собрать кассы, чтобы чистый доход организатора вышел в ноль')
P['be'] = line('Точка безубыточности, платных билетов',
    f'=IFERROR(ROUNDUP({P["be_gross"]}/{B["avg"]},0),0)', INT, pct=False, bold=True)
P['be_fill'] = line('Точка безубыточности, % заполнения зала',
    f'=IFERROR({P["be"]}/{B["paid_share"]}/{V["cap"]},0)', PCT, pct=False, bold=True)
P['safety'] = line('Запас прочности (насколько план выше нуля), %',
    f'=IFERROR(({B["paid"]}-{P["be"]})/{B["paid"]},0)', PCT, pct=False,
    note='Меньше 15% — проект висит на волоске')
P['roi'] = line('Рентабельность к валовому сбору, %', f'=IFERROR({P["net"]}/{G},0)', PCT, pct=False)
P['per_ticket'] = line('Чистый доход на один проданный билет, ₽',
    f'=IFERROR({P["net"]}/{B["sold"]},0)', pct=False)
P['verdict'] = line('ВЕРДИКТ ПО ПРОЕКТУ',
    f'=IF({P["net"]}<0,"УБЫТОК. Нужен сбор от "&TEXT({P["be_gross"]},"# ##0")&" ₽ ('
    f'"&TEXT({P["be_fill"]},"0%")&" зала), чтобы выйти в ноль",'
    f'IF({P["safety"]}<0.15,"НА ГРАНИ. Запас прочности меньше 15%",'
    f'IF({P["roi"]}<0.1,"СЛАБО. Рентабельность ниже 10% от сбора",'
    f'"ЗДОРОВО. Проект окупается с запасом")))', None, pct=False, bold=True)
VROW = pr - 1
ws.conditional_formatting.add(f'C{VROW}', FormulaRule(formula=[f'LEFT($C${VROW},6)="УБЫТОК"'],
    fill=PatternFill('solid', fgColor='FFC7CE'), font=Font(color='9C0006', bold=True)))
ws.conditional_formatting.add(f'C{VROW}', FormulaRule(formula=[f'LEFT($C${VROW},7)="ЗДОРОВО"'],
    fill=PatternFill('solid', fgColor='C6EFCE'), font=Font(color='006100', bold=True)))
ws.freeze_panes = 'A5'

# ================================================================ СЦЕНАРИИ
ws = wb.create_sheet('Сценарии')
title(ws, 'СЦЕНАРИИ: ОТ ПРОВАЛА ДО АНШЛАГА',
      'Цены и вся смета во всех сценариях одинаковые — меняется только заполняемость зала. '
      'Последний столбец показывает, где проходит граница нуля.')
widths(ws, {'A': 50, 'B': 17, 'C': 17, 'D': 17, 'E': 17, 'F': 19, 'G': 46})
hdr(ws, 4, ['Показатель', 'Пессимистичный', 'БАЗОВЫЙ', 'Оптимистичный', 'Аншлаг',
            'Точка безубыточности', 'Комментарий'])
cols = ['B', 'C', 'D', 'E', 'F']
fills_ref = [V['fill_pess'], B['fill_base'], V['fill_opt'], V['fill_full'], P['be_fill']]
rows_def = [
    ('Заполняемость зала, %',                       PCT, 'fill'),
    ('Продано билетов всего, шт',                   INT, 'sold'),
    ('   в том числе платных, шт',                  INT, 'paid'),
    ('Средняя цена платного билета, ₽',             RUB, 'avg'),
    ('1. ВАЛОВОЙ СБОР',                             RUB, 'gross'),
    ('2. Налоги УСН 6%',                            RUB, 'usn'),
    ('3. Комиссия за продажу билетов 5%',           RUB, 'comm'),
    ('4. Отчисления в РАО 8%',                      RUB, 'rao'),
    ('5. Технические расходы',                      RUB, 'tech'),
    ('   гонорары — если до раздела',               RUB, 'feepre'),
    ('   маркетинг — если до раздела',              RUB, 'mktpre'),
    ('   прочие — если до раздела',                 RUB, 'othpre'),
    ('6. ПРИБЫЛЬ',                                  RUB, 'profit'),
    ('   доля площадки',                            RUB, 'vshare'),
    ('ПРИБЫЛЬ ОРГАНИЗАТОРА',                        RUB, 'org'),
    ('   налоги 7%',                                RUB, 'tax2'),
    ('   банковские комиссии 1%',                   RUB, 'bank'),
    ('   гонорары артистам',                        RUB, 'fees'),
    ('   маркетинг и PR',                           RUB, 'mkt'),
    ('   прочие расходы',                           RUB, 'other'),
    ('ЧИСТЫЙ ДОХОД ОРГАНИЗАТОРА',                   RUB, 'net'),
    ('Рентабельность к валовому сбору, %',          PCT, 'roi'),
    ('Отклонение от базового сценария, ₽',          RUB, 'delta'),
]
SR = {k: 5 + i for i, (_, _, k) in enumerate(rows_def)}
notes = {'fill': 'Пессимистичный и оптимистичный задаются на листе «Вводные»',
         'profit': 'Именно эта строка делится с площадкой пополам',
         'org': 'База для всех вычетов этапа 2',
         'net': 'Деньги, которые реально останутся у вас'}
for lab, fmt, key in rows_def:
    r = SR[key]
    strong = key in ('gross', 'profit', 'org', 'net')
    lc = ws.cell(r, 1, lab)
    lc.font = Font(name=FONT, size=10, bold=strong)
    if key in notes:
        ws.cell(r, 7, notes[key]).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
    for ci, col in enumerate(cols):
        base = (ci == 1)
        f = {
          'fill':   f'={fills_ref[ci]}',
          'sold':   (f'={B["sold"]}' if base else f'=ROUND({V["cap"]}*{col}{SR["fill"]},0)'),
          'paid':   (f'={B["paid"]}' if base else f'=ROUND({col}{SR["sold"]}*{B["paid_share"]},0)'),
          'avg':    f'={B["avg"]}',
          'gross':  (f'={B["gross"]}' if base else f'={col}{SR["paid"]}*{col}{SR["avg"]}'),
          'usn':    f'=-{col}{SR["gross"]}*{V["usn"]}',
          'comm':   f'=-IF({V["comm_base"]}="Валовой сбор",{col}{SR["gross"]},'
                    f'{col}{SR["gross"]}*(1-{V["usn"]}))*{V["comm"]}',
          'rao':    f'=-{col}{SR["gross"]}*{V["rao"]}',
          'tech':   f'=-{TECH_TOTAL}',
          'feepre': f'=-IF({V["fee_pre"]}="Да",{FEES["total"]},0)',
          'mktpre': f'=-IF({V["mkt_pre"]}="Да",{MKT["total"]},0)',
          'othpre': f'=-IF({V["oth_pre"]}="Да",{OTHER["total"]},0)',
          'profit': f'=SUM({col}{SR["gross"]}:{col}{SR["othpre"]})',
          'vshare': f'=-IF({col}{SR["profit"]}>=0,{col}{SR["profit"]}*{V["share_v"]},'
                    f'IF({V["loss"]}="Да",{col}{SR["profit"]}*{V["share_v"]},0))',
          'org':    f'={col}{SR["profit"]}+{col}{SR["vshare"]}',
          'tax2':   f'=-MAX(0,{col}{SR["org"]})*{V["tax2"]}',
          'bank':   f'=-MAX(0,{col}{SR["org"]})*{V["bank"]}',
          'fees':   f'=-IF({V["fee_pre"]}="Нет",{FEES["total"]},0)',
          'mkt':    f'=-IF({V["mkt_pre"]}="Нет",{MKT["total"]},0)',
          'other':  f'=-IF({V["oth_pre"]}="Нет",{OTHER["total"]},0)',
          'net':    f'={col}{SR["org"]}+SUM({col}{SR["tax2"]}:{col}{SR["other"]})',
          'roi':    f'=IFERROR({col}{SR["net"]}/{col}{SR["gross"]},0)',
          'delta':  f'={col}{SR["net"]}-$C${SR["net"]}',
        }[key]
        c = ws.cell(r, ci + 2, f); c.number_format = fmt
        c.font = Font(name=FONT, size=10, bold=strong); c.border = BOX
        if key in ('gross', 'profit'): c.fill = F_TOTAL
        if key == 'org': c.fill = F_STAGE
        if key == 'net': c.fill = F_RESULT
        if base and key != 'delta':
            c.border = Border(left=MED, right=MED, top=THIN, bottom=THIN)
    if key == 'net': ws.row_dimensions[r].height = 22
for k in ('net', 'profit', 'org'):
    ws.conditional_formatting.add(f'B{SR[k]}:F{SR[k]}', CellIsRule(
        operator='lessThan', formula=['0'],
        fill=PatternFill('solid', fgColor='FFC7CE'), font=Font(color='9C0006', bold=True)))
ws.freeze_panes = 'B5'

# ================================================================ ЧУВСТВИТЕЛЬНОСТЬ
ws = wb.create_sheet('Чувствительность')
title(ws, 'ЧУВСТВИТЕЛЬНОСТЬ: ЦЕНА ПРОТИВ ЗАПОЛНЯЕМОСТИ',
      'Зелёное — прибыль, красное — убыток. Верхняя таблица — прибыль до раздела, '
      'нижняя — то, что остаётся организатору после раздела и расходов этапа 2.')
widths(ws, {'A': 22})
for col in range(2, 9):
    ws.column_dimensions[get_column_letter(col)].width = 15
prices = [1500, 2000, 2500, 3000, 3500, 4000, 4500]
fillsv = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
CAP, PS = V['cap'], B['paid_share']
LASTCOL = get_column_letter(1 + len(prices))

def grid(top_row, heading, cellf):
    ws.cell(top_row - 1, 1, heading).font = Font(name=FONT, size=11, bold=True, color='1F3864')
    h = ws.cell(top_row, 1, 'Заполняемость \\ Средняя цена')
    h.font = Font(name=FONT, size=9, bold=True, color='FFFFFF')
    h.fill = PatternFill('solid', fgColor='4472C4')
    h.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    h.border = BOX
    ws.row_dimensions[top_row].height = 32
    for j, p_ in enumerate(prices):
        c = ws.cell(top_row, 2 + j, p_); c.number_format = RUB
        c.font = Font(name=FONT, size=10, bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='4472C4')
        c.alignment = Alignment(horizontal='center'); c.border = BOX
    for i, fv in enumerate(fillsv):
        r = top_row + 1 + i
        c = ws.cell(r, 1, fv); c.number_format = PCT
        c.font = Font(name=FONT, size=10, bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='4472C4')
        c.alignment = Alignment(horizontal='center'); c.border = BOX
        for j in range(len(prices)):
            cc = ws.cell(r, 2 + j, cellf(r, get_column_letter(2 + j), top_row, i))
            cc.number_format = RUB; cc.font = Font(name=FONT, size=10); cc.border = BOX
    bottom = top_row + len(fillsv)
    ws.conditional_formatting.add(f'B{top_row+1}:{LASTCOL}{bottom}', ColorScaleRule(
        start_type='num', start_value=-300000, start_color='F8696B',
        mid_type='num', mid_value=0, mid_color='FFEB84',
        end_type='num', end_value=500000, end_color='63BE7B'))
    return bottom

T1 = 5
b1 = grid(T1, 'ПРИБЫЛЬ ДО РАЗДЕЛА С ПЛОЩАДКОЙ (этап 1), ₽',
    lambda r, col, top, i:
        f'=({CAP}*$A{r}*{PS}*{col}${top})*{A_RATE}-{P["pre"]}')
T2 = b1 + 3
b2 = grid(T2, 'ЧИСТЫЙ ДОХОД ОРГАНИЗАТОРА после раздела и расходов этапа 2, ₽',
    lambda r, col, top, i: (
        f'=IF({col}{T1+1+i}>=0,{col}{T1+1+i}*{V["share"]},'
        f'IF({V["loss"]}="Да",{col}{T1+1+i}*{V["share"]},{col}{T1+1+i}))'
        f'-MAX(0,IF({col}{T1+1+i}>=0,{col}{T1+1+i}*{V["share"]},'
        f'IF({V["loss"]}="Да",{col}{T1+1+i}*{V["share"]},{col}{T1+1+i})))*{V["t2"]}-{P["post"]}'))

r2 = b2 + 3
ws.cell(r2, 1, 'Сколько нужно продать при разной средней цене, чтобы выйти в ноль').font = Font(
    name=FONT, size=11, bold=True, color='1F3864')
r2 += 1
ws.cell(r2, 1, 'Средняя цена, ₽').font = Font(name=FONT, size=9, bold=True, color='FFFFFF')
ws.cell(r2, 1).fill = PatternFill('solid', fgColor='4472C4'); ws.cell(r2, 1).border = BOX
for j, p_ in enumerate(prices):
    c = ws.cell(r2, 2 + j, p_); c.number_format = RUB
    c.font = Font(name=FONT, size=10, bold=True, color='FFFFFF')
    c.fill = PatternFill('solid', fgColor='4472C4')
    c.alignment = Alignment(horizontal='center'); c.border = BOX
for off, lab, fmt in ((1, 'Нужно продать платных билетов, шт', INT),
                      (2, 'Это заполняемость зала, %', PCT)):
    rr = r2 + off
    ws.cell(rr, 1, lab).font = Font(name=FONT, size=10, bold=(off == 2))
    for j in range(len(prices)):
        col = get_column_letter(2 + j)
        f = (f'=IFERROR(ROUNDUP({P["be_gross"]}/{col}${r2},0),"н/д")' if off == 1
             else f'=IFERROR({col}{r2+1}/{PS}/{CAP},"н/д")')
        c = ws.cell(rr, 2 + j, f); c.number_format = fmt
        c.font = Font(name=FONT, size=10, bold=(off == 2)); c.border = BOX
        c.alignment = Alignment(horizontal='center')
ws.conditional_formatting.add(f'B{r2+2}:{LASTCOL}{r2+2}', CellIsRule(
    operator='greaterThan', formula=['1'],
    fill=PatternFill('solid', fgColor='FFC7CE'), font=Font(color='9C0006', bold=True)))
ws.freeze_panes = 'B6'

# ================================================================ ДАШБОРД
ws = wb.create_sheet('Дашборд')
wb.move_sheet('Дашборд', offset=-(len(wb.sheetnames) - 1))
title(ws, 'КОНЦЕРТ: ИТОГОВАЯ ЭКОНОМИКА', None, width=6)
widths(ws, {'A': 3, 'B': 42, 'C': 20, 'D': 4, 'E': 42, 'F': 20})
ws['A2'] = ('Один экран с главными цифрами. Всё пересчитывается автоматически — меняйте вводные '
            'на листах «Вводные», «Билеты», «Технические», «Гонорары», «Маркетинг», «Прочие».')
ws['A2'].font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
r = 4
ws.cell(r, 2, 'Проект').font = Font(name=FONT, size=10, bold=True, color='1F3864')
ws.cell(r, 3, f'={V["name"]}').font = Font(name=FONT, size=10, bold=True)
ws.cell(r, 5, 'Дата / площадка').font = Font(name=FONT, size=10, bold=True, color='1F3864')
ws.cell(r, 6, f'={V["date"]}&" · "&{V["venue"]}').font = Font(name=FONT, size=10)
r += 2

def tile(row, col, label, formula, fmt, big=False):
    lc = ws.cell(row, col, label)
    lc.font = Font(name=FONT, size=9, bold=True, color='44546A')
    lc.alignment = Alignment(vertical='center', wrap_text=True)
    c = ws.cell(row, col + 1, formula); c.number_format = fmt
    c.font = Font(name=FONT, size=14 if big else 11, bold=True, color='1F3864')
    c.alignment = Alignment(horizontal='right', vertical='center')
    for cc in (lc, c):
        cc.fill = F_RESULT if big else F_ZEBRA
        cc.border = BOX
    ws.row_dimensions[row].height = 26 if big else 20

block(ws, r, 'ЭТАП 1 — ДО РАЗДЕЛА ПРИБЫЛИ', width=6); r += 1
for i, (lab, f, fmt, big) in enumerate([
        ('Валовой сбор',                     f'={P["gross"]}', RUB, False),
        ('Продано билетов, шт',              f'={B["sold"]}',  INT, False),
        ('Налоги УСН 6%',                    f'={P["usn"]}',   RUB, False),
        ('Комиссия за продажу билетов 5%',   f'={P["comm"]}',  RUB, False),
        ('Отчисления в РАО 8%',              f'={P["rao"]}',   RUB, False),
        ('Технические расходы',              f'={P["tech"]}',  RUB, False),
        ('Средняя цена платного билета',     f'={B["avg"]}',   RUB, False),
        ('Заполняемость зала',               f'={B["fill_base"]}', PCT, False),
        ('ПРИБЫЛЬ (делится пополам)',        f'={P["profit"]}',RUB, True),
        ('ПРИБЫЛЬ ОРГАНИЗАТОРА (50%)',       f'={P["org_profit"]}', RUB, True)]):
    tile(r + i // 2, 2 + (i % 2) * 3, lab, f, fmt, big)
r += 5 + 1

block(ws, r, 'ЭТАП 2 — РАСХОДЫ ИЗ ПРИБЫЛИ ОРГАНИЗАТОРА', width=6); r += 1
for i, (lab, f, fmt, big) in enumerate([
        ('Налоги 7%',                f'={P["tax2"]}',  RUB, False),
        ('Банковские комиссии 1%',   f'={P["bank"]}',  RUB, False),
        ('Гонорары артистам',        f'={P["fees"]}',  RUB, False),
        ('Маркетинг и PR',           f'={P["mkt"]}',   RUB, False),
        ('Прочие расходы',           f'={P["other"]}', RUB, False),
        ('Итого расходов этапа 2',   f'={P["tax2"]}+{P["bank"]}+{P["fees"]}+{P["mkt"]}+{P["other"]}', RUB, False),
        ('ЧИСТЫЙ ДОХОД ОРГАНИЗАТОРА',f'={P["net"]}',   RUB, True),
        ('Рентабельность к сбору',   f'={P["roi"]}',   PCT, True)]):
    tile(r + i // 2, 2 + (i % 2) * 3, lab, f, fmt, big)
r += 4 + 1

block(ws, r, 'УСТОЙЧИВОСТЬ ПРОЕКТА', width=6); r += 1
for i, (lab, f, fmt) in enumerate([
        ('Валовой сбор для выхода в ноль',        f'={P["be_gross"]}', RUB),
        ('Точка безубыточности, платных билетов', f'={P["be"]}',       INT),
        ('Точка безубыточности, % зала',          f'={P["be_fill"]}',  PCT),
        ('Запас прочности',                       f'={P["safety"]}',   PCT)]):
    tile(r + i // 2, 2 + (i % 2) * 3, lab, f, fmt)
r += 2 + 1

ws.cell(r, 2, 'ВЕРДИКТ').font = Font(name=FONT, size=11, bold=True, color='1F3864')
c = ws.cell(r, 3, f'={P["verdict"]}'); c.font = Font(name=FONT, size=11, bold=True)
ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=6)
for col in range(2, 7): ws.cell(r, col).border = BOX
ws.conditional_formatting.add(f'C{r}', FormulaRule(formula=[f'LEFT($C${r},6)="УБЫТОК"'],
    fill=PatternFill('solid', fgColor='FFC7CE'), font=Font(color='9C0006', bold=True)))
ws.conditional_formatting.add(f'C{r}', FormulaRule(formula=[f'LEFT($C${r},7)="ЗДОРОВО"'],
    fill=PatternFill('solid', fgColor='C6EFCE'), font=Font(color='006100', bold=True)))
ws.row_dimensions[r].height = 24
r += 2

block(ws, r, 'СЦЕНАРИИ — ЧИСТЫЙ ДОХОД ОРГАНИЗАТОРА', width=6); r += 1
for i, lab in enumerate(['Пессимистичный', 'Базовый', 'Оптимистичный', 'Аншлаг']):
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
ws.cell(r + 2, 6, '← заполняемость зала').font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
r += 4

block(ws, r, 'ЧТО УТОЧНИТЬ ПЕРЕД ЗАПУСКОМ', width=6); r += 1
for i, t in enumerate([
    'Технический райдер и смету по звуку — пришлите файлом, перенесу построчно на лист «Технические».',
    'Ставка РАО: у вас стоит 8%. Базовый тариф для концертов обычно 5% — сверьте с договором, разница в 3 п.п. от сбора это заметные деньги.',
    'Кто получает деньги от билетов физически — вы или площадка. От этого зависит, у кого возникает доход и кто платит УСН 6% на этапе 1.',
    'Комиссия билетного оператора: если она удерживается из кассы, её место на этапе 1, а не в прочих расходах. Сейчас стоит 0.',
    'Что именно входит в «техническое обеспечение площадки» по договору и кто это оплачивает.',
    'Делится ли убыток пополам, или он только ваш. Сейчас в модели — только ваш.',
    'Можно ли вычитать гонорары и маркетинг ДО раздела прибыли. Это главный рычаг — переключатели на листе «Вводные».',
]):
    cc = ws.cell(r + i, 2, f'{i+1}. {t}')
    cc.font = Font(name=FONT, size=9)
    cc.alignment = Alignment(wrap_text=True, vertical='top')
    ws.merge_cells(start_row=r + i, start_column=2, end_row=r + i, end_column=6)
    ws.row_dimensions[r + i].height = 26
ws.sheet_view.showGridLines = False

# ================================================================ ВАРИАНТЫ
ws = wb.create_sheet('Варианты')
title(ws, 'ВАРИАНТЫ УЛУЧШЕНИЯ ЭКОНОМИКИ',
      'Отсортировано по силе влияния. Первые три меняют саму конструкцию сделки — '
      'они дают больше, чем любая экономия на смете.')
widths(ws, {'A': 5, 'B': 22, 'C': 54, 'D': 32, 'E': 22, 'F': 50})
hdr(ws, 4, ['№', 'Направление', 'Что конкретно сделать', 'Где в модели', 'Оценка эффекта', 'Что учесть / риск'])
options = [
 ('Сделка', 'Вычитать гонорары и маркетинг ДО раздела прибыли. Сейчас площадка получает половину суммы, из которой вы ещё не заплатили ни артистам, ни за рекламу — то есть делит с вами выручку, а не прибыль.',
  'Вводные, раздел 7 — переключатели', 'Самый сильный рычаг', 'Это стандартная конструкция ко-промоушена. Главный пункт переговоров'),
 ('Сделка', 'Прописать раздел убытка, а не только прибыли. Сейчас риск асимметричен: прибыль пополам, убыток целиком ваш.',
  'Вводные: «Убыток делится с площадкой»', 'Снижает риск вдвое', 'Площадки соглашаются редко, но просить нужно всегда'),
 ('Сделка', 'Сдвинуть долю: 60/40 или 70/30 в вашу пользу, если вы приводите свою аудиторию и несёте маркетинг.',
  'Вводные: «Доля организатора в прибыли»', '+10–20 п.п. доли', 'Аргумент — ваш бюджет маркетинга и ваша база'),
 ('РАО', 'Проверить ставку 8%. Базовый тариф РАО для концертов обычно 5%. Уточнить, не входят ли туда смежные права (ВОИС), и декларировать точный репертуар: собственные произведения возвращаются автору.',
  'Вводные: «Отчисления в РАО»', 'До 3% от сбора', 'Нужна корректная рапортичка. Не платить вообще нельзя'),
 ('Налоги', 'Проверить, не возникает ли двойного УСН: 6% на этапе 1 с полной кассы и 7% на этапе 2 с вашей доли. Возможно, форму договора с площадкой можно изменить так, чтобы вашим доходом сразу была ваша доля.',
  'Вводные, разделы 3 и 6', 'До 6% от сбора', 'ОБЯЗАТЕЛЬНО с бухгалтером — зависит от формы договора'),
 ('Техника', 'Разделить технический райдер на «обязательное» и «желательное». Мониторы, свет и видео часто можно упростить без потери качества концерта.',
  'Лист «Технические»', '−15–30% сметы', 'Согласовать с артистом заранее, а не за день'),
 ('Техника', 'Взять звук пакетом у одного подрядчика вместо аренды по позициям. Пакет обычно дешевле суммы строк.',
  'Лист «Технические»', '−10–20% сметы', 'Требуйте в договоре конкретный список оборудования'),
 ('Цена', 'Волновое ценообразование: early bird → предпродажа → цена на входе. Ранняя квота даёт деньги на маркетинг до концерта.',
  'Лист «Билеты», категории 1–3', '+5–10% к сбору', 'Уже заложено. Разрыв больше 40% обесценивает раннюю цену'),
 ('Цена', 'Поднять цену фан-зоны и добавить в неё мерч или ранний вход. Платят за статус, а не за метры.',
  'Лист «Билеты», строка «Фан-зона / VIP»', '+3–7% к сбору', 'Квота VIP выше 15% зала обычно не продаётся'),
 ('Маркетинг', 'Перераспределить бюджет в каналы с низким CPA: своя база и Telegram обычно в разы дешевле таргета.',
  'Лист «Маркетинг», столбец CPA', '−20–30% бюджета', 'Требует заранее собранной базы'),
 ('Маркетинг', 'Кросс-промо с площадками и артистами смежной аудитории вместо платного охвата.',
  'Лист «Маркетинг», строка с бюджетом 0', '−10–15 тыс ₽', 'Договариваться за 4–6 недель'),
 ('Гонорары', 'Перевести часть гонорара в процент от прибыли. Артист разделит риск, а вы снизите постоянные расходы.',
  'Лист «Гонорары»', 'Снижает точку безубыточности', 'Работает только со «своими» артистами'),
 ('Гонорары', 'Проверить статус музыкантов: самозанятые снимают с вас взносы и НДФЛ.',
  'Лист «Гонорары», строка налогов', 'До 15 тыс ₽', 'Нужны договоры и чеки от самозанятых'),
 ('Доходы', 'Добавить источники вне билетов: мерч, доля от бара, спонсорский пакет. Сейчас их в модели нет — скажите, и добавлю отдельным блоком.',
  'Нужен новый блок', '+50–150 тыс ₽', 'Долю от бара надо прописать в договоре с площадкой'),
 ('Риск', 'Предпродажа с порогом: подтверждать концерт только при N проданных билетов.',
  'Экономика: точка безубыточности', 'Убирает риск убытка', 'Нужна возможность вернуть деньги'),
 ('Риск', 'Свести платёжный календарь: предоплаты за технику и рекламу уходят до того, как придут деньги за билеты.',
  'Нужен отдельный лист', 'Убирает кассовый разрыв', 'Скажите — добавлю календарь по неделям'),
]
r = 5
for i, (dirn, what, where, eff, risk) in enumerate(options):
    ws.cell(r, 1, i + 1).font = Font(name=FONT, size=10, bold=True)
    ws.cell(r, 2, dirn).font = Font(name=FONT, size=10, bold=True, color='1F3864')
    ws.cell(r, 3, what).font = Font(name=FONT, size=10)
    ws.cell(r, 4, where).font = Font(name=FONT, size=9, color=C_LINK)
    ws.cell(r, 5, eff).font = Font(name=FONT, size=10, bold=True)
    ws.cell(r, 6, risk).font = Font(name=FONT, size=9, italic=True, color=C_MUTED)
    for col in range(1, 7):
        ws.cell(r, col).border = BOX
        ws.cell(r, col).alignment = Alignment(wrap_text=True, vertical='top',
                                              horizontal='center' if col == 1 else 'left')
        if i < 3: ws.cell(r, col).fill = F_KEY
        elif i % 2: ws.cell(r, col).fill = F_ZEBRA
    ws.row_dimensions[r].height = 50
    r += 1
ws.freeze_panes = 'A5'

# ---------------------------------------------------------------- отделка
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
print('saved. sheets:', wb.sheetnames)
