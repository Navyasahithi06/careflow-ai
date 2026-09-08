import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  detectSpeechSupport,
  expandSpokenNumbers,
  humanizeError,
  parseEmail,
  parsePhone,
  parseTranscript,
  mergeDraft,
  createRecognitionSession,
  type SpeechRecognitionLike,
} from '../src/utils/voice.ts'

function fakeRec(): SpeechRecognitionLike {
  return {
    continuous: false,
    interimResults: false,
    onresult: null,
    onerror: null,
    onend: null,
    start: () => {},
    stop: () => {},
  }
}

test('detectSpeechSupport: unavailable', () => {
  assert.equal(detectSpeechSupport(undefined), false)
  assert.equal(detectSpeechSupport({}), false)
  assert.equal(detectSpeechSupport({ SpeechRecognition: undefined, webkitSpeechRecognition: undefined }), false)
})

test('detectSpeechSupport: available via prefixed/native constructors', () => {
  class MockRec {}
  assert.equal(detectSpeechSupport({ webkitSpeechRecognition: MockRec as never }), true)
  assert.equal(detectSpeechSupport({ SpeechRecognition: MockRec as never }), true)
})

test('expandSpokenNumbers: words, double, triple', () => {
  assert.equal(expandSpokenNumbers('nine eight seven six five four three two one zero'), '9876543210')
  assert.equal(expandSpokenNumbers('double zero one two'), '0012')
  assert.equal(expandSpokenNumbers('triple five'), '555')
  assert.equal(expandSpokenNumbers('John Doe and phone'), 'John Doe and phone')
})

test('parseEmail: spoken "at/dot" normalization', () => {
  assert.equal(parseEmail('john dot doe at gmail dot com'), 'john.doe@gmail.com')
  assert.equal(parseEmail('my email is john at gmail dot com'), 'john@gmail.com')
  assert.equal(parseEmail('email: sarah@clinic.io now'), 'sarah@clinic.io')
})

test('parseEmail: ambiguous input yields empty (no guessing)', () => {
  assert.equal(parseEmail('John Doe nine eight seven'), '')
  assert.equal(parseEmail(''), '')
})

test('parsePhone: spoken words, digits, spaced digits', () => {
  assert.equal(parsePhone('nine eight seven six five four three two one zero'), '9876543210')
  assert.equal(parsePhone('phone number is 9876543210'), '9876543210')
  assert.equal(parsePhone('9 8 7 6 5 4 3 2 1 0'), '9876543210')
  assert.equal(parsePhone('double nine one zero zero zero four'), '9910004')
})

test('parsePhone: ambiguous/incomplete yields empty', () => {
  assert.equal(parsePhone('John Doe'), '')
  assert.equal(parsePhone(''), '')
  assert.equal(parsePhone('double nine one zero zero'), '')
})

test('parseTranscript: field-by-field labels (preferred style)', () => {
  const text = 'Name: John Doe. Email: john dot doe at gmail dot com. Phone: nine eight seven six five four three two one zero'
  const d = parseTranscript(text)
  assert.equal(d.fullName, 'John Doe')
  assert.equal(d.email, 'john.doe@gmail.com')
  assert.equal(d.phone, '9876543210')
})

test('parseTranscript: one structured sentence', () => {
  const text =
    'My name is John Doe, my email is john dot doe at gmail dot com, and my phone number is nine eight seven six five four three two one zero'
  const d = parseTranscript(text)
  assert.equal(d.fullName, 'John Doe')
  assert.equal(d.email, 'john.doe@gmail.com')
  assert.equal(d.phone, '9876543210')
})

test('parseTranscript: inline labels without punctuation', () => {
  const text = 'Name: John Doe Email: john at gmail dot com Phone: 9876543210'
  const d = parseTranscript(text)
  assert.equal(d.fullName, 'John Doe')
  assert.equal(d.email, 'john@gmail.com')
  assert.equal(d.phone, '9876543210')
})

test('parseTranscript: incomplete utterance leaves empty field for manual entry', () => {
  const d = parseTranscript('Name: Riya Patel')
  assert.equal(d.fullName, 'Riya Patel')
  assert.equal(d.email, '')
  assert.equal(d.phone, '')
})

test('parseTranscript: matches user example email local part with dot', () => {
  const d = parseTranscript('Email: john dot doe at gmail dot com')
  assert.equal(d.email, 'john.doe@gmail.com')
})

test('mergeDraft: preserves existing fields, overrides non-empty', () => {
  assert.deepEqual(
    mergeDraft({ fullName: 'New User', email: '', phone: '' }, { fullName: 'Old', email: 'old@x.com', phone: '123' }),
    { fullName: 'New User', email: 'old@x.com', phone: '123' },
  )
  assert.deepEqual(
    mergeDraft({ fullName: '', email: '', phone: '' }, { fullName: 'Old', email: 'old@x.com', phone: '123' }),
    { fullName: 'Old', email: 'old@x.com', phone: '123' },
  )
})

test('humanizeError: permission denied / no speech / fallback', () => {
  assert.match(humanizeError('not-allowed'), /permission/i)
  assert.match(humanizeError('service-not-allowed'), /permission/i)
  assert.match(humanizeError('no-speech'), /No speech/i)
  assert.match(humanizeError('weird-code'), /recognition failed/i)
})

test('createRecognitionSession: wires handlers and recognition never auto-submits', () => {
  const rec = fakeRec()
  const calls: Array<[string, boolean]> = []
  const errors: string[] = []
  let ended = false
  createRecognitionSession(rec, {
    onResult: (t, f) => calls.push([t, f]),
    onError: (e) => errors.push(e),
    onEnd: () => (ended = true),
  })
  assert.equal(rec.continuous, true)
  assert.equal(rec.interimResults, true)
  assert.equal((rec as SpeechRecognitionLike).lang, 'en-IN')

// interim result -> isFinal false
  rec.onresult({ results: [{ isFinal: false, 0: { transcript: 'Name: John ' } }] })
  // final result carries the full committed utterance -> isFinal true
  rec.onresult({ results: [{ isFinal: true, 0: { transcript: 'Name: John Doe' } }] })
  assert.equal(calls.length, 2)
  assert.equal(calls[0][1], false)
  assert.deepEqual(calls[1], ['Name: John Doe', true])

  // empty result ignored
  rec.onresult({ results: [{ isFinal: true, 0: { transcript: '   ' } }] })
  assert.equal(calls.length, 2)
})

test('createRecognitionSession: recognition error surfaces message', () => {
  const rec = fakeRec()
  const errors: string[] = []
  createRecognitionSession(rec, { onResult: () => {}, onError: (e) => errors.push(e), onEnd: () => {} })
  rec.onerror({ error: 'not-allowed' })
  assert.equal(errors.length, 1)
  assert.match(errors[0], /permission/i)
})

test('createRecognitionSession: end fires onEnd', () => {
  const rec = fakeRec()
  let ended = false
  createRecognitionSession(rec, { onResult: () => {}, onError: () => {}, onEnd: () => (ended = true) })
  rec.onend()
  assert.equal(ended, true)
})