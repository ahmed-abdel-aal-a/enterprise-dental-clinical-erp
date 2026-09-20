---
module: treatment_plan
screen: create
route: /treatment-plans/new
related_endpoints:
  - GET /api/v1/treatment_plan/treatment-plans
  - GET /api/v1/treatment_plan/treatment-plans/patient/{patient_id}
  - POST /api/v1/treatment_plan/treatment-plans
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/items
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/generate-budget
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/link-budget
related_permissions:
  - treatment_plan.plans.read
  - treatment_plan.plans.write
related_paths:
  - backend/app/modules/treatment_plan/frontend/pages/treatment-plans/new.vue
  - backend/app/modules/treatment_plan/router.py
last_verified_commit: b1b82f5
---

# New treatment plan

Form to create a treatment plan for a patient. On save, the plan is
born in `draft` and the [detail](./treatment-plans_id.md) opens so
you can add items, confirm, and generate a budget.

## At a glance

- **How you get here.** Usually from the patient record (patient
  pre-selected) or from the inbox via **New plan**.
- **Assigned professional.** Front desk can assign a professional;
  a non-admin professional can only assign themselves.
- **Initial items.** The form lets you add treatments now or create
  the plan empty and add items from the detail.
- **Budget.** Not created here. After creating the plan, on the
  detail click **Generate budget** or **Link to existing budget**.

## Create a plan

> Requires `treatment_plan.plans.write`.

1. Pick the patient (if not pre-selected).
2. Assign the professional. Add a descriptive title (optional but
   recommended when a patient has several plans).
3. Add catalog treatments or, if the patient has planned treatments
   on the odontogram, tick them so they get linked to plan items.
4. **Save**. `treatment_plan.created` is published and you enter
   the detail.

## Permissions

| What you see / can do | Permission |
|-----------------------|------------|
| Access the form and see the catalog | `treatment_plan.plans.read` |
| Create the plan | `treatment_plan.plans.write` |

## Troubleshooting

- **Empty professional picker.** When you can only assign yourself,
  the picker is pinned to your user. If your role is admin / front
  desk and no professionals show up, create or activate them under
  *Settings → Users*.
- **Cannot add a treatment from the odontogram.** The patient has
  no planned treatments visible. Create one from the patient's
  Clinical tab before planning it.
