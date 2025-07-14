# 🔄 Version Switcher

This project has two versions:

## 🔥 Full AI Version (app.py)
- **Best For**: Local development, full-featured hosting (Railway, Render, Heroku)
- **Features**: Complete NLP pipeline, NLTK, scikit-learn, 100+ synonyms
- **Memory**: ~100MB
- **Accuracy**: 95%

## ⚡ Vercel Version (api/index.py)  
- **Best For**: Vercel deployment, fast serverless hosting
- **Features**: Lightweight algorithms, core detection, 20 synonyms
- **Memory**: ~10MB
- **Accuracy**: 85%

## 🚀 Quick Commands

### Deploy Full Version:
```bash
# Railway
railway deploy

# Render
git push origin main

# Heroku  
git push heroku main
```

### Deploy Vercel Version:
```bash
vercel --prod
```

## 🎯 Recommendation

1. **Start with Vercel**: Fast, free, good enough for most users
2. **Upgrade Later**: Move to full version when you need maximum accuracy
3. **Keep Both**: Use Vercel for demos, full version for production

Both versions have the same beautiful UI and core functionality!
