'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Lock, FileText, Send, AlertCircle, FilePlus, ChevronLeft, Building } from 'lucide-react'
import Link from 'next/link'

export default function AdminDashboard() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState(false)

  const [schemeName, setSchemeName] = useState('')
  const [schemeDescription, setSchemeDescription] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [successMsg, setSuccessMsg] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    // Mock authentication for Hackathon Demo
    if (password === 'admin123') {
      setIsAuthenticated(true)
      setLoginError(false)
    } else {
      setLoginError(true)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleBroadcast = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!schemeName || !schemeDescription) return

    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8000/admin/inject_scheme', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: schemeName,
          description: schemeDescription
        })
      });

      const data = await response.json();

      if (response.ok) {
        setSuccessMsg(`Broadcast Successful! Engine scanned ${data.scanned_users} farmers and matched ${data.matches_found} eligible profiles via WhatsApp.`);
        setSchemeName('');
        setSchemeDescription('');
        setSelectedFile(null);
      } else {
        setSuccessMsg(`Failed to broadcast: ${data.detail || "Server Error"}`);
      }
    } catch (error) {
      console.error("Broadcast Error:", error);
      setSuccessMsg("Network connection error. Is the FastAPI server running?");
    } finally {
      setIsLoading(false);
      setTimeout(() => setSuccessMsg(''), 10000);
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
        <Link href="/" className="absolute top-6 left-6 text-emerald-700 hover:text-emerald-900 flex items-center gap-2 font-medium">
          <ChevronLeft size={20} /> Back to App
        </Link>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-emerald-100"
        >
          <div className="flex justify-center mb-6">
            <div className="p-4 bg-emerald-100 rounded-full text-emerald-600">
              <Building size={32} />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-center text-gray-800 mb-2">Government Portal</h1>
          <p className="text-center text-gray-500 mb-8">Authorized Nodal Officers Only</p>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Access Passkey</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none"
                  placeholder="Enter administrator password..."
                />
              </div>
              {loginError && (
                <p className="text-red-500 text-sm mt-2 flex items-center gap-1">
                  <AlertCircle size={14} /> Incorrect credentials
                </p>
              )}
            </div>
            <button
              type="submit"
              className="w-full py-3 bg-emerald-600 text-white font-bold rounded-xl hover:bg-emerald-700 transition-colors shadow-lg hover:shadow-xl active:scale-[0.98]"
            >
              Secure Login
            </button>
          </form>
          <div className="mt-6 text-center text-xs text-gray-400">
            For Demo Purposes: Use 'admin123'
          </div>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-100 rounded-lg text-emerald-600">
              <Building size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Agri-Scheme Command Center</h1>
              <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Reverse RAG Dispatcher</p>
            </div>
          </div>
          <button
            onClick={() => setIsAuthenticated(false)}
            className="text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors"
          >
            Sign Out
          </button>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden"
        >
          <div className="bg-emerald-600 px-8 py-6 text-white">
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Send size={24} />
              Broadcast New Scheme
            </h2>
            <p className="text-emerald-100 mt-2">
              Enter the details of the newly sanctioned scheme below. Our AI engine will actively scan the conversation history of all farmers and instantly dispatch a WhatsApp push notification to those who natively qualify based on their past inputs.
            </p>
          </div>

          <div className="p-8">
            <form onSubmit={handleBroadcast} className="space-y-6">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">Scheme Official Title</label>
                <input
                  type="text"
                  required
                  value={schemeName}
                  onChange={(e) => setSchemeName(e.target.value)}
                  placeholder="e.g. Maharashtra Drought Relief Subsidy 2024"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">Eligibility & Description Criteria</label>
                <textarea
                  required
                  rows={4}
                  value={schemeDescription}
                  onChange={(e) => setSchemeDescription(e.target.value)}
                  placeholder="Explain who gets this scheme. E.g: Available for farmers who own less than 5 acres of land in Nashik or Pune, and suffered crop loss."
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">Attached Government Order (PDF/Image)</label>
                <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:bg-gray-50 transition-colors relative cursor-pointer">
                  <input
                    type="file"
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    accept=".pdf,image/*"
                    onChange={handleFileChange}
                  />
                  {selectedFile ? (
                    <div className="flex flex-col items-center gap-2 text-emerald-600">
                      <FileText size={32} />
                      <span className="font-medium">{selectedFile.name}</span>
                      <span className="text-xs text-gray-400">Click to change file</span>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-2 text-gray-500">
                      <FilePlus size={32} />
                      <span className="font-medium">Drop document here or click to browse</span>
                      <span className="text-xs text-gray-400">Supports PDF, JPG, PNG up to 10MB</span>
                    </div>
                  )}
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-4 bg-emerald-600 text-white font-bold rounded-xl hover:bg-emerald-700 disabled:bg-emerald-400 transition-all shadow-lg hover:shadow-xl active:scale-[0.98] flex items-center justify-center gap-2 text-lg mt-8"
              >
                {isLoading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Scanning Farmer Database...
                  </>
                ) : (
                  <>
                    <Send size={20} /> Deploy Proactive Broadcast
                  </>
                )}
              </button>

              <AnimatePresence>
                {successMsg && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="bg-green-100 text-green-800 p-4 rounded-xl flex items-start gap-3 border border-green-200"
                  >
                    <AlertCircle className="flex-shrink-0 mt-0.5" size={20} />
                    <p className="text-sm font-medium">{successMsg}</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </form>
          </div>
        </motion.div>
      </main>
    </div>
  )
}
