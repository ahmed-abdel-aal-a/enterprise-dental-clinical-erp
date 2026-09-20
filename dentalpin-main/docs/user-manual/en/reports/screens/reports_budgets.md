---
module: reports
screen: budgets
route: /reports/budgets
related_endpoints:
  - GET /api/v1/reports/budgets/by-professional
  - GET /api/v1/reports/budgets/by-status
  - GET /api/v1/reports/budgets/by-treatment
  - GET /api/v1/reports/budgets/summary
related_permissions:
  - reports.budgets.read
related_paths:
  - backend/app/modules/reports/frontend/pages/reports/budgets.vue
  - backend/app/modules/reports/router.py
last_verified_commit: b1b82f5
---

# Budget reports

Budget dashboard. Measures **conversion** from draft to accepted,
average time in each state, and closure reasons. It is the
management view to spot bottlenecks in patient acceptance and to
understand which treatments convert best.

## At a glance

- **Summary** — totals per state in the range (`draft`, `sent`,
  `accepted`, `rejected`, `expired`, `cancelled`), monetary
  totals, and overall conversion rate (`accepted / sent`).
- **By status** — distribution across statuses for the selected
  range.
- **By professional** — conversion rate and monetary volume per
  assigned professional. Useful for internal benchmarking and
  coaching.
- **By treatment** — which catalog items appear most often and
  which have the worst conversion.

## Drill-downs

- Every bar or row links to the budget list
  ([/budgets](../../budget/screens/budgets.md)) filtered by status,
  professional, or closure reason.
- To audit a specific budget from here, open the drill-down and
  enter the detail.

## Permissions

| What you see / can do | Permission |
|-----------------------|------------|
| View the dashboard and breakdowns | `reports.budgets.read` |
| Open the budget list (drill-down) | `budget.read` |

## Troubleshooting

- **0% conversion.** No budgets in `accepted` for the range. Widen
  the range or check the acceptance pipeline.
- **No-one in *By professional*.** Budgets lack
  `assigned_professional_id`. It is optional; assign a
  professional when creating/editing a budget to see them here.
- **A card opens an empty list.** The drill-down combines range +
  status/professional, and that combination has no budgets. Drop a
  filter.
