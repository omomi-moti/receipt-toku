// Reusable error display with optional actions.
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertCircle, RefreshCw, PenLine } from "lucide-react";

type Props = {
  message: string;
  detail?: string;
  onRetry?: () => void;
  onAlternate?: () => void;
  alternateLabel?: string;
};

export function ErrorBox({ message, detail, onRetry, onAlternate, alternateLabel }: Props) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{message}</AlertTitle>
      {detail && <AlertDescription className="mt-2">{detail}</AlertDescription>}
      {(onRetry || onAlternate) && (
        <div className="flex gap-2 mt-4">
          {onRetry && (
            <Button variant="outline" size="sm" onClick={onRetry}>
              <RefreshCw className="h-4 w-4 mr-2" />
              再試行
            </Button>
          )}
          {onAlternate && (
            <Button size="sm" onClick={onAlternate}>
              <PenLine className="h-4 w-4 mr-2" />
              {alternateLabel || "手入力で進む"}
            </Button>
          )}
        </div>
      )}
    </Alert>
  );
}
