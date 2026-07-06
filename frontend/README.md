# Triage — HeroUI v3 Frontend

Text-only chat interface for the RAG-based support ticket backend, built with
**Next.js 15 (App Router)**, **React 19**, **Tailwind CSS v4**, and **HeroUI v3**
(`@heroui/react` 3.2.1 / `@heroui/styles` 3.2.1) — verified against the current
live HeroUI v3 docs, not assumed from older v2/NextUI knowledge.

## What this connects to

Exactly two backend endpoints, nothing else:
- `GET /health` — polled once on load to show the online/offline pill in the header.
- `POST /api/v1/tickets/respond` — sends `{ subject?, body }` with an `X-API-Key`
  header, renders `{ predicted_queue, generated_answer, needs_human_review, confidence_score }`.

There is **no file upload and no separate "sources/citations" endpoint** in the
backend, so this build doesn't include an upload button or a citations panel —
adding either would mean building UI for something the API can't actually serve.
The "Prediction details" accordion on each result card shows exactly the three
fields above; that's the full extent of what the backend hands back per ticket.

## Configure the backend connection

Copy the example env file and fill in your real values (never commit `.env.local`):

```bash
cp .env.example .env.local
```

```
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_KEY=your-api-key-here
```

Set `NEXT_PUBLIC_API_KEY` to match whatever `API_KEY` is set to in the backend's
`.env`. Set `NEXT_PUBLIC_API_BASE_URL` to your Azure URL once deployed.

**CORS reminder:** your FastAPI backend must have `CORSMiddleware` enabled with
this frontend's dev origin (`http://localhost:3000` or `3100`, whichever port
you run it on) included in `allow_origins`, or the browser will block every
request regardless of how correct this frontend's code is.

## Run it

```bash
npm install
npm run dev
```

Open the printed local URL (defaults to `http://localhost:3000`). Make sure
the FastAPI backend is already running and reachable at `API_BASE_URL` first.

For a production build:
```bash
npm run build
npm start
```

## Component map (HeroUI v3 usage)

| UI piece | HeroUI v3 components used |
|---|---|
| Sidebar / ticket history + collapse toggle | Plain layout + `Button` (New ticket) |
| Header online/offline + theme switch | `useTheme` hook, `Button`, `Chip` |
| User message bubble | `Card` (`Card.Header`, `Card.Content`) |
| AI response bubble | `Card` (`Card.Header/Content/Footer`), `Chip` (color-coded queue), custom confidence bar, `Accordion` for prediction details, `Alert` when flagged for human review, `Button` (copy reply) |
| Loading state | `Skeleton` |
| Error state | `Alert` (`Alert.Indicator/Content/Title/Description`) |
| Ticket input form | `TextField`, `Input`, `TextArea`, `Label`, `Description`, `Button` |

Two corrections from the original spec worth flagging: HeroUI v3's Card uses
`Card.Content`, not `Card.Body` (that name existed briefly in an early alpha
and was renamed before stable release), and interactive components use
`onPress` (React Aria convention), not `onClick`.

## Verified before delivery

- `npm install` — clean, no peer-dependency conflicts.
- `npm run build` — compiles and type-checks with zero errors on the first pass.
- `npm run dev` + a real headless-browser session — no console errors, no
  React errors, submit flow tested end-to-end against a mocked backend
  response (light mode, dark mode, loading skeleton, expanded accordion all
  screenshotted and inspected).
- Not tested against your *real* running FastAPI instance in this environment
  (no network path to it from here) — the mocked test covers request/response
  shape and rendering; point `API_BASE_URL` at your real backend and it should
  work unmodified, since the request/response shapes match your actual
  `TicketRequest`/`TicketResponse` schemas.
