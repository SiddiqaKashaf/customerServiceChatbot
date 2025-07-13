# Deployment Guide - AI Customer Service Chatbot

## 🚀 Quick Deployment Options

### Option 1: Vercel (Recommended for Portfolio)

#### Frontend Deployment
1. **Install Vercel CLI**
```bash
npm install -g vercel
```

2. **Deploy Frontend**
```bash
cd frontend
npm run build
vercel --prod
```

3. **Configure Environment**
- Set `VITE_API_URL` to your backend URL
- Update CORS origins in backend

#### Backend Deployment
1. **Deploy to Vercel**
```bash
cd backend
vercel --prod
```

2. **Set Environment Variables**
```bash
vercel env add FLASK_ENV production
vercel env add CORS_ORIGINS https://your-frontend-domain.vercel.app
```

### Option 2: Railway (Full-Stack)

1. **Connect GitHub Repository**
2. **Deploy Backend**
   - Select `backend` folder
   - Set start command: `python app_final.py`
3. **Deploy Frontend**
   - Select `frontend` folder
   - Build command: `npm run build`
   - Start command: `npm run preview`

### Option 3: Heroku

#### Backend (Heroku)
1. **Create Procfile**
```
web: python app_final.py
```

2. **Deploy**
```bash
heroku create your-chatbot-api
git subtree push --prefix backend heroku main
```

#### Frontend (Netlify)
1. **Build Settings**
   - Build command: `npm run build`
   - Publish directory: `dist`

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5000
CORS_ORIGINS=https://your-frontend-domain.com
```

#### Frontend (.env)
```env
VITE_API_URL=https://your-backend-api.com/api
```

### CORS Configuration
Update `app_final.py`:
```python
CORS(app, origins=['https://your-frontend-domain.com'])
```

## 📱 Local Development

### Backend
```bash
cd backend
python app_final.py
# Runs on http://localhost:5001
```

### Frontend
```bash
cd frontend
npm run dev -- --host
# Runs on http://localhost:5173
```

## 🔍 Testing Deployment

### Health Check
```bash
curl https://your-api-domain.com/api/health
```

### Chat Test
```bash
curl -X POST https://your-api-domain.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

## 🛠 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Update CORS_ORIGINS environment variable
   - Ensure frontend URL is whitelisted

2. **Build Failures**
   - Check Node.js version (18+)
   - Verify all dependencies are installed

3. **API Connection Issues**
   - Verify backend URL in frontend config
   - Check network connectivity

### Performance Optimization

1. **Frontend**
   - Enable gzip compression
   - Use CDN for static assets
   - Implement code splitting

2. **Backend**
   - Add Redis caching
   - Implement connection pooling
   - Use production WSGI server (gunicorn)

## 📊 Monitoring

### Health Endpoints
- `/api/health` - System status
- `/api/stats` - Usage statistics

### Logging
- Frontend: Browser console
- Backend: Flask logs

## 🔐 Security

### Production Checklist
- [ ] HTTPS enabled
- [ ] CORS properly configured
- [ ] Environment variables secured
- [ ] Input validation enabled
- [ ] Rate limiting implemented
- [ ] Error messages sanitized

## 📈 Scaling

### Horizontal Scaling
- Load balancer configuration
- Database clustering
- CDN implementation

### Vertical Scaling
- Memory optimization
- CPU utilization monitoring
- Database indexing

---

**Your chatbot is now ready for production deployment!**

