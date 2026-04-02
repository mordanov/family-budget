import api from './client'
export { operationsApi } from './operations'

export const categoriesApi = {
  list: async () => {
    const { data } = await api.get('/categories/')
    return data
  },
  get: async (id) => {
    const { data } = await api.get(`/categories/${id}`)
    return data
  },
  create: async (payload) => {
    const { data } = await api.post('/categories/', payload)
    return data
  },
  update: async (id, payload) => {
    const { data } = await api.patch(`/categories/${id}`, payload)
    return data
  },
  delete: async (id) => {
    await api.delete(`/categories/${id}`)
  },
}

export const usersApi = {
  list: async () => {
    const { data } = await api.get('/users/')
    return data
  },
  get: async (id) => {
    const { data } = await api.get(`/users/${id}`)
    return data
  },
  me: async () => {
    const { data } = await api.get('/users/me')
    return data
  },
  create: async (payload) => {
    const { data } = await api.post('/users/', payload)
    return data
  },
  update: async (id, payload) => {
    const { data } = await api.patch(`/users/${id}`, payload)
    return data
  },
  delete: async (id) => {
    await api.delete(`/users/${id}`)
  },
}

export const balancesApi = {
  list: async () => {
    const { data } = await api.get('/balances/')
    return data
  },
  get: async (year, month) => {
    const { data } = await api.get(`/balances/${year}/${month}`)
    return data
  },
  setOpening: async (year, month, manual_opening_balance) => {
    const { data } = await api.patch(`/balances/${year}/${month}`, { manual_opening_balance })
    return data
  },
}

export const reportsApi = {
  get: async (params = {}) => {
    const { data } = await api.get('/reports/', { params })
    return data
  },
  forecast: async (params = {}) => {
    const { data } = await api.get('/reports/forecast', { params })
    return data
  },
  dailyBalance: async (params = {}) => {
    const { data } = await api.get('/reports/balance-daily', { params })
    return data
  },
}

export const paymentMethodsApi = {
  list: async () => {
    const { data } = await api.get('/payment-methods/')
    return data
  },
  get: async (id) => {
    const { data } = await api.get(`/payment-methods/${id}`)
    return data
  },
  create: async (payload) => {
    const { data } = await api.post('/payment-methods/', payload)
    return data
  },
  update: async (id, payload) => {
    const { data } = await api.patch(`/payment-methods/${id}`, payload)
    return data
  },
  delete: async (id) => {
    await api.delete(`/payment-methods/${id}`)
  },
}

export const attachmentsApi = {
  listByOperation: async (operationId) => {
    const { data } = await api.get(`/attachments/operation/${operationId}`)
    return data
  },
  upload: async (operationId, file, description = '') => {
    const form = new FormData()
    form.append('file', file)
    if (description) form.append('description', description)
    const { data } = await api.post(`/attachments/operation/${operationId}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },
  delete: async (id) => {
    await api.delete(`/attachments/${id}`)
  },
}
