import React, { useEffect, useRef, useState } from 'react'
import { attachmentsApi } from '../../api/index'
import {
  isKitchenConfigured,
  sendReceiptToKitchen,
} from '../../api/kitchenReceiptApi'
import { Alert, Button, Spinner } from '../ui/index'
import { apiError, formatDateTime } from '../../utils'
import { useI18n } from '../../i18n'
import { useTimezone } from '../../hooks/index'
import styles from './AttachmentManager.module.css'

const kitchenEnabled = isKitchenConfigured()

export default function AttachmentManager({ operationId }) {
  const { t } = useI18n()
  const timezone = useTimezone()
  const inputRef = useRef(null)
  const cameraRef = useRef(null)
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState(null)
  // { [attachmentId]: 'sending' | 'sent' | 'error' }
  const [kitchenState, setKitchenState] = useState({})

  const load = async () => {
    if (!operationId) return
    setLoading(true)
    try {
      const fetched = await attachmentsApi.listByOperation(operationId)
      setItems(fetched)
      // Pre-populate kitchen state for already-sent attachments (from DB)
      if (kitchenEnabled) {
        const preloaded = {}
        fetched.forEach((item) => {
          if (item.kitchen_sent_at) preloaded[item.id] = 'sent'
        })
        setKitchenState(preloaded)
      }
    } catch (e) {
      setError(apiError(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [operationId])

  const uploadFiles = async (files) => {
    if (!files?.length) return
    setUploading(true)
    setError(null)
    try {
      for (const file of Array.from(files)) {
        await attachmentsApi.upload(operationId, file)
      }
      await load()
    } catch (e) {
      setError(apiError(e))
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
      if (cameraRef.current) cameraRef.current.value = ''
    }
  }

  const removeItem = async (id) => {
    try {
      await attachmentsApi.delete(id)
      await load()
    } catch (e) {
      setError(apiError(e))
    }
  }

  const sendToKitchen = async (item) => {
    setKitchenState((prev) => ({ ...prev, [item.id]: 'sending' }))
    setError(null)
    try {
      await sendReceiptToKitchen(item.public_url)
      await attachmentsApi.markKitchenSent(item.id)
      setKitchenState((prev) => ({ ...prev, [item.id]: 'sent' }))
    } catch (e) {
      setKitchenState((prev) => ({ ...prev, [item.id]: 'error' }))
      setError(e.message || t('sendToKitchenError'))
    }
  }

  const kitchenButtonLabel = (id) => {
    const state = kitchenState[id]
    if (state === 'sending') return t('sendToKitchenSending')
    if (state === 'sent') return t('sendToKitchenSent')
    if (state === 'error') return t('sendToKitchenError')
    return t('sendToKitchen')
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <h3>{t('attachments')}</h3>
        <div className={styles.buttons}>
          <input
            ref={inputRef}
            type="file"
            hidden
            accept="image/*,application/pdf"
            multiple
            onChange={(e) => uploadFiles(e.target.files)}
          />
          <input
            ref={cameraRef}
            type="file"
            hidden
            accept="image/*"
            capture="environment"
            onChange={(e) => uploadFiles(e.target.files)}
          />
          <Button size="sm" variant="secondary" onClick={() => inputRef.current?.click()} loading={uploading}>
            {t('uploadFile')}
          </Button>
          <Button size="sm" variant="secondary" onClick={() => cameraRef.current?.click()} loading={uploading}>
            {t('cameraPhoto')}
          </Button>
        </div>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      <div
        className={`${styles.dropzone} ${dragOver ? styles.dragOver : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          uploadFiles(e.dataTransfer.files)
        }}
      >
        {uploading ? <Spinner size={18} /> : <span>{t('dragDropHint')}</span>}
      </div>

      {loading ? (
        <div className={styles.loading}><Spinner /></div>
      ) : items.length === 0 ? (
        <div className={styles.empty}>{t('noAttachments')}</div>
      ) : (
        <div className={styles.grid}>
          {items.map((item) => (
            <div key={item.id} className={styles.card}>
              <a href={item.public_url} target="_blank" rel="noreferrer" className={styles.link}>
                {item.mime_type.startsWith('image/') ? '🖼️' : '📄'} {item.original_filename}
              </a>
              <div className={styles.meta}>{formatDateTime(item.created_at, timezone)}</div>
              <div className={styles.actions}>
                <Button size="sm" variant="ghost" onClick={() => window.open(item.public_url, '_blank')}>
                  Open
                </Button>
                {kitchenEnabled && item.mime_type.startsWith('image/') && (
                  <Button
                    size="sm"
                    variant="secondary"
                    loading={kitchenState[item.id] === 'sending'}
                    disabled={kitchenState[item.id] === 'sent' || kitchenState[item.id] === 'sending'}
                    onClick={() => sendToKitchen(item)}
                  >
                    {kitchenButtonLabel(item.id)}
                  </Button>
                )}
                <Button size="sm" variant="danger" onClick={() => removeItem(item.id)}>
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


