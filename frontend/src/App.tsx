// App shell with routes and shared state for analysis results.
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, Route, Routes, useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { ThemeToggle } from "@/components/theme-toggle";
import { Loading } from "@/components/Loading";
import { analyzeReceipt } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";
import { loadSessionResult, saveSessionResult } from "@/lib/storage";
import { Home } from "./pages/Home";
import { ResultPage } from "./pages/Result";
import { EditPage } from "./pages/Edit";
import { HistoryPage } from "./pages/History";
import { Upload, BarChart3, Edit, History, X, Receipt } from "lucide-react";

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);

  useEffect(() => {
    const stored = loadSessionResult();
    if (stored) {
      setResult(stored);
    }
  }, []);

  const runAnalyze = useCallback(
    async (file: File) => {
      setLoading(true);
      setError(null);
      try {
        const res = await analyzeReceipt(file);
        setSelectedFile(file);
        setResult(res);
        saveSessionResult(res);
        setUploadOpen(false);
        navigate("/result");
      } catch (err) {
        const msg = err instanceof Error ? err.message : "解析に失敗しました";
        setError(msg);
      } finally {
        setLoading(false);
      }
    },
    [navigate]
  );

  const clearError = useCallback(() => setError(null), []);

  const summaryCount = useMemo(() => {
    return {
      deal: result?.summary?.deal_count ?? 0,
      overpay: result?.summary?.overpay_count ?? 0,
      unknown: result?.summary?.unknown_count ?? 0
    };
  }, [result]);

  const navItems = [
    { path: "/", label: "履歴", icon: History },
    { path: "/result", label: "結果", icon: BarChart3 },
    { path: "/edit", label: "修正", icon: Edit },
  ];

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <div className="container max-w-6xl mx-auto px-4 py-4 flex flex-col flex-1">
        {/* Header */}
        <header className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Receipt className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-xl font-bold tracking-tight">Receipt Deal Checker</h1>
              <p className="text-sm text-muted-foreground">
                レシート画像から e-Stat 価格と比較して DEAL/FAIR/OVERPAY を判定
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <nav className="flex items-center gap-1 mr-2">
              {navItems.map(({ path, label, icon: Icon }) => (
                <Button
                  key={path}
                  variant={location.pathname === path ? "default" : "ghost"}
                  size="sm"
                  asChild
                >
                  <Link to={path}>
                    <Icon className="h-4 w-4 mr-2" />
                    {label}
                  </Link>
                </Button>
              ))}
              <Button
                variant="default"
                size="sm"
                onClick={() => setUploadOpen(true)}
              >
                <Upload className="h-4 w-4 mr-2" />
                アップロード
              </Button>
            </nav>
            <ThemeToggle />
          </div>
        </header>

        {/* Loading State */}
        {loading && (
          <div className="mb-4">
            <Loading label="解析中..." />
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription className="flex items-center justify-between">
              <span>{error}</span>
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={clearError}>
                <X className="h-4 w-4" />
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Routes */}
        <main className="flex-1 flex flex-col">
          <Routes>
            <Route path="/" element={<HistoryPage />} />
            <Route
              path="/result"
              element={
                <ResultPage
                  result={result}
                  onEdit={() => navigate("/edit")}
                  onReAnalyze={selectedFile ? () => runAnalyze(selectedFile) : undefined}
                  onUpload={() => setUploadOpen(true)}
                  summaryCount={summaryCount}
                />
              }
            />
            <Route
              path="/edit"
              element={
                <EditPage
                  result={result}
                  onUpdate={(updated) => {
                    setResult(updated);
                    saveSessionResult(updated);
                    navigate("/result");
                  }}
                  onBack={() => navigate("/result")}
                />
              }
            />
          </Routes>
        </main>

        {/* Upload Sheet */}
        <Sheet open={uploadOpen} onOpenChange={setUploadOpen}>
          <SheetContent side="right" className="w-full sm:max-w-lg overflow-y-auto">
            <SheetHeader>
              <SheetTitle>レシート画像をアップロード</SheetTitle>
              <SheetDescription>
                画像をドラッグ＆ドロップするか、クリックして選択してください
              </SheetDescription>
            </SheetHeader>
            <div className="mt-6">
              <Home
                file={selectedFile}
                onFileChange={setSelectedFile}
                onAnalyze={runAnalyze}
                isAnalyzing={loading}
                lastResult={result}
                clearError={clearError}
              />
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </div>
  );
}
