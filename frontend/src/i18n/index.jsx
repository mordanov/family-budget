import React, { createContext, useContext, useMemo, useState } from 'react'

const DICT = {
  en: {
    appName: 'Family Budget',
    navDashboard: 'Dashboard',
    navOperations: 'Operations',
    navReports: 'Reports',
    navBalances: 'Balances',
    navCategories: 'Categories',
    navUsers: 'Users',
    logout: 'Logout',
    expand: 'Expand',
    collapse: 'Collapse',
    signInSubtitle: 'Sign in to manage your family finances',
    loginLabel: 'Email or user name',
    loginPlaceholder: 'you@family.local or User 1',
    password: 'Password',
    signIn: 'Sign In',
    defaultUsersHint: 'Default users',
    operationsTitle: 'Operations',
    operationsSubtitle: '{count} operations total',
    newOperation: '+ New Operation',
    attachments: 'Attachments',
    uploadFile: 'Upload file',
    cameraPhoto: 'Take photo',
    dragDropHint: 'Drag and drop image/PDF here',
    noAttachments: 'No attachments yet',
    allTypes: 'All Types',
    allCategories: 'All Categories',
    allUsers: 'All Users',
    allPaymentTypes: 'All Payment Types',
    noOperations: 'No operations found',
    createFirstOperation: 'Create your first operation to get started.',
    notFoundTitle: 'Page not found',
    notFoundText: 'The page does not exist or has been moved.',
    goOperations: 'Go to Operations',
    goLogin: 'Go to Sign In',
  },
  ru: {
    appName: 'Семейный бюджет',
    navDashboard: 'Дашборд',
    navOperations: 'Операции',
    navReports: 'Отчеты',
    navBalances: 'Балансы',
    navCategories: 'Категории',
    navUsers: 'Пользователи',
    logout: 'Выход',
    expand: 'Развернуть',
    collapse: 'Свернуть',
    signInSubtitle: 'Войдите для управления семейными финансами',
    loginLabel: 'Email или имя пользователя',
    loginPlaceholder: 'you@family.local или User 1',
    password: 'Пароль',
    signIn: 'Войти',
    defaultUsersHint: 'Пользователи по умолчанию',
    operationsTitle: 'Операции',
    operationsSubtitle: 'Всего операций: {count}',
    newOperation: '+ Новая операция',
    attachments: 'Вложения',
    uploadFile: 'Загрузить файл',
    cameraPhoto: 'Сделать фото',
    dragDropHint: 'Перетащите сюда изображение/PDF',
    noAttachments: 'Вложений пока нет',
    allTypes: 'Все типы',
    allCategories: 'Все категории',
    allUsers: 'Все пользователи',
    allPaymentTypes: 'Все способы оплаты',
    noOperations: 'Операций не найдено',
    createFirstOperation: 'Создайте первую операцию, чтобы начать.',
    notFoundTitle: 'Страница не найдена',
    notFoundText: 'Страница не существует или была перемещена.',
    goOperations: 'Перейти к операциям',
    goLogin: 'Перейти ко входу',
  },
}

const I18nContext = createContext(null)

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(localStorage.getItem('ui_lang') || 'en')

  const value = useMemo(() => {
    const t = (key, params = {}) => {
      const template = DICT[lang]?.[key] ?? DICT.en[key] ?? key
      return Object.entries(params).reduce(
        (acc, [k, v]) => acc.replaceAll(`{${k}}`, String(v)),
        template
      )
    }

    const switchLanguage = (next) => {
      setLang(next)
      localStorage.setItem('ui_lang', next)
    }

    return { lang, t, switchLanguage }
  }, [lang])

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n() {
  const ctx = useContext(I18nContext)
  if (!ctx) {
    throw new Error('useI18n must be used inside I18nProvider')
  }
  return ctx
}

