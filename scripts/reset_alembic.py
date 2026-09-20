import asyncio
import asyncpg

async def run():
    c = await asyncpg.connect('postgresql://dentalpin_admin:DentalPinSecurePass_2026_scram@127.0.0.1:5432/dentalpin_db')
    await c.execute("DROP TABLE IF EXISTS alembic_version CASCADE;")
    print("Dropped alembic_version table successfully.")
    await c.close()

if __name__ == '__main__':
    asyncio.run(run())
