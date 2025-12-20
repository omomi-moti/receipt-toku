// Simple loading indicator with optional label.
export function Loading({ label = "読み込み中..." }: { label?: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <span className="app-loading-spinner" />
      <span>{label}</span>
    </div>
  );
}
