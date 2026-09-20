#!/usr/bin/env bash
# Runs the first-run wizard E2E against an UNINITIALIZED database, then
# re-seeds the demo so the regular suite (./scripts/e2e.sh) keeps working.
#
#   ./scripts/e2e-fresh.sh
#
# Destroys the local dev DB (same as reset-db.sh). Never point it at prod.
set -e
cd "$(dirname "$0")/.."

./scripts/reset-db.sh
echo "Waiting for http://localhost:3000 to respond..."
until [ "$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/setup)" = "200" ]; do
  sleep 2
done
echo "Running first-run wizard E2E..."
(cd frontend && E2E_FRESH=1 npx playwright test tests/e2e/setup.spec.ts "$@") || status=$?

echo "Re-seeding demo data..."
./scripts/seed-demo.sh
exit ${status:-0}
