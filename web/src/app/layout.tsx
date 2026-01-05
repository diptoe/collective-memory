import type { Metadata } from 'next';
import { Inter, Source_Serif_4, JetBrains_Mono } from 'next/font/google';
import { ClientLayout } from '@/components/client-layout';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

const sourceSerif = Source_Serif_4({
  subsets: ['latin'],
  variable: '--font-source-serif',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains',
});

export const metadata: Metadata = {
  title: 'Collective Memory',
  description: 'Multi-agent AI collaboration platform by Diptoe',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${sourceSerif.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-cm-cream text-cm-charcoal antialiased">
        <div className="flex min-h-screen">
          {/* Sidebar Navigation */}
          <nav className="w-64 bg-cm-ivory border-r border-cm-sand flex flex-col">
            <div className="p-6 border-b border-cm-sand">
              <h1 className="font-serif text-xl font-semibold text-cm-charcoal">
                Collective Memory
              </h1>
              <p className="text-sm text-cm-coffee mt-1">by Diptoe</p>
            </div>

            <div className="flex-1 py-4">
              <NavLink href="/" icon="home">Dashboard</NavLink>
              <NavLink href="/chat" icon="message-circle">Chat</NavLink>
              <NavLink href="/personas" icon="users">Personas</NavLink>
              <NavLink href="/models" icon="brain">Models</NavLink>
              <NavLink href="/entities" icon="database">Entities</NavLink>
              <NavLink href="/documents" icon="file-text">Documents</NavLink>
              <NavLink href="/types" icon="layers">Types</NavLink>
              <NavLink href="/graph" icon="git-branch">Graph</NavLink>
              <NavLink href="/messages" icon="inbox">Messages</NavLink>
              <NavLink href="/agents" icon="cpu">Agents</NavLink>
            </div>

            <div className="p-4 border-t border-cm-sand">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-cm-terracotta flex items-center justify-center text-cm-ivory text-sm font-medium">
                  WH
                </div>
                <div>
                  <p className="text-sm font-medium text-cm-charcoal">Wayne Houlden</p>
                  <p className="text-xs text-cm-coffee">Owner</p>
                </div>
              </div>
            </div>
          </nav>

          {/* Main Content */}
          <main className="flex-1 overflow-auto">
            <ClientLayout>{children}</ClientLayout>
          </main>
        </div>
      </body>
    </html>
  );
}

function NavLink({
  href,
  icon,
  children
}: {
  href: string;
  icon: string;
  children: React.ReactNode;
}) {
  return (
    <a
      href={href}
      className="flex items-center gap-3 px-6 py-2.5 text-cm-coffee hover:text-cm-charcoal hover:bg-cm-sand/50 transition-colors"
    >
      <NavIcon name={icon} />
      <span className="text-sm font-medium">{children}</span>
    </a>
  );
}

function NavIcon({ name }: { name: string }) {
  // Simple icon placeholder - will be replaced with Lucide icons
  const icons: Record<string, string> = {
    'home': '🏠',
    'message-circle': '💬',
    'users': '👥',
    'brain': '🧠',
    'database': '🗄️',
    'file-text': '📄',
    'layers': '📊',
    'git-branch': '🔀',
    'inbox': '📥',
    'cpu': '⚙️',
  };
  return <span className="w-5 text-center">{icons[name] || '•'}</span>;
}
