# ⚡ Quick Start Guide - Kisan Yojana Sahayak

Get Kisan Yojana Sahayak up and running in **under 5 minutes**! 🚀

## 📋 Prerequisites

- **Node.js 18+** (Check with `node -v`)
- **pnpm** (or npm/yarn)

Don't have them? [Install Node.js here](https://nodejs.org/)

---

## 🚀 3-Step Setup

### Step 1: Install Dependencies (1 minute)
```bash
pnpm install
```

This installs all required packages:
- Next.js, React, TypeScript
- Tailwind CSS, Framer Motion
- Lucide icons and more

### Step 2: Run Development Server (30 seconds)
```bash
pnpm dev
```

You'll see:
```
  ▲ Next.js 16.1.6
  - Local:        http://localhost:3000
  - Environments: .env.local
```

### Step 3: Open in Browser (10 seconds)
Navigate to: **http://localhost:3000**

✅ **Done! The app is running!**

---

## 🎮 What You'll See

### 1. **Language Selection Page** (Animated Cards)
- 7 language options with beautiful animations
- Click any language card to proceed
- Smooth transitions and hover effects

### 2. **Landing Page** (Multilingual Content)
- Full content in your selected language
- Hero image and features section
- Support information and resources
- Language switcher in header

### 3. **Chat Interface** (AI Assistant)
- Click "Head to Chatbot" button
- Chat with AI assistant
- Real-time messaging with animations
- Responses in your selected language

---

## 🎨 Customization (Optional)

### Change Colors
Edit `/app/globals.css`, line 7-30:
```css
:root {
  --primary: #2d5016;        /* Change this to your color */
  --accent: #c8835f;         /* And this */
  /* ... other colors */
}
```

### Update Content
Edit `/lib/content.ts` to modify any text for any language.

Example:
```typescript
const content = {
  en: {
    title: "Your new title here",
    subtitle: "Your new subtitle here",
    // ... update other fields
  }
}
```

### Change Logo/Image
Replace `/public/hero-farmer.jpg` with your image (same filename).

---

## 📱 Testing on Different Devices

### Mobile Testing
```bash
# While pnpm dev is running
# On your phone, visit your computer's IP:
http://192.168.1.XXX:3000
```

### Responsive Testing
- Chrome DevTools: Press `F12`
- Toggle device toolbar: `Ctrl+Shift+M`
- Select different devices (iPhone, iPad, etc.)

---

## 🌐 Test All Languages

1. Start on Language Selection page
2. Click each language card
3. Verify:
   - Content displays in correct language
   - Animations work smoothly
   - Chat interface works
   - Navigation is responsive

**All 7 Languages:**
- 🇬🇧 English
- 🇮🇳 हिंदी (Hindi)
- 🇮🇳 मराठी (Marathi)
- 🇮🇳 தமிழ் (Tamil)
- 🇮🇳 తెలుగు (Telugu)
- 🇮🇳 ਪੰਜਾਬੀ (Punjabi)
- 🇮🇳 हरियाणवी (Haryanvi)

---

## 🐛 Troubleshooting

### Port 3000 Already in Use
```bash
# Kill the process or use a different port
pnpm dev -- -p 3001
```

### Dependencies Installation Failed
```bash
# Clear cache and try again
rm -rf node_modules
rm pnpm-lock.yaml
pnpm install
```

### Styles Not Loading
```bash
# Rebuild the app
pnpm dev
# Hard refresh browser (Ctrl+F5)
```

### Image Not Displaying
- Check if `/public/hero-farmer.jpg` exists
- Verify image path in `LandingPage.tsx`

---

## 📦 Deployment (Optional)

### Deploy to Vercel (1 click)

1. Push your code to GitHub
2. Go to [Vercel.com](https://vercel.com)
3. Click "New Project"
4. Select your GitHub repo
5. Click "Deploy"

**That's it! Your app is live!** 🎉

### Deploy to Other Platforms

**Netlify:**
```bash
pnpm run build
# Deploy the .next folder
```

**Docker:**
```dockerfile
FROM node:18
WORKDIR /app
COPY . .
RUN pnpm install
RUN pnpm build
CMD ["pnpm", "start"]
```

---

## 📚 Next Steps

### Learn More
- 📖 [README.md](./README.md) - Full project overview
- ✏️ [CONTENT_GUIDE.md](./CONTENT_GUIDE.md) - How to manage content
- 👨‍💻 [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) - For developers
- 📊 [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) - What's been built

### Customization Ideas
- [ ] Add more languages
- [ ] Change color scheme
- [ ] Update support contact numbers
- [ ] Modify farmer features/benefits
- [ ] Add new content sections
- [ ] Integrate real API for schemes
- [ ] Add user authentication
- [ ] Connect to WhatsApp bot

---

## 🎯 Common Tasks

### Add a New Language
1. Add to language type in `lib/content.ts`
2. Add complete content for that language
3. Add to language cards in `components/LanguageSelection.tsx`

### Update Contact Numbers
Edit `/lib/content.ts`:
```typescript
support: [
  {
    icon: '💬',
    type: 'WhatsApp Support',
    contact: '+91 XXXXX XXXXX',  // Change this
  }
]
```

### Change App Title
Edit `/app/layout.tsx`:
```typescript
export const metadata: Metadata = {
  title: 'Your App Title Here',  // Change this
  description: 'Your description here',
}
```

---

## ✅ Quality Checklist

Before deploying, verify:
- [ ] All 7 languages load correctly
- [ ] Language switching works
- [ ] Chat interface is responsive
- [ ] Images display properly
- [ ] Animations are smooth
- [ ] Mobile view looks good
- [ ] All links work
- [ ] Contact info is correct

---

## 💬 Need Help?

**Common Questions:**

**Q: How do I change the main title?**
A: Edit `lib/content.ts` → search for `title:` field

**Q: Can I add more languages?**
A: Yes! Follow the pattern in `lib/content.ts`

**Q: How do I deploy this?**
A: Push to GitHub → Connect to Vercel → Auto-deployed!

**Q: Can I modify the design?**
A: Yes! Edit `globals.css` for colors, `components` for layout

---

## 🌟 You're All Set!

Your Kisan Yojana Sahayak application is ready! 

### Quick Summary:
✅ Beautiful, multilingual farmer assistance app
✅ 7 languages fully supported
✅ AI chatbot included
✅ Production-ready code
✅ Fully customizable
✅ Ready to deploy

### Next: 
1. Run `pnpm dev`
2. Visit `http://localhost:3000`
3. Explore all 7 languages
4. Test the chatbot
5. Make it your own!

---

**Built with ❤️ for Indian Farmers** 🌾

Happy coding! 🚀
