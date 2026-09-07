# TypeScript and UI Review Risks

Load this reference only when TypeScript, JavaScript, or UI behavior is in scope and repository
tooling does not already decide the question.

## Runtime and boundary risks

- TypeScript types disappear at runtime. Verify parsing and validation for network, storage, URL,
  worker, environment, and user-controlled boundaries.
- Trace `undefined`, `null`, omitted fields, falsy values, optional properties, and partial updates
  through serialization and compatibility boundaries.
- Inspect rejected promises, cancellation, stale responses, race conditions, cleanup, and errors
  across client/server or process boundaries.
- Verify that browser-visible bundles, logs, source maps, and public environment variables contain
  no secret material.

## UI behavior risks

- Test semantic role, accessible name, keyboard operation, focus lifecycle, status/error
  announcements, and disabled/loading states for changed interactions.
- Check hydration and server/client boundaries against the framework version actually pinned by the
  project. Do not prescribe a rendering mode or state library generically.
- Evaluate rendering, bundle, image, or interaction performance only against a measured project
  budget or a demonstrated workload regression; generic size and timing thresholds do not establish
  severity.
- Verify list identity, stale closures, effect cleanup, ownership of subscriptions/timers, and
  optimistic rollback where the change touches them.

## Verification

Use installed dependencies and project-native scripts in check mode. Do not invoke `npx`, install a
package, start a shared service, or run a mutating formatter merely to complete review. Treat lint,
type, accessibility, browser, and performance tools as evidence for the cases they exercised, not
proof that the whole axis passed.
