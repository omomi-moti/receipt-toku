// Drag-and-drop file picker for receipt images.
import { useCallback, useRef, useState, type KeyboardEvent } from "react";

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
      style={{
        border: "2px dashed #cbd5e1",
        borderRadius: 12,
        padding: 20,
        textAlign: "center",
        background: dragOver ? "#e0f2fe" : "#f8fafc",
        cursor: "pointer"
      }}
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={handleKeyDown}
    >
      <p style={{ margin: 0, fontWeight: 600 }}>レシート画像をドラッグ＆ドロップ</p>
      <p className="muted" style={{ marginTop: 6 }}>
        またはクリックしてファイルを選択
      </p>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        style={{ display: "none" }}
        onChange={(e) => handleFiles(e.target.files)}
      />
      {error && <p style={{ color: "#b91c1c", marginTop: 8 }}>{error}</p>}
    </div>
  );
}
