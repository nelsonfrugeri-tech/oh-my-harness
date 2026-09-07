# SLI, SLO, error-budget, and burn-rate mathematics

Use ratios as decimals in calculations; multiply by 100 only for presentation. Reject an empty or
unknown denominator rather than treating it as zero success or zero error.

## Event-based objective

For one aligned population and window:

    SLI                = good_events / eligible_events
    observed_bad_ratio = bad_events / eligible_events
    allowed_bad_ratio  = 1 - SLO
    allowed_bad_events = allowed_bad_ratio * eligible_events
    budget_remaining   = 1 - (bad_events / allowed_bad_events)
    burn_rate          = observed_bad_ratio / allowed_bad_ratio

budget_remaining may be negative. Define whether neutral or excluded events exist; otherwise
good_events + bad_events must equal eligible_events.

The allowed bad ratio is 1 - SLO. Do not divide it by objective-window days. The objective window
belongs in selection of events and in time-to-exhaustion or alert derivations, not in the ratio's
denominator.

## Time-based objective

Use this only when the SLI is genuinely based on eligible duration:

    allowed_bad_duration = (1 - SLO) * eligible_objective_duration
    budget_remaining     = 1 - (observed_bad_duration / allowed_bad_duration)

Do not convert request failures to downtime minutes unless the measurement contract defines and
justifies that transformation.

## Alert derivation

For objective duration W, lookback duration L, and chosen fraction F of the total budget to consume
during L:

    burn_threshold = F * W / L
    bad_ratio_threshold = burn_threshold * (1 - SLO)
    time_to_exhaustion_at_constant_burn = W / burn_rate

Example, derived rather than prescribed: with W = 28 days = 672 hours, F = 0.02, and L = 1 hour,
the burn threshold is 0.02 * 672 / 1 = 13.44. With F = 0.05 and L = 6 hours, it is
0.05 * 672 / 6 = 5.6. A 30-day objective produces different values. Record the inputs and do not
copy these examples as policy.

For event-based SLOs with variable traffic, compute budget consumption from event counts over the
objective population. The duration shortcut assumes a representative or constant rate and must be
labeled as such. Low traffic, delayed events, sampling, missing series, partial ingestion, and
rolling-window boundary changes require explicit handling.

## Provenance record

Every reported quantity includes metric name and unit, eligible population or denominator, exact
start and end times, timezone, source or query revision, collection and calculation method,
exclusions, sampling or missing-data limits, and observation time.
