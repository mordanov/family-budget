import api from './client'

export const authApi = {
  login: async (login, password, rememberMe = false) => {
    const form = new URLSearchParams()
    form.append('username', login)
    form.append('password', password)
    form.append('remember_me', rememberMe ? 'true' : 'false')
    const { data } = await api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },

  register: async (payload) => {
    const { data } = await api.post('/auth/register', payload)
    return data
  },
}
