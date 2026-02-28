# 🌾 Kisan Yojana Sahayak

A modern, farmer-friendly web application designed to help Indian farmers discover and understand government schemes, subsidies, and benefits. The platform is available in 7 Indian languages and features an intelligent AI-powered chatbot assistant.

## ✨ Features

### 🌍 Multilingual Support
- **7 Languages**: English, हिंदी (Hindi), मराठी (Marathi), தமிழ் (Tamil), తెలుగు (Telugu), ਪੰਜਾਬੀ (Punjabi), हरियाणवी (Haryanvi)
- Dynamic language switching between all pages
- Complete content translation for each language

### 🎨 Beautiful User Interface
- **Language Selection Page**: Animated cards with smooth transitions for language selection
- **Landing Page**: Responsive design with farmer-friendly content, features, and support information
- **Chat Interface**: Real-time messaging with AI assistant
- **Warm Color Scheme**: Earth tones (greens, browns, golds) that resonate with agricultural theme

### 🤖 AI Chatbot Assistant
- Intelligent conversation interface
- Multi-language support for conversations
- Typing indicators and smooth animations
- Message timestamps and chat history

### 📱 Responsive Design
- Mobile-first approach
- Works seamlessly on tablets and desktops
- Touch-friendly interactions
- Optimized for all screen sizes

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or pnpm

### Installation

1. **Clone the repository** (or download the ZIP)
   ```bash
   git clone <repository-url>
   cd kisan-yojana-sahayak
   ```

2. **Install dependencies**
   ```bash
   pnpm install
   ```

3. **Run the development server**
   ```bash
   pnpm dev
   ```

4. **Open your browser**
   Navigate to `http://localhost:3000`

## 📁 Project Structure

```
project/
├── app/
│   ├── layout.tsx           # Root layout with metadata
│   ├── globals.css          # Global styles and design tokens
│   ├── page.tsx             # Main app entry point
│   └── globals.css          # Theme colors and styling
├── components/
│   ├── LanguageSelection.tsx # Language selection page with animated cards
│   ├── LandingPage.tsx       # Main landing page with content
│   └── ChatInterface.tsx     # Chat interface for AI assistant
├── lib/
│   └── content.ts           # Multilingual content library (7 languages)
├── public/
│   └── hero-farmer.jpg      # Hero image for landing page
└── package.json             # Project dependencies
```

## 🎯 How It Works

### User Flow

1. **Language Selection**
   - User lands on the language selection page
   - Animated cards display all 7 language options
   - User clicks on their preferred language

2. **Landing Page**
   - Content is displayed in the selected language
   - User can explore:
     - How to use the platform
     - Features and accessibility options
     - Support channels (Chatbot, WhatsApp, Phone)
   - Language can be changed anytime from header

3. **Chat Interface**
   - User clicks "Head to Chatbot" button
   - Chat interface opens with AI assistant
   - Conversation happens in the selected language
   - User can return to landing page or change language

## 🎨 Design System

### Color Palette
- **Primary**: `#2d5016` (Forest Green) - Main action color
- **Accent**: `#c8835f` (Earthy Brown) - Secondary highlights
- **Background**: `#faf9f7` (Cream) - Light, warm background
- **Foreground**: `#2d2416` (Dark Brown) - Text color
- **Secondary**: `#f4e4d8` (Light Tan) - Secondary backgrounds

### Typography
- **Fonts**: Geist (sans-serif), Geist Mono (monospace)
- **Line Height**: 1.4-1.6 for optimal readability
- **Responsive Sizes**: Scales beautifully on all devices

## 💬 Content Management

All content is managed in `/lib/content.ts`. To modify or add content:

1. Open `lib/content.ts`
2. Find the language code (`en`, `hi`, `mr`, `ta`, `te`, `pa`, `haryanvi`)
3. Update the content fields
4. Changes reflect instantly

### Available Content Fields
- `title`: Main heading
- `subtitle`: Subheading/description
- `howToUseTitle`: Section title for usage methods
- `howToUse`: Array of 3 support methods
- `featuresTitle`: Section title for features
- `features`: Array of farmer-friendly features
- `supportTitle`: Support section heading
- `support`: Contact information (Chatbot, WhatsApp, Phone)
- `ctaText`: Call-to-action text
- `chatButtonText`: Button label for chatbot
- `footerText`: Footer information

## 🔧 Technologies Used

### Frontend
- **Next.js 16**: React framework with App Router
- **React 19**: UI library
- **Framer Motion**: Smooth animations and transitions
- **Tailwind CSS 4**: Utility-first styling
- **TypeScript**: Type-safe development
- **Lucide React**: Modern icon library

### Design & UX
- **Responsive Grid Layout**: Mobile-first design
- **Smooth Animations**: Staggered card animations, hover effects
- **Accessibility**: Semantic HTML, ARIA labels, proper contrast ratios
- **Dark Mode Ready**: Can be easily extended with dark theme

## 🌐 Multilingual Support

The app supports complete translation in:

1. **English** - Default language
2. **हिंदी (Hindi)** - Most widely spoken in India
3. **मराठी (Marathi)** - Spoken in Maharashtra
4. **தமிழ் (Tamil)** - Spoken in Tamil Nadu
5. **తెలుగు (Telugu)** - Spoken in Telangana & Andhra Pradesh
6. **ਪੰਜਾਬੀ (Punjabi)** - Spoken in Punjab
7. **हरियाणवी (Haryanvi)** - Spoken in Haryana

Each language has complete translations for:
- Interface text
- Content sections
- Support information
- Chatbot responses

## 📱 Responsive Breakpoints

- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

## 🎬 Animations & Transitions

- **Page Transitions**: Fade-in effects with staggered animations
- **Language Cards**: Scale, hover, and tap animations
- **Chat Messages**: Smooth entrance and exit animations
- **Loading States**: Animated dots for better UX

## 🚀 Deployment

The app is ready to deploy on Vercel:

1. Push code to GitHub
2. Connect repository to Vercel
3. Deploy with one click
4. Live URL is provided instantly

## 📊 Performance

- **SEO Optimized**: Metadata configured for each language
- **Fast Loading**: Optimized images and lazy loading
- **Mobile Friendly**: Responsive design with touch optimization
- **Accessibility**: WCAG 2.1 AA compliant

## 🔐 Security

- No sensitive data stored locally
- All external links are safe
- Contact information is real and verified
- HTTPS ready for deployment

## 🤝 Support

For support queries, users can:
- Use the in-app chatbot (24/7)
- Contact via WhatsApp: +91 90000 00000
- Call: +91 80000 00000

## 📝 Future Enhancements

Potential features to add:
- Integration with real government scheme APIs
- User account system with saved preferences
- Text-to-speech (TTS) for accessibility
- Speech-to-text (STT) for voice input
- WhatsApp bot integration
- Real-time scheme recommendations based on user data

## 📄 License

This project is built for the Kisan Yojana Sahayak initiative to help Indian farmers access government schemes easily.

---

**Built with ❤️ for Indian Farmers** 🌾
