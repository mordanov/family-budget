import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAuthStore } from '../src/store/authStore'

const mockUser = { id: 1, name: 'Test User', email: 'test@example.com' }

vi.mock('../src/api/auth', () => ({
  authApi: {
    login: vi.fn(),
  },
}))

import { authApi } from '../src/api/auth'

describe('useAuthStore', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({ user: null, token: null, loading: false, error: null })
    vi.clearAllMocks()
  })

  it('starts with no user when localStorage is empty', () => {
    const { result } = renderHook(() => useAuthStore())
    expect(result.current.user).toBeNull()
    expect(result.current.token).toBeNull()
  })

  it('login success stores token and user', async () => {
    authApi.login.mockResolvedValue({ access_token: 'tok123', user: mockUser })
    const { result } = renderHook(() => useAuthStore())
    await act(async () => { await result.current.login('test@example.com', 'pass') })
    expect(result.current.user).toEqual(mockUser)
    expect(result.current.token).toBe('tok123')
    expect(localStorage.getItem('access_token')).toBe('tok123')
  })

  it('login failure sets error', async () => {
    authApi.login.mockRejectedValue({ response: { data: { detail: 'Bad credentials' } } })
    const { result } = renderHook(() => useAuthStore())
    await act(async () => {
      try { await result.current.login('bad@example.com', 'wrong') } catch {}
    })
    expect(result.current.error).toBe('Bad credentials')
    expect(result.current.user).toBeNull()
  })

  it('logout clears user and token', async () => {
    useAuthStore.setState({ user: mockUser, token: 'tok123' })
    localStorage.setItem('access_token', 'tok123')
    const { result } = renderHook(() => useAuthStore())
    act(() => { result.current.logout() })
    expect(result.current.user).toBeNull()
    expect(result.current.token).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
  })
})
