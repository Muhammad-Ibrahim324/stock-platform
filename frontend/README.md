# Frontend

Next.js (App Router) + TypeScript + Tailwind CSS v4 + Recharts.

See the [root README](../README.md) for the full project overview, setup
instructions, and architecture notes. This file only covers frontend-specific
commands.

```bash
npm install
cp .env.example .env.local
npm run dev      # http://localhost:3000
npm run build    # production build
npm run lint      # eslint
```

`NEXT_PUBLIC_API_BASE_URL` (in `.env.local`) points the browser at the
FastAPI backend — see the root README's "Architecture" section for why
server-side requests use a different URL when running under Docker Compose.
