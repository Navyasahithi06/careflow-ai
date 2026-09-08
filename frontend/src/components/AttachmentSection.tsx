import { useState, useEffect, useCallback, useRef } from 'react'
import axios from 'axios'
import type { Attachment, AttachmentEntityType } from '../types'

function getAuthHeaders() {
  const token = localStorage.getItem('cf_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

const MAX_SIZE = 5 * 1024 * 1024
const ACCEPT = '.pdf,.jpg,.jpeg,.png,.webp,.txt,.csv,.doc,.docx'

function formatBytes(bytes: number) {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function fileIcon(mime: string) {
  if (mime === 'application/pdf') return '📕'
  if (mime.startsWith('image/')) return '🖼️'
  if (mime === 'text/csv') return '📊'
  if (mime.includes('wordprocessing') || mime === 'application/msword') return '📝'
  return '📄'
}

interface Props {
  entityType: AttachmentEntityType
  entityId: number
}

export default function AttachmentSection({ entityType, entityId }: Props) {
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fetchAttachments = useCallback(async () => {
    setError('')
    try {
      const res = await axios.get<Attachment[]>(`/api/attachments/entity/${entityType}/${entityId}`, { headers: getAuthHeaders() })
      setAttachments(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load attachments')
    } finally {
      setLoading(false)
    }
  }, [entityType, entityId])

  useEffect(() => {
    setLoading(true)
    setAttachments([])
    fetchAttachments()
  }, [fetchAttachments])

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return

    if (file.size > MAX_SIZE) {
      setError('File exceeds the 5 MB limit')
      return
    }

    setUploading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const up = await axios.post<Attachment>('/api/attachments/upload', formData, { headers: getAuthHeaders() })
      await axios.post(`/api/attachments/entity/${entityType}/${entityId}`, { attachment_id: up.data.id }, { headers: getAuthHeaders() })
      await fetchAttachments()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleDownload = async (att: Attachment) => {
    try {
      const res = await axios.get(`/api/attachments/${att.id}/download`, {
        headers: getAuthHeaders(),
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = att.file_name
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Download failed')
    }
  }

  const handleDelete = async (att: Attachment) => {
    if (!window.confirm(`Delete "${att.file_name}"?`)) return
    try {
      await axios.delete(`/api/attachments/${att.id}`, { headers: getAuthHeaders() })
      await fetchAttachments()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Delete failed')
    }
  }

  return (
    <div className="mt-3 border-t border-gray-100 pt-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Attachments</p>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          onChange={handleFileChange}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-primary-600 border border-primary-200 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors disabled:opacity-50"
        >
          {uploading ? (
            <>
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-primary-600"></div>
              Uploading...
            </>
          ) : (
            <>+ Upload</>
          )}
        </button>
      </div>

      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}

      {loading ? (
        <p className="text-xs text-gray-400 mt-1">Loading attachments...</p>
      ) : attachments.length === 0 ? (
        <p className="text-xs text-gray-400 mt-1">No attachments yet</p>
      ) : (
        <ul className="mt-2 space-y-1.5">
          {attachments.map((att) => (
            <li
              key={att.id}
              className="flex items-center gap-2 px-2.5 py-1.5 bg-gray-50 rounded-lg text-sm"
            >
              <span className="text-base leading-none">{fileIcon(att.mime_type)}</span>
              <span className="flex-1 min-w-0">
                <span className="block truncate font-medium text-gray-800">{att.file_name}</span>
                <span className="block text-[11px] text-gray-400">{formatBytes(att.size_bytes)}</span>
              </span>
              <button
                onClick={() => handleDownload(att)}
                className="p-1 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors"
                title="Download"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </button>
              <button
                onClick={() => handleDelete(att)}
                className="p-1 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                title="Delete"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}