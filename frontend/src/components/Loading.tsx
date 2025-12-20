// Simple loading indicator with optional label.
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type Props = {
  label?: string;
  className?: string;
};

export function Loading({ label = "読み込み中", className }: Props) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <Loader2 className="h-5 w-5 animate-spin text-primary" />
      <span className="text-muted-foreground">{label}</span>
    </div>
  );
}
