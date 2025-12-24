# Receipt Deal Checker (Receipt AI Analyzer)

> ⚠️ 本リポジトリについて  
> 本リポジトリは、【技育CAMP2025】ハッカソン Vol.16（オンライン開催）にて開発した  
> **チームリポジトリから fetch した個人用リポジトリ**です。  
>  
> チームでの成果物をベースに、主に自身が担当したバックエンド実装・設計内容が含まれています。

- チームリポジトリ（原本）:  
>   https://github.com/＜organization or user＞/＜team-repo-name＞
---

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
## 👥 チーム体制・開発背景

- **イベント**: 【技育CAMP2025】ハッカソン Vol.16（オンライン開催）
- **開発形態**: チーム開発
- **チーム人数**: 5名
- **開発期間**:
  - 事前準備：約1週間
  - 本開発：ハッカソン期間中の2日間

本プロジェクトは、短期間のハッカソンという制約の中で、  
**実務を意識した設計・レビュー・改善サイクルを回すこと**を重視して開発しました。

---

## 🧑‍💻 担当領域

- 主に **バックエンド（FastAPI）** を担当
- Google Gemini を用いたレシート解析ロジックの実装
- e-Stat API を用いた市場価格取得・比較処理
- Pydantic を用いたデータ構造（スキーマ）設計
- 実務経験のあるメンバーによる **コードレビュー対応・改善**

※ Docker / インフラ周りは他メンバーが担当

---

## 🧠 実装で意識したこと

### FastAPI / Python 設計

- **FastAPI を用いたバックエンド開発（初挑戦）**
  - 公式ドキュメントやベストプラクティスを参照し、
    - ルーティング設計
    - 依存関係（Dependency Injection）
    - スキーマ分割
  を意識した構成で実装

- **型安全性を強く意識した実装**
  - `Any` 型は、JSON などやむを得ない箇所以外では使用しない
  - Pydantic モデルを中心に、API の入出力を厳密に定義
  - Optional 型（`Optional[T]`）を安易に使わず、
    - 値が存在しない状態は `None` を明示的に扱う方針を採用

---

### AI（Gemini）活用の工夫

- レシート解析および価格比較において、
  - e-Stat から取得した市場価格データは商品ごとに単位が異なる（g / kg / 個 など）
- この課題に対し、
  - **単位変換・正規化処理を Gemini API にプロンプトとして委譲**
  - 市場価格と購入価格を比較可能な形式に統一してから判定処理を行う設計とした

- AI の出力結果をそのまま信用せず、
  - ユーザーが解析結果を編集・補正できる設計を採用

---

## 🔍 苦労した点・課題

- **e-Stat API のデータ構造が複雑で分かりにくかった**
  - 統計表・分類コード・単位の理解に時間を要した
- **FastAPI における設計判断**
  - スキーマ分割の粒度
  - 依存関係の切り出し方
  - 短期間でも可読性・保守性を意識した構成への改善

これらについては、  
**実務経験のあるメンバーからコードレビューを受け、指摘を反映しながら修正**しました。

---

## 🧪 開発プロセスで意識したこと

- 機能単位でのコミットを徹底し、Git 履歴を整理
- レビューしやすい Pull Request の作成を意識
- 「とりあえず動く」ではなく、
  - **短期間でも保守性・可読性を意識した実装**を重視

---

## 🚧 今後の改善予定（Future Work）

- 市場価格の **地域差（都道府県別など）を考慮した比較機能**
- e-Stat データのキャッシュ戦略の導入
- レシート解析精度の向上（OCR との併用検討）
- テストコードの追加

---
