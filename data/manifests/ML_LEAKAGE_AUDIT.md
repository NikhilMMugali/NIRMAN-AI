# PAIMANA ML Leakage Audit

| Feature | Available at prediction time? | Leakage Risk | Decision | Reason |
| --- | --- | --- | --- | --- |
| `physical_progress` | Yes | Low | INCLUDE | Current report value at cutoff T |
| `expenditure` | Yes | Low | INCLUDE | Current report value at cutoff T |
| `original_cost` | Yes | Low | INCLUDE | Baseline project field known by cutoff |
| `revised_cost` | Yes, when present | Medium | INCLUDE WITH LIMITATION | A revision in the current report is usable at T; future revisions are excluded |
| `progress_delta_1m` | Yes | Low | INCLUDE | Computed from current and prior observed rows only |
| `expenditure_delta_1m` | Yes | Low | INCLUDE | Computed from current and prior observed rows only |
| `progress_mean_3m` | Yes | Low | INCLUDE | Shifted rolling window excludes current and future rows |
| `progress_std_3m` | Yes | Low | INCLUDE | Shifted rolling window excludes current and future rows |
| `stagnant_months_3m` | Yes | Low | INCLUDE | Shifted rolling window of prior changes |
| `observations_to_date` | Yes | Low | INCLUDE | Count of observations before/at cutoff |
| `months_elapsed` | Yes | Low | INCLUDE | Calendar distance from first observed project period |
| `reporting_gap_months` | Yes | Low | INCLUDE | Gap from prior observed report |
| Next-period physical progress | No | High | EXCLUDE FROM FEATURES | Used only to define one-month implementation-risk target |
| Next-period revised/original cost | No | High | EXCLUDE FROM FEATURES | Used only to define partial cost-overrun target |
| Final cost | No | High | EXCLUDE | Not available as a valid cutoff-time field |
| Completion dates | No | High | EXCLUDE | Not populated in canonical records |
| Final status/outcome | No | High | EXCLUDE | Not available in canonical records |
| Source PDF path/hash | N/A | Medium | EXCLUDE | Provenance only, not predictive signal |

The implementation enforces the cutoff by grouping by project and using `shift(-1)` only for targets. Shifted rolling features use `shift(1)` before rolling. A regression test demonstrates that a future observation is not included in an earlier feature row.
