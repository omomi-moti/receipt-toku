// Upload and health-check page for starting analysis.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Dropzone } from "@/components/Dropzone";
import { Loading } from "@/components/Loading";
import { ErrorBox } from "@/components/ErrorBox";
import { healthCheck } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";
import { Scan, Wifi, PenLine, History } from "lucide-react";

type Props = {
  file: File | null;
  onFileChange: (file: File | null) => void;
  onAnalyze: (file: File) => Promise<void>;
  isAnalyzing: boolean;
  lastResult: AnalyzeResponse | null;
  clearError: () => void;
};

export function Home({ file, onFileChange, onAnalyze, isAnalyzing, lastResult, clearError }: Props) {
  const navigate = useNavigate();
  const [healthStatus, setHealthStatus] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  const handleAnalyze = async () => {
    if (!file) {
      setError("画像ファイルを選択してください");
      return;
    }
    clearError();
    setError(null);
    try {
      await onAnalyze(file);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "解析に失敗しました";
      setError(msg);
    }
  };

  const doHealthCheck = async () => {
    setChecking(true);
    setHealthStatus("");
    try {
      const res = await healthCheck();
      const ok = res.ok ? "OK" : "NG";
      const model = res.vision_model?.join(", ") || "unknown";
      setHealthStatus(`バックエンド: ${ok} / Vision: ${model} / APP_ID: ${res.estat_app_id_set ? "set" : "unset"}`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "接続テストに失敗しました";
      setHealthStatus(msg);
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="space-y-4">
      <Dropzone onFileSelected={(f) => onFileChange(f)} />

      {file && (
        <p className="text-sm">
          選択中: <span className="font-semibold">{file.name}</span>
        </p>
      )}

      <div className="flex flex-wrap gap-3">
        <Button onClick={handleAnalyze} disabled={!file || isAnalyzing}>
          <Scan className="h-4 w-4 mr-2" />
          {isAnalyzing ? "解析中..." : "解析する"}
        </Button>
        <Button variant="outline" onClick={doHealthCheck} disabled={checking}>
          <Wifi className="h-4 w-4 mr-2" />
          {checking ? "確認中..." : "接続テスト"}
        </Button>
        <Button variant="outline" onClick={() => navigate("/edit")}>
          <PenLine className="h-4 w-4 mr-2" />
          手入力で進む
        </Button>
        {lastResult && (
          <Button variant="secondary" onClick={() => navigate("/result")}>
            <History className="h-4 w-4 mr-2" />
            前回の結果を見る
          </Button>
        )}
      </div>

      {isAnalyzing && <Loading label="解析中..." />}

      {healthStatus && (
        <p className="text-sm text-muted-foreground">{healthStatus}</p>
      )}

      {error && (
        <ErrorBox
          message="エラー"
          detail={error}
          onRetry={handleAnalyze}
          onAlternate={() => navigate("/edit")}
        />
      )}
    </div>
  );
}
