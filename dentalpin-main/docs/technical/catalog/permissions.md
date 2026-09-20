---
module: catalog
last_verified_commit: 6b3eb82
---

# Catalog — permissions

Returned by `CatalogModule.get_permissions()`
(relative names; the registry namespaces them as `catalog.<name>`).

| Permission | Allows | Required by |
|------------|--------|-------------|
| `catalog.read` | Browse categories, VAT types, treatments and odontogram mappings. Every role has it. | `GET /api/v1/catalog/categories`, `GET /api/v1/catalog/categories/{id}`, `GET /api/v1/catalog/vat-types`, `GET /api/v1/catalog/vat-types/default`, `GET /api/v1/catalog/vat-types/{id}`, `GET /api/v1/catalog/items`, `GET /api/v1/catalog/items/popular`, `GET /api/v1/catalog/items/search`, `GET /api/v1/catalog/items/{id}`, `GET /api/v1/catalog/odontogram-treatments`, `GET /api/v1/catalog/odontogram-treatments/by-category` |
| `catalog.write` | Create, edit and (soft-)delete treatments. On system items (`is_system`) only commercial/clinical values are editable (price, cost, VAT, names, duration, sessions, `is_active`); changing `internal_code`, `category_id`, `pricing_strategy`, `treatment_scope`, `is_diagnostic` or `requires_surfaces` returns 403, as does `DELETE`. | `POST /api/v1/catalog/items`, `PUT /api/v1/catalog/items/{id}`, `DELETE /api/v1/catalog/items/{id}` |
| `catalog.admin` | Manage categories and VAT types; load the stock catalog. System categories and VAT types (`is_system`) reject edits/deletes with 403 (VAT types: only `is_default` may change). | `POST /api/v1/catalog/categories`, `PUT /api/v1/catalog/categories/{id}`, `DELETE /api/v1/catalog/categories/{id}`, `POST /api/v1/catalog/vat-types`, `PUT /api/v1/catalog/vat-types/{id}`, `DELETE /api/v1/catalog/vat-types/{id}`, `POST /api/v1/catalog/seed` |

## Role assignment

`manifest.role_permissions`: `admin` → `*`; every other role → `read`.
Core table: `backend/app/core/auth/permissions.py`.

## Adding a new permission

1. Add the relative name to `get_permissions()` in
   `backend/app/modules/catalog/__init__.py`.
2. Grant it in `manifest.role_permissions`.
3. Add a row to the table above.
4. Annotate the endpoint(s) with `Depends(require_permission(...))`.
5. Update `frontend/app/config/permissions.ts` if it gates UI.
