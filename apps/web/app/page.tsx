const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const healthUrl = `${apiBaseUrl}/api/health`;

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-6 py-16">
      <p className="mb-4 text-sm font-semibold tracking-[0.18em] text-[var(--accent)]">RECONRA</p>
      <h1 className="max-w-2xl text-4xl font-semibold tracking-tight">Evidence-first settlement reconciliation.</h1>
      <p className="mt-5 max-w-xl text-lg leading-8 text-[var(--muted-ink)]">
        Foundation shell: the web app is ready to connect to the local API health contract.
      </p>
      <a
        className="mt-8 inline-flex w-fit border border-[var(--accent)] px-4 py-2 text-sm font-medium text-[var(--accent)]"
        href={healthUrl}
      >
        Check local API health
      </a>
      <code className="mt-4 w-fit border border-[var(--border)] bg-white px-3 py-2 text-sm">GET /api/health</code>
    </main>
  );
}
