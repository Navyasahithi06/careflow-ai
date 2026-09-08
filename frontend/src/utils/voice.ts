/**
 * Lightweight voice-input parsing for patient registration.
 *
 * Scope:
 * - Field-by-field speech ("Name: John Doe", "Email: john at gmail dot com", "Phone: nine eight seven six ...")
 * - One structured sentence ("My name is ..., my email is ..., and my phone number is ...")
 *
 * Normalization:
 * - Email: " at " -> "@", " dot " -> "."; the match must look like a real email (never invented).
 * - Phone: unambiguous spoken number words -> digits; requires a clean 7-15 digit run (10 preferred).
 * - Name: recognized words kept as spoken (no aggressive transformation).
 *
 * This is intentionally NOT a general NLP parser and adds no AI/LLM dependency. When a value
 * cannot be confidently mapped it is left empty so the user can enter it manually.
 */

export interface VoiceDraft {
  fullName: string
  email: string
  phone: string
}

export interface RegistrationFields {
  fullName: string
  email: string
  phone: string
}

export type VoiceRecognitionStatus = 'idle' | 'listening' | 'error' | 'done' | 'unsupported'

export interface SpeechRecognitionEventLike {
  results: ArrayLike<{
    isFinal?: boolean
    0?: { transcript?: string }
  }>
}

export interface SpeechRecognitionLike {
  lang?: string
  continuous?: boolean
  interimResults?: boolean
  onresult: ((event: SpeechRecognitionEventLike) => void) | null
  onerror: ((event: { error?: string }) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
  abort?: () => void
}

export interface SpeechRecognitionHandlers {
  onResult: (transcript: string, isFinal: boolean) => void
  onError: (errorMessage: string) => void
  onEnd: () => void
}

export interface SpeechRecognitionGlobals {
  SpeechRecognition?: new () => SpeechRecognitionLike
  webkitSpeechRecognition?: new () => SpeechRecognitionLike
}

export function detectSpeechSupport(win?: SpeechRecognitionGlobals): boolean {
  return Boolean(win && (win.SpeechRecognition || win.webkitSpeechRecognition))
}

const EMAIL_RE = /[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}/

const NUMBER_WORDS: Record<string, string> = {
  zero: '0',
  one: '1',
  two: '2',
  three: '3',
  four: '4',
  five: '5',
  six: '6',
  seven: '7',
  eight: '8',
  nine: '9',
}

export function expandSpokenNumbers(text: string): string {
  const words = text.split(/\s+/)
  const out: string[] = []
  for (let i = 0; i < words.length; i++) {
    const word = words[i].toLowerCase().replace(/[^a-z]/g, '')
    const nextWord = (words[i + 1] || '').toLowerCase()
    if ((word === 'double' || word === 'triple') && NUMBER_WORDS[nextWord] !== undefined) {
      const base = NUMBER_WORDS[nextWord]
      out.push(base.repeat(word === 'double' ? 2 : 3))
      i++
    } else if (NUMBER_WORDS[word] !== undefined) {
      out.push(NUMBER_WORDS[word])
    } else {
      out.push(words[i])
    }
  }
  return out.join(' ').replace(/(\d)\s+(?=\d)/g, '$1')
}

function normalizeEmailText(text: string): string {
  return text
    .replace(/\s*[Aa][Tt]\s+/g, '@')
    .replace(/\s*[Dd][Oo][Tt]\s+/g, '.')
    .replace(/\s*@\s*/g, '@')
    .replace(/\s*\.\s*/g, '.')
    .trim()
}

export function parseEmail(text: string): string {
  const match = normalizeEmailText(text).match(EMAIL_RE)
  return match ? match[0] : ''
}

export function parsePhone(text: string): string {
  const expanded = expandSpokenNumbers(text)
  const segments = expanded.split(/[^\d]+/).filter(Boolean)
  let best = ''
  for (const seg of segments) {
    if (seg.length === 10) return seg
    if (seg.length >= 7 && seg.length <= 15 && seg.length > best.length) {
      best = seg
    }
  }
  return best
}

type VoiceDraftField = 'name' | 'email' | 'phone'

const LABEL_SCAN_RE =
  /\b(?:(?:my\s+)?name|my\s+email(?:\s+address)?|email(?:\s+address)?|my\s+phone(?:\s+number)?|phone(?:\s+number)?)\s*(?::|\bis\b)\s*/gi

function scanLabels(text: string): Array<{ field: VoiceDraftField; value: string }> {
  interface Hit {
    index: number
    headEnd: number
    field: VoiceDraftField
  }
  const hits: Hit[] = []
  let m: RegExpExecArray | null
  const re = new RegExp(LABEL_SCAN_RE.source, 'gi')
  while ((m = re.exec(text)) !== null) {
    const matched = m[0].toLowerCase()
    let field: VoiceDraftField = 'name'
    if (matched.includes('email')) field = 'email'
    else if (matched.includes('phone')) field = 'phone'
    hits.push({ index: m.index, headEnd: m.index + m[0].length, field })
    if (m.index === re.lastIndex) re.lastIndex++
  }
  const segments: Array<{ field: VoiceDraftField; value: string }> = []
  for (let i = 0; i < hits.length; i++) {
    const start = hits[i].headEnd
    const end = i + 1 < hits.length ? hits[i + 1].index : text.length
    segments.push({ field: hits[i].field, value: text.slice(start, end).trim() })
  }
  return segments
}

function tidyValue(value: string): string {
  return value
    .replace(/\s*and\s+[^\s,;]*\s*$/i, '')
    .replace(/[\s,.;:]+$/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

export function parseTranscript(text: string): VoiceDraft {
  const cleaned = text.replace(/\s+/g, ' ').trim()
  const draft: VoiceDraft = { fullName: '', email: '', phone: '' }
  const segments = scanLabels(cleaned)

  for (const segment of segments) {
    if (segment.field === 'name') {
      if (!draft.fullName) draft.fullName = tidyValue(segment.value)
    } else if (segment.field === 'email') {
      if (!draft.email) draft.email = parseEmail(segment.value)
    } else if (!draft.phone) {
      draft.phone = parsePhone(segment.value)
    }
  }

  if (!segments.length) {
    if (!draft.email) draft.email = parseEmail(cleaned)
    if (!draft.phone) draft.phone = parsePhone(cleaned)
  }

  return draft
}

export function mergeDraft(draft: VoiceDraft, fields: RegistrationFields): RegistrationFields {
  return {
    fullName: draft.fullName ? draft.fullName : fields.fullName,
    email: draft.email ? draft.email : fields.email,
    phone: draft.phone ? draft.phone : fields.phone,
  }
}

const ERROR_MESSAGES: Record<string, string> = {
  'not-allowed': 'Microphone permission was denied. Enable the microphone in your browser and try again, or register manually.',
  'service-not-allowed': 'Microphone permission was denied. Enable the microphone in your browser and try again, or register manually.',
  'no-speech': 'No speech was detected. Speak clearly or register manually.',
  network: 'Speech recognition is temporarily unavailable (network). Try again or register manually.',
  aborted: 'Voice registration was stopped.',
  'audio-capture': 'No microphone was detected. Check your microphone and try again, or register manually.',
  'language-not-supported': 'Speech recognition is not available for this language.',
  'bad-grammar': 'Speech recognition failed to start. Try again or register manually.',
}

export function humanizeError(code: string): string {
  return ERROR_MESSAGES[code] || `Speech recognition failed (${code || 'unknown'}). Try again or register manually.`
}

export function createRecognitionSession(
  rec: SpeechRecognitionLike,
  handlers: SpeechRecognitionHandlers,
): SpeechRecognitionLike {
  rec.continuous = true
  rec.interimResults = true
  rec.lang = 'en-IN'

  rec.onresult = (event) => {
    let interim = ''
    let final = ''
    for (let i = 0; i < event.results.length; i++) {
      const result = event.results[i]
      const transcript = (result && result[0] && result[0].transcript) || ''
      if (result.isFinal) final += transcript
      else interim += transcript
    }
    const text = (final || interim).trim()
    if (text) handlers.onResult(text, Boolean(final))
  }

  rec.onerror = (event) => {
    handlers.onError(humanizeError((event && event.error) || 'unknown'))
  }

  rec.onend = () => handlers.onEnd()

  return rec
}