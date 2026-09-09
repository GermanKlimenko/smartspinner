import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Умный спиннер для трейдера',
  description: 'Инженерный проект карманного POV-дисплея: корпус, PCB, 81 RGB-пиксель, BLE и полный комплект файлов v0.2.',
  openGraph: {
    title: 'Умный спиннер для трейдера',
    description: 'Карманный POV-дисплей для котировок, сигналов и графики. Инженерный проект v0.2.',
    images: [{ url: './og.png', width: 1536, height: 1024, alt: 'Плата умного спиннера' }],
  },
  twitter: { card: 'summary_large_image', title: 'Умный спиннер для трейдера', description: 'Карманный POV-дисплей для котировок, сигналов и графики.', images: ['./og.png'] },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ru"><body>{children}</body></html>;
}
