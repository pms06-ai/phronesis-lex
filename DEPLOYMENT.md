# Phronesis LEX Deployment Guide

Deploy to Supabase (database) + Vercel (hosting).

## Prerequisites

- Supabase account (https://supabase.com)
- Vercel account (https://vercel.com)
- Anthropic API key (https://console.anthropic.com)
- Git repository (GitHub recommended)

---

## Step 1: Set Up Supabase Database

### 1.1 Create Supabase Project

1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Name: `phronesis-lex`
4. Choose a strong database password (save this!)
5. Select region closest to your users
6. Click "Create new project"

### 1.2 Run Database Schema

1. In Supabase dashboard, go to **SQL Editor**
2. Click "New query"
3. Copy the contents of `backend/db/schema_postgres.sql`
4. Paste into the SQL editor
5. Click "Run" (or Cmd/Ctrl + Enter)
6. Verify: Go to **Table Editor** - you should see 15 tables

### 1.3 Get Connection Credentials

1. Go to **Settings** > **Database**
2. Find "Connection string" section
3. Copy the **URI** (looks like: `postgresql://postgres:[PASSWORD]@...`)
4. Replace `[YOUR-PASSWORD]` with your actual password
5. Save this - you'll need it for Vercel

Also note:
- **Project URL**: `https://[project-ref].supabase.co`
- **Anon Key**: Found in Settings > API

---

## Step 2: Deploy to Vercel

### 2.1 Push to GitHub

```bash
cd /mnt/c/Users/pstep/phronesis-lex
git init
git add .
git commit -m "Initial commit - Phronesis LEX"
git remote add origin https://github.com/YOUR_USERNAME/phronesis-lex.git
git push -u origin main
```

### 2.2 Import to Vercel

1. Go to https://vercel.com/dashboard
2. Click "Add New..." > "Project"
3. Import your GitHub repository
4. Configure project:
   - **Framework Preset**: Other
   - **Root Directory**: `.` (leave as is)

### 2.3 Set Environment Variables

In Vercel project settings, add these environment variables:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Your Supabase PostgreSQL connection string |
| `SUPABASE_URL` | `https://[project-ref].supabase.co` |
| `SUPABASE_KEY` | Your Supabase anon key |
| `ANTHROPIC_API_KEY` | Your Anthropic API key (`sk-ant-...`) |
| `VERCEL` | `1` |

### 2.4 Deploy

1. Click "Deploy"
2. Wait for build to complete
3. Your app will be available at `https://phronesis-lex-[hash].vercel.app`

---

## Step 3: Configure Custom Domain (Optional)

1. In Vercel project, go to **Settings** > **Domains**
2. Add your custom domain (e.g., `phronesis.yourdomain.com`)
3. Follow DNS configuration instructions
4. Update `js/services/api.js` to recognize your domain:

```javascript
if (hostname.includes('vercel.app') || hostname.includes('yourdomain.com')) {
    return '';
}
```

---

## Environment Variables Reference

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-api03-...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | - |
| `SUPABASE_KEY` | Supabase anon/service key | - |
| `CLAUDE_MODEL` | Claude model to use | `claude-sonnet-4-20250514` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

---

## Local Development

### With Local SQLite (No Supabase)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

Frontend: Open `index.html` directly or use `python -m http.server 8080`

### With Supabase (Production DB Locally)

Create `backend/.env`:
```
DATABASE_URL=postgresql://postgres:yourpassword@db.xxx.supabase.co:5432/postgres
ANTHROPIC_API_KEY=sk-ant-...
```

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

---

## Vercel Project Structure

```
phronesis-lex/
├── vercel.json          # Vercel configuration
├── index.html           # Frontend entry point
├── css/                 # Stylesheets
├── js/                  # Frontend JavaScript
│   ├── services/api.js  # API client (auto-detects environment)
│   ├── stores/          # Alpine.js stores
│   └── components/      # UI components
└── backend/
    ├── api/
    │   └── index.py     # Vercel serverless entry point
    ├── db/
    │   ├── schema_postgres.sql  # Supabase schema
    │   └── supabase_connection.py
    ├── services/
    │   ├── claude_service.py
    │   └── document_processor.py
    └── requirements-vercel.txt
```

---

## Troubleshooting

### "Database connection failed"
- Check `DATABASE_URL` is correct
- Ensure password doesn't have special characters that need URL encoding
- Verify Supabase project is active

### "AI analysis not configured"
- Check `ANTHROPIC_API_KEY` is set in Vercel environment variables
- Verify API key is valid at https://console.anthropic.com

### "CORS error"
- Check browser console for specific origin
- Add origin to `CORS_ORIGINS` environment variable

### "Function timeout"
- Vercel free tier has 10s timeout
- Large documents may need Vercel Pro (60s timeout)
- Consider chunking large documents

---

## Upgrading

### Database Migrations

1. Write migration SQL
2. Run in Supabase SQL Editor
3. Update `schema_postgres.sql` for reference

### Code Updates

```bash
git add .
git commit -m "Update description"
git push origin main
# Vercel auto-deploys on push
```

---

## Security Notes

- Never commit `.env` files with real credentials
- Use Supabase Row Level Security (RLS) for production
- Rotate API keys periodically
- Enable Supabase auth for multi-user access
