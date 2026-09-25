import type { Metadata } from 'next'
import { Chakra_Petch, IBM_Plex_Sans, JetBrains_Mono } from 'next/font/google'
import type { ReactNode } from 'react'

import { SiteHeader } from '@/components/site-header'
import { VerifyBanner } from '@/components/verify-banner'

import './globals.css'
import { Providers } from './providers'

const chakra = Chakra_Petch({
  subsets: ['latin'],
  weight: ['500', '600', '700'],
  variable: '--font-chakra',
})
const plex = IBM_Plex_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-plex',
})
const jetbrains = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '700'],
  variable: '--font-jetbrains',
})

export const metadata: Metadata = {
  title: { default: 'Lantern Grid', template: '%s · Lantern Grid' },
  description: 'The social network for software engineers. Share updates, code and wins.',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="en"
      data-theme="dark"
      className={`${chakra.variable} ${plex.variable} ${jetbrains.variable}`}
    >
      {/* Pages marked data-fill-screen (chat) take exactly the space left under the header. */}
      <body className="min-h-dvh has-data-fill-screen:flex has-data-fill-screen:h-dvh has-data-fill-screen:flex-col">
        <Providers>
          <SiteHeader />
          <VerifyBanner />
          {children}
        </Providers>
      </body>
    </html>
  )
}
