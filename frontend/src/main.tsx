import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Leaflet stylesheet must be imported BEFORE Tailwind's CSS so its rules
// (position: relative on .leaflet-container, absolute positioning on tile
// layers, etc.) are not dropped by PostCSS @import-ordering rules. Without
// these styles the map renders with overlapping / fragmented tiles.
import 'leaflet/dist/leaflet.css'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
