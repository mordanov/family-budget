import { useState, useEffect, useCallback } from 'react'
import { categoriesApi, paymentMethodsApi, usersApi } from '../api/index'

export function useAsync(asyncFn, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null })

  const execute = useCallback(async (...args) => {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const data = await asyncFn(...args)
      setState({ data, loading: false, error: null })
      return data
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Unknown error'
      setState((s) => ({ ...s, loading: false, error: msg }))
      throw err
    }
  }, deps) // eslint-disable-line react-hooks/exhaustive-deps

  return { ...state, execute, setData: (data) => setState((s) => ({ ...s, data })) }
}

export function useCategories() {
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    categoriesApi.list()
      .then(setCategories)
      .finally(() => setLoading(false))
  }, [])

  return { categories, loading }
}

export function useUsers() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    usersApi.list()
      .then(setUsers)
      .finally(() => setLoading(false))
  }, [])

  return { users, loading }
}

export function usePaymentMethods() {
  const [paymentMethods, setPaymentMethods] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    paymentMethodsApi.list()
      .then(setPaymentMethods)
      .finally(() => setLoading(false))
  }, [])

  return { paymentMethods, loading }
}

