import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'

// Optional CP-brand fonts. The file + its referenced .ttf assets are
// gitignored — they only exist on workstations where CP has a Monotype
// desktop-use license (see frontend/src/assets/fonts-dev.css for the
// licensing rationale). import.meta.glob matches zero files on clean
// clones / CI, so this is a silent no-op there and falls back to the
// Roboto + Arial Black stack.
//
// IMPORTANT: a `pnpm run build` on a machine that has fonts-dev.css
// WILL bundle the TTFs into dist/. That build must not be deployed
// publicly — it would redistribute commercial fonts. Prod deploys
// should be built on CI (where the fonts are absent) until we acquire
// a Monotype web license.
import.meta.glob('./assets/fonts-dev.css', { eager: true })

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
