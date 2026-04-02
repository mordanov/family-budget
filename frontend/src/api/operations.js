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

  createWithAttachments: async (payload, files = []) => {
    const form = new FormData()
    Object.entries(payload).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') return
      form.append(key, value)
    })
    files.forEach((file) => form.append('files', file))
    const { data } = await api.post('/operations/with-attachments', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
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
