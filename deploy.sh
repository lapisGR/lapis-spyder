#!/bin/bash

# Lapis LLMT Spider Deployment Script
# Deploys backend to Railway and frontend to Vercel

set -e

echo "🚀 Starting Lapis LLMT Spider deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required CLIs are installed
check_requirements() {
    echo "📋 Checking requirements..."
    
    if ! command -v railway &> /dev/null; then
        echo -e "${RED}❌ Railway CLI not found. Please install it:${NC}"
        echo "brew install railway"
        exit 1
    fi
    
    if ! command -v vercel &> /dev/null; then
        echo -e "${RED}❌ Vercel CLI not found. Please install it:${NC}"
        echo "npm i -g vercel"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All requirements met${NC}"
}

# Deploy backend to Railway
deploy_backend() {
    echo -e "\n${YELLOW}🔧 Deploying Backend to Railway...${NC}"
    
    # Check if already linked to Railway
    if ! railway status &> /dev/null; then
        echo "Linking to Railway project..."
        railway login
        railway link
    fi
    
    # Deploy the main service
    echo "Deploying main API service..."
    railway up
    
    # Get the deployed URL
    BACKEND_URL=$(railway status --json | jq -r '.url')
    echo -e "${GREEN}✅ Backend deployed to: $BACKEND_URL${NC}"
    
    # Instructions for additional services
    echo -e "\n${YELLOW}📝 Next steps for Railway:${NC}"
    echo "1. Add PostgreSQL: railway add --database postgres"
    echo "2. Add Redis: railway add --database redis"
    echo "3. Configure MongoDB Atlas connection in Railway dashboard"
    echo "4. Deploy worker services using the Railway dashboard"
}

# Deploy frontend to Vercel
deploy_frontend() {
    echo -e "\n${YELLOW}🎨 Deploying Frontend to Vercel...${NC}"
    
    cd lapis-frontend
    
    # Deploy to Vercel
    echo "Deploying to Vercel..."
    vercel --prod
    
    # Get deployment URL
    echo -e "${GREEN}✅ Frontend deployed successfully${NC}"
    
    cd ..
}

# Create environment templates
create_env_templates() {
    echo -e "\n${YELLOW}📄 Creating environment templates...${NC}"
    
    # Railway environment template
    cat > .env.railway << 'EOF'
# Railway Backend Environment Variables

# API Configuration
API_HOST=0.0.0.0
API_PORT=$PORT
ENVIRONMENT=production

# Database URLs (Railway provides these)
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
MONGODB_URI=your-mongodb-atlas-uri

# Security
JWT_SECRET=generate-a-very-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DELTA=30

# Google Gemini
GOOGLE_API_KEY=your-gemini-api-key

# CORS (update with your Vercel URL)
CORS_ORIGINS=["https://your-app.vercel.app"]

# Celery
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
EOF

    # Vercel environment template
    cat > .env.vercel << 'EOF'
# Vercel Frontend Environment Variables

NEXT_PUBLIC_API_URL=https://your-backend.railway.app
EOF

    echo -e "${GREEN}✅ Environment templates created${NC}"
    echo "- Backend: .env.railway"
    echo "- Frontend: .env.vercel"
}

# Main deployment flow
main() {
    check_requirements
    create_env_templates
    
    echo -e "\n${YELLOW}Choose deployment option:${NC}"
    echo "1) Deploy both backend and frontend"
    echo "2) Deploy backend only (Railway)"
    echo "3) Deploy frontend only (Vercel)"
    
    read -p "Enter choice [1-3]: " choice
    
    case $choice in
        1)
            deploy_backend
            deploy_frontend
            ;;
        2)
            deploy_backend
            ;;
        3)
            deploy_frontend
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
    
    echo -e "\n${GREEN}🎉 Deployment complete!${NC}"
    echo -e "\n${YELLOW}📋 Post-deployment checklist:${NC}"
    echo "1. Configure environment variables in Railway dashboard"
    echo "2. Configure environment variables in Vercel dashboard"
    echo "3. Set up MongoDB Atlas and add connection string"
    echo "4. Run database initialization scripts"
    echo "5. Update CORS settings with your Vercel URL"
    echo "6. Deploy Celery worker and beat services in Railway"
}

# Run main function
main