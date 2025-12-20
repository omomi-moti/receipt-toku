# Receipt Deal Checker Frontend

Frontend setup and usage notes for the receipt checker UI.

Vite + React + TypeScript で実装したフロントエンドです。レシート画像をアップロードし、バックエンドの FastAPI と連携して e-Stat 価格との比較結果を表示・修正・保存できます。

## 前提
- Node.js (LTS 推奨)
- バックエンド (FastAPI) が起動していること  
  例: `uvicorn main:app --reload --host 0.0.0.0 --port 8000` （リポジトリルートで実行）

## セットアップ
```bash
cd frontend
cp .env.example .env       # VITE_API_BASE_URL をバックエンドURLに設定
npm install
npm run dev
```

## 環境変数
- `VITE_API_BASE_URL` : バックエンドのベースURL。フロントと同一オリジンなら `/` のままでOK。例: `http://localhost:8000`
  - 開発時に `vite.config.ts` の `/api` プロキシを使う場合は未設定（空）でもOK

## 開発サーバー
- 起動: `npm run dev`
- ビルド: `npm run build`
- 型チェックのみ: `npm run lint`
- `vite.config.ts` の `server.proxy` で `/api` をバックエンドへプロキシしています。
  - `VITE_API_BASE_URL` 未設定時は `/api` がデフォルトになります。

## 画面フロー
1. **トップ/アップロード** (`/`)  
   - 画像のドラッグ＆ドロップまたは選択  
   - 「解析する」で `/analyzeReceipt` に multipart 送信  
   - 「接続テスト」で `/health` を確認  
   - 失敗時はエラー表示＋再試行/手入力導線
2. **結果表示** (`/result`)  
   - サマリ・アイテム表・判定表示  
   - UNKNOWN の行をハイライト  
   - 「修正する」で編集画面へ / 「もう一度解析」で同じ画像を再送信  
   - 「新規データとしてローカル保存」で localStorage に履歴保存  
   - デバッグ情報は折りたたみ
3. **修正** (`/edit`)  
   - canonical/価格/数量を編集可能なフォーム  
   - metaSearch で候補検索を表示（コピーして貼り付ける運用）  
   - 「修正内容を反映」で結果画面を更新（画像必須の再解析が難しい場合の暫定対応）
4. **履歴** (`/history`)  
   - localStorage に保存した結果一覧を参照・詳細表示

## API 実装メモ
- fetch ベースで `src/lib/api.ts` にラッパーを用意  
- `/analyzeReceipt` は multipart/form-data で画像を送信  
- `/metaSearch` はクエリパラメータ `q` を付与して GET  
- ベースURLは `import.meta.env.VITE_API_BASE_URL` から解決

## ディレクトリ構成
```
frontend/
  src/
    App.tsx, main.tsx
    pages/ (Home, Result, Edit, History)
    components/ (Dropzone, ItemTable, EditItemForm, DebugPanel, Loading, ErrorBox)
    lib/ (api.ts, types.ts, storage.ts)
    styles/global.css
  vite.config.ts
  tsconfig*.json
  .env.example
  README.md
```
