import api from './client'

export const authApi = {
  login: async (login, password) => {
    const form = new URLSearchParams()
    form.append('username', login)
    form.append('password', password)
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
