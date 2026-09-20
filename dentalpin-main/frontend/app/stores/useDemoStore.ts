import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface DemoPatient {
  id: string
  clinic_id?: string
  first_name: string
  last_name: string
  full_name?: string
  national_id?: string
  national_id_type?: string
  birth_date?: string
  date_of_birth?: string
  gender?: string
  phone?: string
  email?: string
  address?: Record<string, any>
  medical_notes?: string
  notes?: string
  allergies?: string[]
  diseases?: string[]
  status?: 'active' | 'archived'
  do_not_contact?: boolean
  has_complete_billing_info?: boolean
  created_at: string
  updated_at?: string
}

export interface DemoAppointment {
  id: string
  clinic_id?: string
  branch_id?: string
  patient_id: string
  patient_name: string
  professional_id?: string
  professional_name: string
  cabinet: string
  cabinet_id?: string
  cabinet_name?: string
  start_time: string
  end_time: string
  status: string
  current_status_since?: string
  treatment_name: string
  treatment_type?: string
  color: string
  created_at?: string
  updated_at?: string
}

export interface DemoToothRecord {
  id?: string
  patient_id?: string
  tooth_number?: number | string
  tooth_type?: 'permanent' | 'deciduous'
  general_condition?: string
  state?: string
  material?: string
  surfaces?: any
  notes?: string
  shade?: string
  system?: string
  is_displaced?: boolean
  is_rotated?: boolean
  created_at?: string
  updated_at?: string
}

export const useDemoStore = defineStore('dentapex-demo', () => {
  // --- Reactive State (Single Source of Truth) ---
  const isDemoMode = ref(true)
  const initialized = ref(false)
  const loading = ref(false)
  const isIncognitoMode = ref(false)

  const clinic = ref({
    id: 'demo-clinic-00000000-0000-0000-0000-000000000001',
    name: 'عيادة دنت أپكس الاستعراضية النموذجية',
    phone: '+201000000000',
    email: 'demo@dentapex.clinic',
    address: { city: 'القاهرة', street: 'شارع التحرير، وسط البلد' },
    currency: 'EGP',
    timezone: 'Africa/Cairo',
    tax_id: 'EG-998877665',
    legal_name: 'عيادة دنت أپكس لطب وجراحة الأسنان',
    settings: { slot_duration_min: 15 },
  })

  const currentUser = ref({
    id: 'demo-user-00000000-0000-0000-0000-000000000001',
    first_name: 'د. أحمد',
    last_name: 'إبراهيم',
    email: 'ahmed@dentapex.clinic',
    role: 'admin',
    is_professional: true,
  })

  const cabinets = ref([
    { id: 'cab-1', name: 'العيادة 1 (الكرسي الرئيسي)', is_active: true, display_order: 1 },
    { id: 'cab-2', name: 'العيادة 2 (كرسي علاج الجذور)', is_active: true, display_order: 2 },
    { id: 'cab-3', name: 'العيادة 3 (كرسي الجراحة والزراعة)', is_active: true, display_order: 3 },
  ])

  const professionals = ref([
    {
      id: 'demo-user-00000000-0000-0000-0000-000000000001',
      professional_name: 'د. أحمد إبراهيم',
      first_name: 'د. أحمد',
      last_name: 'إبراهيم',
      email: 'ahmed@dentapex.clinic',
      role: 'admin',
      is_active: true,
      color: '#0ea5e9',
    },
    {
      id: 'demo-user-00000000-0000-0000-0000-000000000002',
      professional_name: 'د. ريم مصطفى',
      first_name: 'د. ريم',
      last_name: 'مصطفى',
      email: 'reem@dentapex.clinic',
      role: 'dentist',
      is_active: true,
      color: '#10b981',
    },
  ])

  const treatmentsCatalog = ref([
    { id: 't-1', code: 'CHK-01', name: 'كشف واستشارة وتشخيص شامل', category: 'diagnostico', price: 300, currency: 'EGP' },
    { id: 't-2', code: 'RES-01', name: 'حشو كمبوزيت تجميلي سطح واحد', category: 'restauradora', price: 650, currency: 'EGP' },
    { id: 't-3', code: 'RES-02', name: 'حشو كمbوزيت تجميلي سطحين أو أكثر (MOD)', category: 'restauradora', price: 950, currency: 'EGP' },
    { id: 't-4', code: 'ENDO-01', name: 'علاج جذور وعصب ضرس خلفي (Molar Endo)', category: 'endodoncia', price: 2200, currency: 'EGP' },
    { id: 't-5', code: 'CRW-01', name: 'تاج زيركون تجميلي كامل (Zirconia Crown)', category: 'restauradora', price: 3500, currency: 'EGP' },
    { id: 't-6', code: 'IMP-01', name: 'زرعة أسنان تيتانيوم سويسرية مدمجة بالعظم', category: 'cirugia', price: 9500, currency: 'EGP' },
    { id: 't-7', code: 'HYG-01', name: 'جلسة تنظيف وتلميع أسنان وإزالة ترسبات جيرية', category: 'diagnostico', price: 500, currency: 'EGP' },
    { id: 't-8', code: 'EXT-01', name: 'خلع ضرس عقل جراحي مطمور (Surgical Extraction)', category: 'cirugia', price: 1800, currency: 'EGP' },
    { id: 't-9', code: 'VEN-01', name: 'عدسة فينير إيماكس تجميلية (E-Max Veneer)', category: 'restauradora', price: 4200, currency: 'EGP' },
    { id: 't-10', code: 'WHT-01', name: 'جلسة تبييض أسنان احترافي بالعيادة (In-Office Whitening)', category: 'restauradora', price: 3000, currency: 'EGP' },
  ])

  const patients = ref<DemoPatient[]>([])
  const appointments = ref<DemoAppointment[]>([])
  const odontograms = ref<Record<string, Record<string, DemoToothRecord>>>({})
  const patientTreatments = ref<Record<string, any[]>>({})

  function generateTreatmentsFromTeeth(patientId: string, teethRecord: Record<string, DemoToothRecord>): any[] {
    const list: any[] = []
    const conditionMap: Record<string, string> = {
      cavity: 'caries',
      caries: 'caries',
      filled: 'filling',
      filling: 'filling',
      endo: 'root_canal',
      root_canal: 'root_canal',
      crown: 'crown',
      implant: 'implant',
      extracted: 'missing',
      missing: 'missing',
      veneer: 'veneer',
      pulpotomy: 'root_canal',
      space_maintainer: 'filling',
    }

    for (const [tNumStr, tooth] of Object.entries(teethRecord || {})) {
      const num = Number(tNumStr)
      if (isNaN(num)) continue
      const state = tooth.state || ''
      const clinicalType = conditionMap[state]
      if (!clinicalType || state === 'sound' || state === 'healthy') continue

      list.push({
        id: `trt-${patientId}-${num}`,
        clinical_type: clinicalType,
        scope: 'tooth',
        status: 'existing',
        catalog_item_id: null,
        teeth: [
          {
            id: `tt-${patientId}-${num}`,
            tooth_record_id: `tooth-${patientId}-${num}`,
            tooth_number: num,
            role: null,
            surfaces: Array.isArray(tooth.surfaces) ? tooth.surfaces : []
          }
        ],
        recorded_at: new Date().toISOString(),
        performed_at: new Date().toISOString(),
        performed_by_name: 'د. أحمد عبد العال',
        notes: tooth.notes || '',
        source_module: 'odontogram',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
    }

    return list
  }

  const invoices = ref([
    {
      id: 'inv-001',
      invoice_number: 'INV-2026-001',
      number: 'INV-2026-001',
      patient_id: 'p-1',
      patient_name: 'سارة أحمد محمود',
      issue_date: '2026-09-18',
      due_date: '2026-09-18',
      total: 3500,
      total_amount: 3500,
      paid_amount: 3500,
      status: 'paid',
      currency: 'EGP',
      series_id: 'ser-1',
      items: [
        { id: 'item-1', description: 'تاج زيركون تجميلي كامل للضرس العلوي', quantity: 1, unit_price: 3500, total: 3500 }
      ]
    },
    {
      id: 'inv-002',
      invoice_number: 'INV-2026-002',
      number: 'INV-2026-002',
      patient_id: 'p-2',
      patient_name: 'محمود عبد الرحمن الشريف',
      issue_date: '2026-09-19',
      due_date: '2026-09-26',
      total: 2200,
      total_amount: 2200,
      paid_amount: 1000,
      status: 'partially_paid',
      currency: 'EGP',
      series_id: 'ser-1',
      items: [
        { id: 'item-2', description: 'علاج جذور وعصب ثلاث قنوات مع حشو مؤقت', quantity: 1, unit_price: 2200, total: 2200 }
      ]
    },
    {
      id: 'inv-003',
      invoice_number: 'INV-2026-003',
      number: 'INV-2026-003',
      patient_id: 'p-3',
      patient_name: 'مريم حسن عبد الله',
      issue_date: '2026-09-20',
      due_date: '2026-09-20',
      total: 800,
      total_amount: 800,
      paid_amount: 800,
      status: 'paid',
      currency: 'EGP',
      series_id: 'ser-1',
      items: [
        { id: 'item-3', description: 'كشف واستشارة وتشخيص + تنظيف وتلميع أسنان', quantity: 1, unit_price: 800, total: 800 }
      ]
    }
  ])

  const budgets = ref([
    {
      id: 'bud-001',
      budget_number: 'EST-2026-001',
      number: 'EST-2026-001',
      patient_id: 'p-1',
      patient_name: 'سارة أحمد محمود',
      title: 'خطة زراعة الأسنان والتركيبات التجميلية',
      total: 13000,
      total_amount: 13000,
      status: 'accepted',
      created_at: '2026-09-15',
      currency: 'EGP',
      items: [
        { id: 'bi-1', description: 'زرعة أسنان تيتانيوم سويسرية', quantity: 1, unit_price: 9500, total: 9500 },
        { id: 'bi-2', description: 'تاج زيركون فوق الزرعة', quantity: 1, unit_price: 3500, total: 3500 }
      ]
    },
    {
      id: 'bud-002',
      budget_number: 'EST-2026-002',
      number: 'EST-2026-002',
      patient_id: 'p-4',
      patient_name: 'عمر طارق النجار',
      title: 'خطة علاج تقويم الأسنان الشفاف (Invisalign)',
      total: 28000,
      total_amount: 28000,
      status: 'pending',
      created_at: '2026-09-19',
      currency: 'EGP',
      items: [
        { id: 'bi-3', description: 'تقويم أسنان شفاف شامل المتابعة والجبائر', quantity: 1, unit_price: 28000, total: 28000 }
      ]
    }
  ])

  const treatmentPlans = ref([
    {
      id: 'tp-001',
      patient_id: 'p-1',
      patient_name: 'سارة أحمد محمود',
      title: 'إعادة تأهيل القوس العلوي والزراعة',
      status: 'active',
      progress: 50,
      created_at: '2026-09-10',
      total_cost: 13000,
      steps: [
        { id: 's-1', title: 'خلع الجذر المتبقي وتنظيف الجيب', status: 'completed' },
        { id: 's-2', title: 'غرس الزرعة التيتانيوم وتطعيم العظم', status: 'completed' },
        { id: 's-3', title: 'أخذ المقاسات الرقمية للتاج', status: 'pending' },
        { id: 's-4', title: 'تثبيت تاج الزيركون النهائي', status: 'pending' }
      ]
    }
  ])

  const inventory = ref([
    { id: 'inv-1', name: 'مخدر موضعي أرتيكائين 4% (Septanest)', sku: 'ART-400', stock: 45, min_stock: 10, unit: 'أمبول', category: 'أدوية وتخدير', price: 18 },
    { id: 'inv-2', name: 'حشوة كمبوزيت تجميلي 3M Filtek (A2)', sku: 'CMP-A2', stock: 14, min_stock: 4, unit: 'سرنجة', category: 'حشوات تجميلية', price: 650 },
    { id: 'inv-3', name: 'حشوة كمبوزيت تجميلي 3M Filtek (A3)', sku: 'CMP-A3', stock: 9, min_stock: 4, unit: 'سرنجة', category: 'حشوات تجميلية', price: 650 },
    { id: 'inv-4', name: 'زرعات تيتانيوم Straumann 4.1x10mm', sku: 'IMP-ST-41', stock: 6, min_stock: 2, unit: 'علبة', category: 'جراحة وزراعة', price: 3800 },
    { id: 'inv-5', name: 'مبارد علاج الجذور الدوارة (Protaper Gold)', sku: 'ENDO-PTG', stock: 22, min_stock: 5, unit: 'باكيت', category: 'علاج الجذور', price: 420 },
    { id: 'inv-6', name: 'قفازات فحص طبية لاتكس (مقاس M)', sku: 'GLV-LAT-M', stock: 35, min_stock: 10, unit: 'علبة 100ق', category: 'مستهلكات ووقاية', price: 150 }
  ])

  const labOrders = ref([
    {
      id: 'lab-001',
      order_number: 'LAB-2026-012',
      patient_id: 'p-1',
      patient_name: 'سارة أحمد محمود',
      lab_name: 'معمل الأهرام المتخصص لتركيبات الأسنان',
      work_type: 'تاج زيركون كامل (Full Zirconia Crown)',
      shade: 'A2',
      status: 'in_progress',
      order_date: '2026-09-18',
      due_date: '2026-09-24',
      cost: 1100
    },
    {
      id: 'lab-002',
      order_number: 'LAB-2026-013',
      patient_id: 'p-4',
      patient_name: 'عمر طارق النجار',
      lab_name: 'معمل ديجيتال سمايل لتكنولوجيا الكاد كام',
      work_type: 'حافظ مسافة وقالب تبييض منزلي',
      shade: 'N/A',
      status: 'completed',
      order_date: '2026-09-14',
      due_date: '2026-09-18',
      cost: 450
    }
  ])

  const contacts = ref([
    { id: 'con-1', name: 'شركة النيل للتجهيزات الطبية ومستلزمات الأسنان', contact_person: 'م. حسام الدين', type: 'مورد مستلزمات طبية', phone: '+20 100 123 4567', email: 'sales@niledental.com' },
    { id: 'con-2', name: 'معمل الأهرام لتركيبات وزراعة الأسنان', contact_person: 'د. طارق سعيد', type: 'معمل أسنان خارجي', phone: '+20 102 987 6543', email: 'lab@ahramdental.com' },
    { id: 'con-3', name: 'شركة صيانة أجهزة وأشعة الأسنان (DentTech)', contact_person: 'م. أيمن عادل', type: 'صيانة ودعم فني', phone: '+20 111 555 7788', email: 'support@denttech-eg.com' }
  ])

  const expenses = ref([
    { id: 'exp-1', description: 'شراء مستهلكات تخدير وقفازات طبية', amount: 3200, category: 'مستلزمات طبية', payment_method: 'تحويل بنكي', date: '2026-09-18' },
    { id: 'exp-2', description: 'صيانة دورية لجهاز الأوتوكلاف ووحدة الكرسي', amount: 1500, category: 'صيانة أجهزة', payment_method: 'نقدي', date: '2026-09-15' },
    { id: 'exp-3', description: 'فاتورة الكهرباء واشتراك الإنترنت السريع', amount: 2400, category: 'مرافق وخدمات', payment_method: 'فوري', date: '2026-09-10' }
  ])

  const tasks = ref([
    { id: 'tsk-1', title: 'تعقيم كامل لأدوات ومبارد العصب لعيادة 2', assigned_to: 'مروة (تمريض)', priority: 'high', status: 'done', due_date: '2026-09-20' },
    { id: 'tsk-2', title: 'استلام تركيبة الزيركون للمريضة سارة والتأكد من المقاس', assigned_to: 'د. ريم', priority: 'medium', status: 'in_progress', due_date: '2026-09-22' },
    { id: 'tsk-3', title: 'طلب كميات جديدة من أمبولات التخدير قبل نفاد الرصيد', assigned_to: 'أحمد (استقبال)', priority: 'high', status: 'pending', due_date: '2026-09-21' }
  ])

  // --- IndexedDB Helper with Incognito Fallback ---
  const IDB_NAME = 'DentApex_Demo_Sandbox_v2'
  const IDB_VERSION = 1

  async function getIDB(): Promise<IDBDatabase | null> {
    if (typeof window === 'undefined' || !window.indexedDB) {
      isIncognitoMode.value = true
      return null
    }

    try {
      return await new Promise((resolve) => {
        const req = window.indexedDB.open(IDB_NAME, IDB_VERSION)
        req.onupgradeneeded = (e: any) => {
          const db = e.target.result
          if (!db.objectStoreNames.contains('patients')) db.createObjectStore('patients', { keyPath: 'id' })
          if (!db.objectStoreNames.contains('appointments')) db.createObjectStore('appointments', { keyPath: 'id' })
          if (!db.objectStoreNames.contains('odontograms')) db.createObjectStore('odontograms', { keyPath: 'patient_id' })
        }
        req.onsuccess = () => resolve(req.result)
        req.onerror = () => {
          isIncognitoMode.value = true
          resolve(null)
        }
      })
    } catch {
      isIncognitoMode.value = true
      return null
    }
  }

  // --- Safe Serializer to Strip Vue 3 Reactive Proxies for IndexedDB ---
  function safeClone<T>(obj: T): T {
    try {
      return JSON.parse(JSON.stringify(obj))
    } catch {
      return obj
    }
  }

  // --- Helpers for Normalizing Seed Records ---
  function normalizePatient(p: any): DemoPatient {
    const fullName = `${p.first_name || ''} ${p.last_name || ''}`.trim()
    return {
      id: p.id || crypto.randomUUID(),
      clinic_id: clinic.value.id,
      first_name: p.first_name || '',
      last_name: p.last_name || '',
      full_name: fullName,
      national_id: p.national_id || '',
      national_id_type: 'dni',
      birth_date: p.birth_date || p.date_of_birth || '1995-01-01',
      date_of_birth: p.date_of_birth || p.birth_date || '1995-01-01',
      gender: p.gender || 'male',
      phone: p.phone || '',
      email: p.email || '',
      address: p.address || { city: 'القاهرة', street: '' },
      medical_notes: p.medical_notes || p.notes || '',
      notes: p.notes || p.medical_notes || '',
      allergies: Array.isArray(p.allergies) ? p.allergies : [],
      diseases: Array.isArray(p.diseases) ? p.diseases : [],
      status: p.status || 'active',
      do_not_contact: Boolean(p.do_not_contact),
      has_complete_billing_info: true,
      created_at: p.created_at || new Date().toISOString(),
      updated_at: p.updated_at || new Date().toISOString(),
    }
  }

  function normalizeAppointment(a: any, index: number): DemoAppointment {
    // Dynamically adjust seed appointment timestamps around today
    const now = new Date()
    const todayStr = now.toISOString().split('T')[0]

    // Distribution across today, tomorrow, and yesterday
    let targetDate = new Date(now)
    if (index % 3 === 1) targetDate.setDate(now.getDate() + 1) // Tomorrow
    else if (index % 3 === 2) targetDate.setDate(now.getDate() - 1) // Yesterday

    const targetDateStr = targetDate.toISOString().split('T')[0]

    // Extract hours/minutes from seed or generate sensible slot
    let timeSlot = '09:00:00'
    let durationMinutes = 45
    if (a.start_time && a.start_time.includes('T')) {
      const parts = a.start_time.split('T')[1].split(':')
      timeSlot = `${parts[0] || '10'}:${parts[1] || '00'}:00`
    } else {
      const hour = 9 + (index % 8)
      timeSlot = `${String(hour).padStart(2, '0')}:00:00`
    }

    const startIso = `${targetDateStr}T${timeSlot}Z`
    const endDate = new Date(new Date(startIso).getTime() + durationMinutes * 60000)
    const endIso = endDate.toISOString()

    return {
      id: a.id || crypto.randomUUID(),
      clinic_id: clinic.value.id,
      branch_id: 'demo-branch-01',
      patient_id: a.patient_id || '',
      patient_name: a.patient_name || 'مريض تجريبي',
      professional_id: currentUser.value.id,
      professional_name: a.professional_name || currentUser.value.first_name,
      cabinet: a.cabinet_name || a.cabinet || 'العيادة 1 (الكرسي الرئيسي)',
      cabinet_name: a.cabinet_name || a.cabinet || 'العيادة 1 (الكرسي الرئيسي)',
      cabinet_id: a.cabinet_id || 'cab-1',
      start_time: startIso,
      end_time: endIso,
      status: a.status || 'scheduled',
      current_status_since: startIso,
      treatment_name: a.treatment_name || a.treatment_type || 'كشف واستشارة',
      treatment_type: a.treatment_type || a.treatment_name || 'كشف واستشارة',
      color: a.color || '#3b82f6',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  }

  // --- Dynamic Lazy-Loading Initializer ---
  async function initDemoData(forceReset = false) {
    if (initialized.value && !forceReset) return
    loading.value = true

    try {
      const db = await getIDB()

      if (db && !forceReset) {
        // Try reading from IndexedDB
        const storedPatients: DemoPatient[] = await new Promise((resolve) => {
          const tx = db.transaction('patients', 'readonly')
          const req = tx.objectStore('patients').getAll()
          req.onsuccess = () => resolve(req.result || [])
          req.onerror = () => resolve([])
        })

        if (storedPatients.length > 0) {
          patients.value = storedPatients.map(normalizePatient)

          const storedAppts: DemoAppointment[] = await new Promise((resolve) => {
            const tx = db.transaction('appointments', 'readonly')
            const req = tx.objectStore('appointments').getAll()
            req.onsuccess = () => resolve(req.result || [])
            req.onerror = () => resolve([])
          })
          appointments.value = storedAppts

          const storedOdonto: any[] = await new Promise((resolve) => {
            const tx = db.transaction('odontograms', 'readonly')
            const req = tx.objectStore('odontograms').getAll()
            req.onsuccess = () => resolve(req.result || [])
            req.onerror = () => resolve([])
          })

          const mapped: Record<string, Record<string, DemoToothRecord>> = {}
          for (const item of storedOdonto) {
            if (item.patient_id) {
              if (item.teeth) mapped[item.patient_id] = item.teeth
              if (item.treatments && Array.isArray(item.treatments) && item.treatments.length > 0) {
                patientTreatments.value[item.patient_id] = item.treatments
              } else if (item.teeth) {
                patientTreatments.value[item.patient_id] = generateTreatmentsFromTeeth(item.patient_id, item.teeth)
              }
            }
          }
          odontograms.value = mapped

          initialized.value = true
          loading.value = false
          return
        }
      }

      // Dynamic Lazy-Loading (Never imported in initial bundle)
      const [patientsModule, odontogramModule, agendaModule] = await Promise.all([
        import('../demo/demo_patients_seed.json'),
        import('../demo/demo_odontogram_seed.json'),
        import('../demo/demo_agenda_seed.json'),
      ])

      const rawPatients = patientsModule.default || patientsModule
      const rawAgenda = agendaModule.default || agendaModule
      const rawOdonto = odontogramModule.default || odontogramModule

      patients.value = (rawPatients as any[]).map(normalizePatient)
      appointments.value = (rawAgenda as any[]).map((a, idx) => normalizeAppointment(a, idx))

      if (rawOdonto && (rawOdonto as any).patients_odontogram) {
        const mapped: Record<string, Record<string, DemoToothRecord>> = {}
        for (const [pid, data] of Object.entries<any>((rawOdonto as any).patients_odontogram)) {
          const teeth = data.teeth || {}
          mapped[pid] = teeth
          patientTreatments.value[pid] = generateTreatmentsFromTeeth(pid, teeth)
        }
        odontograms.value = mapped
      }

      // Background Async Persist to IndexedDB (if not Incognito)
      if (db) {
        try {
          const tx = db.transaction(['patients', 'appointments', 'odontograms'], 'readwrite')
          const pStore = tx.objectStore('patients')
          const aStore = tx.objectStore('appointments')
          const oStore = tx.objectStore('odontograms')

          pStore.clear()
          aStore.clear()
          oStore.clear()

          for (const p of patients.value) pStore.put(safeClone(p))
          for (const a of appointments.value) aStore.put(safeClone(a))
          for (const [pid, teeth] of Object.entries(odontograms.value)) {
            oStore.put(safeClone({
              patient_id: pid,
              teeth,
              treatments: patientTreatments.value[pid] || []
            }))
          }
        } catch {
          isIncognitoMode.value = true
        }
      }

      initialized.value = true
    } catch (err) {
      console.warn('Demo initialization fallback to in-memory:', err)
      isIncognitoMode.value = true
    } finally {
      loading.value = false
    }
  }

  // --- Reactive Actions (Instant UI Updates + Background Sync) ---

  function getPatient(id: string): DemoPatient | undefined {
    return patients.value.find(p => p.id === id)
  }

  async function addPatient(patientData: Partial<DemoPatient>): Promise<DemoPatient> {
    const newPatient = normalizePatient({
      ...patientData,
      id: crypto.randomUUID ? crypto.randomUUID() : `patient-${Date.now()}`,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })

    // Instant Reactivity (Single Source of Truth)
    patients.value.unshift(newPatient)

    // Background Async Sync
    const db = await getIDB()
    if (db) {
      try {
        const tx = db.transaction('patients', 'readwrite')
        tx.objectStore('patients').put(safeClone(newPatient))
      } catch {
        isIncognitoMode.value = true
      }
    }

    return newPatient
  }

  async function updatePatient(id: string, updates: Partial<DemoPatient>): Promise<DemoPatient | null> {
    const idx = patients.value.findIndex(p => p.id === id)
    if (idx === -1) return null

    const updated = normalizePatient({
      ...patients.value[idx],
      ...updates,
      updated_at: new Date().toISOString(),
    })

    patients.value[idx] = updated

    const db = await getIDB()
    if (db) {
      try {
        const tx = db.transaction('patients', 'readwrite')
        tx.objectStore('patients').put(safeClone(updated))
      } catch {
        isIncognitoMode.value = true
      }
    }

    return updated
  }

  async function deletePatient(id: string): Promise<boolean> {
    const idx = patients.value.findIndex(p => p.id === id)
    if (idx === -1) return false

    patients.value.splice(idx, 1)

    const db = await getIDB()
    if (db) {
      try {
        const tx = db.transaction('patients', 'readwrite')
        tx.objectStore('patients').delete(id)
      } catch {
        isIncognitoMode.value = true
      }
    }

    return true
  }

  function getAppointment(id: string): DemoAppointment | undefined {
    return appointments.value.find(a => a.id === id)
  }

  async function addAppointment(apptData: Partial<DemoAppointment>): Promise<DemoAppointment> {
    const newAppt = normalizeAppointment({
      ...apptData,
      id: crypto.randomUUID ? crypto.randomUUID() : `appt-${Date.now()}`,
      created_at: new Date().toISOString(),
    }, appointments.value.length)

    // Instant Reactivity
    appointments.value.push(newAppt)

    // Background Async Sync
    const db = await getIDB()
    if (db) {
      try {
        const tx = db.transaction('appointments', 'readwrite')
        tx.objectStore('appointments').put(safeClone(newAppt))
      } catch {
        isIncognitoMode.value = true
      }
    }

    return newAppt
  }

  async function updateAppointment(id: string, updates: Partial<DemoAppointment>): Promise<DemoAppointment | null> {
    const idx = appointments.value.findIndex(a => a.id === id)
    if (idx === -1) return null

    const updated: DemoAppointment = {
      ...appointments.value[idx],
      ...updates,
      updated_at: new Date().toISOString(),
    }

    appointments.value[idx] = updated

    const db = await getIDB()
    if (db) {
      try {
        const tx = db.transaction('appointments', 'readwrite')
        tx.objectStore('appointments').put(safeClone(updated))
      } catch {
        isIncognitoMode.value = true
      }
    }

    return updated
  }

  async function deleteAppointment(id: string): Promise<boolean> {
    const idx = appointments.value.findIndex(a => a.id === id)
    if (idx === -1) return false

    appointments.value.splice(idx, 1)

    const db = await getIDB()
    if (db) {
      try {
        const tx = db.transaction('appointments', 'readwrite')
        tx.objectStore('appointments').delete(id)
      } catch {
        isIncognitoMode.value = true
      }
    }

    return true
  }

  // --- Odontogram Mapping & Actions ---
  function getOdontogramData(patientId: string) {
    const rawTeeth = odontograms.value[patientId] || {}
    const teethArray: any[] = []

    // Helper condition mapping from demo state
    const conditionMap: Record<string, string> = {
      sound: 'healthy',
      healthy: 'healthy',
      cavity: 'caries',
      caries: 'caries',
      filled: 'filling',
      filling: 'filling',
      endo: 'root_canal',
      root_canal: 'root_canal',
      crown: 'crown',
      implant: 'implant',
      extracted: 'missing',
      missing: 'missing',
      veneer: 'crown',
      pulpotomy: 'root_canal',
      space_maintainer: 'filling',
    }

    // List of standard permanent teeth (11-48)
    const permanentNumbers = [
      18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28,
      48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38,
    ]

    for (const num of permanentNumbers) {
      const tKey = String(num)
      const record = rawTeeth[tKey]
      const genCondition = record ? (conditionMap[record.state || ''] || 'healthy') : 'healthy'

      const surfacesObj = {
        M: 'healthy',
        D: 'healthy',
        O: 'healthy',
        V: 'healthy',
        L: 'healthy',
      }

      if (record && record.surfaces && Array.isArray(record.surfaces)) {
        for (const s of record.surfaces) {
          if (s in surfacesObj) {
            (surfacesObj as any)[s] = genCondition
          }
        }
      }

      teethArray.push({
        id: `tooth-${patientId}-${num}`,
        patient_id: patientId,
        tooth_number: num,
        tooth_type: 'permanent',
        general_condition: genCondition,
        surfaces: surfacesObj,
        notes: record?.notes || '',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
    }

    return {
      patient_id: patientId,
      teeth: teethArray,
      condition_colors: {
        healthy: '#22c55e',
        caries: '#ef4444',
        filling: '#3b82f6',
        crown: '#f59e0b',
        missing: '#9ca3af',
        root_canal: '#8b5cf6',
        implant: '#06b6d4',
        extraction_indicated: '#dc2626',
        sealant: '#10b981',
        fracture: '#f97316',
      },
      available_conditions: [
        'healthy',
        'caries',
        'filling',
        'crown',
        'missing',
        'root_canal',
        'implant',
        'extraction_indicated',
        'sealant',
        'fracture',
      ],
      surfaces: ['M', 'D', 'O', 'V', 'L'],
    }
  }

  async function persistOdontogram(patientId: string) {
    const db = await getIDB()
    if (db) {
      try {
        const tx = db.transaction('odontograms', 'readwrite')
        tx.objectStore('odontograms').put(safeClone({
          patient_id: patientId,
          teeth: odontograms.value[patientId] || {},
          treatments: patientTreatments.value[patientId] || [],
        }))
      } catch {
        isIncognitoMode.value = true
      }
    }
  }

  function getPatientTreatments(patientId: string): any[] {
    if (!patientTreatments.value[patientId] || patientTreatments.value[patientId].length === 0) {
      const rawTeeth = odontograms.value[patientId] || {}
      patientTreatments.value[patientId] = generateTreatmentsFromTeeth(patientId, rawTeeth)
    }
    return patientTreatments.value[patientId]
  }

  async function createPatientTreatment(patientId: string, payload: any) {
    if (!patientTreatments.value[patientId]) {
      patientTreatments.value[patientId] = getPatientTreatments(patientId)
    }

    const treatmentId = `trt-${patientId}-${Date.now()}`
    const toothNumbers: number[] = Array.isArray(payload.tooth_numbers)
      ? payload.tooth_numbers
      : (Array.isArray(payload.teeth) ? payload.teeth.map((t: any) => t.tooth_number) : [])

    const teethList = toothNumbers.map((num: number) => {
      const role = Array.isArray(payload.teeth)
        ? payload.teeth.find((t: any) => t.tooth_number === num)?.role || null
        : null
      return {
        id: `tt-${treatmentId}-${num}`,
        tooth_record_id: `tooth-${patientId}-${num}`,
        tooth_number: num,
        role,
        surfaces: Array.isArray(payload.surfaces) ? payload.surfaces : []
      }
    })

    const clinicalType = payload.clinical_type || 'caries'
    const status = payload.status || 'existing'

    const treatment = {
      id: treatmentId,
      clinical_type: clinicalType,
      scope: payload.scope || (toothNumbers.length > 1 ? 'multi_tooth' : 'tooth'),
      arch: payload.arch || null,
      status,
      catalog_item_id: payload.catalog_item_id || null,
      teeth: teethList,
      recorded_at: new Date().toISOString(),
      performed_at: (status === 'performed' || status === 'existing') ? new Date().toISOString() : null,
      performed_by_name: 'د. أحمد عبد العال',
      notes: payload.notes || '',
      source_module: 'odontogram',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    patientTreatments.value[patientId].push(treatment)

    // Synchronize odontograms.value so the tooth SVG visuals update instantly
    if (!odontograms.value[patientId]) {
      odontograms.value[patientId] = {}
    }

    for (const num of toothNumbers) {
      const tKey = String(num)
      const existingTooth = odontograms.value[patientId][tKey] || {}
      odontograms.value[patientId][tKey] = {
        ...existingTooth,
        state: clinicalType,
        surfaces: Array.isArray(payload.surfaces) && payload.surfaces.length ? payload.surfaces : (existingTooth.surfaces || []),
        notes: payload.notes || existingTooth.notes || ''
      }
    }

    await persistOdontogram(patientId)
    return treatment
  }

  async function updatePatientTreatment(treatmentId: string, data: any) {
    for (const [pid, list] of Object.entries(patientTreatments.value)) {
      const idx = list.findIndex(t => t.id === treatmentId)
      if (idx >= 0) {
        const updated = {
          ...list[idx],
          ...data,
          updated_at: new Date().toISOString()
        }
        list[idx] = updated
        await persistOdontogram(pid)
        return updated
      }
    }
    return null
  }

  async function deletePatientTreatment(treatmentId: string): Promise<boolean> {
    for (const [pid, list] of Object.entries(patientTreatments.value)) {
      const idx = list.findIndex(t => t.id === treatmentId)
      if (idx >= 0) {
        list.splice(idx, 1)
        await persistOdontogram(pid)
        return true
      }
    }
    return false
  }

  async function performPatientTreatment(treatmentId: string) {
    return updatePatientTreatment(treatmentId, {
      status: 'performed',
      performed_at: new Date().toISOString()
    })
  }

  async function updateToothRecord(patientId: string, toothNumber: string | number, record: DemoToothRecord) {
    const tNum = String(toothNumber)
    if (!odontograms.value[patientId]) {
      odontograms.value[patientId] = {}
    }

    // Instant Reactivity
    odontograms.value[patientId][tNum] = {
      ...odontograms.value[patientId][tNum],
      ...record,
      state: record.general_condition || record.state || 'healthy',
    }

    await persistOdontogram(patientId)
  }

  async function resetDemoData() {
    await initDemoData(true)
  }

  return {
    isDemoMode,
    initialized,
    loading,
    isIncognitoMode,
    clinic,
    currentUser,
    cabinets,
    professionals,
    treatmentsCatalog,
    patients,
    appointments,
    odontograms,
    patientTreatments,
    invoices,
    budgets,
    treatmentPlans,
    inventory,
    labOrders,
    contacts,
    expenses,
    tasks,
    initDemoData,
    getPatient,
    addPatient,
    updatePatient,
    deletePatient,
    getAppointment,
    addAppointment,
    updateAppointment,
    deleteAppointment,
    getOdontogramData,
    getPatientTreatments,
    createPatientTreatment,
    updatePatientTreatment,
    deletePatientTreatment,
    performPatientTreatment,
    updateToothRecord,
    resetDemoData,
  }
})
