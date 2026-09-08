import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'

import apiClient from '../services/apiClient'

const AuthContext = createContext(null)

const USER_KEY = 'nexus_user'
const TOKEN_KEY = 'nexus_access_token'

function formatFullName(identifier = '') {
  const localPart = String(identifier).trim().split('@')[0]

  return localPart
    .replace(/[._-]+/g, ' ')
    .split(/\s+/)
    .filter(Boolean)
    .map(
      (part) =>
        part.charAt(0).toUpperCase() +
        part.slice(1).toLowerCase(),
    )
    .join(' ')
}

function normalizeUser(userData, fallbackIdentifier = '') {
  const source = userData?.user || userData || {}

  const username =
    source.username ||
    source.email ||
    String(fallbackIdentifier).trim()

  return {
    ...source,
    username,
    full_name:
      source.full_name ||
      source.fullName ||
      formatFullName(username),
    role: source.role || 'INVESTIGATOR',
  }
}

function persistSession(user, token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  }

  localStorage.setItem(USER_KEY, JSON.stringify(user))
  localStorage.setItem('nexus_authenticated', 'true')
}

function clearSession() {
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem('nexus_authenticated')

  // Remove values saved by your older AuthContext.
  sessionStorage.removeItem(USER_KEY)
  sessionStorage.removeItem(TOKEN_KEY)
}

function readStoredUser() {
  try {
    const stored =
      localStorage.getItem(USER_KEY) ||
      sessionStorage.getItem(USER_KEY)

    return stored ? JSON.parse(stored) : null
  } catch {
    clearSession()
    return null
  }
}

function getErrorMessage(error) {
  const detail = error?.response?.data?.detail

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg)
      .filter(Boolean)
      .join(', ')
  }

  return (
    detail ||
    error?.response?.data?.message ||
    error?.message ||
    'Unable to complete the request.'
  )
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => readStoredUser())
  const [loading, setLoading] = useState(true)

  const logout = useCallback(() => {
    clearSession()
    setUser(null)
  }, [])

  useEffect(() => {
    let active = true

    async function restoreSession() {
      const token =
        localStorage.getItem(TOKEN_KEY) ||
        sessionStorage.getItem(TOKEN_KEY)

      if (!token) {
        if (active) {
          setUser(null)
          setLoading(false)
        }

        return
      }

      try {
        const response = await apiClient.get('/api/auth/me', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        const restoredUser = normalizeUser(response.data)

        if (active) {
          persistSession(restoredUser, token)
          setUser(restoredUser)
        }
      } catch {
        clearSession()

        if (active) {
          setUser(null)
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    restoreSession()

    return () => {
      active = false
    }
  }, [])

  const login = useCallback(async (credentials, oldPassword) => {
    /*
     * Supports both:
     * login({ username, password })
     * login(username, password)
     */
    const username =
      typeof credentials === 'object'
        ? credentials.username
        : credentials

    const password =
      typeof credentials === 'object'
        ? credentials.password
        : oldPassword

    setLoading(true)

    try {
      const response = await apiClient.post('/api/auth/login', {
        username: String(username || '').trim(),
        password: String(password || ''),
      })

      const token =
        response.data?.access_token ||
        response.data?.token

      if (!token) {
        throw new Error(
          'The backend did not return an access token.',
        )
      }

      const loggedInUser = normalizeUser(
        response.data,
        username,
      )

      persistSession(loggedInUser, token)
      setUser(loggedInUser)

      return loggedInUser
    } catch (error) {
      throw new Error(getErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }, [])

  const signup = useCallback(
    async ({
      fullName,
      full_name,
      username,
      email,
      password,
    }) => {
      setLoading(true)

      try {
        const response = await apiClient.post(
          '/api/auth/signup',
          {
            full_name: String(
              fullName || full_name || '',
            ).trim(),
            username: String(username || '')
              .trim()
              .toLowerCase(),
            email: String(email || '')
              .trim()
              .toLowerCase(),
            password: String(password || ''),
          },
        )

        const token =
          response.data?.access_token ||
          response.data?.token

        if (!token) {
          throw new Error(
            'The backend did not return an access token.',
          )
        }

        const createdUser = normalizeUser(
          response.data,
          username,
        )

        persistSession(createdUser, token)
        setUser(createdUser)

        return createdUser
      } catch (error) {
        throw new Error(getErrorMessage(error))
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      signup,
      logout,
    }),
    [user, loading, login, signup, logout],
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error(
      'useAuth must be used inside AuthProvider',
    )
  }

  return context
}

export function formatRole(role = '') {
  const labels = {
    ADMIN: 'Administrator',
    INVESTIGATOR: 'Senior Investigator',
    ANALYST: 'Intelligence Analyst',
  }

  return (
    labels[String(role).toUpperCase()] ||
    String(role)
      .toLowerCase()
      .split('_')
      .filter(Boolean)
      .map(
        (word) =>
          word.charAt(0).toUpperCase() + word.slice(1),
      )
      .join(' ') ||
    'Investigator'
  )
}

export function getInitials(name = '') {
  return (
    String(name)
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join('') || '?'
  )
}