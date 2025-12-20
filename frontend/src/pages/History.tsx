// Local history viewer for saved results.
import { useEffect, useState } from "react";
import { ItemTable } from "../components/ItemTable";
import { clearHistory, deleteHistoryItem, loadHistory, StoredResult } from "../lib/storage";

export function HistoryPage() {
  const [history, setHistory] = useState<StoredResult[]>([]);
  const [selected, setSelected] = useState<StoredResult | null>(null);

  useEffect(() => {
    const h = loadHistory();
    setHistory(h);
    setSelected(h[0] || null);
  }, []);

  const handleDelete = (at: number) => {
    deleteHistoryItem(at);
    const next = loadHistory();
    setHistory(next);
    if (selected?.at === at) {
      setSelected(next[0] || null);
    }
  };

  const handleClear = () => {
    clearHistory();
    setHistory([]);
    setSelected(null);
  };

  return (
    <div className="card">
      <div className="flex space-between" style={{ alignItems: "center" }}>
        <h2 className="section-title">ローカル履歴</h2>
        {history.length > 0 && (
          <button className="btn btn-secondary" onClick={handleClear}>
            全削除
          </button>
        )}
      </div>
      {history.length === 0 && <p>履歴がありません。UNKNOWN などを保存するとここに表示されます。</p>}
      {history.length > 0 && (
        <div className="flex gap" style={{ alignItems: "flex-start" }}>
          <div style={{ width: "40%" }}>
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {history.map((h, idx) => (
                <li
                  key={h.at}
                  style={{
                    padding: "10px 12px",
                    marginBottom: 6,
                    borderRadius: 10,
                    border: "1px solid #e2e8f0",
                    background: selected?.at === h.at ? "#e0f2fe" : "#fff",
                    cursor: "pointer"
                  }}
                  onClick={() => setSelected(h)}
                >
                  <div className="flex space-between" style={{ alignItems: "center", marginBottom: 4 }}>
                    <p style={{ margin: 0, fontWeight: 700 }}>購入日: {h.payload.purchase_date || "-"}</p>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: "4px 8px", fontSize: 12 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(h.at);
                      }}
                    >
                      削除
                    </button>
                  </div>
                  <p className="muted" style={{ margin: 0 }}>
                    {new Date(h.at).toLocaleString()} / items: {h.payload.items?.length || 0}
                  </p>
                </li>
              ))}
            </ul>
          </div>
          <div style={{ flex: 1 }}>
            {selected ? (
              <>
                <p className="muted" style={{ marginTop: 0 }}>
                  保存時刻: {new Date(selected.at).toLocaleString()}
                </p>
                {selected.payload.items && <ItemTable items={selected.payload.items} />}
              </>
            ) : (
              <p>左のリストから選択してください。</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
