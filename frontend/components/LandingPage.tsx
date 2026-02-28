'use client'

import { motion } from 'framer-motion'
import { ChevronDown, MessageCircle, Globe } from 'lucide-react'
import { getContentForLanguage } from '@/lib/content'
import Image from 'next/image'

type Language = 'en' | 'hi' | 'mr' | 'ta' | 'te' | 'pa' | 'haryanvi'

interface LandingPageProps {
  language: Language
  onChatClick: () => void
  onChangeLanguage: () => void
}

export default function LandingPage({ language, onChatClick, onChangeLanguage }: LandingPageProps) {
  const content = getContentForLanguage(language)

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: 'spring',
        stiffness: 100,
        damping: 12,
      },
    },
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-secondary/30 to-background">
      {/* Header */}
      <motion.header
        className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-border"
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-3xl">🌾</span>
            <h1 className="text-2xl font-bold text-primary">Kisan Yojana Sahayak</h1>
          </div>
          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onChangeLanguage}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary text-foreground hover:bg-secondary/80 transition-colors"
            >
              <Globe size={18} />
              <span className="text-sm font-medium">{language.toUpperCase()}</span>
            </motion.button>
          </div>
        </div>
      </motion.header>

      {/* Main content */}
      <motion.main
        className="max-w-5xl mx-auto px-4 py-16"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Hero image section */}
        <motion.section variants={itemVariants} className="mb-16 rounded-2xl overflow-hidden">
          <div className="relative h-64 md:h-80 w-full">
            <Image
              src="/hero-farmer.jpg"
              alt="Farmer using Kisan Yojana Sahayak"
              fill
              className="object-cover"
              priority
            />
          </div>
        </motion.section>

        {/* Hero section */}
        <motion.section variants={itemVariants} className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-primary mb-6 leading-tight">
            {content.title}
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed max-w-3xl mx-auto">
            {content.subtitle}
          </p>
        </motion.section>

        {/* How to use section */}
        <motion.section variants={itemVariants} className="mb-16">
          <h3 className="text-2xl font-bold text-primary mb-8">{content.howToUseTitle}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {content.howToUse.map((item, index) => (
              <motion.div
                key={index}
                variants={itemVariants}
                className="p-6 rounded-xl bg-white border-2 border-border hover:border-accent hover:shadow-lg transition-all duration-300"
                whileHover={{ y: -5 }}
              >
                <div className="text-3xl mb-3">{item.icon}</div>
                <h4 className="font-bold text-primary mb-2">{item.title}</h4>
                <p className="text-sm text-muted-foreground">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </motion.section>

        {/* Features section */}
        <motion.section variants={itemVariants} className="mb-16 bg-gradient-to-br from-primary/5 to-accent/5 p-8 rounded-2xl border border-border">
          <h3 className="text-2xl font-bold text-primary mb-8">{content.featuresTitle}</h3>
          <div className="space-y-4">
            {content.features.map((feature, index) => (
              <motion.div
                key={index}
                variants={itemVariants}
                className="flex items-start gap-4"
              >
                <span className="text-2xl flex-shrink-0">{feature.icon}</span>
                <div>
                  <h4 className="font-bold text-foreground">{feature.title}</h4>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.section>

        {/* Support section */}
        <motion.section variants={itemVariants} className="bg-white rounded-2xl border-2 border-primary p-8 mb-16">
          <h3 className="text-2xl font-bold text-primary mb-6">{content.supportTitle}</h3>
          <div className="space-y-4">
            {content.support.map((item, index) => (
              <motion.div
                key={index}
                variants={itemVariants}
                className="flex items-center justify-between p-4 bg-secondary rounded-lg hover:bg-secondary/80 transition-colors"
              >
                <div>
                  <p className="font-medium text-foreground">{item.type}</p>
                  <p className="text-sm text-muted-foreground">{item.contact}</p>
                </div>
                <span className="text-2xl">{item.icon}</span>
              </motion.div>
            ))}
          </div>
        </motion.section>

        {/* CTA Section */}
        <motion.section variants={itemVariants} className="text-center mb-16">
          <p className="text-lg text-muted-foreground mb-6">{content.ctaText}</p>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onChatClick}
            className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-primary to-primary/90 text-accent rounded-full font-bold text-lg hover:shadow-lg transition-all duration-300"
          >
            <MessageCircle size={24} />
            {content.chatButtonText}
          </motion.button>
        </motion.section>
      </motion.main>

      {/* Footer */}
      <motion.footer
        className="border-t border-border bg-white/50 backdrop-blur-sm py-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <div className="max-w-5xl mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>{content.footerText}</p>
        </div>
      </motion.footer>
    </div>
  )
}
