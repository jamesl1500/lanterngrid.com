import { reasonSummary, subjectHref, subjectName, type ModerationCase } from './moderation'

const base: ModerationCase = {
  id: 'c1',
  subject_kind: 'post',
  subject_id: 'p1',
  subject_author: {
    id: 'u1',
    username: 'ada',
    display_name: 'Ada',
    headline: null,
    avatar_url: null,
    accent_color: 'cyan',
  },
  author_suspended: false,
  post_id: null,
  snapshot: 'Buy followers',
  subject_gone: false,
  status: 'open',
  report_count: 1,
  reports: [],
  created_at: '2026-10-10T12:00:00Z',
  resolved_at: null,
  resolved_by: null,
  note: null,
}

describe('subjectHref', () => {
  it('links each kind to where it lives', () => {
    expect(subjectHref(base)).toBe('/p/p1')
    expect(subjectHref({ ...base, subject_kind: 'comment', subject_id: 'k1', post_id: 'p1' })).toBe(
      '/p/p1#comment-k1',
    )
    expect(subjectHref({ ...base, subject_kind: 'snippet', subject_id: 's1' })).toBe('/snippets/s1')
    expect(subjectHref({ ...base, subject_kind: 'user', subject_id: 'u1' })).toBe('/u/ada')
  })

  it("doesn't link private messages or deleted accounts", () => {
    expect(subjectHref({ ...base, subject_kind: 'message' })).toBeNull()
    expect(subjectHref({ ...base, subject_kind: 'user', subject_author: null })).toBeNull()
  })
})

describe('reasonSummary', () => {
  it('counts reasons, most common first', () => {
    const reports = [
      { reason: 'hate' as const },
      { reason: 'spam' as const },
      { reason: 'spam' as const },
    ]
    expect(reasonSummary(reports)).toBe('Spam ×2, Hate')
  })
})

describe('subjectName', () => {
  it('names things and people', () => {
    expect(subjectName('post')).toBe('this post')
    expect(subjectName('user', 'ada')).toBe('@ada')
  })
})
