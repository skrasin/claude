# -*- coding: utf-8 -*-
"""Бюджет концерта — одна таблица."""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

FN = 'Arial'
RUB = '#,##0" ₽";[Red]-#,##0" ₽";"—"'
PCT = '0.0%'
INT = '#,##0;[Red]-#,##0;"—"'
BLUE = '0000FF'
FILL_IN = PatternFill('solid', fgColor='FFF9E6')
LINE = Side(style='thin', color='404040')
DBL = Side(style='double', color='404040')

wb = openpyxl.Workbook()
ws = wb.active
ws.title = 'Бюджет'
ws.sheet_view.showGridLines = False
for col, w in {'A': 46, 'B': 12, 'C': 14, 'D': 18}.items():
    ws.column_dimensions[col].width = w

ws['A1'] = 'БЮДЖЕТ КОНЦЕРТА'
ws['A1'].font = Font(name=FN, size=16, bold=True)
ws['A2'] = 'Жёлтые ячейки заполняете вы. Суммы считаются сами.'
ws['A2'].font = Font(name=FN, size=9, italic=True, color='808080')

r = 4
for i, h in enumerate(['Статья', 'Кол-во', 'Цена / ставка', 'Сумма, ₽']):
    c = ws.cell(r, 1 + i, h)
    c.font = Font(name=FN, size=9, bold=True, color='FFFFFF')
    c.fill = PatternFill('solid', fgColor='44546A')
    c.alignment = Alignment(horizontal='left' if i == 0 else 'center')
r += 1

def inp(row, col, value, fmt):
    c = ws.cell(row, col, value)
    c.number_format = fmt
    c.font = Font(name=FN, size=10, color=BLUE)
    c.fill = FILL_IN
    c.alignment = Alignment(horizontal='center' if col == 2 else 'right')
    return c

def out(row, formula, bold=False, size=10):
    c = ws.cell(row, 4, formula)
    c.number_format = RUB
    c.font = Font(name=FN, size=size, bold=bold)
    return c

def label(row, text, bold=False, size=10, indent=1):
    c = ws.cell(row, 1, text)
    c.font = Font(name=FN, size=size, bold=bold)
    c.alignment = Alignment(indent=0 if bold else indent)

def rule(row, double=False):
    for i in range(1, 5):
        ws.cell(row, i).border = Border(top=DBL if double else LINE)

# 1. валовой сбор
label(r, '1. ВАЛОВОЙ СБОР', bold=True, size=11)
inp(r, 2, 200, INT)
inp(r, 3, 2500, RUB)
out(r, f'=B{r}*C{r}', bold=True, size=11)
GROSS = r
r += 1

# 2. вычеты из валового сбора
for text, pct in [('2. Налоги УСН', 0.06),
                  ('Комиссия за продажу билетов', 0.05),
                  ('Отчисления в РАО', 0.08)]:
    label(r, text, bold=text.startswith('2.'))
    inp(r, 3, pct, PCT)
    out(r, f'=-$D${GROSS}*C{r}')
    r += 1
USN, COMM, RAO = GROSS + 1, GROSS + 2, GROSS + 3

# 3. технические расходы
label(r, '3. Технические расходы', bold=True)
inp(r, 4, -150000, RUB)
ws.cell(r, 4).alignment = Alignment(horizontal='right')
TECH = r
r += 1

# 4. прибыль
rule(r)
label(r, '4. ПРИБЫЛЬ', bold=True, size=12)
out(r, f'=$D${GROSS}+$D${USN}+$D${COMM}+$D${RAO}+$D${TECH}', bold=True, size=12)
ws.row_dimensions[r].height = 22
PROFIT = r
r += 1

# 5. доля площадки
label(r, '5. Доля площадки', bold=True)
inp(r, 3, 0.50, PCT)
out(r, f'=-$D${PROFIT}*C{r}')
VSHARE = r
r += 1

# 6. прибыль организатора
rule(r)
label(r, '6. ПРИБЫЛЬ ОРГАНИЗАТОРА', bold=True, size=12)
out(r, f'=$D${PROFIT}+$D${VSHARE}', bold=True, size=12)
ws.row_dimensions[r].height = 22
ORG = r
r += 1

# вычеты из прибыли организатора
first_deduction = r
for text, pct in [('Налоги', 0.07), ('Банковские комиссии', 0.01)]:
    label(r, text)
    inp(r, 3, pct, PCT)
    out(r, f'=-MAX(0,$D${ORG})*C{r}')
    r += 1
for text, amount in [('Гонорары', -50000), ('Маркетинг', -50000),
                     ('PR', -15000), ('Прочие расходы', -50000)]:
    label(r, text)
    inp(r, 4, amount, RUB)
    ws.cell(r, 4).alignment = Alignment(horizontal='right')
    r += 1
last_deduction = r - 1

# 7. чистый доход
rule(r, double=True)
label(r, '7. ЧИСТЫЙ ДОХОД ОРГАНИЗАТОРА', bold=True, size=14)
out(r, f'=$D${ORG}+SUM(D{first_deduction}:D{last_deduction})', bold=True, size=14)
ws.row_dimensions[r].height = 30

ws.print_area = f'A1:D{r}'
ws.page_setup.fitToWidth = 1
ws.sheet_properties.pageSetUpPr.fitToPage = True
wb.save('Бюджет_концерта.xlsx')
print(f'saved, строк в таблице: {r - 4}')
