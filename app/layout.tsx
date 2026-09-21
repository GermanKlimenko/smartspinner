import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Умный спиннер для трейдера',
  description: 'Четырёхлучевой карманный POV-дисплей: 128 RGB-пикселей, BLE, корпус и полный инженерный комплект v0.3.',
  openGraph: {
    title: 'Умный спиннер для трейдера',
    description: 'Четыре луча, 80 верхних и 48 торцевых RGB-пикселей. Инженерный проект v0.3.',
    images: [{ url: './project-files/ticker_spinner_v0_3_partner_handheld.png', width: 1536, height: 1024, alt: 'Четырёхлучевой умный спиннер v0.3' }],
  },
  twitter: { card: 'summary_large_image', title: 'Умный спиннер для трейдера', description: 'Четырёхлучевой POV-дисплей v0.3 для котировок, сигналов и графики.', images: ['./project-files/ticker_spinner_v0_3_partner_handheld.png'] },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ru"><body>{children}</body></html>;
}
