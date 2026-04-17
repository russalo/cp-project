// Map Equipment.category string → imported SVG asset. Add new entries as
// the SVGs land in frontend/src/assets/. Categories without an icon fall
// back to null and the UI skips rendering anything.
//
// Canonical list (from Equipment.category values on the dev DB):
//   BACKHOES, BLOWERS / VENTILATION, COMPRESSORS, CRANES, DEMOLITION,
//   DOZERS, DUMP TRUCKS, EXCAVATORS, GENERATORS / LIGHTS, HOSES, LOADERS,
//   MISC, PUMPS, ROLLERS / COMPACTORS, SAFETY, SAWS / GRINDERS, SHORING,
//   SKIDSTEERS, TRAFFIC CONTROL, TRAILERS, TRENCHERS, TRUCKS

import excavatorIcon from '../assets/excavator-icon.svg'

export const CATEGORY_ICONS = {
  EXCAVATORS: excavatorIcon,
  // Add:  BACKHOES: backhoeIcon,
  //       DUMP_TRUCKS: dumpTruckIcon, (use the DB value verbatim as key)
  //       …
}

export function iconFor(category) {
  if (!category) return null
  return CATEGORY_ICONS[category] ?? null
}
