// Results page showing summary counts and the item table.
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { DebugPanel } from "@/components/DebugPanel";
import { ItemTable } from "@/components/ItemTable";
import { saveHistory } from "@/lib/storage";
import type { AnalyzeResponse, StoredResult } from "@/lib/types";
import { Edit, RefreshCw, Save, History, AlertTriangle, Check, Upload } from "lucide-react";

type Props = {
  result: AnalyzeResponse | null;
  onEdit: () => void;
  onReAnalyze?: () => Promise<void>;
  onUpload: () => void;
  summaryCount: { deal: number; overpay: number; unknown: number };
};

export function ResultPage({ result, onEdit, onReAnalyze, onUpload, summaryCount }: Props) {
  const navigate = useNavigate();
  const [saved, setSaved] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  const items = useMemo(() => result?.items || [], [result]);

  if (!result) {
    return (
      <Card>
        <CardContent className="pt-6 text-center">
          <p className="text-muted-foreground mb-4">
            結果がまだありません。まずはレシートをアップロードしてください。
          </p>
          <Button onClick={onUpload}>
            <Upload className="h-4 w-4 mr-2" />
            アップロードへ
          </Button>
        </CardContent>
      </Card>
    );
  }

  const save = () => {
    const stored: StoredResult = {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      timestamp: Date.now(),
      result
    };
    saveHistory(stored);
    setSaved(true);
    setNote("ローカル履歴に保存しました");
  };

  const unknownItems = items.filter((i) => (i.estat?.judgement || "UNKNOWN") === "UNKNOWN");

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle>解析結果</CardTitle>
          <CardDescription>購入日: {result.purchase_date || "-"}</CardDescription>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onEdit}>
            <Edit className="h-4 w-4 mr-2" />
            修正する
          </Button>
          {onReAnalyze && (
            <Button onClick={() => onReAnalyze()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              もう一度解析
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-4">
          <Card className="bg-green-500/10 border-green-500/20">
            <CardContent className="pt-4">
              <p className="text-sm font-medium text-green-500">DEAL</p>
              <p className="text-2xl font-bold text-green-400">{summaryCount.deal} 件</p>
            </CardContent>
          </Card>
          <Card className="bg-red-500/10 border-red-500/20">
            <CardContent className="pt-4">
              <p className="text-sm font-medium text-red-500">OVERPAY</p>
              <p className="text-2xl font-bold text-red-400">{summaryCount.overpay} 件</p>
            </CardContent>
          </Card>
          <Card className="bg-yellow-500/10 border-yellow-500/20">
            <CardContent className="pt-4">
              <p className="text-sm font-medium text-yellow-500">UNKNOWN</p>
              <p className="text-2xl font-bold text-yellow-400">{summaryCount.unknown} 件</p>
            </CardContent>
          </Card>
        </div>

        <Separator />

        <ItemTable items={items} />

        {unknownItems.length > 0 && (
          <Alert className="bg-yellow-500/10 border-yellow-500/30">
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
            <AlertTitle className="text-yellow-500">比較対象がありませんでした</AlertTitle>
            <AlertDescription className="text-yellow-400/80">
              UNKNOWN の行を修正して再解析するか、「新規データとしてローカル保存」を試してください。
            </AlertDescription>
          </Alert>
        )}

        <div className="flex gap-3">
          <Button variant="outline" onClick={save} disabled={saved}>
            {saved ? <Check className="h-4 w-4 mr-2" /> : <Save className="h-4 w-4 mr-2" />}
            {saved ? "保存済み" : "新規データとしてローカル保存"}
          </Button>
          <Button variant="outline" onClick={() => navigate("/")}>
            <History className="h-4 w-4 mr-2" />
            履歴を見る
          </Button>
        </div>

        {note && <p className="text-sm text-muted-foreground">{note}</p>}

        <DebugPanel data={result.debug as Record<string, unknown> | undefined} />
      </CardContent>
    </Card>
  );
}
