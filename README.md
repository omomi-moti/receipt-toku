このリポジトリはチームリポジトリからfetchしたものです
# Receipt Deal Checker (Receipt AI Analyzer)

レシート画像をAIで解析し、市場価格（e-Stat）と比較してお得度を判定するアプリケーションです。
日々の買い物がお得だったのか（DEAL）、適正価格だったのか（FAIR）、高かったのか（OVERPAY）を可視化し、節約額のランキング機能などで楽しく節約をサポートします。

## 🚀 主な機能

- **レシート画像解析**: Google Gemini Pro Visionを使用してレシート画像を読み取り、品目・価格・数量を自動抽出します。
- **市場価格比較**: 政府統計の総合窓口（e-Stat）のAPIから取得した市場価格データと購入価格を比較します。
- **お得度判定**: 商品ごとに「DEAL（お得）」「FAIR（適正）」「OVERPAY（割高）」を判定します。
- **節約額ランキング**: ユーザーごとの純節約額（節約額 - 過払い額）を集計し、ランキング形式で表示します。
- **履歴管理**: 過去のレシート解析結果を保存・閲覧できます。
- **結果編集**: AIの解析結果をユーザーが手動で修正・補正することが可能です。

## 🛠️ 技術スタック

### Frontend
- **Framework**: React (Vite)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **State/Routing**: React Router, Supabase Auth

### Backend
- **Framework**: FastAPI (Python)
- **Package Manager**: uv
- **AI Model**: Google Gemini 1.5 Pro / Flash
- **Data Source**: e-Stat API (小売物価統計調査)
- **Database**: Supabase (PostgreSQL)

### Infrastructure
- **Containerization**: Docker, Docker Compose
- **Hosting**: (想定: Render, Vercel, or Cloud Run)

## ⚙️ セットアップと実行方法

### 前提条件
- Docker Desktop がインストールされていること
- Google AI Studio の API Key (Gemini API)
- e-Stat の アプリケーションID
- Supabase プロジェクト (URL & Anon Key)

### 環境変数の設定

プロジェクトルートの `docker/.env.example` をコピーして `docker/.env` を作成し、必要な値を設定してください。

```bash
cp docker/.env.example docker/.env
```

`docker/.env` の中身を編集します:

```ini
# Backend Settings
GEMINI_API_KEY=your_gemini_api_key
ESTAT_APP_ID=your_estat_app_id
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Frontend Settings (Vite prefix required)
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### アプリケーションの起動

Docker Compose を使用してバックエンドとフロントエンドを一括で起動します。

```bash
cd docker
docker-compose up --build
```

起動後、以下のURLでアクセスできます。
- **Frontend**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/docs

## 📂 プロジェクト構成

```
.
├── backend/            # Python/FastAPI Backend
│   ├── main.py         # API Entrypoint
│   ├── services/       # Business Logic (AI, e-Stat, Parsing)
│   ├── schemas/        # Pydantic Models
│   ├── db/             # Database Connection
│   └── ...
├── frontend/           # React/TypeScript Frontend
│   ├── src/
│   │   ├── components/ # UI Components
│   │   ├── pages/      # Page Views
│   │   ├── lib/        # API Client & Utils
│   │   └── ...
├── docker/             # Docker Configuration
│   ├── docker-compose.yml
│   └── ...
├── supabase/           # Database Migrations
└── ...
```

## 📝 開発フロー

### バックエンド開発 (Local)
`uv` を使用して依存関係を管理しています。

```bash
cd backend
uv sync
source .venv/bin/activate
fastapi dev main.py
```

### フロントエンド開発 (Local)

```bash
cd frontend
npm install
npm run dev
```
