// Toggleable panel to view debug payloads.
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, Bug } from "lucide-react";

type Props = {
  data?: Record<string, unknown>;
};

export function DebugPanel({ data }: Props) {
  const [open, setOpen] = useState(false);

  if (!data) return null;

  return (
    <Card className="mt-4 border-dashed">
      <Collapsible open={open} onOpenChange={setOpen}>
        <CardHeader className="py-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <Bug className="h-4 w-4" />
              デバッグ情報
            </CardTitle>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm">
                {open ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
                <span className="ml-2">{open ? "閉じる" : "開く"}</span>
              </Button>
            </CollapsibleTrigger>
          </div>
        </CardHeader>
        <CollapsibleContent>
          <CardContent className="pt-0">
            <pre className="max-h-80 overflow-auto bg-slate-950 text-slate-100 dark:bg-slate-900 p-4 rounded-lg text-xs font-mono">
              {JSON.stringify(data, null, 2)}
            </pre>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
