export type RawEmailSource = "paste" | "file";

export interface RawEmail {
  readonly id: string;
  readonly subject: string;
  readonly sender: string;
  readonly body: string;
  readonly raw_text: string;
  readonly source: RawEmailSource;
  readonly char_count: number;
}

export type DegreeLevel = "undergraduate" | "graduate" | "phd";
export type OpportunityType =
  | "scholarship"
  | "internship"
  | "competition"
  | "fellowship"
  | "admission"
  | "conference"
  | "grant"
  | "job";
export type LocationPreference = "remote" | "pakistan" | "any";

export interface StudentProfile {
  readonly name: string | null;
  readonly degree: string;
  readonly degree_level: DegreeLevel;
  readonly semester: number;
  readonly cgpa: number;
  readonly skills: readonly string[];
  readonly preferred_types: readonly OpportunityType[];
  readonly financial_need: boolean;
  readonly location_preference: LocationPreference;
  readonly past_experience: string | null;
}

export interface ClassificationResult {
  readonly id: string;
  readonly is_opportunity: boolean;
  readonly category: string;
  readonly confidence: number;
  readonly reject_reason: string | null;
}

export interface OpportunityObject {
  readonly email_id: string;
  readonly title: string | null;
  readonly organization: string | null;
  readonly category: string | null;
  readonly deadline_raw: string | null;
  readonly deadline_iso: string | null;
  readonly deadline_type: "explicit" | "inferred" | "rolling" | "missing";
  readonly degree_levels: readonly string[];
  readonly min_cgpa: number | null;
  readonly skills_required: readonly string[];
  readonly location_type:
    | "remote"
    | "pakistan_only"
    | "international"
    | "unknown";
  readonly financial_need_required: boolean;
  readonly year_of_study: readonly number[];
  readonly required_documents: readonly string[];
  readonly compensation: string | null;
  readonly duration: string | null;
  readonly application_link: string | null;
  readonly contact_email: string | null;
  readonly eligibility_raw: string;
  readonly deadline_raw_context: string;
  readonly extraction_incomplete: boolean;
}

export interface ScoredOpportunity {
  readonly opportunity: OpportunityObject;
  readonly total_score: number;
  readonly profile_fit: number;
  readonly urgency_score: number;
  readonly completeness_score: number;
  readonly value_score: number;
  readonly evidence: readonly string[];
  readonly urgency_badge:
    | "RED"
    | "YELLOW"
    | "GREEN"
    | "ROLLING"
    | "NO_DEADLINE"
    | "EXPIRED";
  readonly is_ineligible: boolean;
  readonly days_left: number | null;
  readonly classification_uncertain: boolean;
}

export interface RankedOutput {
  readonly rank: number;
  readonly opportunity: OpportunityObject;
  readonly total_score: number;
  readonly score_breakdown: {
    readonly profile_fit: number;
    readonly urgency: number;
    readonly completeness: number;
    readonly value: number;
  };
  readonly evidence: readonly string[];
  readonly checklist: readonly string[];
  readonly urgency_badge: string;
  readonly is_ineligible: boolean;
  readonly days_left: number | null;
  readonly classification_uncertain: boolean;
}

export interface FilteredOut {
  readonly email_id: string;
  readonly subject: string;
  readonly sender: string;
  readonly reject_reason: string;
}

export interface FinalResponse {
  readonly ranked_opportunities: readonly RankedOutput[];
  readonly filtered_out: readonly FilteredOut[];
  readonly total_emails_input: number;
  readonly opportunities_found: number;
  readonly processing_time_ms: number;
  readonly warnings: readonly string[];
}

