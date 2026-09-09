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
  { src: './assets/drawings/sheet-1.png', title: 'Общий вид и сечение', caption: 'Габарит Ø100 мм, толщина сборки 16 мм и расположение платы.' },
  { src: './assets/drawings/sheet-2.png', title: 'Нижняя часть корпуса', caption: 'Посадка подшипника, карманы питания и три стойки M2.' },
  { src: './assets/drawings/sheet-3.png', title: 'Верхняя крышка', caption: 'Световые окна, рассеиватели и доступ к крепежу.' },
  { src: './assets/drawings/sheet-4.png', title: 'Плата и внутренняя компоновка', caption: 'Зоны электроники, аккумуляторов и балансировки.' },
  { src: './assets/drawings/sheet-5.png', title: 'Торцевая плата — 12 пикселей', caption: 'Вертикальная колонка для цилиндрической бегущей строки.' },
];

const fileGroups = [
  {
    icon: FileArchive, title: 'Полный комплект v0.2',
    text: 'Вся актуальная механика, PCB-макеты, чертежи, исходники и проверки одним архивом.',
    files: [['Скачать ZIP · 1,6 МБ', 'Ticker_Spinner_v0_2_package.zip']], featured: true,
  },
  {
    icon: Box, title: 'Корпус для печати',
    text: 'Верх, низ и рассеиватели в производственных и редактируемых форматах.',
    files: [
      ['Верх · STL', 'ticker_spinner_v0_2_top.stl'], ['Низ · STL', 'ticker_spinner_v0_2_bottom.stl'],
      ['Рассеиватели · STL', 'ticker_spinner_v0_2_diffusers.stl'], ['Сборка · STEP', 'ticker_spinner_v0_2_assembly.step'],
      ['Верх · STEP', 'ticker_spinner_v0_2_top.step'], ['Низ · STEP', 'ticker_spinner_v0_2_bottom.step'],
    ],
  },
  {
    icon: Cpu, title: 'Печатные платы',
    text: 'Контуры DXF и редактируемые макеты KiCad основной и торцевой плат.',
    files: [
      ['Основная плата · KiCad', 'ticker_spinner_v0_2_main_board_mockup.kicad_pcb'],
      ['Торцевая плата · KiCad', 'ticker_spinner_v0_2_tip_board_mockup.kicad_pcb'],
      ['Контур PCB · DXF', 'ticker_spinner_v0_2_pcb_outline.dxf'], ['Торцевая PCB · DXF', 'ticker_spinner_v0_2_tip_led_board.dxf'],
      ['Предварительный BOM · CSV', 'ticker_spinner_v0_2_preliminary_bom.csv'], ['Назначение сигналов · JSON', 'ticker_spinner_v0_2_pinmap.json'],
    ],
  },
  {
    icon: FileCode2, title: 'Документация и исходники',
    text: 'Чертёж, описание параметров и генератор всей геометрии v0.2.',
    files: [
      ['Инженерный чертёж · PDF', 'ticker_spinner_v0_2_engineering_drawing.pdf'],
      ['Описание проекта · MD', 'README_Ticker_Spinner_v0_2.md'], ['Генератор модели · Python', 'generate_ticker_spinner_v0_2.py'],
      ['Отчёт проверки · JSON', 'ticker_spinner_v0_2_validation.json'],
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
          <div className="eyebrow"><span /> Инженерный прототип · v0.2</div>
          <h1>Умный спиннер<br /><em>для трейдера</em></h1>
          <p className="hero-lead">Карманный POV‑дисплей, который превращает вращение в экран: котировки, проценты, сигналы и логотипы возникают прямо в воздухе.</p>
          <div className="hero-actions">
            <a className="button button-primary" href="./project-files/Ticker_Spinner_v0_2_package.zip" download><Download size={18} /> Скачать проект v0.2</a>
            <a className="button button-ghost" href="#concept">Изучить конструкцию <ArrowDown size={18} /></a>
          </div>
          <div className="hero-note"><span className="pulse" /> Параметрическая модель готова для первой 3D‑печати</div>
        </div>
        <div className="hero-visual">
          <div className="hero-image-frame"><img src="./assets/pcb-render.png" alt="Трёхлучевая плата умного спиннера и торцевая плата на 12 светодиодов" /></div>
          <div className="float-card float-card-top"><span>RGB PIXELS</span><strong>81</strong><small>45 сверху + 36 на торцах</small></div>
          <div className="float-card float-card-bottom"><span>FORM FACTOR</span><strong>Ø100</strong><small>миллиметров</small></div>
        </div>
      </section>

      <section className="metrics" aria-label="Основные параметры">
        <div><Ruler /><strong>100 мм</strong><span>внешний диаметр</span></div>
        <div><Layers3 /><strong>16 мм</strong><span>толщина сборки</span></div>
        <div><Sparkles /><strong>12 × 3</strong><span>торцевых пикселей</span></div>
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
            <div className="spinner-demo"><div className="demo-arm arm-a"><i /></div><div className="demo-arm arm-b"><i /></div><div className="demo-arm arm-c"><i /></div><div className="demo-bearing" /></div>
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
          <h2>Одна основная плата.<br /><em>Три световых луча.</em></h2>
          <p>Тяжёлые элементы собраны ближе к оси, а повторяющиеся узлы расположены с симметрией 120°. Так электроника помогает балансу, а не борется с ним.</p>
        </div>
        <div className="pcb-showcase">
          <figure className="pcb-image"><img src="./assets/pcb-layout.png" alt="Инженерный макет размещения компонентов основной и торцевой платы" /><figcaption>Размещение v0.2 — основа для финальной схемы и трассировки</figcaption></figure>
          <div className="component-list">
            <article><span>01</span><div><h3>45 × RGB 2020</h3><p>По 15 адресных верхних LED на каждом луче. Шаг 2,20 мм.</p></div></article>
            <article><span>02</span><div><h3>3 × 12 RGB 0909</h3><p>Сменные вертикальные платы 7 × 13,6 мм для кругового тикера.</p></div></article>
            <article><span>03</span><div><h3>nRF52840 + BLE</h3><p>Получение данных со смартфона, точный тайминг и управление кадром.</p></div></article>
            <article><span>04</span><div><h3>Hall index</h3><p>Один точный импульс на оборот для привязки изображения к углу.</p></div></article>
            <article><span>05</span><div><h3>Питание 3,3 / 5 В</h3><p>Зарядка LiPo и повышающий преобразователь с импульсным запасом ≥1,5 А.</p></div></article>
          </div>
        </div>
        <div className="signal-flow">
          <div><Radio /><span>Котировки</span><small>телефон / API</small></div><ArrowRight /><div><Bluetooth /><span>BLE</span><small>пакет данных</small></div><ArrowRight /><div><Cpu /><span>nRF52</span><small>рендер кадра</small></div><ArrowRight /><div><Gauge /><span>Hall</span><small>угол вращения</small></div><ArrowRight /><div className="flow-accent"><Sparkles /><span>81 RGB</span><small>воздушный экран</small></div>
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
          <div className="spec-intro"><h3>Зафиксированная геометрия v0.2</h3><p>Не абстрактный концепт, а печатаемый механический envelope с проверенными замкнутыми STL‑телами.</p><a href="./project-files/ticker_spinner_v0_2_engineering_drawing.pdf" target="_blank">Открыть полный PDF <ArrowRight size={17} /></a></div>
          <dl className="spec-table"><div><dt>Габарит</dt><dd>Ø100 × 16 мм</dd></div><div><dt>Подшипник</dt><dd>608 · 22 × 7 × 8 мм</dd></div><div><dt>Посадка корпуса</dt><dd>Ø21,85 мм · тестовый coupon</dd></div><div><dt>Основная PCB</dt><dd>до Ø96 мм · толщина ~1,0 мм</dd></div><div><dt>Крепёж</dt><dd>3 × M2 · через 120°</dd></div><div><dt>Материал прототипа</dt><dd>PETG · слой 0,20 мм</dd></div></dl>
        </div>
      </section>

      <section className="section production" id="production">
        <div className="section-heading compact"><div><span className="section-number">04</span><p className="kicker">Маршрут к прототипу</p></div><h2>От файла до вращения</h2><p>Первая версия строится ради быстрой проверки эргономики, света и баланса. Серийные решения пока намеренно не фиксируем.</p></div>
        <div className="timeline">
          {[
            ['01', 'Финальная схема', 'Выбрать точные LED, nRF52, Hall, зарядник и топологию аккумулятора.', 'Следующий шаг'],
            ['02', 'Разводка PCB', 'Трассировка питания и данных, антенна, тест‑пойнты, DRC и проверка баланса.', 'План'],
            ['03', 'PCBA · 5 штук', 'Завод изготавливает платы, закупает компоненты и выполняет SMT‑монтаж.', 'План'],
            ['04', '3D‑печать', 'PETG‑корпус, посадочный coupon 608 и прозрачные рассеиватели.', 'Файлы готовы'],
            ['05', 'Сборка и тест', 'Прошивка, статическая и динамическая балансировка в защитном кожухе.', 'План'],
          ].map(([number, title, text, status]) => <article key={number}><span className="timeline-number">{number}</span><div><small>{status}</small><h3>{title}</h3><p>{text}</p></div></article>)}
        </div>
        <div className="manufacturing-card"><div className="manufacturing-icon"><PackageCheck /></div><div><p className="kicker">Первая партия</p><h3>Заказывать лучше уже собранные платы</h3><p>Мелкие 2020 и особенно 0909 LED разумнее устанавливать на заводской SMT‑линии. Самостоятельно остаются аккумуляторы, корпус, вертикальные платы, прошивка и балансировка.</p></div><div className="delivery-estimate"><span>Ориентир с доставкой</span><strong>30–45</strong><small>календарных дней</small></div></div>
      </section>

      <section className="section downloads" id="downloads">
        <div className="section-heading compact"><div><span className="section-number">05</span><p className="kicker">Архив проекта</p></div><h2>Всё, что уже готово</h2><p>Файлы v0.2 можно скачать отдельно или одним архивом. Исходная параметрическая модель позволяет менять размеры и пересобирать комплект.</p></div>
        <div className="download-grid">
          {fileGroups.map((group) => { const Icon = group.icon; return <article className={group.featured ? 'download-card featured' : 'download-card'} key={group.title}><div className="download-card-head"><Icon /><span>{group.featured ? 'Рекомендуется' : `${group.files.length} файлов`}</span></div><h3>{group.title}</h3><p>{group.text}</p><div className="file-list">{group.files.map(([label, file]) => <DownloadLink key={file} label={label} file={file} />)}</div></article>; })}
        </div>
        <div className="legacy-link"><span>Нужна предыдущая итерация?</span><a href="./project-files/Ticker_Spinner_v0_1_package.zip" download>Скачать архив v0.1 <Download size={16} /></a></div>
      </section>

      <section className="section status-section">
        <div className="status-card"><div><p className="kicker">Текущий статус</p><h2>Механика готова.<br />Электроника — <em>макет.</em></h2></div><div className="status-columns"><div><h3><Check /> Уже сделано</h3><ul><li>параметрический корпус v0.2</li><li>STL и STEP верхней/нижней частей</li><li>рассеиватели и окна LED</li><li>контуры обеих PCB</li><li>макеты плат KiCad</li><li>размерный чертёж</li><li>автоматическая проверка STL</li></ul></div><div><h3><Zap /> До заказа PCBA</h3><ul><li>утвердить конкретные компоненты</li><li>создать электрическую схему</li><li>выполнить финальную трассировку</li><li>рассчитать питание и нагрев</li><li>подготовить Gerber, BOM и CPL</li><li>проверить антенну и прошивку</li><li>провести DFM‑контроль</li></ul></div></div></div>
        <div className="safety-note"><ShieldAlert /><p><strong>Инженерная оговорка.</strong> v0.2 — проверяемая основа для прототипирования, но ещё не готовая производственная электроника. Первые динамические испытания проводить на ограниченных оборотах и только в защитном кожухе.</p></div>
      </section>

      <footer><a className="brand" href="#top"><span className="brand-mark"><CircleDot size={22} /></span><span>SMART<span>SPINNER</span></span></a><p>Умный спиннер для трейдера · инженерный проект v0.2</p><a href="https://github.com/GermanKlimenko/smartspinner" target="_blank" rel="noreferrer"><Code2 size={18} /> Исходники на GitHub</a></footer>
    </main>
  );
}
