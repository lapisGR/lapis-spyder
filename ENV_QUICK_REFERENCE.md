# 🚀 Lapis LLMT Spider - Environment Quick Reference

Generated: 2025-06-08 22:00:03

## 🔐 Generated Secrets

### JWT Secret (Railway)
```
j8pOxKUBJaTsEaiVIavgKiHNN_2cfcKY6lepZ9_Hp-W13CdvA_lsg6Peoferb1rK6Cdp3U0O4tagAdKIp5OodA
```

### Admin Credentials (for initial setup)
- Email: `admin@lapis-spider.com`
- Password: `XVU0nvjA9VEMvhT2Gd_BUp-N743-IRHh`

## 📋 Required External Services

### 1. MongoDB Atlas
- Sign up: https://mongodb.com/atlas
- Create free M0 cluster
- Get connection string
- Update MONGODB_URI in Railway

### 2. Google Gemini API
- Get API key: https://makersuite.google.com/app/apikey
- Update GOOGLE_API_KEY in Railway

### 3. Railway Services
- PostgreSQL: Auto-provisioned
- Redis: Auto-provisioned

## 🔧 Environment Files Created

1. **`.env.railway`** - Production backend variables
2. **`.env.vercel`** - Production frontend variables
3. **`.env.local`** - Local development reference

## 📝 Deployment Steps

### Backend (Railway)
```bash
# 1. Login to Railway
railway login

# 2. Create new project
railway new

# 3. Add services
railway add --database postgres
railway add --database redis

# 4. Deploy
railway up

# 5. Copy .env.railway contents to Railway dashboard
```

### Frontend (Vercel)
```bash
# 1. Navigate to frontend
cd lapis-frontend

# 2. Deploy
vercel --prod

# 3. Add environment variables from .env.vercel
```

## ⚠️ Important Updates Required

After deployment, update these values:

1. **Railway (.env.railway)**:
   - `MONGODB_URI` - Your MongoDB Atlas connection string
   - `GOOGLE_API_KEY` - Your Gemini API key
   - `CORS_ORIGINS` - Add your Vercel URL

2. **Vercel (.env.vercel)**:
   - `NEXT_PUBLIC_API_URL` - Your Railway backend URL

## 🔒 Security Notes

- All secrets are cryptographically generated
- Never commit .env files to Git
- Rotate secrets regularly
- Use environment-specific values

## 📞 Support Resources

- Railway Discord: https://discord.gg/railway
- Vercel Support: https://vercel.com/support
- MongoDB Atlas Docs: https://docs.atlas.mongodb.com
