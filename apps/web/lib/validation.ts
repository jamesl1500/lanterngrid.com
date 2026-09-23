import { z } from 'zod'

import { LINK_KINDS, MAX_LINKS } from './links'
import { MAX_TAGS } from './tags'

// Mirrors the API's rules so people see problems before submitting. The API still decides.
export const USERNAME_PATTERN = /^[A-Za-z0-9](?:[A-Za-z0-9_-]{1,28}[A-Za-z0-9])$/

export const email = z.string().trim().email('Enter a valid email address.')
export const password = z
  .string()
  .min(10, 'Use at least 10 characters.')
  .max(128, 'Use at most 128 characters.')
export const displayName = z
  .string()
  .trim()
  .min(1, 'Tell people what to call you.')
  .max(50, 'Keep it under 50 characters.')
export const username = z
  .string()
  .trim()
  .regex(
    USERNAME_PATTERN,
    'Use 3 to 30 letters, numbers, dashes or underscores, starting and ending with a letter or number.',
  )
export const headline = z.string().trim().max(120, 'Keep it under 120 characters.')

export const signInSchema = z.object({ email, password: z.string().min(1, 'Enter your password.') })
export const signUpSchema = z.object({ display_name: displayName, email, password })
export const forgotPasswordSchema = z.object({ email })
export const resetPasswordSchema = z.object({ password })
export const onboardingSchema = z.object({
  username,
  display_name: displayName,
  headline,
  tags: z.array(z.string()).max(MAX_TAGS, `Pick up to ${MAX_TAGS} tags.`),
})

const httpUrl = (max: number) =>
  z
    .string()
    .trim()
    .max(max, `Keep it under ${max} characters.`)
    .refine(
      (v) => v === '' || /^https?:\/\/\S+\.\S+/.test(v),
      'Use a full link, like https://you.dev',
    )
export const profileSchema = z.object({
  display_name: displayName,
  headline,
  bio: z.string().trim().max(1000, 'Keep it under 1000 characters.'),
  location: z.string().trim().max(80, 'Keep it under 80 characters.'),
  website: httpUrl(200),
  accent_color: z.enum(['cyan', 'violet', 'lime', 'amber', 'magenta', 'coral']),
})

export const linksSchema = z.object({
  links: z
    .array(
      z.object({
        kind: z.enum(LINK_KINDS),
        url: httpUrl(300).refine((v) => v !== '', 'Add the link, or remove this row.'),
      }),
    )
    .max(MAX_LINKS, `Add up to ${MAX_LINKS} links.`),
})
