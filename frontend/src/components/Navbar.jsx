export default function Navbar({ hasResult }) {
  return (
    <header className="nav">
      <div className="brand">Plagiarism Detector</div>
      <nav>
        <a href="#upload">Upload</a>
        <a href="#compare">Compare</a>
        <a
          href={hasResult ? "#result" : undefined}
          className={hasResult ? "" : "disabled"}
          aria-disabled={!hasResult}
        >
          Result
        </a>
        <a href="#history">History</a>
      </nav>
    </header>
  );
}