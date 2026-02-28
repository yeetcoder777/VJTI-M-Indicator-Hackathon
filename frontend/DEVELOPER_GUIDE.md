# 👨‍💻 Developer Guide - Kisan Yojana Sahayak

Complete guide for developers working on Kisan Yojana Sahayak.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────┐
│      User Interface Layer            │
│  (React Components with Framer Motion)
├─────────────────────────────────────┤
│   page.tsx (State Management)       │
├─────────────────────────────────────┤
│  LanguageSelection → LandingPage    │
│        ↓                             │
│     ChatInterface                   │
└─────────────────────────────────────┘
         ↓
   Content Library (lib/content.ts)
   - Multilingual strings
   - UI text
   - Support info
```

## 🗂️ File Structure Explained

```
kisan-yojana-sahayak/
├── app/
│   ├── page.tsx              # Main app logic (state management)
│   ├── layout.tsx            # Root layout with metadata
│   └── globals.css           # Global styles & design tokens
│
├── components/
│   ├── LanguageSelection.tsx # 1️⃣ Language selection with animations
│   ├── LandingPage.tsx       # 2️⃣ Main content page
│   └── ChatInterface.tsx     # 3️⃣ AI chatbot interface
│
├── lib/
│   └── content.ts            # 📝 All content in 7 languages
│
├── public/
│   └── hero-farmer.jpg       # 🖼️ Landing page image
│
├── package.json              # Dependencies
├── README.md                 # User guide
├── CONTENT_GUIDE.md          # Content management
└── DEVELOPER_GUIDE.md        # This file

```

## 🚀 Key Components

### 1. **app/page.tsx** - State Management Hub
```typescript
function Home() {
  const [selectedLanguage, setSelectedLanguage] = useState<Language | null>(null)
  const [showChat, setShowChat] = useState(false)
  
  // Logic flow:
  // !selectedLanguage → LanguageSelection
  // showChat → ChatInterface
  // else → LandingPage
}
```

**Responsibilities**:
- Manage selected language state
- Control chat visibility
- Route between components

**Props passed down**:
- `selectedLanguage`: Current language ('en' | 'hi' | 'mr' | etc.)
- `onSelectLanguage`: Callback from LanguageSelection
- `onChatClick`: Callback from LandingPage
- `onChangeLanguage`: Reset language selection

### 2. **components/LanguageSelection.tsx** - Entry Point
```typescript
function LanguageSelection({ onSelectLanguage })
```

**Features**:
- 7 animated cards for language selection
- Staggered animation using Framer Motion
- Hover and tap effects
- Decorative background elements

**Key Elements**:
- `containerVariants`: Controls stagger animation for cards
- `cardVariants`: Individual card animation states
- Language array with emoji flags

**State & Hooks**:
- `useState(mounted)`: Prevents hydration mismatch
- `useEffect()`: Sets mounted to true after component loads

### 3. **components/LandingPage.tsx** - Main Content
```typescript
function LandingPage({ language, onChatClick, onChangeLanguage })
```

**Features**:
- Responsive content in selected language
- Multiple content sections (How to use, Features, Support)
- Hero image display
- Language switcher in header
- CTA button to chatbot

**Content Sections**:
1. Header with language selector
2. Hero image
3. Title and description
4. How to use section (3 cards)
5. Features section (3 features with icons)
6. Support information section
7. CTA and chatbot button
8. Footer

**Animations**:
- Header slides in from top
- All content staggered with `containerVariants`
- Cards have hover and scale effects
- Smooth transitions on all interactions

### 4. **components/ChatInterface.tsx** - AI Chatbot
```typescript
function ChatInterface({ language, onBack, onChangeLanguage })
```

**Features**:
- Real-time messaging UI
- Multi-language support
- Typing indicators
- Message timestamps
- Smooth animations

**Message Structure**:
```typescript
interface Message {
  id: string              // Unique identifier
  text: string            // Message content
  sender: 'user' | 'bot'  // Who sent it
  timestamp: Date         // When sent
}
```

**Chatbot Responses**:
- 5 pre-defined responses per language
- Random selection on each user message
- Delay simulation (800ms) for realistic UX

**Functions**:
- `handleSendMessage()`: Process user input and add messages
- `scrollToBottom()`: Auto-scroll to latest message
- Language-based greetings and placeholders

## 🎨 Styling System

### Design Tokens (globals.css)

**Color Variables**:
```css
--primary: #2d5016           /* Forest Green */
--accent: #c8835f            /* Earthy Brown */
--background: #faf9f7        /* Cream */
--foreground: #2d2416        /* Dark Brown */
--secondary: #f4e4d8         /* Light Tan */
```

**Usage in Components**:
```tsx
className="bg-primary text-white"  // Uses CSS variables
className="hover:bg-accent"         // Color tokens
className="border-border"           // Border color token
```

### Tailwind CSS

**Responsive Design**:
```tsx
className="text-2xl md:text-4xl lg:text-5xl"  // Mobile first
className="grid grid-cols-1 md:grid-cols-2"   // Responsive grid
```

**Spacing Scale**:
- `p-4`, `m-6`, `gap-3`: Uses Tailwind's spacing
- `rounded-2xl`: Border radius using scale
- `shadow-lg`: Box shadows

## 🎬 Animation Patterns

### Framer Motion Usage

**1. Container Animations (Stagger)**:
```typescript
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,  // Delay between children
    },
  },
}
```

**2. Item Animations**:
```typescript
const itemVariants = {
  hidden: { opacity: 0, y: 20 },      // Start state
  visible: {                           // End state
    opacity: 1,
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 12,
    },
  },
}
```

**3. Interactive Animations**:
```typescript
motion.button
  whileHover={{ scale: 1.05 }}    // On hover
  whileTap={{ scale: 0.95 }}      // On click
```

## 🌐 Multilingual Architecture

### Content Management (lib/content.ts)

**Structure**:
```typescript
const content: Record<Language, PageContent> = {
  en: { title: "...", subtitle: "...", ... },
  hi: { title: "...", subtitle: "...", ... },
  // ... 7 languages total
}

export function getContentForLanguage(language: Language) {
  return content[language] || content.en
}
```

**How It Works**:
1. Component receives `language` prop
2. Calls `getContentForLanguage(language)`
3. Gets all content for that language
4. Displays in the correct language

**Language Codes**:
```typescript
type Language = 'en' | 'hi' | 'mr' | 'ta' | 'te' | 'pa' | 'haryanvi'
```

## 🔄 Data Flow

### User Language Selection Flow
```
LanguageSelection Component
    ↓
User clicks language card
    ↓
onSelectLanguage callback
    ↓
page.tsx: setSelectedLanguage(language)
    ↓
State update triggers re-render
    ↓
LandingPage rendered with selected language
```

### Chat Flow
```
LandingPage
    ↓
User clicks "Head to Chatbot"
    ↓
onChatClick() → setShowChat(true)
    ↓
ChatInterface rendered
    ↓
User types message
    ↓
handleSendMessage() fires
    ↓
Add user message to state
    ↓
Simulate bot response (800ms delay)
    ↓
Add bot message to state
    ↓
Messages re-render with animations
```

## 🔧 Customization Guide

### Adding a New Language

1. **Add language code** to type:
```typescript
type Language = 'en' | 'hi' | 'mr' | 'ta' | 'te' | 'pa' | 'haryanvi' | 'new'
```

2. **Add content** in lib/content.ts:
```typescript
const content: Record<Language, PageContent> = {
  // ... existing languages
  new: {
    title: "Title in new language",
    subtitle: "Subtitle in new language",
    // ... all required fields
  }
}
```

3. **Add to language selection**:
```typescript
const languages: { code: Language; name: string; flag: string; nativeName: string }[] = [
  // ... existing
  { code: 'new', name: 'Language Name', flag: '🌾', nativeName: 'Native Name' }
]
```

### Changing Colors

1. **Update globals.css** color variables:
```css
:root {
  --primary: #newcolor;
  --accent: #newcolor;
  // ... other colors
}
```

2. **All components automatically update** due to CSS variables

### Adding New Page Sections

1. **Create content in lib/content.ts**:
```typescript
newSection: {
  title: "Section title",
  items: [
    { icon: '🎯', title: "Item 1", description: "..." }
  ]
}
```

2. **Add to PageContent interface** (lib/content.ts):
```typescript
interface PageContent {
  // ... existing
  newSection: SectionType;
}
```

3. **Add to LandingPage.tsx**:
```tsx
<motion.section>
  <h3>{content.newSection.title}</h3>
  {content.newSection.items.map(item => (
    // Render item
  ))}
</motion.section>
```

## 📦 Dependencies

### Core Dependencies
- **Next.js 16**: React framework
- **React 19**: UI library
- **TypeScript**: Type safety
- **Tailwind CSS 4**: Styling
- **Framer Motion**: Animations
- **Lucide React**: Icons

### Why These?
- **Next.js**: Server-side rendering, routing, optimization
- **Framer Motion**: Smooth, performant animations
- **Tailwind CSS**: Rapid UI development with utility classes
- **TypeScript**: Catch errors early, better DX
- **Lucide**: Consistent, modern icon set

## 🧪 Testing Considerations

### Manual Testing Checklist
- [ ] All 7 languages load correctly
- [ ] Language switching works on all pages
- [ ] Animations smooth on mobile
- [ ] Chat messages send and display
- [ ] Responsive design works (mobile/tablet/desktop)
- [ ] Accessibility (keyboard navigation, screen readers)
- [ ] Links and buttons functional
- [ ] Images load and display correctly

### Browser Compatibility
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## 🚀 Performance Tips

1. **Image Optimization**:
   - Use Next.js Image component
   - Lazy load non-critical images
   - Compress images before deployment

2. **Code Splitting**:
   - Dynamic imports for heavy components
   - Route-based code splitting (Next.js handles)

3. **Animation Performance**:
   - Use transform and opacity (GPU accelerated)
   - Avoid expensive repaints
   - Use `will-change` sparingly

4. **Bundle Size**:
   - Tree shake unused code
   - Minimize large dependencies
   - Monitor with `next/bundle-analyzer`

## 🔐 Security Best Practices

1. **Input Validation**:
   - Validate chat input
   - Sanitize any user-generated content
   - Use TypeScript for type safety

2. **API Security** (when implemented):
   - Use environment variables for API keys
   - HTTPS only
   - Rate limiting on chat API
   - CORS configuration

3. **Data Privacy**:
   - No sensitive data in localStorage
   - Clear cookies appropriately
   - GDPR compliance ready

## 📊 Analytics Integration (Optional)

To add analytics:

```typescript
// In components
import { track } from '@/lib/analytics'

function LandingPage() {
  useEffect(() => {
    track('page_view', { language })
  }, [language])
}
```

## 🐛 Common Issues & Debugging

### Issue: Hydration Mismatch
**Cause**: Client-side rendering differences
**Solution**: Use `useEffect` for mount checks

### Issue: Animations Not Smooth
**Cause**: Low frame rate or too many animations
**Solution**: Check browser performance, reduce animation count

### Issue: Content Not Loading
**Cause**: Missing language in content.ts
**Solution**: Add fallback to English

### Issue: Images Not Displaying
**Cause**: Wrong path or missing image
**Solution**: Check `public/` folder path

## 📚 Useful Resources

- [Next.js Docs](https://nextjs.org/docs)
- [React Docs](https://react.dev)
- [Framer Motion Docs](https://www.framer.com/motion/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

## 🎯 Development Workflow

1. **Setup**:
   ```bash
   git clone <repo>
   cd project
   pnpm install
   pnpm dev
   ```

2. **Development**:
   - Make changes in components
   - Test in browser at localhost:3000
   - Check all languages

3. **Testing**:
   - Test on mobile devices
   - Test all language switches
   - Test chat functionality

4. **Deployment**:
   ```bash
   git push origin main
   # Vercel auto-deploys
   ```

---

**Questions?** Check README.md or CONTENT_GUIDE.md for more information.
