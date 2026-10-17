# Dashboard

React 19 + Vite 6 + Tailwind 4 + react-router 7. Four screens: Datasets, Experiments, Ablations, Settings. Design rules: `docs/DESIGN.md`.

```bash
npm install
npm run build     # → ../src/promptgauge/api/static, served by `promptgauge ui`
npm run dev       # Vite on :5173, /api proxied to a running `promptgauge ui` on :7331
```

Users never install Node: the built files ship inside the wheel.
