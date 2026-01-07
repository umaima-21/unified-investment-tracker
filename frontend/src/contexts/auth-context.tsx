import React, { createContext, useContext, useState, useEffect } from 'react'

interface AuthContextType {
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  user: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState<string | null>(null)

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('auth_token')
    const storedUser = localStorage.getItem('user')
    if (token && storedUser) {
      setIsAuthenticated(true)
      setUser(storedUser)
    }
  }, [])

  const login = async (username: string, password: string) => {
    // No validation - allow login with any credentials (including empty)
    const token = 'mock_token_' + Date.now()
    localStorage.setItem('auth_token', token)
    const displayUser = username || 'User'
    localStorage.setItem('user', displayUser)
    setIsAuthenticated(true)
    setUser(displayUser)
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    setIsAuthenticated(false)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, user }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

