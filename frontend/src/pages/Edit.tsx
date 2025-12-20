// Manual correction page with metaSearch helper.
import { useEffect, useMemo, useState } from "react";
import { EditItemForm } from "../components/EditItemForm";
import { Loading } from "../components/Loading";
import { ErrorBox } from "../components/ErrorBox";
import { metaSearch } from "../lib/api";
import { AnalyzeResponse, ItemResult, MetaHit } from "../lib/types";

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
      setHits(res.hits || []);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "metaSearch に失敗しました";
      setSearchError(msg);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="card">
      <div className="flex space-between" style={{ alignItems: "center" }}>
        <h2 className="section-title">データ修正</h2>
        <div className="flex gap">
          <button className="btn btn-secondary" onClick={onBack}>
            結果へ戻る
          </button>
          <button className="btn btn-primary" onClick={save}>
            修正内容を反映
          </button>
        </div>
      </div>

      <div style={{ marginTop: 10 }}>
        <label className="muted">購入日 (YYYY-MM-DD)</label>
        <input className="input" value={purchaseDate} onChange={(e) => setPurchaseDate(e.target.value)} placeholder="2024-04-01" />
      </div>

      <EditItemForm items={items} onChange={setItems} />

      <div className="card" style={{ marginTop: 12 }}>
        <h3 className="section-title">metaSearch (候補サジェスト)</h3>
        <p className="muted" style={{ marginTop: 0 }}>
          canonical や品目名を入力して e-Stat メタを検索します。ヒットした名称をコピーして貼り付けてください。
        </p>
        <div className="flex gap" style={{ alignItems: "center" }}>
          <input
            className="input"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="例: 食パン / 鶏卵"
            style={{ flex: 1 }}
          />
          <button className="btn btn-secondary" onClick={runSearch} disabled={searching || !searchTerm}>
            {searching ? "検索中..." : "候補を検索"}
          </button>
        </div>
        {searching && (
          <div style={{ marginTop: 6 }}>
            <Loading label="検索中..." />
          </div>
        )}
        {searchError && (
          <div style={{ marginTop: 8 }}>
            <ErrorBox message="metaSearch エラー" detail={searchError} />
          </div>
        )}
        {hits.length > 0 && (
          <div style={{ marginTop: 10 }}>
            <table className="table">
              <thead>
                <tr>
                  <th>class_id</th>
                  <th>name</th>
                  <th>code</th>
                </tr>
              </thead>
              <tbody>
                {hits.slice(0, META_HITS_LIMIT).map((h, idx) => (
                  <tr key={`${h.code}-${idx}`}>
                    <td>{h.class_id}</td>
                    <td>{h.name}</td>
                    <td>{h.code}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
