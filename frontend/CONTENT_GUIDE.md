# 📝 Content Management Guide

This guide explains how to manage and update content for Kisan Yojana Sahayak.

## 🗂️ Content Location

All content is stored in `/lib/content.ts`

## 📚 Content Structure

The app supports 7 languages with the following codes:
- `en` - English
- `hi` - हिंदी (Hindi)
- `mr` - मराठी (Marathi)
- `ta` - தமிழ் (Tamil)
- `te` - తెలుగు (Telugu)
- `pa` - ਪੰਜਾਬੀ (Punjabi)
- `haryanvi` - हरियाणवी (Haryanvi)

## 📋 Content Fields

Each language has the following content fields:

### 1. **title** (Main Heading)
- Large, bold text that appears at the top of the landing page
- Example: "Find Government Schemes in Seconds"

### 2. **subtitle** (Description)
- Explains what the platform does
- Should be informative and encouraging
- Example: "This platform is built to make government schemes simple and accessible for every farmer..."

### 3. **howToUseTitle** (Section Heading)
- Title for the "How to Use" section
- Example: "How You Can Use It"

### 4. **howToUse** (Array of 3 items)
Each item has:
- `icon`: Emoji representing the method
- `title`: Name of the support method
- `description`: Brief description

Examples:
```javascript
{
  icon: '🤖',
  title: 'Chatbot on the website',
  description: 'Get instant answers anytime'
}
```

### 5. **featuresTitle** (Section Heading)
- Title for the features section
- Example: "Built for all farmers"

### 6. **features** (Array of features)
Each feature has:
- `icon`: Emoji or symbol
- `title`: Feature name
- `description`: What this feature does

Examples:
```javascript
{
  icon: '🌍',
  title: 'Available in multiple Indian languages',
  description: 'No language barriers'
}
```

### 7. **supportTitle** (Section Heading)
- Title for support/contact section
- Example: "Get Help Anytime"

### 8. **support** (Array of 3 support methods)
Each support method has:
- `icon`: Emoji
- `type`: Support channel name
- `contact`: Contact information

Examples:
```javascript
{
  icon: '🤖',
  type: 'Website Chatbot',
  contact: 'Available 24/7'
}
```

### 9. **ctaText** (Call-to-Action)
- Text that encourages users to click the chatbot button
- Example: "Need help finding schemes? Start chatting with our AI assistant now!"

### 10. **chatButtonText** (Button Label)
- Text displayed on the chatbot button
- Example: "Head to Chatbot"

### 11. **footerText** (Footer Message)
- Final message at the bottom of the page
- Example: "This platform ensures that no farmer misses out on benefits..."

## 🔄 How to Update Content

### Example: Updating Hindi Content

1. Open `/lib/content.ts`
2. Find the `hi` section in the `content` object
3. Update the specific field:

```typescript
const content: Record<Language, PageContent> = {
  hi: {
    title: 'नई हेडिंग', // Change this
    subtitle: 'नया विवरण', // Or this
    // ... rest of the content
  }
}
```

4. Save the file
5. Changes will be live immediately in development mode

### Example: Adding a New Feature

To add a new feature to the features list:

```typescript
features: [
  // ... existing features
  {
    icon: '🎓',
    title: 'शिक्षा कार्यक्रम',
    description: 'किसानों के लिए विशेष प्रशिक्षण'
  }
]
```

## 🌐 Translation Tips

When translating content for a new language:

1. Keep the meaning consistent across all languages
2. Adapt idioms to the local language culture
3. Use culturally appropriate emojis
4. Maintain the same tone (friendly, helpful, professional)
5. Ensure text length is similar (some languages are longer)

## 📱 Content Best Practices

### Title Guidelines
- Keep it under 10 words
- Make it action-oriented
- Use simple, farmer-friendly language
- Avoid technical jargon

### Description Guidelines
- 2-3 sentences maximum
- Explain benefits clearly
- Use real examples when possible
- Address farmer concerns directly

### Feature Guidelines
- Focus on benefits, not features
- Use active voice
- Make it relatable to farmers
- Keep descriptions brief

### Support Information Guidelines
- Use real, updated contact information
- Include multiple support channels
- Provide 24/7 availability where possible
- Make it easy to remember

## 🎨 Emoji Selection

Recommended emojis for different sections:

**Support Methods:**
- 🤖 Chatbot
- 💬 WhatsApp/Messaging
- 📞 Phone
- 📧 Email

**Features:**
- 🌍 Languages/Global
- 🔊 Audio/Sound
- 🎙️ Voice/Speaking
- 📱 Mobile/Device

**Agriculture:**
- 🌾 Crops/Farming
- 🚜 Tractor/Farming
- 🌱 Growth/Planting
- 👨‍🌾 Farmer

## ⚠️ Important Notes

1. **Do Not Change**:
   - Language codes (en, hi, mr, etc.)
   - Field names in the interface
   - Component structure

2. **Always Keep**:
   - Proper Unicode encoding for non-English text
   - Consistent formatting across all languages
   - Proper quotes and punctuation

3. **Test After Changes**:
   - Switch between languages to verify
   - Check that content displays correctly
   - Verify no text is cut off
   - Test on mobile devices

## 🔍 Common Issues & Solutions

### Issue: Text appears cut off
**Solution**: Reduce text length or check for very long words

### Issue: Emoji not displaying
**Solution**: Copy emoji directly from the existing list (avoid pasting from web)

### Issue: Language switcher not showing updated text
**Solution**: Clear browser cache or do a hard refresh (Ctrl+F5)

### Issue: Special characters showing as boxes
**Solution**: Ensure the file is saved as UTF-8 encoding

## 🚀 Deploying Content Changes

After updating content in `/lib/content.ts`:

1. Save the file
2. If using Vercel: Changes deploy automatically
3. If using local development: Refresh the browser
4. Clear cache if needed (browser dev tools)

## 📊 Content Statistics

Current content sizes:
- **English**: ~500 words
- **Hindi**: ~600 words (Hindi is slightly more verbose)
- **Marathi**: ~580 words
- **Tamil**: ~550 words
- **Telugu**: ~540 words
- **Punjabi**: ~560 words
- **Haryanvi**: ~520 words

Try to keep new content within similar word counts to maintain consistency.

## 💡 Content Ideas

### New Features to Add
- Real government scheme listings
- Eligibility calculator
- Document checklist
- Application timeline
- FAQ section
- Success stories from farmers

### New Support Methods
- Email support
- Social media integration
- Video tutorials
- Live chat with human support
- Community forum

### Seasonal Content
- Monsoon scheme updates
- Harvest season benefits
- Winter crop subsidies
- Post-harvest storage support

---

**Need Help?** Check the main README.md for more information about the project structure and deployment.
