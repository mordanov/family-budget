import React, { useEffect, useRef, useState } from 'react'
import { attachmentsApi } from '../../api/index'
import { Alert, Button, Spinner } from '../ui/index'
import { apiError, formatDateTime } from '../../utils'
import { useI18n } from '../../i18n'
import { useTimezone } from '../../hooks/index'
import styles from './AttachmentManager.module.css'

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

  const load = async () => {
    if (!operationId) return
    setLoading(true)
    try {
      setItems(await attachmentsApi.listByOperation(operationId))
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


