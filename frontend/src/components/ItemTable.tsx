// Table view for analyzed items and price comparisons.
import type { ItemResult } from "@/lib/types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type Judgement = "DEAL" | "OVERPAY" | "FAIR" | "UNKNOWN";

type Props = {
  items: ItemResult[];
  showUnknownHighlight?: boolean;
};

function JudgementBadge({ judgement }: { judgement: Judgement }) {
  return (
    <Badge
      variant="outline"
      className={cn(
        judgement === "DEAL" && "bg-green-500/20 text-green-500 border-green-500/30",
        judgement === "OVERPAY" && "bg-red-500/20 text-red-500 border-red-500/30",
        judgement === "FAIR" && "bg-blue-500/20 text-blue-500 border-blue-500/30",
        judgement === "UNKNOWN" && "bg-yellow-500/20 text-yellow-500 border-yellow-500/30"
      )}
    >
      {judgement}
    </Badge>
  );
}

export function ItemTable({ items, showUnknownHighlight = true }: Props) {
  return (
    <div className="rounded-md border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50">
            <TableHead>raw_name</TableHead>
            <TableHead>canonical</TableHead>
            <TableHead className="text-right">paid_unit_price</TableHead>
            <TableHead className="text-right">quantity</TableHead>
            <TableHead className="text-right">stat_price</TableHead>
            <TableHead className="text-right">diff</TableHead>
            <TableHead className="text-right">rate</TableHead>
            <TableHead>judgement</TableHead>
            <TableHead>note</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item, idx) => {
            const j = (item.estat?.judgement || "UNKNOWN") as Judgement;
            const isUnknown = j === "UNKNOWN" && showUnknownHighlight;
            return (
              <TableRow
                key={`${item.raw_name}-${idx}`}
                className={cn(isUnknown && "bg-yellow-500/10")}
              >
                <TableCell className="font-medium">{item.raw_name}</TableCell>
                <TableCell>{item.canonical || "-"}</TableCell>
                <TableCell className="text-right">{item.paid_unit_price ?? "-"}</TableCell>
                <TableCell className="text-right">{item.quantity ?? "-"}</TableCell>
                <TableCell className="text-right">{item.estat?.stat_price ?? "-"}</TableCell>
                <TableCell className="text-right">{item.estat?.diff ?? "-"}</TableCell>
                <TableCell className="text-right">
                  {item.estat?.rate === undefined || item.estat?.rate === null
                    ? "-"
                    : `${(item.estat.rate * 100).toFixed(1)}%`}
                </TableCell>
                <TableCell><JudgementBadge judgement={j} /></TableCell>
                <TableCell className="text-muted-foreground">{item.estat?.note || "-"}</TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
