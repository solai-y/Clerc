# 🚀 Deployment Guide

## **Environment Configuration**

Your frontend is configured to work seamlessly across different environments using environment variables.

### **📁 Environment Files Structure:**

```
frontend/
├── .env.example          # Template with all available variables
├── .env.local           # Local development (ignored by git)
├── .env.development     # Development defaults (committed)
└── .env.production      # Production values (committed)
```

### **🔄 For Local Development (Current Setup)**

Currently working with:
- **Document Service**: `http://localhost:5003`
- **Frontend**: `http://localhost:3000`

No changes needed - everything is already configured!

### **🌐 For Dev/Production Deployment**

**When you're ready to deploy to dev environment:**

1. **Update `.env.production`** (THIS IS THE ONLY FILE YOU NEED TO CHANGE):
   ```bash
   # Change this line in .env.production:
   NEXT_PUBLIC_DOCUMENT_SERVICE_URL=https://your-dev-api-domain.com
   
   # Example:
   NEXT_PUBLIC_DOCUMENT_SERVICE_URL=https://api.dev.yourcompany.com
   ```

2. **That's it!** 🎉 All API calls will automatically use the new URL.

### **🔧 Environment Variable Priority**

Next.js loads environment variables in this order (highest to lowest priority):
1. `.env.local` (always ignored by git)
2. `.env.production` or `.env.development` (based on NODE_ENV)
3. `.env`

### **📍 Where URLs Are Used**

All backend API calls are centralized in `/lib/api.ts`:
- ✅ Document listing: `GET /documents`
- ✅ Document details: `GET /documents/{id}`  
- ✅ Create document: `POST /documents`
- ✅ Update document: `PUT /documents/{id}`
- ✅ Delete document: `DELETE /documents/{id}`
- ✅ Update status: `PATCH /documents/{id}/status`

### **🧪 Testing Different Environments**

```bash
# Test with local URLs
npm run dev

# Test with production URLs (without building)
NODE_ENV=production npm run dev

# Build and test production
npm run build
npm run start
```

### **🔒 Security Notes**

- ✅ All environment variables use `NEXT_PUBLIC_` prefix (required for client-side)
- ✅ `.env.local` is git-ignored for sensitive local config
- ✅ Production URLs are committed to git (not sensitive)

### **🚀 Deployment Checklist**

Before deploying to dev/production:

- [ ] Update `NEXT_PUBLIC_DOCUMENT_SERVICE_URL` in `.env.production`
- [ ] Test build: `npm run build`
- [ ] Verify environment: Check Network tab in browser DevTools
- [ ] Test all CRUD operations work with new URL

### **🔧 Alternative Configuration Options**

If your dev environment uses a different structure:

```bash
# Option 1: Direct service URL (current setup)
NEXT_PUBLIC_DOCUMENT_SERVICE_URL=https://document-api.dev.com

# Option 2: If using API gateway/nginx
NEXT_PUBLIC_API_URL=https://api.dev.com
# This would make document calls go to: https://api.dev.com/documents
```

## **💡 Benefits of This Setup**

- ✅ **One file change** for deployment
- ✅ **Environment-specific** configuration
- ✅ **Git-safe** (no sensitive data in commits)
- ✅ **Team-friendly** (developers can have different local setups)
- ✅ **CI/CD ready** (can override with environment variables)

---

**📞 Ready to Deploy?** Just update the URL in `.env.production` and deploy! 🎯