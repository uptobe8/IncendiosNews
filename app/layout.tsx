import './globals.css';
export const metadata = { title: 'FireWatch Centro', description: 'Monitor de incendios Madrid, Ávila y Toledo' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="es"><body>{children}</body></html>;
}
