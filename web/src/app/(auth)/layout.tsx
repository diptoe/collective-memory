/**
 * Auth Layout - Minimal layout for login/register pages
 *
 * Displays auth pages centered without the main sidebar navigation.
 */
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-cm-cream">
      {children}
    </div>
  );
}
