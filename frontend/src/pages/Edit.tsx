// Manual correction page with metaSearch helper.
import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EditItemForm } from "@/components/EditItemForm";
import { Loading } from "@/components/Loading";
import { ErrorBox } from "@/components/ErrorBox";
import { metaSearch } from "@/lib/api";
import type { AnalyzeResponse, ItemResult, MetaHit } from "@/lib/types";
import { ArrowLeft, Check, Search } from "lucide-react";

type Props = {
  result: AnalyzeResponse | null;
  onUpdate: (result: AnalyzeResponse) => void;
  onBack: () => void;
};

const emptyItem: ItemResult = { raw_name: "", canonical: "", paid_unit_price: null, quantity: 1, estat: { judgement: "UNKNOWN" } };
const META_HITS_LIMIT = 10;

export function EditPage({ result, onUpdate, onBack }: Props) {
  const initialItems = useMemo(() => (result?.items && result.items.length > 0 ? result.items : [emptyItem]), [result]);
  const [items, setItems] = useState<ItemResult[]>(initialItems);
  const [purchaseDate, setPurchaseDate] = useState(result?.purchase_date || "");
  const [searchTerm, setSearchTerm] = useState("");
  const [hits, setHits] = useState<MetaHit[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  useEffect(() => {
    setItems(initialItems);
  }, [initialItems]);

  const save = () => {
    const summary = {
      deal_count: items.filter((i) => i.estat?.judgement === "DEAL").length,
      overpay_count: items.filter((i) => i.estat?.judgement === "OVERPAY").length,
      unknown_count: items.filter((i) => (i.estat?.judgement || "UNKNOWN") === "UNKNOWN").length,
      total_diff: items.reduce((sum, i) => sum + (i.estat?.diff || 0), 0)
    };
    const next: AnalyzeResponse = {
      ...(result || {}),
      purchase_date: purchaseDate || result?.purchase_date || "",
      items,
      summary
    };
    onUpdate(next);
  };

  const runSearch = async () => {
    if (!searchTerm) return;
    setSearching(true);
    setSearchError(null);
    try {
      const res = await metaSearch(searchTerm);
      setHits(res);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "metaSearch に失敗しました";
      setSearchError(msg);
    } finally {
      setSearching(false);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle>データ修正</CardTitle>
          <CardDescription>
            解析結果を手動で修正できます
          </CardDescription>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            結果へ戻る
          </Button>
          <Button onClick={save}>
            <Check className="h-4 w-4 mr-2" />
            修正内容を反映
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="purchase-date">購入日 (YYYY-MM-DD)</Label>
          <Input
            id="purchase-date"
            value={purchaseDate}
            onChange={(e) => setPurchaseDate(e.target.value)}
            placeholder="2024-04-01"
            className="max-w-xs"
          />
        </div>

        <EditItemForm items={items} onChange={setItems} />

        {/* metaSearch Section */}
        <Card className="border-dashed">
          <CardHeader>
            <CardTitle className="text-lg">metaSearch (候補サジェスト)</CardTitle>
            <CardDescription>
              canonical や品目名を入力して e-Stat メタを検索します。ヒットした名称をコピーして貼り付けてください。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-3">
              <Input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="例: 食パン / 鶏卵"
                className="flex-1"
              />
              <Button variant="outline" onClick={runSearch} disabled={searching || !searchTerm}>
                <Search className="h-4 w-4 mr-2" />
                {searching ? "検索中..." : "候補を検索"}
              </Button>
            </div>

            {searching && <Loading label="検索中..." />}
            {searchError && <ErrorBox message="metaSearch エラー" detail={searchError} />}

            {hits.length > 0 && (
              <div className="rounded-md border overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-muted/50">
                      <TableHead>class_id</TableHead>
                      <TableHead>name</TableHead>
                      <TableHead>code</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {hits.slice(0, META_HITS_LIMIT).map((h, idx) => (
                      <TableRow key={`${h.code}-${idx}`}>
                        <TableCell>{h.class_id}</TableCell>
                        <TableCell className="font-medium">{h.name}</TableCell>
                        <TableCell className="text-muted-foreground">{h.code}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  );
}
