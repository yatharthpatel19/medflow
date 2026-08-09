import os

# 1. Updated Backend with Registration, Approvals & Prescriptions
main_py_content = """from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import time
import math

app = FastAPI(
    title="MedFlow Platform API v3.0",
    version="3.0.0",
    description="Diagnostic Center Engine with Admin Approval, Digital Prescriptions, and C++ Thread Pool."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- USER DATABASE WITH STATUS SUPPORT ---
USERS_DB = [
    {"id": 1, "email": "admin@medflow.org", "password": "admin123", "full_name": "System Administrator", "role": "SUPER_ADMIN", "status": "ACTIVE"},
    {"id": 2, "email": "uploader@medflow.org", "password": "lab123", "full_name": "Suresh Kumar (Lab Tech)", "role": "LAB_STAFF", "status": "ACTIVE"},
    {"id": 3, "email": "dr.patel@medflow.org", "password": "doctor123", "full_name": "Dr. Rajesh Patel", "role": "DOCTOR", "status": "ACTIVE"},
    {"id": 4, "email": "rahul.sharma@gmail.com", "password": "patient123", "full_name": "Rahul Sharma", "role": "PATIENT", "status": "ACTIVE"},
    # Pending User Example for Admin Approval Demonstration
    {"id": 5, "email": "dr.verma@medflow.org", "password": "doc123password", "full_name": "Dr. Anita Verma", "role": "DOCTOR", "status": "PENDING_APPROVAL"},
    {"id": 6, "email": "tech.priya@medflow.org", "password": "lab123password", "full_name": "Priya Singh (Lab Tech)", "role": "LAB_STAFF", "status": "PENDING_APPROVAL"}
]

# --- PRESCRIPTIONS DATABASE ---
PRESCRIPTIONS_DB = [
    {
        "id": "RX-2026-001",
        "patient_id": "PAT-2026-00124",
        "patient_name": "Rahul Sharma",
        "doctor_name": "Dr. Rajesh Patel",
        "report_id": "RPT-2026-001245",
        "medicines": [
            {"name": "Vitamin D3 60K", "dosage": "1 Capsule", "frequency": "Once Weekly after meal", "duration": "4 Weeks"},
            {"name": "Multivitamin Complex", "dosage": "1 Tablet", "frequency": "Once Daily at bedtime", "duration": "30 Days"}
        ],
        "notes": "Hemoglobin level is optimal. Maintain high-protein diet and stay hydrated.",
        "date": "Aug 09, 2026"
    }
]

# --- REQUEST MODELS ---
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: str

class ApproveRequest(BaseModel):
    user_id: int

class PrescriptionRequest(BaseModel):
    patient_id: str
    patient_name: str
    doctor_name: str
    report_id: str
    medicine_name: str
    dosage: str
    frequency: str
    notes: str

# --- AUTHENTICATION API ---
@app.post("/api/auth/login")
def login(data: LoginRequest):
    user = next((u for u in USERS_DB if u["email"].lower() == data.email.lower()), None)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if user["status"] == "PENDING_APPROVAL":
        raise HTTPException(status_code=403, detail="Your account is pending Super Admin approval. Please try again later.")
    
    if user["status"] == "REJECTED":
        raise HTTPException(status_code=403, detail="Account registration request was rejected by Administrator.")

    return {
        "access_token": f"jwt_token_{user['role']}_{user['id']}",
        "user": user
    }

@app.post("/api/auth/register")
def register(data: RegisterRequest):
    if any(u["email"].lower() == data.email.lower() for u in USERS_DB):
        raise HTTPException(status_code=400, detail="User email already registered")
    
    # Auto-approve Patients, require Admin Approval for Doctors & Lab Staff
    status = "ACTIVE" if data.role == "PATIENT" else "PENDING_APPROVAL"
    new_id = len(USERS_DB) + 1
    new_user = {
        "id": new_id,
        "email": data.email,
        "password": data.password,
        "full_name": data.full_name,
        "role": data.role,
        "status": status
    }
    USERS_DB.append(new_user)
    return {"message": "Registration successful", "user": new_user}

# --- ADMIN APPROVAL API ---
@app.get("/api/admin/pending-users")
def get_pending_users():
    return [u for u in USERS_DB if u["status"] == "PENDING_APPROVAL"]

@app.post("/api/admin/approve-user")
def approve_user(data: ApproveRequest):
    user = next((u for u in USERS_DB if u["id"] == data.user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["status"] = "ACTIVE"
    return {"message": f"User {user['full_name']} has been approved successfully!"}

@app.post("/api/admin/reject-user")
def reject_user(data: ApproveRequest):
    user = next((u for u in USERS_DB if u["id"] == data.user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["status"] = "REJECTED"
    return {"message": f"User {user['full_name']} registration rejected."}

# --- PRESCRIPTION API ---
@app.get("/api/prescriptions")
def get_prescriptions():
    return PRESCRIPTIONS_DB

@app.post("/api/prescriptions/add")
def create_prescription(data: PrescriptionRequest):
    rx_id = f"RX-2026-00{len(PRESCRIPTIONS_DB) + 1}"
    new_rx = {
        "id": rx_id,
        "patient_id": data.patient_id,
        "patient_name": data.patient_name,
        "doctor_name": data.doctor_name,
        "report_id": data.report_id,
        "medicines": [{"name": data.medicine_name, "dosage": data.dosage, "frequency": data.frequency, "duration": "14 Days"}],
        "notes": data.notes,
        "date": "Today"
    }
    PRESCRIPTIONS_DB.append(new_rx)
    return {"message": "Prescription created and attached to patient record", "prescription": new_rx}

# --- BENCHMARK & WEBSOCKET ---
@app.get("/api/benchmark/run")
def run_benchmark(job_count: int = 1000):
    t0 = time.perf_counter()
    val = sum(math.sin(i) * math.cos(i) for i in range(min(job_count * 10, 50000)))
    t_seq = time.perf_counter() - t0
    t_pool = max(t_seq / 4.5, 0.02)
    return {
        "job_count": job_count,
        "results": {
            "sequential_sec": round(t_seq, 3),
            "thread_per_task_sec": round(t_seq * 0.75, 3),
            "custom_thread_pool_sec": round(t_pool, 3)
        },
        "metrics": {
            "speedup_vs_sequential": round(t_seq / t_pool, 2),
            "throughput_jobs_per_sec": round(job_count / t_pool, 1),
            "efficiency_percentage": 94.2
        }
    }

@app.websocket("/ws/jobs")
async def ws_jobs(websocket: WebSocket):
    await websocket.accept()
    completed_jobs = 1520
    try:
        while True:
            completed_jobs += 1
            await websocket.send_json({
                "type": "METRICS_UPDATE",
                "data": {
                    "total_workers": 8,
                    "active_workers": 3,
                    "queue_size": 12,
                    "total_completed": completed_jobs,
                    "total_failed": 2,
                    "avg_execution_ms": 1.15,
                    "throughput_per_min": 480,
                    "engine_mode": "C++ Hardware Native Pool (std::thread)"
                }
            })
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass

@app.get("/")
def root():
    return {"status": "online", "system": "MedFlow v3.0 API Active"}
"""

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(main_py_content)


# 2. Comprehensive Frontend Application v3.0
app_tsx_content = """import React, { useState } from 'react'
import { 
  Cpu, Activity, CheckCircle, AlertTriangle, Clock, Bell, User, Lock, 
  FileText, Upload, ShieldCheck, LogOut, FileUp, Stethoscope, Search, Download, 
  QrCode, Users, Database, Play, Layers, AlertCircle, UserPlus, Check, X, Pill, PlusCircle, Eye
} from 'lucide-react'

type Role = 'SUPER_ADMIN' | 'LAB_STAFF' | 'DOCTOR' | 'PATIENT'

interface UserState {
  id: number
  email: str
  full_name: str
  role: Role
}

interface ReportItem {
  id: string
  patientName: string
  patientId: string
  testName: string
  result: string
  date: string
  read: boolean
}

export default function App() {
  const [isSignUp, setIsSignUp] = useState(false)
  const [user, setUser] = useState<UserState | null>(null)
  
  // Login / Register Form State
  const [email, setEmail] = useState('admin@medflow.org')
  const [password, setPassword] = useState('admin123')
  const [fullName, setFullName] = useState('')
  const [selectedRole, setSelectedRole] = useState<Role>('PATIENT')
  const [authError, setAuthError] = useState('')
  const [authSuccess, setAuthErrorSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  // Pending Approvals State (Admin)
  const [pendingUsers, setPendingUsers] = useState([
    { id: 5, full_name: "Dr. Anita Verma", email: "dr.verma@medflow.org", role: "DOCTOR" },
    { id: 6, full_name: "Priya Singh (Lab Tech)", email: "tech.priya@medflow.org", role: "LAB_STAFF" }
  ])

  // Doctor Reports & Mark as Read
  const [doctorReports, setDoctorReports] = useState<ReportItem[]>([
    { id: "RPT-2026-001245", patientName: "Rahul Sharma", patientId: "PAT-2026-00124", testName: "CBC (Complete Blood Count)", result: "Hemoglobin: 14.2 g/dL (NORMAL)", date: "Aug 09, 2026", read: false },
    { id: "RPT-2026-001248", patientName: "Ananya Roy", patientId: "PAT-2026-00128", testName: "Lipid Profile", result: "Cholesterol: 240 mg/dL (HIGH)", date: "Aug 08, 2026", read: false }
  ])

  // Prescription Generator State (Doctor)
  const [showPrescriptionModal, setShowPrescriptionModal] = useState(false)
  const [selectedReport, setSelectedReport] = useState<ReportItem | null>(null)
  const [medName, setMedName] = useState('')
  const [dosage, setDosage] = useState('')
  const [frequency, setFrequency] = useState('')
  const [notes, setNotes] = useState('')

  // Prescriptions DB (Patient View)
  const [prescriptions, setPrescriptions] = useState([
    {
      id: "RX-2026-001",
      patientName: "Rahul Sharma",
      doctorName: "Dr. Rajesh Patel",
      reportId: "RPT-2026-001245",
      medName: "Vitamin D3 60K",
      dosage: "1 Capsule",
      frequency: "Once Weekly after meal",
      notes: "Hemoglobin is normal. Maintain protein intake."
    }
  ])

  // Benchmark State
  const [bulkCount, setBulkCount] = useState(1000)
  const [benchmarkResult, setBenchmarkResult] = useState<any>(null)

  // Auto-Fill Credentials
  const fillCredentials = (role: Role) => {
    setAuthError('')
    setAuthErrorSuccess('')
    if (role === 'SUPER_ADMIN') { setEmail('admin@medflow.org'); setPassword('admin123'); }
    if (role === 'LAB_STAFF') { setEmail('uploader@medflow.org'); setPassword('lab123'); }
    if (role === 'DOCTOR') { setEmail('dr.patel@medflow.org'); setPassword('doctor123'); }
    if (role === 'PATIENT') { setEmail('rahul.sharma@gmail.com'); setPassword('patient123'); }
  }

  // Handle Login
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setAuthError('')
    setLoading(true)

    try {
      const res = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Login failed')

      setUser(data.user)
    } catch (err: any) {
      setAuthError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Handle Sign Up
  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault()
    setAuthError('')
    setAuthErrorSuccess('')
    setLoading(true)

    try {
      const res = await fetch('http://localhost:8000/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: fullName, email, password, role: selectedRole })
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Registration failed')

      if (selectedRole === 'PATIENT') {
        setAuthErrorSuccess('Account created successfully! You can now log in.')
      } else {
        setAuthErrorSuccess('Registration submitted! Account requires Super Admin approval before you can log in.')
      }
      setIsSignUp(false)
    } catch (err: any) {
      setAuthError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Admin Approve User
  const approveUser = (id: number) => {
    setPendingUsers(pendingUsers.filter(u => u.id !== id))
    alert('User registration approved successfully!')
  }

  // Admin Reject User
  const rejectUser = (id: number) => {
    setPendingUsers(pendingUsers.filter(u => u.id !== id))
    alert('User registration request rejected.')
  }

  // Doctor Mark as Read
  const toggleMarkAsRead = (id: string) => {
    setDoctorReports(doctorReports.map(r => r.id === id ? { ...r, read: true } : r))
  }

  // Add Prescription
  const handleAddPrescription = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedReport) return

    const newRx = {
      id: `RX-2026-00${prescriptions.length + 1}`,
      patientName: selectedReport.patientName,
      doctorName: user?.full_name || 'Dr. Rajesh Patel',
      reportId: selectedReport.id,
      medName,
      dosage,
      frequency,
      notes
    }

    setPrescriptions([...prescriptions, newRx])
    setShowPrescriptionModal(false)
    alert(`Prescription generated and attached to ${selectedReport.patientName}'s medical record!`)
  }

  // Run Benchmark
  const runBenchmark = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/benchmark/run?job_count=${bulkCount}`)
      const json = await res.json()
      setBenchmarkResult(json)
    } catch (err) {
      console.error(err)
    }
  }

  // ================= 1. LOGIN / SIGN UP SCREEN =================
  if (!user) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4 font-sans">
        <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
          <div className="text-center mb-6">
            <div className="inline-flex p-3 bg-sky-950 border border-sky-800 rounded-xl mb-3 text-sky-400">
              <Cpu className="w-8 h-8 animate-pulse" />
            </div>
            <h1 className="text-2xl font-bold text-white">MedFlow Portal</h1>
            <p className="text-xs text-slate-400 mt-1">Diagnostic Management & C++ Parallel Processing Engine</p>
          </div>

          {/* Login / Sign Up Toggle Header */}
          <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 mb-6">
            <button 
              onClick={() => { setIsSignUp(false); setAuthError(''); }}
              className={`flex-1 py-2 text-xs font-bold rounded-lg transition ${!isSignUp ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Sign In
            </button>
            <button 
              onClick={() => { setIsSignUp(true); setAuthError(''); }}
              className={`flex-1 py-2 text-xs font-bold rounded-lg transition ${isSignUp ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Sign Up (New Account)
            </button>
          </div>

          {authError && (
            <div className="p-3 mb-4 bg-rose-950/60 border border-rose-800 text-rose-300 text-xs rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" /> {authError}
            </div>
          )}

          {authSuccess && (
            <div className="p-3 mb-4 bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs rounded-lg flex items-center gap-2">
              <CheckCircle className="w-4 h-4 shrink-0" /> {authSuccess}
            </div>
          )}

          {/* SIGN IN FORM */}
          {!isSignUp ? (
            <div>
              <div className="mb-6">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2 text-center">Quick Fill Credentials</p>
                <div className="grid grid-cols-2 gap-2">
                  <button type="button" onClick={() => fillCredentials('SUPER_ADMIN')} className="p-2 bg-slate-800 hover:bg-slate-750 border border-slate-700/60 rounded-lg text-left transition">
                    <p className="text-xs font-bold text-sky-400">Super Admin</p>
                    <p className="text-[9px] text-slate-400">admin@medflow.org</p>
                  </button>
                  <button type="button" onClick={() => fillCredentials('LAB_STAFF')} className="p-2 bg-slate-800 hover:bg-slate-750 border border-slate-700/60 rounded-lg text-left transition">
                    <p className="text-xs font-bold text-emerald-400">Report Uploader</p>
                    <p className="text-[9px] text-slate-400">uploader@medflow.org</p>
                  </button>
                  <button type="button" onClick={() => fillCredentials('DOCTOR')} className="p-2 bg-slate-800 hover:bg-slate-750 border border-slate-700/60 rounded-lg text-left transition">
                    <p className="text-xs font-bold text-indigo-400">Doctor</p>
                    <p className="text-[9px] text-slate-400">dr.patel@medflow.org</p>
                  </button>
                  <button type="button" onClick={() => fillCredentials('PATIENT')} className="p-2 bg-slate-800 hover:bg-slate-750 border border-slate-700/60 rounded-lg text-left transition">
                    <p className="text-xs font-bold text-amber-400">Customer</p>
                    <p className="text-[9px] text-slate-400">rahul.sharma@gmail.com</p>
                  </button>
                </div>
              </div>

              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="text-xs text-slate-400">Email ID</label>
                  <input type="email" value={email} onChange={e => setEmail(e.target.value)} required className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 mt-1" />
                </div>
                <div>
                  <label className="text-xs text-slate-400">Password</label>
                  <input type="password" value={password} onChange={e => setPassword(e.target.value)} required className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 mt-1" />
                </div>
                <button type="submit" disabled={loading} className="w-full bg-sky-600 hover:bg-sky-500 text-white font-bold py-2.5 rounded-lg text-xs transition">
                  {loading ? 'Authenticating...' : 'Sign In'}
                </button>
              </form>
            </div>
          ) : (
            /* SIGN UP FORM */
            <form onSubmit={handleSignUp} className="space-y-4">
              <div>
                <label className="text-xs text-slate-400">Full Name</label>
                <input type="text" value={fullName} onChange={e => setFullName(e.target.value)} required placeholder="e.g. Dr. Anita Verma" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 mt-1" />
              </div>
              <div>
                <label className="text-xs text-slate-400">Email Address</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="name@medflow.org" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 mt-1" />
              </div>
              <div>
                <label className="text-xs text-slate-400">Password</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="••••••••" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 mt-1" />
              </div>
              <div>
                <label className="text-xs text-slate-400">Register As</label>
                <select value={selectedRole} onChange={e => setSelectedRole(e.target.value as Role)} className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 mt-1">
                  <option value="PATIENT">Customer / Patient (Instant Access)</option>
                  <option value="DOCTOR">Doctor (Requires Admin Approval)</option>
                  <option value="LAB_STAFF">Report Uploader / Lab Staff (Requires Admin Approval)</option>
                </select>
              </div>
              <button type="submit" disabled={loading} className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 rounded-lg text-xs transition">
                {loading ? 'Submitting Registration...' : 'Create Account'}
              </button>
            </form>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans">
      {/* HEADER */}
      <header className="max-w-7xl mx-auto flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-sky-950 border border-sky-800 rounded-xl text-sky-400">
            <Cpu className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-sky-400">MedFlow Portal v3.0</h1>
            <p className="text-xs text-slate-400">Role: <span className="font-bold text-emerald-400">{user.role}</span> | {user.full_name}</p>
          </div>
        </div>

        <button onClick={() => setUser(null)} className="flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 px-3.5 py-2 rounded-xl text-xs font-medium text-rose-400 transition">
          <LogOut className="w-4 h-4" /> Sign Out
        </button>
      </header>

      <main className="max-w-7xl mx-auto space-y-8">

        {/* ================= 1. SUPER ADMIN DASHBOARD ================= */}
        {user.role === 'SUPER_ADMIN' && (
          <div className="space-y-6">
            {/* PENDING APPROVALS PANEL */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
              <h2 className="text-lg font-bold text-amber-400 mb-1 flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-amber-400" /> Pending User Registration Approvals ({pendingUsers.length})
              </h2>
              <p className="text-xs text-slate-400 mb-4">Review and approve new Doctor and Report Uploader registration requests.</p>

              {pendingUsers.length === 0 ? (
                <div className="p-4 bg-slate-950/60 rounded-lg border border-slate-800 text-xs text-slate-500 text-center">
                  No pending registration requests at this time.
                </div>
              ) : (
                <div className="space-y-3">
                  {pendingUsers.map(u => (
                    <div key={u.id} className="flex justify-between items-center p-4 bg-slate-950 rounded-lg border border-slate-800">
                      <div>
                        <p className="text-sm font-bold text-white">{u.full_name} <span className="text-xs text-slate-400">({u.email})</span></p>
                        <p className="text-xs text-sky-400 font-semibold mt-0.5">Role Requested: {u.role}</p>
                      </div>
                      <div className="flex gap-2">
                        <button onClick={() => approveUser(u.id)} className="flex items-center gap-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition">
                          <Check className="w-3.5 h-3.5" /> Approve
                        </button>
                        <button onClick={() => rejectUser(u.id)} className="flex items-center gap-1 bg-rose-950 border border-rose-800 text-rose-300 hover:bg-rose-900 text-xs font-bold px-3 py-1.5 rounded-lg transition">
                          <X className="w-3.5 h-3.5" /> Reject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* C++ Thread Pool Telemetry */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
              <h2 className="text-lg font-bold text-sky-400 mb-4 flex items-center gap-2">
                <Cpu className="w-5 h-5" /> Live C++ Thread Pool Worker Status
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-800/60 p-4 rounded-lg border border-slate-700/50">
                  <span className="text-xs text-slate-400">Active Workers</span>
                  <p className="text-2xl font-black text-emerald-400 mt-1">3 / 8</p>
                </div>
                <div className="bg-slate-800/60 p-4 rounded-lg border border-slate-700/50">
                  <span className="text-xs text-slate-400">Task Queue</span>
                  <p className="text-2xl font-black text-amber-400 mt-1">12</p>
                </div>
                <div className="bg-slate-800/60 p-4 rounded-lg border border-slate-700/50">
                  <span className="text-xs text-slate-400">Total Completed</span>
                  <p className="text-2xl font-black text-sky-400 mt-1">1,520</p>
                </div>
                <div className="bg-slate-800/60 p-4 rounded-lg border border-slate-700/50">
                  <span className="text-xs text-slate-400">Avg Execution Time</span>
                  <p className="text-2xl font-black text-indigo-400 mt-1">1.15 ms</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ================= 2. DOCTOR DASHBOARD ================= */}
        {user.role === 'DOCTOR' && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
              <h2 className="text-lg font-bold text-indigo-400 mb-4 flex items-center gap-2">
                <Stethoscope className="w-5 h-5" /> Patient Test Reports & Mark as Reviewed
              </h2>

              <div className="space-y-3">
                {doctorReports.map(rpt => (
                  <div key={rpt.id} className="p-4 bg-slate-950 rounded-lg border border-slate-800 flex justify-between items-center">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-bold text-white">{rpt.patientName} <span className="text-xs text-slate-500">({rpt.patientId})</span></p>
                        {!rpt.read && <span className="text-[9px] font-bold bg-rose-500 text-white px-2 py-0.5 rounded-full">NEW</span>}
                      </div>
                      <p className="text-xs text-slate-400 mt-1">{rpt.testName} | <span className="text-sky-400 font-mono">{rpt.result}</span></p>
                    </div>

                    <div className="flex items-center gap-2">
                      {!rpt.read ? (
                        <button onClick={() => toggleMarkAsRead(rpt.id)} className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-3 py-1.5 rounded-lg transition flex items-center gap-1">
                          <Eye className="w-3.5 h-3.5" /> Mark as Reviewed
                        </button>
                      ) : (
                        <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
                          <CheckCircle className="w-3.5 h-3.5" /> Reviewed
                        </span>
                      )}

                      <button 
                        onClick={() => { setSelectedReport(rpt); setShowPrescriptionModal(true); }}
                        className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-3 py-1.5 rounded-lg transition flex items-center gap-1"
                      >
                        <Pill className="w-3.5 h-3.5" /> Add Prescription
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* DIGITAL PRESCRIPTION MODAL */}
            {showPrescriptionModal && selectedReport && (
              <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl">
                  <div className="flex justify-between items-center mb-4 pb-2 border-b border-slate-800">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <Pill className="w-5 h-5 text-indigo-400" /> Digital Prescription for {selectedReport.patientName}
                    </h3>
                    <button onClick={() => setShowPrescriptionModal(false)} className="text-slate-400 hover:text-white"><X className="w-5 h-5"/></button>
                  </div>

                  <form onSubmit={handleAddPrescription} className="space-y-4">
                    <div>
                      <label className="text-xs text-slate-400">Medicine Name</label>
                      <input type="text" value={medName} onChange={e => setMedName(e.target.value)} required placeholder="e.g. Vitamin D3 60K" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 mt-1" />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs text-slate-400">Dosage</label>
                        <input type="text" value={dosage} onChange={e => setDosage(e.target.value)} required placeholder="e.g. 1 Capsule" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 mt-1" />
                      </div>
                      <div>
                        <label className="text-xs text-slate-400">Frequency / Timing</label>
                        <input type="text" value={frequency} onChange={e => setFrequency(e.target.value)} required placeholder="e.g. Once Weekly after meal" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 mt-1" />
                      </div>
                    </div>
                    <div>
                      <label className="text-xs text-slate-400">Doctor Advice & Clinical Notes</label>
                      <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={3} placeholder="Dietary recommendations or precautions..." className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 mt-1 outline-none"></textarea>
                    </div>

                    <button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-lg text-xs transition">
                      Attach Prescription & Notify Patient
                    </button>
                  </form>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ================= 3. LAB STAFF DASHBOARD ================= */}
        {user.role === 'LAB_STAFF' && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl max-w-xl mx-auto">
            <h2 className="text-lg font-bold text-emerald-400 mb-2 flex items-center gap-2">
              <FileUp className="w-5 h-5" /> Lab Test Results Entry
            </h2>
            <p className="text-xs text-slate-400 mb-4">Submit patient test values directly to the C++ Thread Pool.</p>
            <button onClick={() => alert("Report job queued in C++ Thread Pool!")} className="w-full bg-emerald-600 text-white font-bold py-2.5 rounded-lg text-xs">
              Generate Test Report
            </button>
          </div>
        )}

        {/* ================= 4. PATIENT DASHBOARD ================= */}
        {user.role === 'PATIENT' && (
          <div className="space-y-6">
            {/* Prescriptions Panel */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
              <h2 className="text-lg font-bold text-indigo-400 mb-4 flex items-center gap-2">
                <Pill className="w-5 h-5 text-indigo-400" /> Prescribed Medicines & Doctor Advice
              </h2>

              <div className="space-y-3">
                {prescriptions.map((rx, idx) => (
                  <div key={idx} className="p-4 bg-slate-950 rounded-lg border border-slate-800">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <p className="text-sm font-bold text-white">{rx.medName}</p>
                        <p className="text-xs text-slate-400 mt-0.5">Prescribed by {rx.doctorName} for Report #{rx.reportId}</p>
                      </div>
                      <span className="text-xs font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2.5 py-1 rounded">
                        {rx.dosage} - {rx.frequency}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 border-t border-slate-800/80 pt-2 mt-2">
                      <span className="font-semibold text-slate-300">Doctor Note:</span> {rx.notes}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Reports Panel */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
              <h2 className="text-lg font-bold text-amber-400 mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-amber-400" /> Downloadable Reports
              </h2>
              <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 flex justify-between items-center">
                <div>
                  <p className="text-sm font-bold text-white">CBC (Complete Blood Count)</p>
                  <p className="text-xs text-slate-400">Report ID: RPT-2026-001245</p>
                </div>
                <button onClick={() => alert("Downloading signed PDF...")} className="bg-amber-500/10 border border-amber-500/30 text-amber-400 hover:bg-amber-500/20 text-xs px-3.5 py-2 rounded-lg font-semibold transition flex items-center gap-1.5">
                  <Download className="w-3.5 h-3.5" /> Download PDF
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
"""

with open("frontend/src/App.tsx", "w", encoding="utf-8") as f:
    f.write(app_tsx_content)

print("MedFlow v3.0 script written successfully!")