# -*- coding: utf-8 -*-
"""Бюджет мероприятия: концерт — 20.10.2026, Музей ЗИЛАРТ."""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

FN = 'Arial'
RUB = '_-* #,##0_-;\\-* #,##0_-;_-* "-"??_-;_-@_-'
PCT = '0%'
INT = '_-* #,##0_-;\\-* #,##0_-;_-* "-"??_-;_-@_-'
YEL = PatternFill('solid', fgColor='FFFFFF00')
LINE = Side(style='thin', color='404040')
DBL = Side(style='double', color='404040')

wb = openpyxl.Workbook()
ws = wb.active
ws.title = 'Бюджет'
for col, w in {'A': 2.5, 'B': 44, 'C': 9, 'D': 13, 'E': 14, 'F': 2, 'G': 58}.items():
    ws.column_dimensions[col].width = w

ws['B1'] = 'БЮДЖЕТ МЕРОПРИЯТИЯ'
ws['B1'].font = Font(name=FN, size=13, bold=True)
ws['B2'] = 'Концерт · 20.10.2026 · Музей ЗИЛАРТ'
ws['B2'].font = Font(name=FN, size=9, color='FF808080')

HDR = 4
for i, h in enumerate(['#', 'Статья', 'Кол-во', 'Цена / ставка', 'Сумма, ₽']):
    c = ws.cell(HDR, 1 + i, h)
    c.font = Font(name=FN, size=10, bold=True)
    c.border = Border(bottom=LINE)
    c.alignment = Alignment(horizontal='left' if i < 2 else 'center')

def row(r, num, name, qty, price, fmt_price=RUB, bold=False, note=None):
    if num is not None:
        c = ws.cell(r, 1, num); c.font = Font(name=FN, size=10, bold=True)
    c = ws.cell(r, 2, name); c.font = Font(name=FN, size=10, bold=bold)
    if qty is not None:
        c = ws.cell(r, 3, qty); c.number_format = INT
        c.font = Font(name=FN, size=10); c.fill = YEL
        c.alignment = Alignment(horizontal='center')
    if price is not None:
        c = ws.cell(r, 4, price); c.number_format = fmt_price
        c.font = Font(name=FN, size=10); c.fill = YEL
    if note:
        ws.cell(r, 7, note).font = Font(name=FN, size=9, color='FF808080')

# --- расходы
row(5, 1, 'Технический райдер (смета СМ-2026-024)', 1, 90000,
    note='Округлённая сумма. По смете Спотыкача 75 669 ₽ (68 790 ₽ + налог 10%)')
row(6, 2, 'Музыканты', 4, 20000, note='4 человека по 20 000 ₽')
row(7, 3, 'Звукорежиссёр', 1, 20000)
for r in (5, 6, 7):
    c = ws.cell(r, 5, f'=C{r}*D{r}')
    c.number_format = RUB; c.font = Font(name=FN, size=10)

# --- итого расходы
ws.cell(8, 2, 'ИТОГО РАСХОДЫ').font = Font(name=FN, size=10, bold=True)
c = ws.cell(8, 5, '=SUM(E5:E7)')
c.number_format = RUB; c.font = Font(name=FN, size=10, bold=True)
for col in range(1, 6):
    ws.cell(8, col).border = Border(top=LINE)

# --- комиссия
row(9, 4, 'Комиссия и налоги', None, 0.20, PCT)
c = ws.cell(9, 5, '=ROUND($E$8*D9,0)')
c.number_format = RUB; c.font = Font(name=FN, size=10)
ws.cell(9, 7, '20% на всю сумму расходов').font = Font(name=FN, size=9, color='FF808080')

# --- итого к оплате
ws.cell(10, 2, 'ИТОГО К ОПЛАТЕ').font = Font(name=FN, size=12, bold=True)
c = ws.cell(10, 5, '=E8+E9')
c.number_format = RUB; c.font = Font(name=FN, size=12, bold=True)
for col in range(1, 6):
    ws.cell(10, col).border = Border(top=DBL)
ws.row_dimensions[10].height = 20

# --- примечания
notes = [
    'Жёлтые ячейки — вводимые значения, остальное считается формулами.',
    'Райдер округлён до 90 000 ₽; по смете СМ-2026-024 выходит 75 669 ₽ (налог 10% внутри).',
    'Комиссия и налоги — 20% на всю сумму расходов.',
    'Дата на уточнении — по примечанию в смете ожидается согласование с артистами '
    'после просмотра площадки.',
]
for i, t in enumerate(notes):
    c = ws.cell(12 + i, 2, ('• ' if i else 'Примечания:\n• ') + t if i else '• ' + t)
    c.font = Font(name=FN, size=9, color='FF808080')
ws.cell(12, 2).value = '• ' + notes[0]

wb.save('Бюджет_ЗИЛАРТ_20.10.2026.xlsx')
print('готово')
