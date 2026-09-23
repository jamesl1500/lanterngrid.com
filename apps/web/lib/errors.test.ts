import { toProblem } from './errors'

describe('toProblem', () => {
  it('passes through a plain error message', () => {
    expect(toProblem({ detail: 'That username is taken.' })).toEqual({
      message: 'That username is taken.',
      fields: {},
    })
  })

  it('maps validation errors to their fields', () => {
    const problem = toProblem({
      detail: [
        { loc: ['body', 'username'], msg: 'Value error, That username is reserved.' },
        { loc: ['body', 'password'], msg: 'String should have at least 10 characters' },
      ],
    })
    expect(problem.fields).toEqual({
      username: 'That username is reserved.',
      password: 'String should have at least 10 characters',
    })
  })

  it('falls back for anything else', () => {
    expect(toProblem(undefined).message).toMatch(/Something went wrong/)
  })
})
