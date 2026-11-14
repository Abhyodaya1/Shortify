import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[var(--color-dominant)] text-[var(--color-secondary)] p-8 text-center">
      <h2 className="text-2xl font-black mb-2 text-[var(--color-emphasis)]">Page Not Found</h2>
      <p className="text-sm text-[var(--color-muted)] mb-6">
        The requested resource could not be found.
      </p>
      <Link
        href="/"
        className="px-4 py-2 min-h-[var(--touch-target-min)] inline-flex items-center justify-center rounded-lg bg-[var(--color-secondary)] text-[var(--color-dominant)] text-xs font-bold hover:bg-[var(--color-emphasis)] transition-colors"
      >
        Return to Studio
      </Link>
    </div>
  );
}
