import type { FinalResponse, StudentProfile } from "../types/models";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

export function buildFormData(
  emails: File[],
  pastedText: string,
  profile: StudentProfile,
): FormData {
  const fd = new FormData();
  fd.append("profile", JSON.stringify(profile));

  const trimmed = pastedText.trim();
  if (trimmed) fd.append("pasted_text", trimmed);

  for (const f of emails) fd.append("files", f, f.name);
  return fd;
}

async function parseError(response: Response): Promise<ApiError> {
  let detail = `Request failed with status ${response.status}`;
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string" && body.detail.trim()) {
      detail = body.detail;
    }
  } catch {
    // Preserve generic status message when response is not JSON.
  }
  return new ApiError(response.status, detail);
}

export async function analyze(
  emails: File[],
  pastedText: string,
  profile: StudentProfile,
): Promise<FinalResponse> {
  const response = await fetch("/api/analyze", {
    method: "POST",
    body: buildFormData(emails, pastedText, profile),
  });

  if (!response.ok) {
    throw await parseError(response);
  }
  return (await response.json()) as FinalResponse;
}

export async function loadDemo(): Promise<FinalResponse> {
  const response = await fetch("/api/demo");
  if (!response.ok) {
    throw await parseError(response);
  }
  return (await response.json()) as FinalResponse;
}

