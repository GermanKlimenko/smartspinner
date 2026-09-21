'use client';

import {
  ArrowDown, ArrowRight, Bluetooth, Box, Check, ChevronLeft, ChevronRight,
  CircleDot, Code2, Cpu, Download, FileArchive, FileCode2, FileDown, Gauge,
  Layers3, Menu, PackageCheck, Radio, Ruler, ShieldAlert, Sparkles, X, Zap,
} from 'lucide-react';
import { useState } from 'react';

const nav = [
  ['Идея', 'concept'], ['Электроника', 'electronics'], ['Механика', 'mechanics'],
  ['Производство', 'production'], ['Файлы', 'downloads'],
];

const drawings = [
  { src: './assets/drawings/sheet-1.png', title: 'Общий вид и сечение v0.3', caption: 'Четыре луча, габарит Ø100 × 16 мм, подшипник 608 и компоновка сборки.' },
  { src: './assets/drawings/sheet-2.png', title: 'Нижняя часть корпуса', caption: 'Четыре симметричных кармана питания и четыре стойки M2 через 90°.' },
  { src: './assets/drawings/sheet-3.png', title: 'Верхняя крышка', caption: 'Четыре световых окна, сменные рассеиватели и защита торцевых плат.' },
  { src: './assets/drawings/sheet-4.png', title: 'Четырёхлучевая PCB', caption: '80 верхних LED, центральная электроника и симметричные зоны балансировки.' },
  { src: './assets/drawings/sheet-5.png', title: 'Торцевая плата — 12 пикселей', caption: 'Четыре сменные вертикальные колонки для цилиндрической бегущей строки.' },
];

const fileGroups = [
  {
    icon: PackageCheck, title: 'Пакет для запроса производителям',
    text: 'Готовый комплект для инженерной оценки и расчёта 10 электронных комплектов: RFQ-бриф, письма на русском и английском, форма ответа, электроника и механика.',
    files: [
      ['Полный RFQ-пакет · ZIP', 'SmartSpinner_v0_4_RFQ_Send_Package.zip'],
      ['Краткий RFQ-бриф · PDF', 'SmartSpinner_v0_4_RFQ_Brief_EN.pdf'],
    ], featured: true,
  },
  {
    icon: Cpu, title: 'Электроника v0.4 · ERC',
    text: 'KiCad-платы, обзорные Gerber, BOM, CPL, электрическая архитектура, расчёт питания и план первого включения. Пакет предназначен для RFQ и завершения DFM, а не для немедленного запуска в производство.',
    files: [
      ['Полный электро-пакет · ZIP', 'SmartSpinner_v0_4_electronics_ERC.zip'],
      ['Электрическая архитектура · PDF', 'electronics-v0.4/smartspinner_v0_4_schematic.pdf'],
      ['Чертёж изготовления · PDF', 'electronics-v0.4/smartspinner_v0_4_fabrication_drawing.pdf'],
      ['Основная плата · KiCad', 'electronics-v0.4/smartspinner_main_v0_4.kicad_pcb'],
      ['Торцевая плата · KiCad', 'electronics-v0.4/smartspinner_tip_v0_4.kicad_pcb'],
      ['BOM · CSV', 'electronics-v0.4/smartspinner_v0_4_bom.csv'],
      ['CPL основной платы · CSV', 'electronics-v0.4/assembly/smartspinner_main_v0_4_cpl.csv'],
      ['CPL торцевой платы · CSV', 'electronics-v0.4/assembly/smartspinner_tip_v0_4_cpl.csv'],
      ['Статус DRC · JSON', 'electronics-v0.4/smartspinner_v0_4_release_status.json'],
    ],
  },
  {
    icon: FileArchive, title: 'Полный комплект v0.3',
    text: 'Четырёхлучевая механика, контуры плат, чертежи, визуализации, исходники и проверки одним архивом.',
    files: [['Скачать ZIP · 16 МБ', 'ticker_spinner_v0_3_complete_package.zip']],
  },
  {
    icon: Box, title: 'Корпус для печати',
    text: 'Верх, низ и рассеиватели в производственных и редактируемых форматах.',
    files: [
      ['Верх · STL', 'ticker_spinner_v0_3_top.stl'], ['Низ · STL', 'ticker_spinner_v0_3_bottom.stl'],
      ['Рассеиватели · STL', 'ticker_spinner_v0_3_diffusers.stl'], ['Сборка · STEP', 'ticker_spinner_v0_3_assembly.step'],
      ['Верх · STEP', 'ticker_spinner_v0_3_top.step'], ['Низ · STEP', 'ticker_spinner_v0_3_bottom.step'],
      ['Крышка подшипника · STL', 'ticker_spinner_v0_3_finger_cap_top.stl'],
    ],
  },
  {
    icon: Cpu, title: 'Печатные платы',
    text: 'Механические контуры и объёмные envelopes основной и торцевой плат для финальной разводки.',
    files: [
      ['Контур основной PCB · DXF', 'ticker_spinner_v0_3_pcb_outline.dxf'],
      ['Контур торцевой PCB · DXF', 'ticker_spinner_v0_3_tip_led_board.dxf'],
      ['Envelope основной PCB · STEP', 'ticker_spinner_v0_3_pcb_envelope.step'],
      ['Envelope торцевой PCB · STEP', 'ticker_spinner_v0_3_tip_led_board_envelope.step'],
    ],
  },
  {
    icon: FileCode2, title: 'Документация и исходники',
    text: 'Чертежи, партнёрский материал, описание параметров и генератор всей геометрии v0.3.',
    files: [
      ['Инженерный чертёж · PDF', 'ticker_spinner_v0_3_engineering_drawing.pdf'],
      ['Презентация для партнёров · PDF', 'ticker_spinner_v0_3_partner_brief.pdf'],
      ['Ответ на техническую критику · PDF', 'ticker_spinner_critique_assessment.pdf'],
      ['Описание проекта · MD', 'README_Ticker_Spinner_v0_3.md'], ['Генератор модели · Python', 'generate_ticker_spinner_v0_3.py'],
      ['Отчёт проверки · JSON', 'ticker_spinner_v0_3_validation.json'],
    ],
  },
];

function DownloadLink({ label, file }: { label: string; file: string }) {
  return <a className="file-link" href={`./project-files/${file}`} download><span>{label}</span><FileDown size={16} aria-hidden="true" /></a>;
}

export default function Home() {
  const [activeDrawing, setActiveDrawing] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);
  const previousDrawing = () => setActiveDrawing((current) => (current + drawings.length - 1) % drawings.length);
  const nextDrawing = () => setActiveDrawing((current) => (current + 1) % drawings.length);

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Умный спиннер — наверх">
          <span className="brand-mark"><CircleDot size={22} /></span><span>SMART<span>SPINNER</span></span>
        </a>
        <nav className={menuOpen ? 'nav open' : 'nav'} aria-label="Навигация по проекту">
          {nav.map(([label, id]) => <a key={id} href={`#${id}`} onClick={() => setMenuOpen(false)}>{label}</a>)}
          <a className="nav-github" href="https://github.com/GermanKlimenko/smartspinner" target="_blank" rel="noreferrer"><Code2 size={17} /> GitHub</a>
        </nav>
        <button className="menu-button" onClick={() => setMenuOpen(!menuOpen)} aria-label="Открыть меню" aria-expanded={menuOpen}>{menuOpen ? <X /> : <Menu />}</button>
      </header>

      <section className="hero" id="top">
        <div className="hero-glow" />
        <div className="hero-copy">
          <div className="eyebrow"><span /> Механика v0.3 · электроника v0.4 ERC</div>
          <h1>Умный спиннер<br /><em>для трейдера</em></h1>
          <p className="hero-lead">Карманный POV‑дисплей, который превращает вращение в экран: котировки, проценты, сигналы и логотипы возникают прямо в воздухе.</p>
          <div className="hero-actions">
            <a className="button button-primary" href="./project-files/SmartSpinner_v0_4_electronics_ERC.zip" download><Download size={18} /> Скачать электронику v0.4</a>
            <a className="button button-ghost" href="#concept">Изучить конструкцию <ArrowDown size={18} /></a>
          </div>
          <div className="hero-note"><span className="pulse" /> Параметрическая модель готова для первой 3D‑печати</div>
        </div>
        <div className="hero-visual">
          <div className="hero-image-frame"><img src="./project-files/ticker_spinner_v0_3_partner_handheld.png" alt="Четырёхлучевой умный спиннер v0.3 в руке" /></div>
          <div className="float-card float-card-top"><span>RGB PIXELS</span><strong>128</strong><small>80 сверху + 48 на торцах</small></div>
          <div className="float-card float-card-bottom"><span>FORM FACTOR</span><strong>Ø100</strong><small>миллиметров</small></div>
        </div>
      </section>

      <section className="metrics" aria-label="Основные параметры">
        <div><Ruler /><strong>100 мм</strong><span>внешний диаметр</span></div>
        <div><Layers3 /><strong>16 мм</strong><span>толщина сборки</span></div>
        <div><Sparkles /><strong>20 × 4</strong><span>верхних пикселей</span></div>
        <div><Bluetooth /><strong>nRF52</strong><span>BLE и управление</span></div>
      </section>

      <section className="section concept" id="concept">
        <div className="section-heading">
          <div><span className="section-number">01</span><p className="kicker">Принцип работы</p></div>
          <h2>Экран, которого<br />физически <em>нет</em></h2>
          <p>Зрение объединяет короткие вспышки в цельное изображение. Датчик Холла отмечает каждый оборот, контроллер рассчитывает угол и включает нужные пиксели в нужную микросекунду.</p>
        </div>
        <div className="pov-grid">
          <div className="pov-stage" aria-label="Схематичная демонстрация цилиндрического POV-тикера">
            <div className="orbit orbit-one"><span>SBER&nbsp; 317.42&nbsp; ▲1.73%</span></div>
            <div className="orbit orbit-two"><span>GAZP&nbsp; 168.90&nbsp; ▼0.28%</span></div>
            <div className="spinner-demo"><div className="demo-arm arm-a"><i /></div><div className="demo-arm arm-b"><i /></div><div className="demo-arm arm-c"><i /></div><div className="demo-arm arm-d"><i /></div><div className="demo-bearing" /></div>
            <div className="scan-line" />
          </div>
          <div className="pov-copy">
            <div className="comparison">
              <div className="comparison-old"><span>Было</span><strong>6</strong><small>пикселей по высоте</small><div className="pixel-column six">{Array.from({ length: 6 }).map((_, i) => <i key={i} />)}</div></div>
              <ArrowRight className="compare-arrow" />
              <div className="comparison-new"><span>Стало</span><strong>12</strong><small>пикселей по высоте</small><div className="pixel-column twelve">{Array.from({ length: 12 }).map((_, i) => <i key={i} />)}</div></div>
            </div>
            <h3>Двенадцать пикселей меняют всё</h3>
            <p>Вертикальная торцевая плата рисует «цилиндр» вокруг спиннера. При 12 пикселях буквы получают нормальные пропорции, стрелки читаются мгновенно, а цвет можно использовать для направления движения цены.</p>
            <ul className="check-list"><li><Check /> читаемые тикеры и числа</li><li><Check /> двухстрочные композиции</li><li><Check /> графики, иконки и цветовые сигналы</li></ul>
          </div>
        </div>
      </section>

      <section className="section dark-section" id="electronics">
        <div className="section-heading light">
          <div><span className="section-number">02</span><p className="kicker">Электроника</p></div>
          <h2>Одна основная плата.<br /><em>Четыре световых луча.</em></h2>
          <p>Тяжёлые элементы собраны ближе к оси, а повторяющиеся узлы расположены с симметрией 90°. Четыре одинаковых сектора упрощают статическую и динамическую балансировку.</p>
        </div>
        <div className="pcb-showcase">
          <figure className="pcb-image"><img src="./project-files/ticker_spinner_v0_3_partner_dock.png" alt="Четырёхлучевой спиннер v0.3 в рабочем режиме на демонстрационной опоре" /><figcaption>Рабочая визуализация v0.3 — четыре луча и защищённые торцевые LED-колонки</figcaption></figure>
          <div className="component-list">
            <article><span>01</span><div><h3>80 × RGB 1313/2020</h3><p>По 20 адресных верхних LED на каждом из четырёх лучей.</p></div></article>
            <article><span>02</span><div><h3>4 × 12 RGB 0909</h3><p>Сменные вертикальные платы для кругового цветного тикера.</p></div></article>
            <article><span>03</span><div><h3>nRF52840 + BLE</h3><p>Получение данных со смартфона, точный тайминг и управление кадром.</p></div></article>
            <article><span>04</span><div><h3>Hall + IMU</h3><p>Индекс оборота и компенсация неравномерной скорости вращения рукой.</p></div></article>
            <article><span>05</span><div><h3>8 параллельных LED‑каналов</h3><p>Четыре цепи 4×20 для верхнего изображения и четыре независимые цепи 4×12 для торцевого тикера.</p></div></article>
          </div>
        </div>
        <div className="signal-flow">
          <div><Radio /><span>Котировки</span><small>телефон / API</small></div><ArrowRight /><div><Bluetooth /><span>BLE</span><small>пакет данных</small></div><ArrowRight /><div><Cpu /><span>nRF52</span><small>рендер кадра</small></div><ArrowRight /><div><Gauge /><span>Hall + IMU</span><small>угол вращения</small></div><ArrowRight /><div className="flow-accent"><Sparkles /><span>128 RGB</span><small>воздушный экран</small></div>
        </div>
      </section>

      <section className="section" id="mechanics">
        <div className="section-heading">
          <div><span className="section-number">03</span><p className="kicker">Механика</p></div>
          <h2>Корпус, который можно<br /><em>быстро менять</em></h2>
          <p>Вся геометрия строится из параметров. Верх, низ, рассеиватели и контур PCB обновляются согласованно — без ручной перерисовки каждого файла.</p>
        </div>
        <div className="drawing-viewer">
          <div className="drawing-image"><img src={drawings[activeDrawing].src} alt={drawings[activeDrawing].title} /></div>
          <div className="drawing-controls"><div><span>{String(activeDrawing + 1).padStart(2, '0')} / 05</span><h3>{drawings[activeDrawing].title}</h3><p>{drawings[activeDrawing].caption}</p></div><div className="arrow-buttons"><button onClick={previousDrawing} aria-label="Предыдущий чертёж"><ChevronLeft /></button><button onClick={nextDrawing} aria-label="Следующий чертёж"><ChevronRight /></button></div></div>
          <div className="drawing-dots" aria-label="Выбор чертежа">{drawings.map((drawing, index) => <button key={drawing.title} className={index === activeDrawing ? 'active' : ''} onClick={() => setActiveDrawing(index)} aria-label={drawing.title} />)}</div>
        </div>
        <div className="spec-layout">
          <div className="spec-intro"><h3>Зафиксированная геометрия v0.3</h3><p>Не абстрактный концепт, а печатаемый четырёхлучевой envelope с проверенными замкнутыми STL‑телами.</p><a href="./project-files/ticker_spinner_v0_3_engineering_drawing.pdf" target="_blank">Открыть полный PDF <ArrowRight size={17} /></a></div>
          <dl className="spec-table"><div><dt>Габарит</dt><dd>Ø100 × 16 мм</dd></div><div><dt>Подшипник</dt><dd>608 · 22 × 7 × 8 мм</dd></div><div><dt>Посадка корпуса</dt><dd>Ø21,85 мм · тестовый coupon</dd></div><div><dt>Основная PCB</dt><dd>до Ø96 мм · 4 луча</dd></div><div><dt>Крепёж</dt><dd>4 × M2 · через 90°</dd></div><div><dt>Материал прототипа</dt><dd>PETG · слой 0,20 мм</dd></div></dl>
        </div>
      </section>

      <section className="section production" id="production">
        <div className="section-heading compact"><div><span className="section-number">04</span><p className="kicker">Маршрут к прототипу</p></div><h2>От файла до вращения</h2><p>Первая версия строится ради быстрой проверки эргономики, света и баланса. Серийные решения пока намеренно не фиксируем.</p></div>
        <div className="timeline">
          {[
            ['01', 'Электро-пакет v0.4', 'Зафиксированы компоненты, восемь LED‑каналов, KiCad, BOM, CPL, Gerber и проверка DRC.', 'Готов для RFQ'],
            ['02', 'Закрытие DRC и DFM', 'Довести центральные соединения до нуля ошибок, проверить footprints, питание и антенну.', 'Следующий шаг'],
            ['03', 'PCBA · 5 штук', 'Завод изготавливает платы, закупает компоненты и выполняет SMT‑монтаж.', 'План'],
            ['04', '3D‑печать', 'PETG‑корпус, посадочный coupon 608 и прозрачные рассеиватели.', 'Файлы готовы'],
            ['05', 'Сборка и тест', 'Прошивка, статическая и динамическая балансировка в защитном кожухе.', 'План'],
          ].map(([number, title, text, status]) => <article key={number}><span className="timeline-number">{number}</span><div><small>{status}</small><h3>{title}</h3><p>{text}</p></div></article>)}
        </div>
        <figure className="partner-visual"><img src="./project-files/ticker_spinner_v0_3_partner_color.png" alt="Цветные изображения и котировки, формируемые четырёхлучевым POV-спиннером" /><figcaption>Концепт рабочего режима: верхние LED формируют изображение на плоскости вращения, торцевые — цветную строку по цилиндру.</figcaption></figure>
        <div className="manufacturing-card"><div className="manufacturing-icon"><PackageCheck /></div><div><p className="kicker">Первая партия</p><h3>Заказывать лучше уже собранные платы</h3><p>Мелкие 2020 и особенно 0909 LED разумнее устанавливать на заводской SMT‑линии. Самостоятельно остаются аккумуляторы, корпус, вертикальные платы, прошивка и балансировка.</p></div><div className="delivery-estimate"><span>Ориентир с доставкой</span><strong>30–45</strong><small>календарных дней</small></div></div>
      </section>

      <section className="section critique-section" id="critique">
        <div className="critique-card">
          <div className="critique-icon"><ShieldAlert /></div>
          <div>
            <p className="kicker">Независимая проверка идеи</p>
            <h2>Разбор критики проекта</h2>
            <p>Отдельный инженерный документ разбирает главные сомнения: дрожание руки, фазовую синхронизацию, центральную слепую зону, реальные обороты, прочность торцевых плат и отличие презентационной визуализации от ожидаемого физического результата.</p>
          </div>
          <div className="critique-actions">
            <a className="button button-primary" href="./project-files/ticker_spinner_critique_assessment.pdf" target="_blank" rel="noreferrer"><FileCode2 size={18} /> Читать PDF</a>
            <a className="button button-ghost" href="./project-files/ticker_spinner_critique_assessment.pdf" download><Download size={18} /> Скачать</a>
          </div>
        </div>
      </section>

      <section className="section downloads" id="downloads">
        <div className="section-heading compact"><div><span className="section-number">05</span><p className="kicker">Архив проекта</p></div><h2>Всё, что уже готово</h2><p>Механика v0.3 и электроника v0.4 доступны отдельно. Электро-пакет содержит открытые DRC‑соединения и предназначен для RFQ/DFM, а не для немедленного изготовления.</p></div>
        <div className="download-grid">
          {fileGroups.map((group) => { const Icon = group.icon; return <article className={group.featured ? 'download-card featured' : 'download-card'} key={group.title}><div className="download-card-head"><Icon /><span>{group.featured ? 'Рекомендуется' : `${group.files.length} файлов`}</span></div><h3>{group.title}</h3><p>{group.text}</p><div className="file-list">{group.files.map(([label, file]) => <DownloadLink key={file} label={label} file={file} />)}</div></article>; })}
        </div>
        <div className="legacy-link"><span>Нужна предыдущая трёхлучевая итерация?</span><a href="./project-files/Ticker_Spinner_v0_2_package.zip" download>Скачать архив v0.2 <Download size={16} /></a></div>
      </section>

      <section className="section status-section">
        <div className="status-card"><div><p className="kicker">Текущий статус</p><h2>Механика готова.<br />Электроника — <em>ERC.</em></h2></div><div className="status-columns"><div><h3><Check /> Уже сделано</h3><ul><li>параметрический корпус v0.3 на 4 луча</li><li>STL и STEP всех деталей</li><li>80 верхних и 48 торцевых LED</li><li>восемь независимых каналов данных</li><li>KiCad, Gerber, drill, BOM и CPL</li><li>электрическая архитектура и производственный чертёж PDF</li><li>расчёт питания и план первого запуска</li></ul></div><div><h3><Zap /> До заказа PCBA</h3><ul><li>закрыть все open nets из DRC</li><li>сверить land patterns с точными MPN</li><li>завершить пассивы boost/зарядки</li><li>проверить RF keep‑out на всех слоях</li><li>повторно выпустить Gerber после DRC=0</li><li>провести DFM у изготовителя</li><li>собрать сначала один first article</li></ul></div></div></div>
        <div className="safety-note"><ShieldAlert /><p><strong>Инженерная оговорка.</strong> Файлы v0.4 годятся для оценки и завершения DFM, но текущие Gerber нельзя отправлять напрямую в производство: в комплект включён честный DRC‑отчёт с незакрытыми соединениями. Первые динамические испытания — только в защитном кожухе.</p></div>
      </section>

      <footer><a className="brand" href="#top"><span className="brand-mark"><CircleDot size={22} /></span><span>SMART<span>SPINNER</span></span></a><p>Умный спиннер для трейдера · механика v0.3 · электроника v0.4 ERC</p><a href="https://github.com/GermanKlimenko/smartspinner" target="_blank" rel="noreferrer"><Code2 size={18} /> Исходники на GitHub</a></footer>
    </main>
  );
}
