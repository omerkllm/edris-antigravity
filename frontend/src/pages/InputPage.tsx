import { useMemo, useState, type FormEvent } from "react";
import { EmailInput } from "../components/EmailInput";
import { ProfileForm } from "../components/ProfileForm";
import type { StudentProfile } from "../types/models";

type Props = {
  profile: StudentProfile;
  loading: boolean;
  errorMessage: string | null;
  onProfileChange: (next: StudentProfile) => void;
  onAnalyze: (payload: { pastedText: string; files: File[] }) => Promise<void>;
  onLoadDemo: () => Promise<void>;
};

function profileIsValid(profile: StudentProfile) {
  return profile.cgpa >= 0 && profile.cgpa <= 4 && profile.semester >= 1 && profile.semester <= 8;
}

export function InputPage({
  profile,
  loading,
  errorMessage,
  onProfileChange,
  onAnalyze,
  onLoadDemo,
}: Props) {
  const [mode, setMode] = useState<"paste" | "upload">("paste");
  const [pastedText, setPastedText] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const canSubmit = useMemo(() => {
    return Boolean(pastedText.trim()) || files.length > 0;
  }, [files.length, pastedText]);

  async function handleAnalyzeSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitAttempted(true);
    setLocalError(null);

    if (!canSubmit) {
      setLocalError("Provide pasted text or upload at least one file.");
      return;
    }
    if (!profileIsValid(profile)) {
      setLocalError("Fix profile validation errors before submitting.");
      return;
    }

    await onAnalyze({ pastedText, files });
  }

  return (
    <main className="container">
      <h1>AI Opportunity Inbox Copilot</h1>
      <form onSubmit={handleAnalyzeSubmit}>
        <EmailInput
          mode={mode}
          pastedText={pastedText}
          files={files}
          onModeChange={setMode}
          onPastedTextChange={setPastedText}
          onFilesChange={setFiles}
        />

        <ProfileForm
          value={profile}
          onChange={onProfileChange}
          submitAttempted={submitAttempted}
        />

        {localError ? <p className="error">{localError}</p> : null}
        {errorMessage ? <p className="error">{errorMessage}</p> : null}

        <div className="actions-row">
          <button type="submit" disabled={loading || !canSubmit}>
            {loading ? "Analyzing..." : "Analyze Emails"}
          </button>
          <button type="button" disabled={loading} onClick={onLoadDemo}>
            Load Demo
          </button>
        </div>
      </form>
    </main>
  );
}
