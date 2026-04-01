import api from './client'

export const operationsApi = {
  list: async (params = {}) => {
    const { data } = await api.get('/operations/', { params })
    return data
  },

  get: async (id) => {
    const { data } = await api.get(`/operations/${id}`)
    return data
  },

  create: async (payload) => {
    const { data } = await api.post('/operations/', payload)
    return data
  },

  update: async (id, payload) => {
    const { data } = await api.patch(`/operations/${id}`, payload)
    return data
  },

  delete: async (id) => {
    await api.delete(`/operations/${id}`)
  },
}
