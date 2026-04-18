type EmailInputMode = "paste" | "upload";

type EmailInputProps = {
  mode: EmailInputMode;
  pastedText: string;
  files: readonly File[];
  onModeChange: (mode: EmailInputMode) => void;
  onPastedTextChange: (value: string) => void;
  onFilesChange: (files: File[]) => void;
};

const PLACEHOLDER =
  "From: scholarships@hec.gov.pk\nSubject: HEC Need-Based Scholarship\nBody: ...\n---EMAIL---\nFrom: events@campus.edu\nSubject: Webinar Reminder\nBody: ...";

export function EmailInput({
  mode,
  pastedText,
  files,
  onModeChange,
  onPastedTextChange,
  onFilesChange,
}: EmailInputProps) {
  return (
    <section>
      <h2>Email Input</h2>
      <div className="tab-row" role="tablist" aria-label="Email input mode">
        <button
          type="button"
          role="tab"
          aria-selected={mode === "paste"}
          className={mode === "paste" ? "tab active" : "tab"}
          onClick={() => onModeChange("paste")}
        >
          Paste
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "upload"}
          className={mode === "upload" ? "tab active" : "tab"}
          onClick={() => onModeChange("upload")}
        >
          Upload
        </button>
      </div>

      {mode === "paste" ? (
        <label>
          Paste one or more emails (use ---EMAIL--- between emails)
          <textarea
            value={pastedText}
            rows={10}
            placeholder={PLACEHOLDER}
            onChange={(e) => onPastedTextChange(e.target.value)}
          />
        </label>
      ) : (
        <label>
          Upload .txt or .eml files
          <input
            type="file"
            multiple
            accept=".txt,.eml"
            onChange={(e) => onFilesChange(Array.from(e.target.files ?? []))}
          />
        </label>
      )}

      <p>Characters: {pastedText.length}</p>
      {files.length ? (
        <p>
          Selected files ({files.length}): {files.map((f) => f.name).join(", ")}
        </p>
      ) : null}
    </section>
  );
}
