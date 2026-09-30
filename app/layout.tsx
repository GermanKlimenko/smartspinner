import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Умный спиннер для трейдера',
  description: 'Исследовательский проект POV-спиннера: аудит, неподвижный стенд B0.1, инструкция и реальные фото LED. Физические испытания ещё не проведены.',
  openGraph: {
    title: 'Умный спиннер для трейдера',
    description: 'От концепции четырёхлучевого спиннера к неподвижному стенду B0.1. Документация и программные проверки, не готовый производственный релиз.',
    images: [{ url: './project-files/ticker_spinner_v0_3_partner_handheld.png', width: 1536, height: 1024, alt: 'Четырёхлучевой умный спиннер v0.3' }],
  },
  twitter: { card: 'summary_large_image', title: 'Умный спиннер для трейдера', description: 'Исследовательский стенд B0.1: документация, аудит и реальные фотографии LED.', images: ['./project-files/ticker_spinner_v0_3_partner_handheld.png'] },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ru"><body>{children}</body></html>;
}
