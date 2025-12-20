// Editable table for item fields on the edit page.
import { ItemResult } from "../lib/types";

type Props = {
  items: ItemResult[];
  onChange: (items: ItemResult[]) => void;
};

export function EditItemForm({ items, onChange }: Props) {
  const handleChange = (idx: number, field: keyof ItemResult, value: string) => {
    const next = items.map((it, i) =>
      i === idx
        ? {
            ...it,
            [field]:
              field === "paid_unit_price" || field === "quantity"
                ? value === ""
                  ? null
                  : Number(value)
                : value
          }
        : it
    );
    onChange(next);
  };

  const addRow = () => {
    onChange([
      ...items,
      { raw_name: "", canonical: "", paid_unit_price: null, quantity: 1, estat: { judgement: "UNKNOWN", note: "手入力" } }
    ]);
  };

  return (
    <div className="card" style={{ marginTop: 12 }}>
      <div className="flex space-between" style={{ alignItems: "center" }}>
        <h3 className="section-title">アイテム編集</h3>
        <button className="btn btn-secondary" onClick={addRow}>
          行を追加
        </button>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>canonical / 品目名</th>
              <th>支払い単価</th>
              <th>数量</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, idx) => (
              <tr key={idx}>
                <td>
                  <input
                    className="input"
                    value={item.canonical ?? item.raw_name ?? ""}
                    onChange={(e) => handleChange(idx, "canonical", e.target.value)}
                    placeholder="例: 食パン"
                  />
                </td>
                <td>
                  <input
                    className="input"
                    type="number"
                    value={item.paid_unit_price ?? ""}
                    onChange={(e) => handleChange(idx, "paid_unit_price", e.target.value)}
                    min={0}
                    step="0.01"
                  />
                </td>
                <td>
                  <input
                    className="input"
                    type="number"
                    value={item.quantity ?? 1}
                    onChange={(e) => handleChange(idx, "quantity", e.target.value)}
                    min={1}
                    step="1"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
