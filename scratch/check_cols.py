import asyncio
import asyncpg

async def check():
    c = await asyncpg.connect('postgresql://dentapex_admin:DentApexSecurePass_2026_scram@127.0.0.1:5432/dentapex_db')
    rows = await c.fetch("SELECT column_name FROM information_schema.columns WHERE table_name = 'treatment_catalog_items'")
    cols = [r['column_name'] for r in rows]
    print('treatment_catalog_items cols count:', len(cols))
    print('has is_default_for_type:', 'is_default_for_type' in cols)
    
    # check patient_earned_entries
    rows2 = await c.fetch("SELECT column_name FROM information_schema.columns WHERE table_name = 'patient_earned_entries'")
    print('has patient_earned_entries:', len(rows2) > 0)
    
    # check patients count
    patients = await c.fetch("SELECT count(*) FROM patients")
    print('patients count in DB:', patients[0]['count'])
    
    await c.close()

asyncio.run(check())
