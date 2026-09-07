# Frontend interaction and responsive verification

Load only for controls, transient UI, dynamic state, or responsive layout.

## Discover

Inspect product intent, nearby rendered flows, authoritative tokens/primitives, framework rendering
boundary, supported browser/device policy, localization constraints, and existing test commands.
Source alone cannot establish computed layout, focus order, clipping, overlays, or responsive
behavior. Without a rendered environment, mark interaction and visual verification as degraded.

Follow generated themes, copied components, and compiled CSS to their authoritative source. Preserve
versions resolved by the project. Installing a component or test library is a separate decision.

## Exercise interaction and state

Describe the journey as trigger, visible state change, keyboard/focus behavior, completion or
recovery, and focus destination. Compare custom controls with the nearest native element or project
primitive. Verify keyboard activation, visible focus, accessible name, exposed state, disabled
semantics, and usable target behavior. ARIA attributes and library claims are not proof by themselves.

Dialogs, menus, popovers, and drawers need explicit focus entry, containment when appropriate,
dismissal, and restoration. If the origin disappears, choose a stable logical successor. Background
content must not remain accidentally operable when unavailable.

For async surfaces, exercise applicable loading, partial, empty, success, validation failure,
operational failure, cancellation, and retry transitions. Announce important status without
unnecessary focus theft. Do not claim optimistic success when rollback cannot restore truth.

## Exercise layout

Choose widths from observed layout transitions and include narrow, intermediate, and wide conditions
inside the supported range. Exercise long localized content, keyboard focus visibility,
zoom/enlarged text under project policy, overflow/wrapping/overlays, and loading/error/empty geometry.

A screenshot proves pixels for one state and viewport. Pair it with interaction assertions and DOM
semantics. Record browser/runtime version, viewport or container dimensions, state fixture, input
mode, procedure, and observed result. Report unavailable assistive-technology testing as a gap.

Retrieve official current documentation for browser, framework, performance, or accessibility facts
that affect the change; prefer explicit project support policy over global usage statistics.
