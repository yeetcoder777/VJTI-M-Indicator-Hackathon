'use client'

import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, ArrowLeft, Globe, X, Mic, Square, MapPin } from 'lucide-react'

type Language = 'en' | 'hi' | 'mr' | 'ta' | 'te' | 'pa' | 'haryanvi'

interface ChatInterfaceProps {
  language: Language
  onBack: () => void
  onChangeLanguage: () => void
}

interface Message {
  id: string
  text: React.ReactNode
  sender: 'user' | 'bot'
  timestamp: Date
  attachment?: string
}

const greetings: Record<Language, { greeting: React.ReactNode; placeholder: string; sendButton: string }> = {
  en: {
    greeting: <>Hello! 👋 I&apos;m your <span className="text-black font-bold">Kisan Yojana Assistant</span>. How can I help you find the right government schemes today?</>,
    placeholder: 'Type your question here...',
    sendButton: 'Send',
  },
  hi: {
    greeting: <>नमस्ते! 👋 मैं आपका <span className="text-black font-bold">किसान योजना सहायक</span> हूँ। आज मैं आपको कौन सी सरकारी योजना खोजने में मदद कर सकता हूँ?</>,
    placeholder: 'अपना सवाल यहाँ लिखें...',
    sendButton: 'भेजें',
  },
  mr: {
    greeting: <>नमस्कार! 👋 मी तुमचा <span className="text-black font-bold">किसान योजना सहायक</span> आहे. आज मी तुम्हाला कोणत्या सरकारी योजना शोधण्यात मदत करू शकतो?</>,
    placeholder: 'आपला प्रश्न येथे लिहा...',
    sendButton: 'पाठवा',
  },
  ta: {
    greeting: <>வணக்கம்! 👋 நான் உங்கள் <span className="text-black font-bold">கிसான் யோஜனா உதவிக்கர்</span>. இன்று எந்த அரசு திட்டத்தை கண்டறிய உதவ முடியும்?</>,
    placeholder: 'உங்கள் கேள்வியை இங்கே எழுதுங்கள்...',
    sendButton: 'அனுப்பு',
  },
  te: {
    greeting: <>స్వాగతం! 👋 నేను మీ <span className="text-black font-bold">కిసాన్ యోజన సహాయకుడిని</span>. ఈ రోజు మీకు ఏ ప్రభుత్వ పథకం కనుగొనడంలో సహాయం చేయగలను?</>,
    placeholder: 'మీ ప్రశ్నను ఇక్కడ టైప్ చేయండి...',
    sendButton: 'పంపించు',
  },
  pa: {
    greeting: <>ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! 👋 ਮੈਂ ਤੁਹਾਡਾ <span className="text-black font-bold">ਕਿਸਾਨ ਯੋਜਨਾ ਸਹਾਇਕ</span> ਹਾਂ। ਅੱਜ ਮੈਂ ਤੁਹਾਨੂੰ ਕਿਹੜੀ ਸਰਕਾਰੀ ਸਕੀਮ ਖੋਜਣ ਵਿਚ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?</>,
    placeholder: 'ਆਪਣਾ ਸਵਾਲ ਇੱਥੇ ਲਿਖੋ...',
    sendButton: 'ਭੇਜੋ',
  },
  haryanvi: {
    greeting: <>नमस्ते! 👋 मैं तुम्हारा <span className="text-black font-bold">किसान योजना सहायक</span> हूँ। आज मैं तुम्हारी कौन सी सरकारी योजना खोजने में मदद कर सकता हूँ?</>,
    placeholder: 'अपना सवाल यहाँ लिखो...',
    sendButton: 'भेजो',
  },
}

const botResponses: Record<Language, string[]> = {
  en: [
    'That\'s a great question! Let me help you find the right scheme.',
    'I understand. Based on your needs, you might be eligible for several schemes.',
    'Let me gather more information to provide you the best recommendation.',
    'Thank you for sharing that. This is helpful information.',
    'Would you like to know more details about any specific scheme?',
  ],
  hi: [
    'यह एक बहुत अच्छा सवाल है! मुझे आपको सही योजना खोजने में मदद करने दें।',
    'मैं समझता हूँ। आपकी जरूरतों के आधार पर, आप कई योजनाओं के लिए पात्र हो सकते हैं।',
    'मुझे अधिक जानकारी इकट्ठा करने दें।',
    'आपकी जानकारी साझा करने के लिए धन्यवाद।',
    'क्या आप किसी विशेष योजना के बारे में अधिक जानना चाहते हैं?',
  ],
  mr: [
    'हा एक चांगला प्रश्न आहे! मला तुम्हाला योग्य योजना शोधण्यात मदत करू द्या.',
    'मी समजतो. तुमच्या गरजांवर आधारित, तुम्ही अनेक योजनांसाठी पात्र असू शकता.',
    'मला अधिक माहिती गोळा करू द्या.',
    'आपली माहिती शेअर केल्याबद्दल धन्यवाद.',
    'तुम्हाला कोणत्या विशेष योजनाबद्दल अधिक जाणून घ्यायचे आहे?',
  ],
  ta: [
    'அது ஒரு பெரிய கேள்வி! சரியான திட்டத்தை கண்டறிய உதவ விடுங்கள்.',
    'நான் புரிந்துகொள்ளுகிறேன். உங்கள் தேவைகளின் அடிப்படையில், நீங்கள் பல திட்டங்களுக்கு தகுதியுடையவர் இருக்கலாம்.',
    'மேலும் தகவல் சேகரிக்க விடுங்கள்.',
    'உங்கள் தகவல் பகிர்ந்தமைக்கு நன்றி.',
    'ஏதேனும் குறிப்பிட்ட திட்டம் பற்றி மேலும் அறிய விரும்புகிறீர்களா?',
  ],
  te: [
    'ఇది ఒక గొప్ప ప్రశ్న! సరైన పథకం కనుగొనడంలో సహాయం చేయనివ్వండి.',
    'నేను అర్థం చేసుకున్నాను. మీ అవసరాల ఆధారంగా, మీరు అనేక పథకాలకు అర్హులు కావచ్చు.',
    'మరిన్ని సమాచారం సేకరించనివ్వండి.',
    'మీ సమాచారం భాగస్వామ్యం చేసినందుకు ధన్యవాదాలు.',
    'ఏదైనా నిర్దిష్ట పథకం గురించి మరిన్ని తెలుసుకోవాలనుకుంటున్నారా?',
  ],
  pa: [
    'ਇਹ ਇੱਕ ਵਧੀਆ ਸਵਾਲ ਹੈ! ਮੈਨੂੰ ਤੁਹਾਨੂੰ ਸਹੀ ਸਕੀਮ ਖੋਜਣ ਵਿਚ ਮਦਦ ਕਰਨ ਦਿਓ।',
    'ਮੈਂ ਸਮਝ ਗਿਆ ਹਾਂ। ਤੁਹਾਡੀ ਜ਼ਰੂਰਤਾਂ ਦੇ ਆਧਾਰ ਤੇ, ਤੁਸੀਂ ਕਈ ਸਕੀਮਾਂ ਲਈ ਯੋਗ ਹੋ ਸਕਦੇ ਹੋ।',
    'ਮੈਨੂੰ ਹੋਰ ਜਾਣਕਾਰੀ ਇਕੱਠੀ ਕਰਨ ਦਿਓ।',
    'ਤੁਹਾਡੀ ਜਾਣਕਾਰੀ ਸਾਂਝੀ ਕਰਨ ਲਈ ਧੰਨਵਾਦ।',
    'ਕੀ ਤੁਸੀਂ ਕਿਸੇ ਖਾਸ ਸਕੀਮ ਬਾਰੇ ਹੋਰ ਜਾਣਨਾ ਚਾਹੁੰਦੇ ਹੋ?',
  ],
  haryanvi: [
    'वो तो बहुत अच्छा सवाल है! मुझे तुम्हारी सही योजना खोजने में मदद करने दो।',
    'मैं समझता हूँ। तुम्हारी जरूरतां के हिसाब से, तुम कई योजनां के लिए योग्य हो सको।',
    'मुझे और ज्यादा जानकारी इकट्ठा करने दो।',
    'तुम्हारी जानकारी शेयर करने के लिए धन्यवाद।',
    'क्या तुम किसी खास योजना के बारे में और ज्यादा जानना चाहो?',
  ],
}

export default function ChatInterface({ language, onBack, onChangeLanguage }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isRecording, setIsRecording] = useState(false)

  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [imageBase64, setImageBase64] = useState<string | null>(null)
  const [isFetchingLocation, setIsFetchingLocation] = useState(false)

  const [currentUserId] = useState(() => `next_user_${Math.random().toString(36).substr(2, 9)}`)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const apiUrl = "http://127.0.0.1:8000/web_chat"

  // Map Backend HTML to React properly
  const createMarkup = (htmlString: string) => {
    return { __html: htmlString };
  };

  const initChat = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: currentUserId,
          message: "reset"
        })
      });
      const data = await response.json();
      if (!data.error) {
        const botMsg: Message = {
          id: Date.now().toString(),
          text: <div dangerouslySetInnerHTML={createMarkup(data.response)} />,
          sender: 'bot',
          timestamp: new Date(),
        };
        setMessages([botMsg]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    initChat()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (e?: React.FormEvent, overrideText?: string) => {
    if (e) e.preventDefault()

    const textToSend = overrideText || input
    if (!textToSend.trim() && !imageBase64) return

    // Add user message
    let displayMsg = textToSend
    if (selectedFile) {
      displayMsg = `[Attached Image: ${selectedFile.name}] ${textToSend}`
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      text: displayMsg,
      sender: 'user',
      timestamp: new Date(),
      attachment: imageBase64 ? 'true' : undefined
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const payload: any = {
        user_id: currentUserId,
        message: textToSend,
        is_voice: isRecording || overrideText ? true : false
      }

      if (imageBase64 && selectedFile) {
        payload.image_base64 = imageBase64
        payload.image_mime = selectedFile.type
      }

      // Reset file attachment UI state aggressively
      setSelectedFile(null)
      setImageBase64(null)
      if (fileInputRef.current) fileInputRef.current.value = ''

      const response = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await response.json();

      if (data.error) {
        setMessages(prev => [...prev, { id: Date.now().toString(), text: `Error: ${data.error}`, sender: 'bot', timestamp: new Date() }])
      } else {
        let botHtml = data.response

        if ((data.state === "end" || data.next_state === "end") && (data.rag_payload || data.rag_response)) {
          try {
            let cleanJson = data.rag_response ? data.rag_response.replace(/```json/g, '').replace(/```/g, '').trim() : null;
            const ragData = data.rag_payload || JSON.parse(cleanJson);

            if (ragData?.eligible_schemes?.length > 0) {
              botHtml += "<br><br><b>✅ Eligible Schemes:</b><br>";
              ragData.eligible_schemes.forEach((s: any) => {
                botHtml += `🟢 <b>${s.scheme}</b><br><i>${s.reason}</i><br>`;
                if (s.key_features) botHtml += `➔ <b>Key Features:</b> ${s.key_features}<br>`;
                if (s.documents) botHtml += `➔ <b>Documents Required:</b> ${s.documents}<br><br>`;
              });
            } else {
              botHtml += "<br><br><i>Based on your answers, we couldn't find specific schemes, or further verification is required.</i>";
            }

            // Localization Prompt
            let nextPrompt = "<br><br><b>Which scheme are you interested in?</b>";
            if (language === "hi") nextPrompt = "<br><br><b>आप किस योजना में रुचि रखते हैं?</b>";
            if (language === "mr") nextPrompt = "<br><br><b>तुम्हाला कोणत्या योजनेत रस आहे?</b>";
            if (language === "ta") nextPrompt = "<br><br><b>நீங்கள் எந்த திட்டத்தில் ஆர்வமாக உள்ளீர்கள்?</b>";
            if (language === "te") nextPrompt = "<br><br><b>మీరు ఏ పథకం పట్ల ఆసక్తి చూపుతున్నారు?</b>";
            botHtml += nextPrompt;

          } catch (e) {
            console.error("RAG JSON Parser fallback:", e)
          }
        }

        if (data.audio_url) {
          const audio = new Audio(data.audio_url);
          audio.play().catch(e => console.error("Audio playback error:", e));
        }

        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          text: <div dangerouslySetInnerHTML={createMarkup(botHtml)} />,
          sender: 'bot',
          timestamp: new Date()
        }])
      }

    } catch (error) {
      console.error("Endpoint Failed:", error)
      setMessages(prev => [...prev, { id: Date.now().toString(), text: "Network connection to Assistant Server failed.", sender: 'bot', timestamp: new Date() }])
    } finally {
      setIsLoading(false)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      const options = { mimeType: 'audio/webm' };
      const mediaRecorder = new MediaRecorder(stream, options)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })

        // Stop all tracks to release microphone
        stream.getTracks().forEach((track) => track.stop())

        setIsLoading(true)
        try {
          const formData = new FormData()
          formData.append('audio_file', audioBlob, 'recording.webm')
          formData.append('language', language)

          const response = await fetch('http://127.0.0.1:8000/stt', {
            method: 'POST',
            body: formData,
          })

          if (!response.ok) {
            throw new Error(`Server error: ${response.status}`)
          }

          const data = await response.json()
          if (data.text) {
            setInput(data.text)
            // Automate the submit dispatch so the user doesn't have to push physical Send after Mic Stop
            handleSendMessage(undefined, data.text)
          }
        } catch (error) {
          console.error("Failed to transcribe audio:", error)
          // Add a temporary bot error message or toast here if desired
        } finally {
          setIsLoading(false)
        }
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (err) {
      console.error("Microphone access denied or not supported:", err)
      alert("Microphone access is required to use voice input.")
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  const handleLocationWeather = async () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.")
      return
    }

    setIsFetchingLocation(true)

    // Add a user message showing location is being shared
    const userMsg: Message = {
      id: Date.now().toString(),
      text: "📍 Sharing my location for weather-based recommendations...",
      sender: 'user',
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords
        try {
          const langMap: Record<Language, string> = {
            en: 'english', hi: 'hindi', mr: 'marathi',
            ta: 'tamil', te: 'telugu', pa: 'punjabi', haryanvi: 'haryanvi'
          }

          const response = await fetch('http://127.0.0.1:8000/weather-schemes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              latitude,
              longitude,
              language: langMap[language] || 'english',
            }),
          })
          const data = await response.json()

          let botHtml = ''
          if (data.error) {
            botHtml = `<b>Weather Alert:</b> ${data.error}`
          } else {
            const w = data.weather_summary
            botHtml = `<b>🌦️ Weather Report (Last 30 Days)</b><br>`
            botHtml += `📍 Location: ${latitude.toFixed(2)}°N, ${longitude.toFixed(2)}°E<br>`
            botHtml += `🌧️ Total Rainfall: ${w.total_rainfall_mm} mm (${w.rainy_days} rainy days)<br>`
            botHtml += `🌡️ Avg Temp: ${w.avg_temp_min_c}°C - ${w.avg_temp_max_c}°C<br>`
            botHtml += `💨 Max Wind: ${w.max_wind_kmh} km/h<br><br>`
            botHtml += `<b>📋 Weather-Based Scheme Recommendations:</b><br>`
            botHtml += data.recommendation.replace(/\n/g, '<br>')
          }

          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            text: <div dangerouslySetInnerHTML={createMarkup(botHtml)} />,
            sender: 'bot',
            timestamp: new Date(),
          }])
        } catch (error) {
          console.error("Weather fetch failed:", error)
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            text: "Could not fetch weather data. Please try again.",
            sender: 'bot',
            timestamp: new Date(),
          }])
        } finally {
          setIsLoading(false)
          setIsFetchingLocation(false)
        }
      },
      (error) => {
        console.error("Geolocation error:", error)
        setIsLoading(false)
        setIsFetchingLocation(false)
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          text: "Location access denied. Please allow location access and try again.",
          sender: 'bot',
          timestamp: new Date(),
        }])
      },
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        setImageBase64(result.split(',')[1]);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Chat container */}
      <div className="flex flex-col w-full max-w-2xl mx-auto bg-white">
        {/* Header */}
        <motion.header
          className="sticky top-0 z-50 bg-gradient-to-r from-primary to-primary/90 text-gray-900 p-4 shadow-md"
          initial={{ y: -100 }}
          animate={{ y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={onBack}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft size={24} />
              </button>
              <div>
                <h1 className="text-xl font-bold">🤖 Kisan Yojana Assistant</h1>
                <p className="text-sm text-gray-600">Always here to help</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={onChangeLanguage}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <Globe size={20} />
              </button>
              <span className="text-sm font-medium px-3 py-1 bg-gray-200 rounded-full">{language.toUpperCase()}</span>
            </div>
          </div>
        </motion.header>

        {/* Messages container */}
        <motion.div
          className="flex-1 overflow-y-auto p-4 space-y-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <AnimatePresence mode="popLayout">
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md xl:max-w-lg px-4 py-3 rounded-2xl ${message.sender === 'user'
                    ? 'bg-primary text-white rounded-br-none'
                    : 'bg-secondary text-foreground rounded-bl-none'
                    }`}
                >
                  <div className="text-sm md:text-base leading-relaxed">{message.text}</div>
                  <span className={`text-xs mt-1 block ${message.sender === 'user' ? 'text-white/70' : 'text-muted-foreground'}`}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </motion.div>
            ))}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="bg-secondary text-foreground px-4 py-3 rounded-2xl rounded-bl-none">
                  <div className="flex gap-2">
                    <motion.div
                      className="w-2 h-2 rounded-full bg-primary"
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 0.6, repeat: Infinity }}
                    />
                    <motion.div
                      className="w-2 h-2 rounded-full bg-primary"
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 0.6, repeat: Infinity, delay: 0.1 }}
                    />
                    <motion.div
                      className="w-2 h-2 rounded-full bg-primary"
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
                    />
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </motion.div>

        {/* Input area */}
        <motion.form
          onSubmit={handleSendMessage}
          className="border-t border-border p-4 bg-white"
          initial={{ y: 100 }}
          animate={{ y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {selectedFile && (
            <div className="text-sm text-primary font-semibold mb-2 ml-2">
              Attached: {selectedFile.name}
            </div>
          )}
          <div className="flex gap-2 items-center">

            <input
              type="file"
              accept="image/*"
              className="hidden"
              ref={fileInputRef}
              onChange={handleFileChange}
            />

            <button
              type="button"
              className="p-3 text-gray-500 hover:text-primary transition-colors hover:bg-gray-100 rounded-full"
              onClick={() => fileInputRef.current?.click()}
              title="Attach Document"
            >
              📎
            </button>
            <button
              type="button"
              className={`p-3 transition-colors rounded-full ${isFetchingLocation ? 'text-primary animate-pulse' : 'text-gray-500 hover:text-primary hover:bg-gray-100'}`}
              onClick={handleLocationWeather}
              title="Share Location for Weather Alerts"
              disabled={isFetchingLocation || isLoading}
            >
              <MapPin size={20} />
            </button>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={greetings[language].placeholder}
              className="flex-1 px-4 py-3 bg-secondary border border-border rounded-full focus:outline-none focus:ring-2 focus:ring-primary text-foreground placeholder:text-muted-foreground"
              disabled={isLoading}
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="button"
              onClick={toggleRecording}
              className={`p-3 rounded-full transition-all duration-200 flex items-center justify-center border flex-shrink-0 ${isRecording
                ? 'bg-red-500 text-white border-red-600 animate-pulse'
                : 'bg-secondary text-primary hover:bg-secondary/80 border-border'
                }`}
              title={isRecording ? "Stop Recording" : "Voice Input"}
              disabled={isLoading && !isRecording}
            >
              {isRecording ? <Square size={20} fill="currentColor" /> : <Mic size={20} />}
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="submit"
              disabled={isLoading || (!input.trim() && !imageBase64)}
              className="px-6 py-3 bg-primary text-white rounded-full hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2 font-medium"
            >
              <Send size={18} />
              <span className="hidden sm:inline">{greetings[language].sendButton}</span>
            </motion.button>
          </div>
        </motion.form>
      </div>
    </div>
  )
}
