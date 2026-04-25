import { create } from 'zustand'
import { authApi } from '../api/auth'
import { COOKIE_TOKEN, COOKIE_USER, setCookie, getCookie, clearRememberCookies } from '../utils/cookies'

const REMEMBER_EXPIRE_DAYS = 30

// On init: restore from localStorage, falling back to cookie
const initToken = () => {
  const stored = localStorage.getItem('access_token')
  if (stored) return stored
  const fromCookie = getCookie(COOKIE_TOKEN)
  if (fromCookie) {
    localStorage.setItem('access_token', fromCookie)
    return fromCookie
  }
  return null
}

const initUser = () => {
  try {
    const stored = localStorage.getItem('user')
    if (stored) return JSON.parse(stored)
    const fromCookie = getCookie(COOKIE_USER)
    if (fromCookie) {
      localStorage.setItem('user', fromCookie)
      return JSON.parse(fromCookie)
    }
  } catch {}
  return null
}

export const useAuthStore = create((set) => ({
  user: initUser(),
  token: initToken(),
  loading: false,
  error: null,

  login: async (loginValue, password, rememberMe = false) => {
    set({ loading: true, error: null })
    try {
      const data = await authApi.login(loginValue, password, rememberMe)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      if (rememberMe) {
        setCookie(COOKIE_TOKEN, data.access_token, REMEMBER_EXPIRE_DAYS)
        setCookie(COOKIE_USER, JSON.stringify(data.user), REMEMBER_EXPIRE_DAYS)
      } else {
        clearRememberCookies()
      }
      set({ user: data.user, token: data.access_token, loading: false })
      return data.user
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login failed'
      set({ loading: false, error: msg })
      throw new Error(msg)
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    clearRememberCookies()
    set({ user: null, token: null, error: null })
  },

  updateUser: (updatedUser) => {
    localStorage.setItem('user', JSON.stringify(updatedUser))
    if (getCookie(COOKIE_TOKEN)) {
      setCookie(COOKIE_USER, JSON.stringify(updatedUser), REMEMBER_EXPIRE_DAYS)
    }
    set({ user: updatedUser })
  },

  clearError: () => set({ error: null }),
}))
