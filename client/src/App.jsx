import React, { useState, useEffect } from 'react';
import { User, Mail, Camera, Lock, CheckCircle, AlertCircle, Loader, ScanFace } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('login'); // 'login' or 'register'
  const [formData, setFormData] = useState({ name: '', email: '' });
  const [status, setStatus] = useState({ type: '', message: '' });
  const [isLoading, setIsLoading] = useState(false);
  const [cursorPos, setCursorPos] = useState({ x: 0, y: 0 });

  // Flask Backend URL - Change if your port is different
  const API_BASE_URL = "http://127.0.0.1:5000";

  // Cursor Tracking Effect
  useEffect(() => {
    const updateCursor = (e) => {
      setCursorPos({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', updateCursor);
    return () => window.removeEventListener('mousemove', updateCursor);
  }, []);

  // Handle Input Changes
  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // Helper for API Calls
  const handleAuth = async (endpoint) => {
    setStatus({ type: '', message: '' });
    setIsLoading(true);

    // Validation for Register
    if (endpoint === '/register' && (!formData.name || !formData.email)) {
      setStatus({ type: 'error', message: 'Please fill in all fields.' });
      setIsLoading(false);
      return;
    }

    try {
      const config = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      };

      if (endpoint === '/register') {
        config.body = JSON.stringify(formData);
      }

      // Connecting to Python Backend
      const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
      const data = await response.json();

      if (response.ok) {
        setStatus({ 
          type: 'success', 
          // CHANGED HERE: Uses data.username for login success
          message: endpoint === '/register' 
            ? `Welcome, ${formData.name}! Registration complete.` 
            : `Access Granted! Welcome back, ${data.username}.`
        });
        
        if(endpoint === '/register') setFormData({ name: '', email: '' });
      } else {
        setStatus({ type: 'error', message: data.error || 'Authentication failed.' });
      }
    } catch (error) {
      setStatus({ type: 'error', message: 'Could not connect to server. Is app.py running?' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4 font-sans text-slate-100 overflow-hidden cursor-none">
      
      {/* --- CUSTOM CURSOR --- */}
      {/* Main Glow */}
      <div 
        className="fixed w-8 h-8 bg-blue-400 rounded-full blur-md pointer-events-none z-[100] mix-blend-screen transition-transform duration-75 ease-out"
        style={{ 
          left: cursorPos.x, 
          top: cursorPos.y, 
          transform: 'translate(-50%, -50%)' 
        }}
      />
      {/* Secondary Trailing Glow */}
      <div 
        className="fixed w-24 h-24 bg-purple-500/30 rounded-full blur-xl pointer-events-none z-[90] mix-blend-screen transition-transform duration-500 ease-out"
        style={{ 
          left: cursorPos.x, 
          top: cursorPos.y, 
          transform: 'translate(-50%, -50%)' 
        }}
      />

      {/* Main Card */}
      <div className="w-full max-w-md bg-white/10 backdrop-blur-lg border border-white/20 rounded-3xl shadow-2xl overflow-hidden relative z-10">
        
        {/* Decorative Background Blobs */}
        <div className="absolute top-0 left-0 w-32 h-32 bg-blue-500/30 rounded-full blur-3xl -translate-x-10 -translate-y-10 pointer-events-none"></div>
        <div className="absolute bottom-0 right-0 w-32 h-32 bg-purple-500/30 rounded-full blur-3xl translate-x-10 translate-y-10 pointer-events-none"></div>

        {/* Header Section */}
        <div className="p-8 text-center relative z-10">
          <div className="mx-auto w-16 h-16 bg-blue-500/20 rounded-2xl flex items-center justify-center mb-4 border border-blue-400/30 shadow-[0_0_15px_rgba(59,130,246,0.5)]">
            <ScanFace className="w-8 h-8 text-blue-300" />
          </div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-200 to-purple-200">
            SecureFace
          </h1>
          <p className="text-blue-200/60 text-sm mt-2">Biometric Authentication System</p>
        </div>

        {/* Tab Switcher */}
        <div className="flex px-8 mb-6 relative z-10">
          <button
            onClick={() => { setActiveTab('login'); setStatus({ type: '', message: '' }); }}
            className={`cursor-none flex-1 py-3 text-sm font-medium transition-all duration-300 rounded-l-xl border-y border-l ${
              activeTab === 'login'
                ? 'bg-blue-600 border-blue-500 text-white shadow-lg'
                : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            Login
          </button>
          <button
            onClick={() => { setActiveTab('register'); setStatus({ type: '', message: '' }); }}
            className={`cursor-none flex-1 py-3 text-sm font-medium transition-all duration-300 rounded-r-xl border-y border-r ${
              activeTab === 'register'
                ? 'bg-blue-600 border-blue-500 text-white shadow-lg'
                : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            Register
          </button>
        </div>

        {/* Content Area */}
        <div className="px-8 pb-8 relative z-10">
          
          {/* LOGIN VIEW */}
          {activeTab === 'login' && (
            <div className="space-y-6 animate-pulse-fade">
              <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5 text-center">
                <p className="text-slate-300 mb-4 text-sm">
                  Look at the camera and click below to verify identity.
                </p>
                
                <button
                  onClick={() => handleAuth('/login')}
                  disabled={isLoading}
                  className={`cursor-none group w-full py-4 rounded-xl font-bold text-lg shadow-lg flex items-center justify-center gap-3 transition-all duration-300 ${
                    isLoading 
                      ? 'bg-slate-700 cursor-not-allowed opacity-70'
                      : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 hover:shadow-blue-500/25 active:scale-[0.98]'
                  }`}
                >
                  {isLoading ? (
                    <Loader className="w-6 h-6 animate-spin text-blue-200" />
                  ) : (
                    <Lock className="w-5 h-5 group-hover:scale-110 transition-transform" />
                  )}
                  {isLoading ? 'Scanning...' : 'Authenticate'}
                </button>
              </div>
            </div>
          )}

          {/* REGISTER VIEW */}
          {activeTab === 'register' && (
            <div className="space-y-4 animate-pulse-fade">
              <div className="relative group">
                <User className="absolute left-4 top-3.5 w-5 h-5 text-slate-400 group-focus-within:text-blue-400 transition-colors" />
                <input
                  type="text"
                  name="name"
                  placeholder="Full Name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="cursor-none w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 pl-12 pr-4 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
              </div>

              <div className="relative group">
                <Mail className="absolute left-4 top-3.5 w-5 h-5 text-slate-400 group-focus-within:text-blue-400 transition-colors" />
                <input
                  type="email"
                  name="email"
                  placeholder="Email Address"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="cursor-none w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 pl-12 pr-4 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
              </div>

              <button
                onClick={() => handleAuth('/register')}
                disabled={isLoading}
                className={`cursor-none mt-2 w-full py-4 rounded-xl font-bold text-lg shadow-lg flex items-center justify-center gap-3 transition-all duration-300 ${
                  isLoading 
                    ? 'bg-slate-700 cursor-not-allowed opacity-70'
                    : 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 hover:shadow-emerald-500/25 active:scale-[0.98]'
                }`}
              >
                {isLoading ? (
                  <Loader className="w-6 h-6 animate-spin text-emerald-200" />
                ) : (
                  <Camera className="w-5 h-5 group-hover:scale-110 transition-transform" />
                )}
                {isLoading ? 'Processing...' : 'Register Face'}
              </button>
            </div>
          )}

          {/* Status Messages */}
          {status.message && (
            <div className={`mt-6 p-4 rounded-xl flex items-start gap-3 text-sm animate-bounce-in ${
              status.type === 'success' 
                ? 'bg-emerald-500/20 border border-emerald-500/30 text-emerald-200' 
                : 'bg-red-500/20 border border-red-500/30 text-red-200'
            }`}>
              {status.type === 'success' ? (
                <CheckCircle className="w-5 h-5 shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              )}
              <span>{status.message}</span>
            </div>
          )}

          <div className="mt-8 text-center">
            <p className="text-xs text-slate-500">
              Powered by Python Face Recognition & PostgreSQL
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}