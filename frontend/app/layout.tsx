import './globals.css';
import 'leaflet/dist/leaflet.css';
import type { Metadata } from 'next';
import { ReactNode } from 'react';

export const metadata: Metadata = {
  title: 'Mobility Freedom Index',
  description: 'Safety intelligence platform that calculates route level MOBILITY FREEDOM SCORE.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}