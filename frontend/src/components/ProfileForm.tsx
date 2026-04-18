import { useMemo, useState } from "react";
import type {
  DegreeLevel,
  LocationPreference,
  OpportunityType,
  StudentProfile,
} from "../types/models";

type Props = {
  value: StudentProfile;
  onChange: (next: StudentProfile) => void;
  submitAttempted: boolean;
};

const OPPORTUNITY_TYPES: readonly OpportunityType[] = [
  "scholarship",
  "internship",
  "competition",
  "fellowship",
  "admission",
  "conference",
  "grant",
  "job",
];

const DEGREE_LEVELS: readonly DegreeLevel[] = ["undergraduate", "graduate", "phd"];
const LOCATION_PREFS: readonly LocationPreference[] = ["remote", "pakistan", "any"];

function clampInt(value: string, fallback: number) {
  const n = Number.parseInt(value, 10);
  return Number.isFinite(n) ? n : fallback;
}

function clampFloat(value: string, fallback: number) {
  const n = Number.parseFloat(value);
  return Number.isFinite(n) ? n : fallback;
}

export function ProfileForm({ value, onChange, submitAttempted }: Props) {
  const [skillDraft, setSkillDraft] = useState("");

  const errors = useMemo(() => {
    const out: { cgpa?: string; semester?: string } = {};
    if (value.cgpa < 0 || value.cgpa > 4) out.cgpa = "CGPA must be between 0.0 and 4.0";
    if (value.semester < 1 || value.semester > 8)
      out.semester = "Semester must be an integer between 1 and 8";
    return out;
  }, [value.cgpa, value.semester]);

  const showCgpaError = submitAttempted || Boolean(errors.cgpa);
  const showSemesterError = submitAttempted || Boolean(errors.semester);

  const set = (patch: Partial<StudentProfile>) => onChange({ ...value, ...patch });

  const addSkill = () => {
    const s = skillDraft.trim();
    if (!s) return;
    if (value.skills.some((x) => x.toLowerCase() === s.toLowerCase())) {
      setSkillDraft("");
      return;
    }
    set({ skills: [...value.skills, s] });
    setSkillDraft("");
  };

  const removeSkill = (skill: string) =>
    set({ skills: value.skills.filter((s) => s !== skill) });

  const togglePreferredType = (t: OpportunityType) => {
    const has = value.preferred_types.includes(t);
    set({
      preferred_types: has
        ? value.preferred_types.filter((x) => x !== t)
        : [...value.preferred_types, t],
    });
  };

  return (
    <section>
      <h2>Student Profile</h2>

      <label>
        Name (optional)
        <input
          value={value.name ?? ""}
          onChange={(e) => set({ name: e.target.value || null })}
        />
      </label>

      <label>
        Degree
        <input value={value.degree} onChange={(e) => set({ degree: e.target.value })} />
      </label>

      <label>
        Degree level
        <select
          value={value.degree_level}
          onChange={(e) => set({ degree_level: e.target.value as DegreeLevel })}
        >
          {DEGREE_LEVELS.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </label>

      <label>
        Semester (1–8)
        <input
          type="number"
          min={1}
          max={8}
          value={value.semester}
          onChange={(e) => set({ semester: clampInt(e.target.value, value.semester) })}
        />
      </label>
      {showSemesterError && errors.semester ? (
        <p className="error">{errors.semester}</p>
      ) : null}

      <label>
        CGPA (0.0–4.0)
        <input
          type="number"
          min={0}
          max={4}
          step={0.01}
          value={value.cgpa}
          onChange={(e) => set({ cgpa: clampFloat(e.target.value, value.cgpa) })}
        />
      </label>
      {showCgpaError && errors.cgpa ? <p className="error">{errors.cgpa}</p> : null}

      <fieldset>
        <legend>Skills</legend>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            value={skillDraft}
            onChange={(e) => setSkillDraft(e.target.value)}
            placeholder="e.g., Python"
          />
          <button type="button" onClick={addSkill}>
            Add
          </button>
        </div>
        {value.skills.length ? (
          <ul>
            {value.skills.map((s) => (
              <li key={s}>
                {s}{" "}
                <button type="button" onClick={() => removeSkill(s)}>
                  remove
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </fieldset>

      <fieldset>
        <legend>Preferred opportunity types</legend>
        {OPPORTUNITY_TYPES.map((t) => (
          <label key={t} style={{ display: "block" }}>
            <input
              type="checkbox"
              checked={value.preferred_types.includes(t)}
              onChange={() => togglePreferredType(t)}
            />{" "}
            {t}
          </label>
        ))}
      </fieldset>

      <label>
        Financial need
        <input
          type="checkbox"
          checked={value.financial_need}
          onChange={(e) => set({ financial_need: e.target.checked })}
        />
      </label>

      <label>
        Location preference
        <select
          value={value.location_preference}
          onChange={(e) => set({ location_preference: e.target.value as LocationPreference })}
        >
          {LOCATION_PREFS.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
      </label>

      <label>
        Past experience (optional)
        <textarea
          value={value.past_experience ?? ""}
          onChange={(e) => set({ past_experience: e.target.value || null })}
          rows={3}
        />
      </label>
    </section>
  );
}

