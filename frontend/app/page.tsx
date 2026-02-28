'use client'

import { useState } from 'react'
import LanguageSelection from '@/components/LanguageSelection'
import LandingPage from '@/components/LandingPage'
import ChatInterface from '@/components/ChatInterface'

type Language = 'en' | 'hi' | 'mr' | 'ta' | 'te' | 'pa' | 'haryanvi'

export default function Home() {
  const [selectedLanguage, setSelectedLanguage] = useState<Language | null>(null)
  const [showChat, setShowChat] = useState(false)

  if (!selectedLanguage) {
    return <LanguageSelection onSelectLanguage={setSelectedLanguage} />
  }

  if (showChat) {
    return (
      <ChatInterface
        language={selectedLanguage}
        onBack={() => setShowChat(false)}
        onChangeLanguage={() => setSelectedLanguage(null)}
      />
    )
  }

  return (
    <LandingPage
      language={selectedLanguage}
      onChatClick={() => setShowChat(true)}
      onChangeLanguage={() => setSelectedLanguage(null)}
    />
  )
}
