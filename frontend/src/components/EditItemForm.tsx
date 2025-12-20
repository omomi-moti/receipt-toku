// Editable table for item fields on the edit page.
import type { ItemResult } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

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
    <Card className="mt-4">
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle className="text-lg">アイテム編集</CardTitle>
        <Button variant="outline" size="sm" onClick={addRow}>
          <Plus className="h-4 w-4 mr-2" />
          行を追加
        </Button>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead className="min-w-[200px]">canonical / 品目名</TableHead>
                <TableHead className="min-w-[120px]">支払い単価</TableHead>
                <TableHead className="min-w-[100px]">数量</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item, idx) => (
                <TableRow key={idx}>
                  <TableCell>
                    <Input
                      value={item.canonical ?? item.raw_name ?? ""}
                      onChange={(e) => handleChange(idx, "canonical", e.target.value)}
                      placeholder="例: 食パン"
                      className="bg-background"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      value={item.paid_unit_price ?? ""}
                      onChange={(e) => handleChange(idx, "paid_unit_price", e.target.value)}
                      min={0}
                      step="0.01"
                      className="bg-background"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      value={item.quantity ?? 1}
                      onChange={(e) => handleChange(idx, "quantity", e.target.value)}
                      min={1}
                      step="1"
                      className="bg-background"
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
