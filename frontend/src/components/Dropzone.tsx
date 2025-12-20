// Drag-and-drop file picker for receipt images.
import { useCallback, useRef, useState, type KeyboardEvent } from "react";
import { Upload } from "lucide-react";
import { cn } from "@/lib/utils";

type Props = {
  onFileSelected: (file: File) => void;
};

export function Dropzone({ onFileSelected }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      if (e.key === " ") {
        e.preventDefault();
      }
      inputRef.current?.click();
    }
  };

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const file = files[0];
      if (!file.type.startsWith("image/")) {
        setError("画像ファイルを選択してください");
        return;
      }
      setError(null);
      onFileSelected(file);
    },
    [onFileSelected]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleFiles(e.dataTransfer?.files || null);
      }}
      className={cn(
        "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200",
        "bg-muted/50 border-muted-foreground/25",
        "hover:border-primary/50 hover:bg-muted",
        dragOver && "border-primary bg-primary/10 scale-[1.02]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      )}
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={handleKeyDown}
    >
      <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
      <p className="font-semibold text-foreground">
        レシート画像をドラッグ＆ドロップ
      </p>
      <p className="text-sm text-muted-foreground mt-2">
        またはクリックしてファイルを選択
      </p>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      {error && <p className="text-destructive text-sm mt-3">{error}</p>}
    </div>
  );
}
