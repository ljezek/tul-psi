# Frontend — Student Projects Catalogue

React SPA for the Student Projects Catalogue (FM TUL).

## Tech Stack

- **React 19** + TypeScript
- **Vite 6** — build tool & dev server
- **React Router 7** — client-side routing
- **Tailwind CSS 3** — utility-first styling
- **Vitest** + **@testing-library/react** — unit tests
- **ESLint** — linting

## Getting Started

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
# edit .env — set VITE_API_URL to your backend address
```

### 3. Start development server

```bash
npm run dev   # starts on http://localhost:3000
```

## Available Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start dev server (port 3000) |
| `npm run build` | TypeScript check + production build |
| `npm run lint` | Run ESLint |
| `npm test` | Run unit tests once |
| `npm run test:watch` | Run tests in watch mode |
| `npm run preview` | Preview production build |

## Routes

| Path | Page |
|------|------|
| `/` | Landing page |
| `/catalog` | Project catalogue (public) |
| `/student` | Student Zone |
| `/admin` | Lecturer Administration |

## Configuration

Copy `.env.example` to `.env` and set the variables:

```env
VITE_API_URL=http://localhost:3001   # Backend API base URL
```

All `VITE_` prefixed variables are available via `import.meta.env` and are
loaded through `src/config.ts`.
