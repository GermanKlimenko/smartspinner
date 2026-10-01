import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://germanklimenko.github.io/smartspinner/'),
  title: 'Смартлаб — умный спиннер для трейдера',
  description: 'Проект Смартлаба: концепты «Пульс рынка» и «Биржевой сигнал», аудит и неподвижный стенд B0.1. Физические испытания ещё не проведены.',
  openGraph: {
    title: 'Смартлаб — умный спиннер для трейдера',
    description: 'От концепции четырёхлучевого спиннера к неподвижному стенду B0.1. Документация и программные проверки, не готовый производственный релиз.',
    images: [{ url: 'https://germanklimenko.github.io/smartspinner/assets/smartlab/market-full.png', width: 1536, height: 1024, alt: 'Проект Смартлаба — концепт «Пульс рынка»' }],
  },
  twitter: { card: 'summary_large_image', title: 'Смартлаб — умный спиннер для трейдера', description: 'Проект Смартлаба: концептуальные визуализации и исследовательский стенд B0.1.', images: ['https://germanklimenko.github.io/smartspinner/assets/smartlab/market-full.png'] },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ru"><body>{children}</body></html>;
}
