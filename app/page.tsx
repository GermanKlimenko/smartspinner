'use client';
/* Static GitHub Pages export: plain images deliberately preserve relative URLs. */
/* eslint-disable next/no-img-element */

import {
  ArrowDown, ArrowRight, Bluetooth, Box, Check, ChevronLeft, ChevronRight,
  CircleDot, Code2, Cpu, Download, FileCode2, FileDown, Gauge,
  Layers3, Menu, Radio, Ruler, ShieldAlert, Sparkles, X,
} from 'lucide-react';
import { useState } from 'react';

const nav = [
  ['Стенд', 'bench'], ['Фото LED', 'reference-fan'], ['Механика', 'mechanics'],
  ['План', 'production'], ['Файлы', 'downloads'],
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
    icon: Cpu, title: 'Стенд B0.1 · текущий этап',
    text: 'Неподвижный стенд: инструкция, покупки, соединения и прошивка. Программные проверки пройдены; на железе не проверено. Это не плата готового спиннера.',
    files: [
      ['Весь пакет · ZIP', 'SmartSpinner_B01_DIY_Package.zip'],
      ['Инструкция · PDF', 'bench-b0.1/SmartSpinner_B01_Bench.pdf'],
      ['Список покупок · MD', 'bench-b0.1/shopping.md'],
      ['Таблица соединений · HTML', 'bench-b0.1/wiring.html'],
    ], featured: true,
  },
  {
    icon: Box, title: 'Корпус для печати',
    text: 'Геометрический концепт v0.3 для переработки. Не проверенная сборка: совместимость с будущей электроникой и безопасность вращения не подтверждены.',
    files: [
      ['Верх · STL', 'ticker_spinner_v0_3_top.stl'], ['Низ · STL', 'ticker_spinner_v0_3_bottom.stl'],
      ['Рассеиватели · STL', 'ticker_spinner_v0_3_diffusers.stl'], ['Сборка · STEP', 'ticker_spinner_v0_3_assembly.step'],
      ['Верх · STEP', 'ticker_spinner_v0_3_top.step'], ['Низ · STEP', 'ticker_spinner_v0_3_bottom.step'],
      ['Крышка подшипника · STL', 'ticker_spinner_v0_3_finger_cap_top.stl'],
    ],
  },
  {
    icon: Cpu, title: 'Печатные платы',
    text: 'Предварительные контуры и объёмные модели. Аудит обнаружил несовместимость прежней PCB с корпусом; размеры нужно пересогласовать.',
    files: [
      ['Контур основной PCB · DXF', 'ticker_spinner_v0_3_pcb_outline.dxf'],
      ['Контур торцевой PCB · DXF', 'ticker_spinner_v0_3_tip_led_board.dxf'],
      ['Envelope основной PCB · STEP', 'ticker_spinner_v0_3_pcb_envelope.step'],
      ['Envelope торцевой PCB · STEP', 'ticker_spinner_v0_3_tip_led_board_envelope.step'],
    ],
  },
  {
    icon: FileCode2, title: 'Документация и исходники',
    text: 'Сохранённая геометрия v0.3 и её генератор. Это исходная концепция, а не производственный комплект.',
    files: [
      ['Инженерный чертёж · PDF', 'ticker_spinner_v0_3_engineering_drawing.pdf'],
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
          <div className="eyebrow"><span /> Исследовательский стенд B0.1 · 30.09.2026</div>
          <h1>Умный спиннер<br /><em>для трейдера</em></h1>
          <p className="hero-lead">Идея карманного POV-дисплея: котировки на плоскости вращения и цветной тикер по кругу. Сейчас проверяем электронику на неподвижном стенде.</p>
          <div className="hero-actions">
            <a className="button button-primary" href="./project-files/SmartSpinner_B01_DIY_Package.zip" download><Download size={18} /> Скачать стенд B0.1</a>
            <a className="button button-ghost" href="#concept">Изучить конструкцию <ArrowDown size={18} /></a>
          </div>
          <div className="hero-note"><span className="pulse" /> Документация готова. Физических испытаний ещё не было.</div>
        </div>
        <div className="hero-visual">
          <div className="hero-image-frame"><img src="./project-files/ticker_spinner_v0_3_partner_handheld.png" alt="Концептуальный рендер четырёхлучевого спиннера в руке" /></div><p className="research-caption">Визуализация идеи — не фотография работающего образца.</p>
          <div className="float-card float-card-top"><span>ЦЕЛЬ: RGB PIXELS</span><strong>128</strong><small>80 сверху + 48 на торцах</small></div>
          <div className="float-card float-card-bottom"><span>FORM FACTOR</span><strong>Ø100</strong><small>миллиметров</small></div>
        </div>
      </section>

      <aside className="release-warning"><ShieldAlert /><div><strong>Старые схемы сняты с публикации. Не изготавливать.</strong><p>Аудит обнаружил ошибки питания, посадочных мест и согласования PCB с корпусом. Пакеты электроники v0.4/v0.5 удалены из текущего каталога. История Git сохранена.</p><a href="https://github.com/GermanKlimenko/smartspinner/blob/main/audits/2026-09-29-electronics/README.md">Читать аудит от 29.09.2026 →</a></div></aside>
      <section className="section" id="bench">
        <div className="section-heading"><div><span className="section-number">B0.1</span><p className="kicker">Текущий этап</p></div><h2>Сначала свет.<br /><em>Потом вращение.</em></h2><p>Один неподвижный эквивалент луча: 20 верхних + 12 торцевых RGB. Проверяем управление, ток и отключение до разработки компактной платы.</p></div>
        <div className="bench-grid"><figure><img src="./project-files/bench-b0.1/schematic.svg" alt="Схема питания и управления неподвижного стенда B0.1" loading="lazy" /><figcaption className="research-caption">Опытная ручная сборка. Подробные соединения — в инструкции.</figcaption></figure><div className="bench-copy"><h3>Что собираем на столе</h3><ul><li>Arduino UNO R3 — временный тестовый контроллер.</li><li>6 × SM16306SJ, 96 цветовых каналов.</li><li>32 выводных RGB LED: удобные для пайки, не для конечного корпуса.</li><li>Раздельное питание логики и LED, общий GND, ручное отключение.</li></ul><p>Программно проверены сборка прошивки, адресация каналов и таблица соединений. Ток, нагрев и оптические импульсы предстоит измерить.</p><p><strong>Без аккумулятора и мотора. Не закреплять стенд на купленном вентиляторе.</strong></p><a className="button button-primary" href="./project-files/bench-b0.1/SmartSpinner_B01_Bench.pdf" target="_blank" rel="noreferrer">План сборки и испытаний</a></div></div>
      </section>
      <section className="section reference-section" id="reference-fan">
        <div className="section-heading"><div><span className="section-number">Фото</span><p className="kicker">Реальное устройство</p></div><h2>Изучаем<br /><em>POV-вентилятор</em></h2><p>Фотографии купленного Германом «голографического» LED-вентилятора, 29.09.2026. Это образец для изучения, а не наша сборка. Нажмите на фото, чтобы рассмотреть детали.</p></div>
        <div className="photo-grid">{[
          ['led-ruler.jpg', 'LED рядом с линейкой', 'Фото позволяет оценивать шаг. Точный тип корпуса и артикул LED пока не установлены.'],
          ['driver-sm16306sj.jpg', 'Драйверы SM16306SJ', 'Маркировка читается на корпусах. Ориентир для эксперимента с внешними драйверами, но не готовая схема нашего спиннера.'],
          ['led-closeup.jpg', 'Световая сторона линейки', 'Реальные светодиоды купленного устройства. Ток, яркость и оптические импульсы ещё не измерены.'],
        ].map(([src, title, caption]) => <figure key={src}><a href={`./assets/reference-fan/${src}`} target="_blank" rel="noreferrer" aria-label={`Увеличить: ${title}`}><img src={`./assets/reference-fan/${src}`} alt={title} loading="lazy" /></a><figcaption><h3>{title}</h3><p>{caption}</p></figcaption></figure>)}</div>
        <p className="research-caption">Фото не заменяют измерения. Бытовое название «3D-голограф» не означает объёмную голограмму. Маленький корпус LED сам по себе не гарантирует чёткость: важны также шаг, оптика, управление и синхронизация.</p>
      </section>
      <section className="metrics" aria-label="Целевые параметры концепции, не проверенного устройства">
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
            <h3>Цель: двенадцать пикселей по высоте</h3>
            <p>Планируем вертикальную LED-колонку для цветной строки по кругу. Читаемость, допустимые обороты и число строк нужно подтвердить оптическими испытаниями. Ниже — цели, не результаты теста.</p>
            <ul className="check-list"><li><Check /> читаемые тикеры и числа</li><li><Check /> двухстрочные композиции</li><li><Check /> графики, иконки и цветовые сигналы</li></ul>
          </div>
        </div>
      </section>

      <section className="section dark-section" id="electronics">
        <div className="section-heading light">
          <div><span className="section-number">02</span><p className="kicker">Электроника</p></div>
          <h2>Одна основная плата.<br /><em>Четыре световых луча.</em></h2>
          <p>Планируем держать тяжёлые элементы ближе к оси и соблюдать симметрию 90°. Конечная схема, подбор компонентов и размещение требуют переработки после испытаний стенда.</p>
        </div>
        <div className="pcb-showcase">
          <figure className="pcb-image"><img src="./project-files/ticker_spinner_v0_3_partner_dock.png" alt="Четырёхлучевой спиннер v0.3 в рабочем режиме на демонстрационной опоре" /><figcaption>Концептуальный рендер v0.3. Не доказательство достижимой чёткости.</figcaption></figure>
          <div className="component-list">
            <article><span>01</span><div><h3>Цель: 80 верхних RGB</h3><p>По 20 LED на луч. Тип LED и способ управления ещё выбираем.</p></div></article>
            <article><span>02</span><div><h3>Цель: 4 × 12 торцевых RGB</h3><p>Сменные вертикальные платы для кругового цветного тикера.</p></div></article>
            <article><span>03</span><div><h3>nRF52840 + BLE</h3><p>Кандидат для BLE и управления кадром; реализация ещё не проверена.</p></div></article>
            <article><span>04</span><div><h3>Hall + IMU</h3><p>Синхронизация требует отдельной проверки. IMU не гарантирует компенсацию движения руки.</p></div></article>
            <article><span>05</span><div><h3>LED-драйверы: проверка на стенде</h3><p>В B0.1 изучаем внешние драйверы SM16306SJ. Архитектура компактной платы ещё не зафиксирована.</p></div></article>
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
          <p>Сохраняем параметрическую модель v0.3 как основу для переработки. Аудит выявил пересечения прежней PCB с корпусом: компоновку нужно согласовать заново.</p>
        </div>
        <div className="drawing-viewer">
          <div className="drawing-image"><img src={drawings[activeDrawing].src} alt={drawings[activeDrawing].title} /></div>
          <div className="drawing-controls"><div><span>{String(activeDrawing + 1).padStart(2, '0')} / 05</span><h3>{drawings[activeDrawing].title}</h3><p>{drawings[activeDrawing].caption}</p></div><div className="arrow-buttons"><button onClick={previousDrawing} aria-label="Предыдущий чертёж"><ChevronLeft /></button><button onClick={nextDrawing} aria-label="Следующий чертёж"><ChevronRight /></button></div></div>
          <div className="drawing-dots" aria-label="Выбор чертежа">{drawings.map((drawing, index) => <button key={drawing.title} className={index === activeDrawing ? 'active' : ''} onClick={() => setActiveDrawing(index)} aria-label={drawing.title} />)}</div>
        </div>
        <div className="spec-layout">
          <div className="spec-intro"><h3>Зафиксированная геометрия v0.3</h3><p>Геометрическая модель для примерки и переработки, не проверенная сборка готового устройства.</p><a href="./project-files/ticker_spinner_v0_3_engineering_drawing.pdf" target="_blank">Открыть полный PDF <ArrowRight size={17} /></a></div>
          <dl className="spec-table"><div><dt>Габарит</dt><dd>Ø100 × 16 мм</dd></div><div><dt>Подшипник</dt><dd>608 · 22 × 7 × 8 мм</dd></div><div><dt>Посадка корпуса</dt><dd>Ø21,85 мм · тестовый coupon</dd></div><div><dt>Основная PCB</dt><dd>до Ø96 мм · 4 луча</dd></div><div><dt>Крепёж</dt><dd>4 × M2 · через 90°</dd></div><div><dt>Материал прототипа</dt><dd>PETG · слой 0,20 мм</dd></div></dl>
        </div>
      </section>

      <section className="section production" id="production">
        <div className="section-heading compact"><div><span className="section-number">04</span><p className="kicker">Маршрут к прототипу</p></div><h2>От файла до вращения</h2><p>Первая версия строится ради быстрой проверки эргономики, света и баланса. Серийные решения пока намеренно не фиксируем.</p></div>
        <div className="timeline">
          {[
            ['01', 'Ревизия', 'Ошибки зафиксированы, прежние электрические пакеты сняты с публикации.', 'Выполнено'],
            ['02', 'Документация B0.1', 'Инструкция, список покупок, соединения и тестовая прошивка.', 'Подготовлено'],
            ['03', 'Сборка стенда', 'Адресация, ток, отключение, нагрев и оптические импульсы.', 'Следующий шаг'],
            ['04', 'Новая компактная PCB', 'Схема, компоненты, разводка, ERC/DRC и согласование с корпусом.', 'После испытаний'],
            ['05', 'PCBA · 10 штук', 'DFM, изготовление и проверка прототипов. Вращение — только с защитой.', 'После проверки проекта'],
          ].map(([number, title, text, status]) => <article key={number}><span className="timeline-number">{number}</span><div><small>{status}</small><h3>{title}</h3><p>{text}</p></div></article>)}
        </div>
        <figure className="partner-visual"><img src="./project-files/ticker_spinner_v0_3_partner_color.png" alt="Цветные изображения и котировки, формируемые четырёхлучевым POV-спиннером" /><figcaption>Концепт рабочего режима: верхние LED формируют изображение на плоскости вращения, торцевые — цветную строку по цилиндру.</figcaption></figure>

      </section>

      <section className="section critique-section" id="critique">
        <div className="critique-card">
          <div className="critique-icon"><ShieldAlert /></div>
          <div>
            <p className="kicker">Ревизия электроники</p>
            <h2>Что показал аудит</h2>
            <p>Перепутанные сети питания, неверные footprints, незавершённые соединения и механические пересечения. Ранние оценки готовности были завышены. Полный отчёт содержит доказательства и ограничения проверки.</p>
          </div>
          <div className="critique-actions"><a className="button button-primary" href="https://github.com/GermanKlimenko/smartspinner/blob/main/audits/2026-09-29-electronics/README.md">Открыть аудит <ArrowRight size={18} /></a>
          </div>
        </div>
      </section>

      <section className="section downloads" id="downloads">
        <div className="section-heading compact"><div><span className="section-number">05</span><p className="kicker">Актуальные материалы</p></div><h2>Без старых пакетов</h2><p>Для начала используйте B0.1. Геометрия — только основа для переработки. Производственного комплекта готового спиннера пока нет.</p></div>
        <div className="download-grid">
          {fileGroups.map((group) => { const Icon = group.icon; return <article className={group.featured ? 'download-card featured' : 'download-card'} key={group.title}><div className="download-card-head"><Icon /><span>{group.featured ? 'Текущий этап' : `${group.files.length} файлов`}</span></div><h3>{group.title}</h3><p>{group.text}</p><div className="file-list">{group.files.map(([label, file]) => <DownloadLink key={file} label={label} file={file} />)}</div></article>; })}
        </div>
        <div className="legacy-link"><span>Устаревшие файлы сохранены только в истории Git, не для изготовления.</span><a href="https://github.com/GermanKlimenko/smartspinner/tree/main/bench/v0.1">Исходники стенда →</a></div>
      </section>

      <section className="section status-section">
        <div className="safety-note"><ShieldAlert /><p><strong>Статус на 30.09.2026.</strong> Документация и программные проверки B0.1 готовы. Физическая сборка, измерения, BLE, время работы от аккумулятора и читаемость при вращении ещё не подтверждены.</p></div>
      </section>

      <footer><a className="brand" href="#top"><span className="brand-mark"><CircleDot size={22} /></span><span>SMART<span>SPINNER</span></span></a><p>Умный спиннер для трейдера · исследовательский стенд B0.1</p><a href="https://github.com/GermanKlimenko/smartspinner" target="_blank" rel="noreferrer"><Code2 size={18} /> Исходники на GitHub</a></footer>
    </main>
  );
}
