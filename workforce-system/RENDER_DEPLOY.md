# Deploy to Render.com (Free Tier)

## Prerequisites
1. A [Render.com](https://render.com) account (free)
2. Your project pushed to a **GitHub** repository

---

## Step 1: Push to GitHub

```powershell
cd workforce-system
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/workforce-system.git
git branch -M main
git push -u origin main
```

---

## Step 2: Create a PostgreSQL Database on Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **New +** → **PostgreSQL**
3. Fill in:
   - **Name**: `workforce-db`
   - **Database**: `workforce`
   - **User**: `workforce_user`
   - **Region**: Choose one close to you
4. Click **Create Database**
5. Copy the **Internal Database URL** (starts with `postgresql://...`)

---

## Step 3: Deploy the Web Service

1. Click **New +** → **Web Service**
2. Connect your GitHub repo
3. Fill in:
   - **Name**: `workforce-system`
   - **Region**: Same as your database
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:create_app()`
4. Select **Free** plan
5. Click **Advanced** and add these environment variables:

| Key | Value |
|---|---|
| `SECRET_KEY` | (generate a random string) |
| `DATABASE_URL` | Paste your PostgreSQL Internal URL |
| `MAIL_USERNAME` | (optional) your Gmail |
| `MAIL_PASSWORD` | (optional) your Gmail app password |
| `MAIL_DEFAULT_SENDER` | (optional) your Gmail |

6. Click **Create Web Service**

---

## Step 4: Seed the Supply Catalog

After deployment, run this in Render's **Shell** tab:

```bash
python seed_catalog.py
```

---

## Step 5: Add Gunicorn to Requirements

Add `gunicorn` to `requirements.txt` for production:

```
gunicorn==21.2.0
```

---

## Useful Commands

| Action | Command |
|---|---|
| Run locally (Windows) | `python app.py` |
| Run locally (with waitress) | `pip install waitress && waitress-serve --port=5000 app:create_app` |
| Create admin user | Register via the web, then from shell: `python -c "from app import create_app; from models import db; from models.user import User; app=create_app(); app.app_context().push(); u=User.query.filter_by(email='admin@example.com').first(); u.role='admin'; db.session.commit()"` |

---

## Notes

- The **Free tier** spins down after 15 min of inactivity. First request after idle takes ~30s to wake up.
- Uploaded images are stored on the server's ephemeral disk. For production, use **Cloudinary** or **AWS S3**.
- To upgrade: Render's **Starter** plan ($7/month) keeps the service always-on.
