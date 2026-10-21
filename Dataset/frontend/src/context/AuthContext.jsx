import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    try {
      const data = await api.me()
      setUser(data)
      return data
    } catch {
      setUser(null)
      return null
    }
  }, [])

  useEffect(() => {
    refreshUser().finally(() => setLoading(false))
  }, [refreshUser])

  const login = async (credentials) => {
    const data = await api.login(credentials)
    setUser(data)
    return data
  }

  const register = async (payload) => {
    await api.register(payload)
    return login({ username: payload.username, password: payload.password })
  }

  const logout = async () => {
    await api.logout()
    setUser(null)
  }

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser }),
    [user, loading, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
