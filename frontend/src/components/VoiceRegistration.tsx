import { useEffect, useRef, useState } from 'react'
import {
  detectSpeechSupport,
  createRecognitionSession,
  parseTranscript,
  type SpeechRecognitionGlobals,
  type SpeechRecognitionLike,
  type VoiceDraft,
} from '../utils/voice'

function resolveConstructor(): (new () => SpeechRecognitionLike) | null {
  if (typeof window === 'undefined') return null
  const win = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike
    webkitSpeechRecognition?: new () => SpeechRecognitionLike
  }
  return win.SpeechRecognition || win.webkitSpeechRecognition || null
}

interface VoiceRegistrationProps {
  onPopulate: (draft: VoiceDraft) => void
}

export default function VoiceRegistration({ onPopulate }: VoiceRegistrationProps) {
  const [supported, setSupported] = useState(true)
  const [listening, setListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [message, setMessage] = useState('')
  const [isError, setIsError] = useState(false)

  const recRef = useRef<SpeechRecognitionLike | null>(null)
  const baseTextRef = useRef('')
  const hadFinalRef = useRef(false)
  const lastFinalRef = useRef('')

  useEffect(() => {
    setSupported(
      detectSpeechSupport(typeof window !== 'undefined' ? (window as unknown as SpeechRecognitionGlobals) : undefined),
    )
  }, [])

  useEffect(() => {
    return () => {
      if (recRef.current) {
        try {
          recRef.current.abort?.()
        } catch {
          // ignore teardown errors
        }
      }
    }
  }, [])

  const stopListening = () => {
    if (recRef.current) {
      try {
        recRef.current.stop()
      } catch {
        // ignore
      }
    }
    recRef.current = null
    setListening(false)
  }

  const startListening = () => {
    const Ctor = resolveConstructor()
    if (!Ctor) {
      setSupported(false)
      return
    }
    setIsError(false)
    setMessage('')
    baseTextRef.current = transcript || ''
    hadFinalRef.current = false

    try {
      const rec = new Ctor()
      recRef.current = rec

      createRecognitionSession(rec, {
        onResult: (text, isFinal) => {
          const fullText =
            baseTextRef.current && !text.includes(baseTextRef.current)
              ? `${baseTextRef.current} ${text}`
              : text
          setTranscript(fullText)
          if (isFinal && fullText !== lastFinalRef.current) {
            lastFinalRef.current = fullText
            hadFinalRef.current = true
            onPopulate(parseTranscript(fullText))
          }
        },
        onError: (msg) => {
          setIsError(true)
          setMessage(msg)
          recRef.current = null
          setListening(false)
        },
        onEnd: () => {
          if (!hadFinalRef.current && !isError) {
            setMessage('Recognition stopped. No details captured — try again or enter the details manually.')
          }
          recRef.current = null
          setListening(false)
        },
      })

      rec.start()
      setListening(true)
    } catch {
      recRef.current = null
      setListening(false)
      setIsError(true)
      setMessage('Could not start voice registration. Try again or register manually.')
    }
  }

  return (
    <div className="mb-5">
      {!supported ? (
        <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
          <p className="text-sm text-gray-600">
            🎤 Voice registration isn't supported in this browser. You can still create an account manually below.
          </p>
        </div>
      ) : (
        <>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={listening ? stopListening : startListening}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                listening
                  ? 'bg-red-50 text-red-600 border border-red-200 hover:bg-red-100'
                  : 'bg-primary-50 text-primary-700 border border-primary-200 hover:bg-primary-100'
              }`}
            >
              {listening ? '⏹ Stop' : '🎤 Voice Registration'}
            </button>
            {listening && <span className="animate-pulse text-sm text-red-500 font-medium">Listening…</span>}
          </div>

          <p className="text-xs text-gray-500 mt-2">
            Speak in a simple format, e.g. “Name: John Doe”, “Email: john at gmail dot com”,
            “Phone: nine eight seven six five four three two one zero”.
          </p>

          {transcript && (
            <div className="mt-3">
              <label className="block text-xs font-medium text-gray-500 mb-1">Recognized transcript</label>
              <textarea
                readOnly
                value={transcript}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-gray-50 text-gray-700 outline-none resize-none"
              />
            </div>
          )}

          {message && (
            <div
              className={`mt-2 px-3 py-2 rounded-lg text-sm ${
                isError ? 'bg-red-50 border border-red-200 text-red-700' : 'bg-blue-50 border border-blue-200 text-blue-700'
              }`}
            >
              {message}
            </div>
          )}

          <p className="text-[11px] text-gray-400 mt-2">
            Your voice is only used to pre-fill the fields below. Nothing is recorded or uploaded.
            Review and edit the fields before submitting.
          </p>
        </>
      )}
    </div>
  )
}