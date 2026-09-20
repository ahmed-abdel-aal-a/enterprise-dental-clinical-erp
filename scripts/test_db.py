import asyncio
import asyncpg

async def run():
    c = await asyncpg.connect('postgresql://dentalpin_admin:DentalPinSecurePass_2026_scram@127.0.0.1:5432/dentalpin_db')
    sb = await c.fetchval("SHOW shared_buffers;")
    wm = await c.fetchval("SHOW work_mem;")
    mc = await c.fetchval("SHOW max_connections;")
    print(f"shared_buffers: {sb}")
    print(f"work_mem: {wm}")
    print(f"max_connections: {mc}")
    await c.close()

if __name__ == '__main__':
    asyncio.run(run())
