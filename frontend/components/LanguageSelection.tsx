'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

type Language = 'en' | 'hi' | 'mr' | 'ta' | 'te' | 'pa' | 'haryanvi'

interface LanguageSelectionProps {
  onSelectLanguage: (language: Language) => void
}

const languages: { code: Language; name: string; flag: string; nativeName: string }[] = [
  { code: 'en', name: 'English', flag: '🌍', nativeName: 'English' },
  { code: 'hi', name: 'हिंदी', flag: '🌾', nativeName: 'हिंदी' },
  { code: 'mr', name: 'मराठी', flag: '🌿', nativeName: 'मराठी' },
  { code: 'ta', name: 'தமிழ்', flag: '🌱', nativeName: 'தமிழ்' },
  { code: 'te', name: 'తెలుగు', flag: '🚜', nativeName: 'తెలుగు' },
  { code: 'pa', name: 'ਪੰਜਾਬੀ', flag: '🌾', nativeName: 'ਪੰਜਾਬੀ' },
  { code: 'haryanvi', name: 'हरियाणवी', flag: '🌾', nativeName: 'हरियाणवी' },
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
}

const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.9 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 12,
    },
  },
  hover: {
    scale: 1.05,
    y: -5,
    transition: {
      type: 'spring',
      stiffness: 400,
      damping: 10,
    },
  },
  tap: {
    scale: 0.95,
  },
}

export default function LanguageSelection({ onSelectLanguage }: LanguageSelectionProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-secondary to-background p-4 overflow-hidden">
      {/* Decorative elements */}
      <div className="absolute top-10 left-10 w-32 h-32 rounded-full bg-accent/10 blur-3xl"></div>
      <div className="absolute bottom-10 right-10 w-40 h-40 rounded-full bg-primary/10 blur-3xl"></div>

      <motion.div
        className="relative z-10 max-w-4xl mx-auto"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* Header */}
        <div className="text-center mb-12">
          <motion.h1
            className="text-5xl md:text-6xl font-bold text-primary mb-4"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            🌾 Kisan Yojana Sahayak
          </motion.h1>
          <motion.p
            className="text-lg text-muted-foreground mb-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            Government Schemes for Farmers
          </motion.p>
          <motion.div
            className="h-1 w-24 bg-gradient-to-r from-primary to-accent rounded-full mx-auto"
            initial={{ width: 0 }}
            animate={{ width: 96 }}
            transition={{ duration: 0.8, delay: 0.3 }}
          ></motion.div>
        </div>

        {/* Language selection text */}
        <motion.p
          className="text-center text-muted-foreground mb-8"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          Select your language to get started
        </motion.p>

        {/* Language cards grid */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {languages.map((lang) => (
            <motion.button
              key={lang.code}
              variants={cardVariants}
              whileHover="hover"
              whileTap="tap"
              onClick={() => onSelectLanguage(lang.code)}
              className="relative group p-6 rounded-2xl bg-white border-2 border-border hover:border-accent cursor-pointer transition-all duration-300 shadow-sm hover:shadow-lg"
            >
              {/* Gradient background on hover */}
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary/5 to-accent/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>

              <div className="relative z-10">
                <div className="text-5xl mb-3">{lang.flag}</div>
                <h3 className="text-xl font-bold text-primary mb-1">{lang.name}</h3>
                <p className="text-sm text-muted-foreground">{lang.nativeName}</p>
              </div>

              {/* Animated shine effect */}
              <motion.div
                className="absolute inset-0 rounded-2xl bg-gradient-to-r from-transparent via-white to-transparent opacity-0 group-hover:opacity-20"
                initial={{ x: '-100%' }}
                whileHover={{ x: '100%' }}
                transition={{ duration: 0.5 }}
              ></motion.div>
            </motion.button>
          ))}
        </motion.div>

        {/* Footer info */}
        <motion.div
          className="mt-12 text-center text-sm text-muted-foreground"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.5 }}
        >
          <p>Available in 7 Indian languages • Farmer-friendly interface</p>
        </motion.div>
      </motion.div>
    </div>
  )
}
