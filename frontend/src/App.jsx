import { useEffect, useState } from "react";
import api from "./api";
import Navbar from "./components/Navbar";
import UploadSection from "./components/UploadSection";
import CompareSection from "./components/CompareSection";
import ResultSection from "./components/ResultSection";
import HistorySection from "./components/HistorySection";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [history, setHistory] = useState([]);
  const [result, setResult] = useState(null);
  const [comparing, setComparing] = useState(false);
  const [compareError, setCompareError] = useState(null);
  const [loadError, setLoadError] = useState(null);

  const refreshDocuments = async () => setDocuments(await api.listDocuments());
  const refreshHistory = async () => setHistory(await api.listComparisons());

  // Page khulte hi documents aur history laao
  useEffect(() => {
    Promise.all([refreshDocuments(), refreshHistory()]).catch((err) =>
      setLoadError(err.message)
    );
  }, []);

  // Result aate hi us tak scroll karo
  useEffect(() => {
    if (result) document.getElementById("result")?.scrollIntoView({ behavior: "smooth" });
  }, [result]);

  async function handleUpload(file) {
    await api.uploadDocument(file);
    await refreshDocuments();
  }

  async function handleDeleteDocument(id) {
    await api.deleteDocument(id);
    await refreshDocuments();
  }

  async function handleCompare(payload) {
    setComparing(true);
    setCompareError(null);
    try {
      const comparison = await api.runComparison(payload);
      setResult(comparison);
      await refreshHistory();
    } catch (err) {
      setCompareError(err.message);
    } finally {
      setComparing(false);
    }
  }

  async function handleOpen(id) {
    try {
      setResult(await api.getComparison(id));
    } catch (err) {
      setCompareError(err.message);
    }
  }

  async function handleDeleteComparison(id) {
    await api.deleteComparison(id);
    if (result?.id === id) setResult(null);
    await refreshHistory();
  }

  return (
    <>
      <Navbar hasResult={!!result} />
      {loadError && (
        <div className="sec"><div className="error">{loadError}</div></div>
      )}

      <UploadSection
        documents={documents}
        onUpload={handleUpload}
        onDelete={handleDeleteDocument}
      />
      <CompareSection
        documents={documents}
        onCompare={handleCompare}
        loading={comparing}
        error={compareError}
      />

      {result && <ResultSection key={result.id} result={result} />}

      <HistorySection
        history={history}
        onOpen={handleOpen}
        onDelete={handleDeleteComparison}
      />
      <div className="footer-space" />
    </>
  );
}