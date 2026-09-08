import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import {
  Eye,
  EyeOff,
  Fingerprint,
  Network,
  ShieldCheck,
  UserPlus,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const navigate = useNavigate()

  const {
    login,
    signup,
    isAuthenticated,
    loading: authLoading,
  } = useAuth()

  const [mode, setMode] = useState('login')
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const [form, setForm] = useState({
    fullName: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  })

  if (!authLoading && isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  function updateField(event) {
    const { name, value } = event.target

    setForm((current) => ({
      ...current,
      [name]: value,
    }))

    setError('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    if (!form.username.trim()) {
      setError('Please enter your username or Investigator ID.')
      return
    }

    if (!form.password) {
      setError('Please enter your password.')
      return
    }

    if (mode === 'signup') {
      if (!form.fullName.trim()) {
        setError('Please enter your full name.')
        return
      }

      if (!form.email.trim()) {
        setError('Please enter your email address.')
        return
      }

      if (form.password.length < 8) {
        setError('Password must contain at least 8 characters.')
        return
      }

      if (form.password !== form.confirmPassword) {
        setError('Passwords do not match.')
        return
      }
    }

    try {
      setSubmitting(true)

      if (mode === 'login') {
        await login({
          username: form.username,
          password: form.password,
        })
      } else {
        await signup({
          fullName: form.fullName,
          username: form.username,
          email: form.email,
          password: form.password,
        })
      }

      navigate('/dashboard', {
        replace: true,
      })
    } catch (requestError) {
      setError(
        requestError.message ||
          'Authentication failed. Please try again.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  function changeMode(nextMode) {
    setMode(nextMode)
    setError('')
    setShowPassword(false)

    setForm({
      fullName: '',
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
    })
  }

  return (
    <div className="grid min-h-screen bg-base-950 text-ink-100 lg:grid-cols-2">
      {/* Left information panel */}
      <section className="relative hidden overflow-hidden border-r border-base-border p-12 lg:flex lg:flex-col lg:justify-between">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_25%_20%,rgba(139,92,246,0.15),transparent_35%),radial-gradient(circle_at_70%_70%,rgba(34,211,238,0.08),transparent_35%)]" />

        <div className="relative z-10">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-accent/40 bg-accent/10 text-accent">
              <Network size={23} />
            </div>

            <div>
              <h1 className="font-display text-2xl font-bold tracking-wide">
                NEXUS
              </h1>

              <p className="text-xs uppercase tracking-[0.2em] text-ink-500">
                Intelligence Platform
              </p>
            </div>
          </div>
        </div>

        <div className="relative z-10 max-w-xl">
          {/* Written only once */}
          <p className="mb-6 text-sm uppercase tracking-[0.18em] text-accent">
            Criminal Intelligence & Network Analysis
          </p>

          <h2 className="font-display text-5xl font-semibold leading-tight">
            Connecting the dots.
            <br />
            Revealing hidden
            <br />
            networks.
          </h2>

          <p className="mt-7 max-w-lg text-base leading-7 text-ink-300">
            NEXUS transforms fragmented investigation data into an
            evidence-grounded and explainable criminal intelligence
            network for authorized investigators.
          </p>
        </div>

        <div className="relative z-10 flex flex-wrap gap-6 text-xs uppercase tracking-[0.16em] text-ink-500">
          <span>Entity Resolution</span>
          <span>Pattern Analysis</span>
          <span>Explainable Risk</span>
        </div>
      </section>

      {/* Authentication panel */}
      <section className="flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-lg">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-3">
              <Network className="text-accent" />
              <strong className="font-display text-2xl">NEXUS</strong>
            </div>
          </div>

          <div className="mb-7">
            <div className="mb-5 flex rounded-xl border border-base-border bg-base-900 p-1">
              <button
                type="button"
                onClick={() => changeMode('login')}
                className={`flex-1 rounded-lg px-4 py-3 text-sm font-semibold transition ${
                  mode === 'login'
                    ? 'bg-accent text-white shadow-lg shadow-accent/20'
                    : 'text-ink-400 hover:text-ink-100'
                }`}
              >
                Login
              </button>

              <button
                type="button"
                onClick={() => changeMode('signup')}
                className={`flex-1 rounded-lg px-4 py-3 text-sm font-semibold transition ${
                  mode === 'signup'
                    ? 'bg-accent text-white shadow-lg shadow-accent/20'
                    : 'text-ink-400 hover:text-ink-100'
                }`}
              >
                Create Account
              </button>
            </div>

            <h2 className="font-display text-3xl font-semibold">
              {mode === 'login'
                ? 'Secure Login'
                : 'Create Investigator Account'}
            </h2>

            <p className="mt-2 text-sm text-ink-500">
              {mode === 'login'
                ? 'Sign in to your authorized NEXUS workspace.'
                : 'Register an authorized prototype investigator account.'}
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            className="space-y-4"
          >
            {mode === 'signup' && (
              <label className="block">
                <span className="mb-2 block text-sm text-ink-300">
                  Full name
                </span>

                <input
                  type="text"
                  name="fullName"
                  value={form.fullName}
                  onChange={updateField}
                  placeholder="e.g. Krisha Mange"
                  autoComplete="name"
                  className="w-full rounded-xl border border-base-border bg-base-900 px-4 py-3.5 outline-none transition focus:border-accent"
                />
              </label>
            )}

            <label className="block">
              <span className="mb-2 block text-sm text-ink-300">
                Username or Investigator ID
              </span>

              <input
                type="text"
                name="username"
                value={form.username}
                onChange={updateField}
                placeholder="e.g. krisha"
                autoComplete="username"
                className="w-full rounded-xl border border-base-border bg-base-900 px-4 py-3.5 outline-none transition focus:border-accent"
              />
            </label>

            {mode === 'signup' && (
              <label className="block">
                <span className="mb-2 block text-sm text-ink-300">
                  Official email
                </span>

                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={updateField}
                  placeholder="krisha@nexus.gov"
                  autoComplete="email"
                  className="w-full rounded-xl border border-base-border bg-base-900 px-4 py-3.5 outline-none transition focus:border-accent"
                />
              </label>
            )}

            <label className="block">
              <span className="mb-2 block text-sm text-ink-300">
                Password
              </span>

              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={form.password}
                  onChange={updateField}
                  placeholder="Minimum 8 characters"
                  autoComplete={
                    mode === 'login'
                      ? 'current-password'
                      : 'new-password'
                  }
                  className="w-full rounded-xl border border-base-border bg-base-900 px-4 py-3.5 pr-12 outline-none transition focus:border-accent"
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowPassword((current) => !current)
                  }
                  aria-label={
                    showPassword ? 'Hide password' : 'Show password'
                  }
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-ink-500 hover:text-ink-100"
                >
                  {showPassword ? (
                    <EyeOff size={18} />
                  ) : (
                    <Eye size={18} />
                  )}
                </button>
              </div>
            </label>

            {mode === 'signup' && (
              <label className="block">
                <span className="mb-2 block text-sm text-ink-300">
                  Confirm password
                </span>

                <input
                  type={showPassword ? 'text' : 'password'}
                  name="confirmPassword"
                  value={form.confirmPassword}
                  onChange={updateField}
                  placeholder="Enter password again"
                  autoComplete="new-password"
                  className="w-full rounded-xl border border-base-border bg-base-900 px-4 py-3.5 outline-none transition focus:border-accent"
                />
              </label>
            )}

            {error && (
              <div
                role="alert"
                className="flex items-start gap-2 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300"
              >
                <ShieldCheck size={17} className="mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-accent px-4 py-3.5 font-semibold text-white transition hover:bg-accent-soft disabled:cursor-not-allowed disabled:opacity-60"
            >
              {mode === 'login' ? (
                <Fingerprint size={18} />
              ) : (
                <UserPlus size={18} />
              )}

              {submitting
                ? 'Please wait...'
                : mode === 'login'
                  ? 'Secure Login'
                  : 'Create Account'}
            </button>
          </form>

          <div className="mt-7 flex items-start gap-2 text-xs leading-5 text-ink-500">
            <Fingerprint size={16} className="mt-0.5 shrink-0" />

            <p>
              Passwords are hashed in the backend database. NEXUS never
              stores your plain password.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}