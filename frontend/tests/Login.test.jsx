import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import LoginPage from '../src/pages/Login'
import { useAuthStore } from '../src/store/authStore'
import { I18nProvider } from '../src/i18n'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async (importActual) => {
  const actual = await importActual()
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../src/store/authStore', () => ({
  useAuthStore: vi.fn(),
}))

describe('LoginPage', () => {
  const mockLogin = vi.fn()
  const mockClear = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.mockReturnValue({
      login: mockLogin,
      loading: false,
      error: null,
      clearError: mockClear,
    })
  })

  const renderLogin = () =>
    render(
      <I18nProvider>
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      </I18nProvider>
    )

  it('renders email and password inputs', () => {
    renderLogin()
    expect(screen.getByPlaceholderText(/family\.local/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/••/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('calls login with login identifier and password on submit', async () => {
    mockLogin.mockResolvedValue({})
    renderLogin()
    await userEvent.type(screen.getByPlaceholderText(/family\.local/i), 'user1@family.local')
    await userEvent.type(screen.getByPlaceholderText(/••/), 'password1')
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith('user1@family.local', 'password1'))
  })

  it('navigates to /operations on successful login', async () => {
    mockLogin.mockResolvedValue({})
    renderLogin()
    await userEvent.type(screen.getByPlaceholderText(/family\.local/i), 'user@test.com')
    await userEvent.type(screen.getByPlaceholderText(/••/), 'pass123')
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/operations'))
  })

  it('displays error message when login fails', () => {
    useAuthStore.mockReturnValue({
      login: mockLogin,
      loading: false,
      error: 'Incorrect login or password',
      clearError: mockClear,
    })
    renderLogin()
    expect(screen.getByText('Incorrect login or password')).toBeInTheDocument()
  })

  it('shows loading state on submit', () => {
    useAuthStore.mockReturnValue({
      login: mockLogin,
      loading: true,
      error: null,
      clearError: mockClear,
    })
    renderLogin()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeDisabled()
  })
})
