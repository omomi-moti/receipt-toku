// Local history viewer for saved results.
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ItemTable } from "@/components/ItemTable";
import { clearHistory, deleteHistoryItem, loadHistory } from "@/lib/storage";
import type { StoredResult } from "@/lib/types";
import { Trash2, Trash, Calendar, Package } from "lucide-react";
import { cn } from "@/lib/utils";

export function HistoryPage() {
  const [history, setHistory] = useState<StoredResult[]>([]);
  const [selected, setSelected] = useState<StoredResult | null>(null);

  useEffect(() => {
    const h = loadHistory();
    setHistory(h);
    setSelected(h[0] || null);
  }, []);

  const handleDelete = (id: string) => {
    deleteHistoryItem(id);
    const next = loadHistory();
    setHistory(next);
    if (selected?.id === id) {
      setSelected(next[0] || null);
    }
  };

  const handleClear = () => {
    clearHistory();
    setHistory([]);
    setSelected(null);
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold">ローカル履歴</h2>
          <p className="text-sm text-muted-foreground">
            保存した解析結果を閲覧・管理できます
          </p>
        </div>
        {history.length > 0 && (
          <Button variant="destructive" size="sm" onClick={handleClear}>
            <Trash2 className="h-4 w-4 mr-2" />
            全削除
          </Button>
        )}
      </div>

      {/* Content */}
      {history.length === 0 ? (
        <Card className="flex-1 flex items-center justify-center">
          <CardContent className="text-center py-12 text-muted-foreground">
            <Package className="h-16 w-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium mb-2">履歴がありません</p>
            <p className="text-sm">レシートを解析して保存するとここに表示されます</p>
          </CardContent>
        </Card>
      ) : (
        <div className="flex gap-4 flex-1 min-h-0">
          {/* History List */}
          <Card className="w-80 flex flex-col">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                保存済み ({history.length}件)
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-2 min-h-0">
              <ScrollArea className="h-full">
                <div className="space-y-2 pr-2">
                  {history.map((h) => (
                    <div
                      key={h.id}
                      className={cn(
                        "p-3 rounded-lg cursor-pointer transition-all border",
                        selected?.id === h.id
                          ? "bg-primary/10 border-primary/50 ring-1 ring-primary/30"
                          : "bg-card hover:bg-muted/50 border-transparent hover:border-muted"
                      )}
                      onClick={() => setSelected(h)}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                          <span className="font-medium text-sm">
                            {h.result.purchase_date || "-"}
                          </span>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(h.id);
                          }}
                        >
                          <Trash className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{new Date(h.timestamp).toLocaleDateString()}</span>
                        <span>{h.result.items.length} 品目</span>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Detail View */}
          <Card className="flex-1 flex flex-col min-h-0">
            {selected ? (
              <>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">
                      {selected.result.purchase_date || "購入日不明"}
                    </CardTitle>
                    <span className="text-sm text-muted-foreground">
                      {new Date(selected.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex gap-4 mt-2">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="w-2 h-2 rounded-full bg-green-500"></span>
                      <span className="text-muted-foreground">DEAL:</span>
                      <span className="font-medium text-green-500">
                        {selected.result.items.filter(i => i.estat?.judgement === "DEAL").length}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="w-2 h-2 rounded-full bg-red-500"></span>
                      <span className="text-muted-foreground">OVERPAY:</span>
                      <span className="font-medium text-red-500">
                        {selected.result.items.filter(i => i.estat?.judgement === "OVERPAY").length}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                      <span className="text-muted-foreground">UNKNOWN:</span>
                      <span className="font-medium text-yellow-500">
                        {selected.result.items.filter(i => !i.estat?.judgement || i.estat?.judgement === "UNKNOWN").length}
                      </span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 overflow-auto">
                  <ItemTable items={selected.result.items} />
                </CardContent>
              </>
            ) : (
              <CardContent className="flex-1 flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>左のリストから選択してください</p>
                </div>
              </CardContent>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
