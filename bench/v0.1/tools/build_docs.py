#!/usr/bin/env python3
"""Generate B0.1 documents from manual.md and explicit electrical connections."""
from pathlib import Path
import json
import re
from html import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                               Table, TableStyle, KeepTogether)
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Polygon
from reportlab.graphics import renderSVG

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'pdf'
OUT.mkdir(parents=True, exist_ok=True)
FONT_DIR = Path('/Users/germanklimenko/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/fonts')
def font_path(name):
    lo = FONT_DIR.parents[2] / 'libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fonts/truetype'
    for p in [FONT_DIR / name, lo / name, Path('/usr/share/fonts/truetype/dejavu') / name]:
        if p.exists(): return str(p)
    raise FileNotFoundError('Install DejaVu fonts or update FONT_DIR')
pdfmetrics.registerFont(TTFont('DV', font_path('DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DVB', font_path('DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('DV', normal='DV', bold='DVB', italic='DV', boldItalic='DVB')

INK = colors.HexColor('#19324c')
TEAL = colors.HexColor('#007c83')
PALE = colors.HexColor('#edf4f7')
GRAY = colors.HexColor('#516475')
RED = colors.HexColor('#b63232')
styles = {
    'p': ParagraphStyle('p', fontName='DV', fontSize=9.5, leading=13.6, spaceAfter=8, textColor=INK),
    'h1': ParagraphStyle('h1', fontName='DVB', fontSize=25, leading=31, spaceAfter=18, textColor=INK),
    'h2': ParagraphStyle('h2', fontName='DVB', fontSize=17, leading=22, spaceAfter=14, textColor=INK),
    'h3': ParagraphStyle('h3', fontName='DVB', fontSize=11, leading=15, spaceBefore=7, spaceAfter=7, textColor=TEAL),
    'cell': ParagraphStyle('cell', fontName='DV', fontSize=8.0, leading=10.6, textColor=INK),
    'url': ParagraphStyle('url', fontName='DV', fontSize=7.3, leading=10, spaceAfter=10, textColor=TEAL, splitLongWords=True),
}

def rich(s):
    s = escape(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'`(.+?)`', r'<font color="#007c83">\1</font>', s)
    return s

def para(s, style='p'):
    return Paragraph(rich(s), styles[style])

def table(rows, widths=None):
    w = widths or ([110, 88, 305] if len(rows[0]) == 3 else [160, 343])
    tab = Table([[para(c, 'cell') for c in row] for row in rows], colWidths=w, repeatRows=1, hAlign='LEFT')
    tab.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PALE), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f7f9fb')]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7), ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5), ('LINEBELOW', (0,0), (-1,0), .7, TEAL),
        ('LINEBELOW', (0,1), (-1,-1), .25, colors.HexColor('#d9e3e9')),
    ]))
    return tab

def build_netlist():
    nets = {}
    components = {}
    def add(net, *nodes):
        nets.setdefault(net, []).extend(nodes)
    components['A1'] = 'Arduino UNO R3 5V 16MHz ATmega328P'
    components['PS1'] = 'Isolated bench PSU 5.00V, current limit up to 0.60A'
    for i in range(1, 7):
        u = f'U{i}'
        components[u] = 'SM16306SJ QSOP24'
        components[f'R{i}'] = '3.74k 1% 0.25W'
        components[f'C{i}'] = '100nF X7R 16V'
        add('GND', f'{u}.1', f'R{i}.2', f'C{i}.2')
        add('+5V_LOGIC', f'{u}.24', f'C{i}.1')
        add(f'REXT_{i}', f'{u}.23', f'R{i}.1')
        add('CLK_BUS', f'{u}.3'); add('LE_BUS', f'{u}.4'); add('OE_BUS', f'{u}.21')
        if i == 1: add('DATA_0', f'{u}.2')
        else: add(f'DATA_{i-1}', f'U{i-1}.22', f'{u}.2')
    add('DATA_6', 'U6.22', 'TP_SDO.1')
    for name, value in {'R7':'47R', 'R8':'47R', 'R9':'47R', 'R10':'100R', 'R11':'10k',
                        'R12':'10k', 'C7':'10uF >=10V polarized', 'C8':'100uF >=10V polarized',
                        'C9':'100nF X7R 16V', 'S1':'SPDT BBM OFF/RUN', 'S2':'SPST power',
                        'F1':'0.75A DC-rated fuse', 'PD1':'Vishay BPW34 optional'}.items():
        components[name] = value
    add('MOSI_RAW', 'A1.D11', 'R7.1'); add('DATA_0', 'R7.2')
    add('CLK_RAW', 'A1.D13', 'R8.1'); add('CLK_BUS', 'R8.2', 'TP_CLK.1')
    add('LE_RAW', 'A1.D10', 'R9.1'); add('LE_BUS', 'R9.2', 'TP_LE.1')
    add('OE_RAW', 'A1.D9', 'R10.1'); add('OE_RUN', 'R10.2', 'S1.RUN')
    add('OE_BUS', 'S1.COM', 'R11.2', 'TP_OE.1')
    add('+5V_LOGIC', 'A1.5V', 'S1.OFF', 'R11.1', 'C7.+', 'PD1.K', 'TP_LOGIC.1')
    add('PSU_PLUS', 'PS1.+', 'F1.1'); add('FUSED_PLUS', 'F1.2', 'S2.1')
    add('+5V_LED', 'S2.2', 'C8.+', 'C9.1', 'TP_LED.1')
    add('GND', 'A1.GND', 'PS1.-', 'C7.-', 'C8.-', 'C9.2', 'R12.2', 'TP_GND.1')
    add('MARK', 'A1.D8', 'TP_MARK.1'); add('LIGHT', 'PD1.A', 'R12.1', 'TP_LIGHT.1')
    mapping = []
    for p in range(32):
        d = f'D{p+1}'
        components[d] = 'Kingbright WP154A4SEJ3VBDZGW/CA'
        add('+5V_LED', f'{d}.2')
        item = {'pixel': p, 'led': d, 'bank': 'TOP' if p < 20 else 'TIP', 'anode': f'{d}.2'}
        for color, offset, pin in [('R',0,1), ('G',1,4), ('B',2,3)]:
            ch = p * 3 + offset
            node = f'U{ch // 16 + 1}.{ch % 16 + 5}'
            lednode = f'{d}.{pin}'
            add(f'CH_{ch:02d}_{color}', node, lednode)
            item[color] = {'channel': ch, 'driver': node, 'cathode': lednode}
        mapping.append(item)
    obj = {'revision':'B0.1', 'status':'UNTESTED HARDWARE / STATIONARY ONLY',
           'optional':'PD1/R12 optical measurement; R13 replaces R12; R14 is not fitted in main assembly',
           'components':components, 'nets':nets, 'pixels':mapping}
    (ROOT / 'wiring.json').write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    return obj

def schematic():
    d = Drawing(503, 390)
    def line(x1,y1,x2,y2,color=INK): d.add(Line(x1,y1,x2,y2,strokeColor=color,strokeWidth=.9))
    def text(x,y,s,size=8,color=INK): d.add(String(x,y,s,fontName='DV',fontSize=size,fillColor=color))
    def box(x,y,w,h,title):
        d.add(Rect(x,y,w,h,strokeColor=INK,fillColor=PALE,strokeWidth=.7)); text(x+7,y+h-16,title,9)
    box(2,120,120,245,'A1 / UNO R3')
    text(10,330,'USB → +5V_LOGIC',8)
    text(10,316,'5V   GND',8)
    labels=[('D11', 'R7 47R', 'SDI U1.2',296),('D13','R8 47R','CLK all .3',263),('D10','R9 47R','LE all .4',230)]
    box(331,120,170,245,'U1...U6 / SM16306SJ')
    for pin,res,dest,y in labels:
        text(16,y-3,pin); line(122,y,157,y)
        d.add(Rect(157,y-5,52,10,strokeColor=INK,fillColor=colors.white)); text(159,y+10,res,7)
        line(209,y,331,y); text(339,y-3,dest,8)
    text(339,324,'24 VDD = +5V_LOGIC',8)
    text(339,135,'1 GND; 23 → 3.74k → GND',7.7)
    text(16,162,'D9'); line(122,165,145,165)
    d.add(Rect(145,160,30,10,strokeColor=INK,fillColor=colors.white))
    text(136,149,'R10 100R',7); line(175,165,200,165); text(182,153,'RUN',7)
    text(181,212,'OFF',7); line(135,205,200,205); text(129,216,'+5V_LOGIC',7)
    line(221,185,201,203); line(221,185,331,185)
    text(211,170,'S1 COM',7); text(339,182,'21 OE_BUS',8)
    line(290,185,290,198)
    d.add(Rect(286,198,8,10,strokeColor=INK,fillColor=colors.white))
    line(290,208,290,216); text(240,218,'+5V_LOGIC',7); text(242,202,'R11 10k',7)
    text(10,131,'D8 → TP_MARK',8)
    text(4,103,'Цепочка: U1.22 → U2.2; U2.22 → U3.2; ...; U5.22 → U6.2; U6.22 → TP_SDO',8)
    box(2,6,112,67,'PS1 / 5.00 V CC')
    text(10,31,'+     - → GND',8)
    line(114,48,133,48); text(118,60,'F1 0.75A',7)
    d.add(Rect(133,44,18,8,strokeColor=INK,fillColor=colors.white))
    line(151,48,170,48); line(170,48,186,55); text(169,66,'S2',8)
    line(188,48,260,48); text(206,60,'+5V_LED',8)
    box(260,6,241,67,'D1...D32 / common anode')
    text(270,36,'pin2 → +5V_LED; R(pin1)/G(4)/B(3) → OUT',7.5)
    text(270,20,'C8 100u + C9 100n → GND',8)
    text(8,375,'Раздельные плюсы питания. Общий GND. S1=OFF; S2=OFF.',8,RED)
    return d

def photo_diagram():
    d = Drawing(503,120)
    def t(x,y,s): d.add(String(x,y,s,fontName='DV',fontSize=9,fillColor=INK))
    def l(a,b,c,e): d.add(Line(a,b,c,e,strokeColor=INK))
    t(15,100,'+5V_LOGIC'); l(80,90,80,70); t(94,78,'K')
    d.add(Line(69,70,91,70,strokeColor=INK,strokeWidth=2))
    d.add(Polygon([69,48,91,48,80,70],strokeColor=INK,fillColor=colors.white))
    l(80,48,80,32); l(80,32,245,32); t(94,42,'A'); t(130,47,'TP_LIGHT → CH2 ×10')
    l(245,32,245,20); t(260,24,'R12 10k → GND')
    t(330,95,'UNO D8 → CH1 ×10'); t(330,77,'Земли щупов → GND')
    t(15,7,'PD1 BPW34. R13 1k заменяет R12 только при насыщении. Не измеритель люкс.')
    return d

def footer(canvas, doc):
    canvas.saveState(); canvas.setStrokeColor(TEAL); canvas.line(46,42,549,42)
    canvas.setFont('DV',7); canvas.setFillColor(GRAY)
    canvas.drawString(46,29,'SmartSpinner B0.1 • Только неподвижный стенд • На железе не проверено')
    canvas.drawRightString(549,29,str(doc.page)); canvas.restoreState()

def mapping_rows(items):
    rows=[['LED / PIX','Банк','R: pin1','G: pin4','B: pin3']]
    for m in items:
        rows.append([f"{m['led']} / {m['pixel']}",m['bank']] +
                    [f"{m[c]['driver']} (CH {m[c]['channel']})" for c in 'RGB'])
    return rows

def main():
    obj=build_netlist()
    draw=schematic(); renderSVG.drawToFile(draw,str(ROOT/'schematic.svg'))
    renderSVG.drawToFile(photo_diagram(),str(ROOT/'photodiode.svg'))
    parts=(ROOT/'manual.md').read_text().split('<!-- page -->')
    (ROOT/'shopping.md').write_text('# B0.1 - список покупок\n\n'+parts[2].strip()+'\n\n'+parts[3].strip()+'\n\nСсылки S1-S6: раздел 13 инструкции manual.md и PDF.\n')
    story=[]
    for page_index,part in enumerate(parts):
        if page_index: story.append(PageBreak())
        lines=part.strip().splitlines(); i=0
        while i<len(lines):
            s=lines[i].strip()
            if not s: i+=1; continue
            if s=='{{SCHEMATIC}}': story.extend([draw,Spacer(1,10)]); i+=1; continue
            if s=='{{PHOTO}}': story.extend([photo_diagram(),Spacer(1,10)]); i+=1; continue
            if s in ('{{MAP_TOP}}','{{MAP_TIP}}'):
                subset=obj['pixels'][:20] if s=='{{MAP_TOP}}' else obj['pixels'][20:]
                story.extend([table(mapping_rows(subset),[70,45,129,129,130]),Spacer(1,10)]); i+=1; continue
            if s.startswith('|'):
                rows=[]
                while i<len(lines) and lines[i].strip().startswith('|'):
                    row=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                    if not all(re.fullmatch(r'[-: ]+',c) for c in row): rows.append(row)
                    i+=1
                widths=None
                # Custom columns for purchasing and test tables.
                if rows[0][0]=='Позиция': widths=[80,68,355]
                elif rows[0][0]=='Что': widths=[120,65,318]
                elif rows[0][0]=='Тест': widths=[97,168,238]
                elif rows[0][0].startswith('Вывод'): widths=[97,62,344]
                story.extend([table(rows,widths),Spacer(1,10)]); continue
            if s.startswith('### '): story.append(para(s[4:],'h3')); i+=1; continue
            if s.startswith('## '): story.append(para(s[3:],'h2')); i+=1; continue
            if s.startswith('# '): story.append(para(s[2:],'h1')); i+=1; continue
            paragraph=[s]; i+=1
            while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','{{')):
                paragraph.append(lines[i].strip()); i+=1
            text=' '.join(paragraph)
            if text.startswith('https://'):
                story.append(Paragraph(f'<link href="{escape(text,quote=True)}">{escape(text)}</link>',styles['url']))
            else: story.append(para(text))
    doc=SimpleDocTemplate(str(OUT/'SmartSpinner_B01_Bench.pdf'),pagesize=(595.28,841.89),
        leftMargin=46,rightMargin=46,topMargin=43,bottomMargin=57,
        title='Умный спиннер для трейдера - B0.1 настольный стенд',author='SmartSpinner project')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    h=['<!doctype html><html lang="ru"><meta charset="utf-8"><title>B0.1 - полная таблица проводов</title>',
       '<style>body{font:15px system-ui;max-width:1100px;margin:30px auto;color:#19324c}table{border-collapse:collapse;width:100%;margin:20px 0}td,th{border:1px solid #ccd9e0;padding:7px;text-align:left}th{background:#edf4f7}code{font-size:13px}h1,h2{color:#007c83}@media print{body{font-size:10px}thead{display:table-header}}</style>',
       '<h1>SmartSpinner B0.1: монтажная таблица</h1><p>Неподвижный стенд. На железе не проверено. Все узлы одной именованной сети электрически соединены. Номера выводов корпуса, не случайные номера переходника. Не соединять +5V_LOGIC и +5V_LED.</p>',
       '<p><a href="output/pdf/SmartSpinner_B01_Bench.pdf">Инструкция PDF</a> · <a href="wiring.json">Исходный список сетей</a></p>',
       '<img src="schematic.svg" width="100%" alt="Схема питания и управления"><h2>96 цветовых каналов</h2>']
    def html_table(rows):
        return '<table><thead><tr>'+''.join('<th>'+escape(c)+'</th>' for c in rows[0])+\
               '</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(c)+'</td>' for c in row)+'</tr>' for row in rows[1:])+'</tbody></table>'
    h.append(html_table(mapping_rows(obj['pixels'])))
    h.append('<h2>Все электрические сети</h2>')
    h.append(html_table([['Сеть','Соединённые контакты']]+[[n,', '.join(nodes)] for n,nodes in obj['nets'].items()]))
    h.append('<h2>Обозначения компонентов</h2>')
    h.append(html_table([['Ref','Компонент']]+list(map(list,obj['components'].items()))))
    h.append('<p>R13 1k - возможная замена R12, не дополнительный параллельный резистор. R14 470R - отдельный тест LED до монтажа; в основной сети его нет. PD1/R12 необязательны для статического запуска.</p></html>')
    (ROOT/'wiring.html').write_text('\n'.join(h))
    print(f'Generated {OUT / "SmartSpinner_B01_Bench.pdf"}; {len(obj["nets"])} nets, 96 channels')

if __name__=='__main__': main()
