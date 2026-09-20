# Changelog — contacts module

## Unreleased

- Initial version: lab/supplier/other contact CRUD, name search, type
  filter, soft delete, EN/ES/FR translations.
- Review fixes: dropped the frontend coupling to the not-yet-existing
  `suppliers` / `supplier_ratings` modules, `auto_install=False`,
  POST returns 201 and DELETE 204, delete asks for confirmation,
  type filter is clearable, `nav.contacts` added to host locales.
