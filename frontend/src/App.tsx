import { useMemo, useState } from "react";
import { ApiError, analyze, loadDemo } from "./services/api";
import { InputPage } from "./pages/InputPage";
import type { StudentProfile } from "./types/models";

export function App() {
  const initial = useMemo<StudentProfile>(
    () => ({
      name: null,
      degree: "BS Computer Science",
      degree_level: "undergraduate",
      semester: 6,
      cgpa: 3.3,
      skills: [],
      preferred_types: [],
      financial_need: false,
      location_preference: "any",
      past_experience: null,
    }),
    [],
  );

  const [profile, setProfile] = useState<StudentProfile>(initial);
  const [state, setState] = useState<"input" | "loading">("input");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function runAnalyze(payload: { pastedText: string; files: File[] }) {
    setErrorMessage(null);
    setState("loading");
    try {
      await analyze(payload.files, payload.pastedText, profile);
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.detail);
      } else {
        setErrorMessage("Unexpected error while analyzing emails.");
      }
    } finally {
      setState("input");
    }
  }

  async function runLoadDemo() {
    setErrorMessage(null);
    setState("loading");
    try {
      await loadDemo();
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.detail);
      } else {
        setErrorMessage("Unexpected error while loading demo.");
      }
    } finally {
      setState("input");
    }
  }

  return (
    <InputPage
      profile={profile}
      loading={state === "loading"}
      errorMessage={errorMessage}
      onProfileChange={setProfile}
      onAnalyze={runAnalyze}
      onLoadDemo={runLoadDemo}
    />
  );
}

