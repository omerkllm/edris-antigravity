# Feature Specification: AI Opportunity Inbox Copilot

**Feature Branch**: `001-ai-opportunity-ranker`  
**Created**: 2026-04-18  
**Status**: Draft  
**Input**: User description: "AI-powered student opportunity email scanner, extractor, and ranked priority list generator for university students"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Full Pipeline: Email Batch to Ranked Priority List (Priority: P1)

A university student pastes 5–15 emails (mix of real opportunities and noise) into the system along with their structured profile. The system identifies which emails are genuine opportunities, extracts structured details from each, and returns a ranked priority list with evidence, urgency badges, and action checklists. The student sees exactly which opportunity to act on first and why.

**Why this priority**: This is the core end-to-end demo flow explicitly required by the problem statement. Without this working, the product has zero value. Every other story depends on this pipeline functioning.

**Independent Test**: Can be tested by pasting the 3-email sample (HEC Scholarship + pizza spam + ICPC) with a pre-filled student profile, and verifying: (a) pizza email is filtered out, (b) HEC and ICPC appear ranked with scores and evidence, (c) action checklist is generated for each.

**Acceptance Scenarios**:

1. **Given** a student pastes 10 emails containing 4 real opportunities and 6 spam/noise, **When** they submit with a valid profile, **Then** the output shows exactly 4 ranked opportunities (not 6, not 10), each with a numeric score (0–100), urgency badge, ranked position, and 2–3 action bullets.

2. **Given** all 15 emails are genuine opportunities, **When** submitted, **Then** all 15 appear ranked, none filtered out, and the highest-scoring opportunity is shown first.

3. **Given** all 15 emails are spam or promotional, **When** submitted, **Then** zero opportunities appear in the ranked list, and a "No opportunities found" message is displayed. The filtered-out section shows all 15 with rejection reasons.

4. **Given** the student's CGPA (2.5) is below the minimum for one opportunity (3.0), **When** ranked, **Then** that opportunity still appears in the output but is placed below eligible ones, marked with a visible "BELOW CGPA REQUIREMENT" warning, and its score reflects the penalty — it is NOT silently removed.

5. **Given** one email has a deadline that has already passed (before today's date), **When** processed, **Then** that opportunity appears with an "EXPIRED" badge, zero urgency score, sorted to the bottom, and the student is notified it may no longer be actionable.

---

### User Story 2 — Student Profile Form: Structured Input Collection (Priority: P1)

A student fills in a web form with their academic and personal profile. The form has validated, structured fields only — no free text parsing of profile data. This profile drives all scoring downstream.

**Why this priority**: Without a correct profile, the ranking engine produces meaningless generic results. The profile is the personalization layer; a broken profile breaks everything downstream.

**Independent Test**: Can be tested in isolation by filling the profile form and verifying all fields are correctly captured and validated without submitting any emails.

**Acceptance Scenarios**:

1. **Given** a student fills in all required profile fields (degree, semester, CGPA, skills, preferred types, financial need, location preference), **When** they complete the form, **Then** the data is captured in structured machine-readable format with no ambiguity.

2. **Given** a student enters CGPA as "3.7" (valid), **When** submitted, **Then** it is accepted. **Given** a student enters "5.0" (out of 4.0 scale), **When** submitted, **Then** a validation error is shown and submission is blocked.

3. **Given** a student selects "financial need: yes", **When** an opportunity requiring financial need is encountered, **Then** it receives a positive match signal in the scoring evidence.

4. **Given** a student leaves the "skills" field empty, **When** scored against an opportunity with required skills, **Then** the skills match score is 0, but the opportunity is still shown (not silently excluded).

---

### User Story 3 — Email Input: Paste and File Upload (Priority: P1)

A student can provide emails either by pasting raw text with `---EMAIL---` delimiters, or by uploading `.txt`/`.eml` files. Both paths produce identical downstream behavior.

**Why this priority**: Input is the entry point. If either input method is broken, the demo fails immediately.

**Independent Test**: Can be tested by submitting one email via paste and one via file upload, verifying both produce a consistent internal email object with the same fields populated (subject, sender, body, source).

**Acceptance Scenarios**:

1. **Given** a user pastes 3 emails separated by `---EMAIL---`, **When** submitted, **Then** the system splits correctly into 3 separate emails and processes each independently.

2. **Given** a user uploads 3 `.eml` files, **When** submitted, **Then** each file is treated as one email and processed the same way as pasted input.

3. **Given** a user pastes text with NO `---EMAIL---` delimiter, **When** submitted, **Then** the entire paste is treated as one single email (not an error).

4. **Given** a user uploads an empty `.txt` file, **When** processed, **Then** that file is silently skipped with a warning note in the response, and processing continues for remaining files.

5. **Given** more than 15 emails are submitted, **When** processed, **Then** only the first 15 are analyzed, and the user is shown a visible warning: "Input truncated to 15 emails — {N} emails were not processed."

---

### User Story 4 — Graceful Degradation: Partial AI Failures (Priority: P2)

The system handles AI API failures (rate limits, timeouts, malformed JSON) without crashing or silently misleading the student. Fallback logic kicks in and the student always receives output, even if less polished.

**Why this priority**: A demo that crashes when the judge runs it 10 times due to rate limits is a catastrophic failure. Graceful degradation is non-negotiable for a hackathon.

**Independent Test**: Can be tested by deliberately injecting a malformed JSON response at the classification layer and verifying the system falls back to treating all emails as potential opportunities rather than discarding them.

**Acceptance Scenarios**:

1. **Given** the classification AI call returns malformed JSON, **When** the parse fails, **Then** all emails are conservatively passed to the extraction layer as potential opportunities — no email is silently dropped.

2. **Given** the checklist generation AI call fails or times out, **When** the error occurs, **Then** a deterministic fallback checklist is generated from structured fields (link, deadline, documents), and no error is shown to the user.

3. **Given** the extraction AI call returns a partial JSON array (truncated due to token limits), **When** parsed, **Then** successfully parsed opportunities are processed normally; those with parse failures show partial info with a "(extraction incomplete)" label.

4. **Given** an extracted application link does NOT appear verbatim in the original email text, **When** validated, **Then** the link is set to `null` and the completeness score is reduced — the hallucinated link is never shown to the student.

---

### User Story 5 — Offline / Pre-loaded Demo Mode (Priority: P2)

A pre-computed demo mode with 5 static emails already processed is available so that internet outages or API exhaustion during judging cannot break the demo.

**Why this priority**: Judges running the demo repeatedly during evaluation can exhaust free-tier API quotas or face connectivity issues. Offline mode guarantees a working demo.

**Independent Test**: Can be tested by disabling internet access and triggering "Demo Mode" — the full ranked output must appear without any API calls.

**Acceptance Scenarios**:

1. **Given** demo mode is activated, **When** the student clicks "Load Demo", **Then** 5 pre-selected emails and a sample student profile are auto-populated, and pre-computed ranked results are displayed immediately without any API call.

2. **Given** demo mode is active, **When** the user views results, **Then** all urgency badges, scores, evidence strings, and checklists appear identical to what a live API call would produce for those inputs.

---

### Edge Cases

**Ingestion Edge Cases:**
- What happens when an `.eml` file has no `text/plain` part? → Fall back to stripping HTML from `text/html`; if both absent, skip the file with a warning.
- What happens when a paste email segment is fewer than 30 characters? → Skip it; do not send to AI. Too short to be a real email.
- What happens when two emails have identical first 200 characters of body content? → Deduplicate silently; keep only first occurrence.
- What happens when an `.eml` file has a non-UTF-8 encoding (e.g., latin-1)? → Re-decode with latin-1 fallback; if still failing, skip with a warning.
- What happens when a user pastes a WhatsApp message or informal text? → Classification layer handles it; likely classified as `not_opportunity`. No crash.
- What happens when an email body is very long? → Use first 3000 characters for AI; truncation applied silently before sending.

**Classification Edge Cases:**
- What happens when an email is a reminder about an opportunity (e.g., "Reminder: ICPC deadline tomorrow")? → Classified as `is_opportunity: true` — deadline reminders ARE actionable.
- What happens when an email is a forwarded opportunity ("FWD: HEC Scholarship")? → Prompt instructs: forwarded opportunity emails count as real opportunities.
- What happens when the classifier returns confidence < 0.6? → Respect the boolean verdict; show an "(uncertain)" label in the UI next to that item.
- What happens when a spam email mimics opportunity language ("You won a $5,000 scholarship!")? → Classifier should catch it. If it slips through, completeness and value scores will be low and it will rank poorly — trust is maintained by transparency.
- What happens when an email is about an opportunity for the wrong audience (e.g., "MBA scholarship for executives")? → Classified as `is_opportunity: true` — profile fit scoring naturally penalizes it.
- What happens when an email is a generic event announcement with no call to action (e.g., "Webinar on AI Ethics this Friday")? → May be classified as `not_opportunity`. If it passes classification, it ranks low due to missing deadline/completeness fields.
- What happens when an email is purely an internal administrative notice (e.g., "Course registration extended")? → Should be classified as `not_opportunity`. If it slips through, completeness score will be near-zero.

**Extraction Edge Cases:**
- What happens when a deadline is expressed in relative terms ("within the next two weeks") without a send date? → Use today's date as the reference; compute ISO date and note `deadline_type="inferred"`.
- What happens when two deadlines exist (early decision + final)? → Use the earlier date as `deadline_iso`; store both verbatim in `deadline_raw`.
- What happens when rolling admissions are stated? → `deadline_type="rolling"`, `deadline_iso=null`, urgency score uses the rolling bucket (medium-low, not zero).
- What happens when a CGPA threshold is expressed as a percentage ("70% marks required")? → Convert using `(pct/100)*4.0`.
- What happens when eligibility has "OR" conditions ("3.5 CGPA OR 2 years experience")? → Extract both; scoring uses the more favorable interpretation for the student (if either condition is met, full CGPA score is awarded).
- What happens when eligibility has "NOT" conditions ("Not open to final year students")? → Extract the exclusion as a string; apply it as a hard penalty to matching students (semester 7–8 → 0 on degree/year sub-score).
- What happens when the extracted URL is NOT present in the original email text? → Discard it (hallucination guard) — set `application_link=null`.
- What happens when a date format is ambiguous ("03/04/2026")? → Prompt forces `YYYY-MM-DD` output; LLM resolves ambiguity. If genuinely ambiguous, use the later date and flag as `deadline_type="inferred"`.
- What happens when the email body contains a forwarded chain with multiple (old + new) dates? → Prompt instructs: use the MOST RECENT actionable deadline found.
- What happens when skills are listed as soft skills only ("Strong communication skills required")? → `skills_required` is set to `[]`; soft skills are excluded per prompt rules.

**Scoring Edge Cases:**
- What happens when two opportunities have the same total score? → Tie-break: sort by `days_left` ascending (more urgent first), then alphabetically by title.
- What happens when a student's semester is below the stated requirement ("5th semester and above required", student is 4th)? → Score 0 on degree/year sub-dimension; shown with a warning but not removed.
- What happens when a student's location preference is "Lahore" but the opportunity is "Remote"? → Remote is treated as compatible for any student — full location score awarded regardless of student location preference.
- What happens when no opportunities pass classification? → Display friendly message: "No genuine opportunities detected in your emails." Filtered-out list shows all 15 with rejection reasons.
- What happens when all opportunities are expired? → All appear with "EXPIRED" badge and zero urgency. A banner warns: "All detected opportunities have passed their deadlines."
- What happens when `days_left` equals exactly 7? → Badge is "RED" (≤ 7), urgency score 30/30.
- What happens when a student's CGPA is borderline (within 0.2 below requirement)? → Partial score (5/10 on CGPA sub-dimension) with a visible "borderline — check directly with the organization" warning.

**Output / Checklist Edge Cases:**
- What happens when an opportunity email contains only a link and no other details? → Completeness score reflects missing fields (low). Checklist fallback says: "Visit the link for full application details."
- What happens when required documents list is empty? → Completeness loses 5 points on the documents sub-criterion; checklist omits a document-prep step.
- What happens when both `application_link` and `contact_email` are missing? → Completeness loses 5 points on the contact sub-criterion; checklist fallback says: "Review the original email for application instructions."

---

## Requirements *(mandatory)*

### Functional Requirements

**Ingestion**
- **FR-001**: The system MUST accept email input via two mutually-compatible methods: (a) paste with `---EMAIL---` delimiters, and (b) file upload of `.txt` or `.eml` files.
- **FR-002**: The system MUST normalize all email inputs into a consistent internal structure with fields: id, subject, sender, body, raw_text, source, char_count — before any AI processing occurs.
- **FR-003**: The system MUST reject submissions where neither pasted text nor files are provided, with a clear user-facing validation error (HTTP 400 equivalent).
- **FR-004**: The system MUST skip emails with fewer than 30 characters without throwing an error or halting processing.
- **FR-005**: The system MUST truncate the input to the first 15 emails and display a visible warning to the user when more than 15 are submitted.
- **FR-006**: The system MUST silently deduplicate emails sharing identical first-200-character body hashes, keeping only the first occurrence.
- **FR-007**: The system MUST fall back to latin-1 decoding for `.eml` files that fail UTF-8 decoding; if the file still cannot be read, it MUST skip it with a logged warning included in the response.
- **FR-008**: The system MUST fall back to stripping HTML tags when an `.eml` file has no `text/plain` MIME part.
- **FR-009**: The system MUST truncate email bodies to the first 3000 characters before sending to AI to prevent context window overflows.

**Profile Input**
- **FR-010**: The system MUST collect a student profile via a structured form with: name (display only), degree program (text), degree level (dropdown: undergraduate/graduate/PhD), semester (1–8 integer), CGPA (0.0–4.0 decimal), skills (multi-value input), preferred opportunity types (multi-select from: scholarship, internship, competition, fellowship, admission, conference, grant, job), financial need (boolean toggle), location preference (dropdown: remote/pakistan/any), past experience (free text, display/context only).
- **FR-011**: The system MUST validate CGPA is between 0.0 and 4.0 and block submission with a clear error if outside this range.
- **FR-012**: The system MUST validate semester is an integer between 1 and 8 and block submission with a clear error if outside this range.

**Classification**
- **FR-013**: The system MUST classify all emails in exactly one batch AI call (never one call per email) returning structured JSON per email with: id, is_opportunity (boolean), category (enum), confidence (float 0–1), reject_reason (string or null).
- **FR-014**: The system MUST treat classification AI JSON parse failures conservatively: ALL emails MUST be forwarded to extraction rather than any being discarded.
- **FR-015**: The system MUST display an "(uncertain)" label next to any opportunity classified with confidence below 0.6.
- **FR-016**: Emails classified as `is_opportunity: false` MUST be stored and displayed to the user in a "filtered out" section with their rejection reasons — they MUST NOT disappear silently.

**Extraction**
- **FR-017**: The system MUST extract structured fields from all opportunity emails in exactly one batch AI call (never one call per email). Fields: title, organization, category, deadline_raw, deadline_iso, deadline_type, degree_levels, min_cgpa, skills_required, location_type, financial_need_required, year_of_study, required_documents, compensation, duration, application_link, contact_email, eligibility_raw, deadline_raw_context.
- **FR-018**: The system MUST validate every extracted application URL by checking whether it appears verbatim in the original email's raw text. Any URL not found verbatim MUST be discarded (set to null).
- **FR-019**: The system MUST convert CGPA thresholds stated as percentages using the formula: `(percentage / 100) * 4.0`.
- **FR-020**: The system MUST set `deadline_type="rolling"` and `deadline_iso=null` when rolling admissions language is detected.
- **FR-021**: When multiple deadlines are present, the system MUST use the earlier one as `deadline_iso` and preserve both in `deadline_raw`.
- **FR-022**: When extraction JSON parsing fails for a specific email (malformed response), the system MUST still include that email in output with all fields set to null/empty and a visible "(extraction incomplete)" label — it MUST NOT be silently removed.
- **FR-023**: The system MUST exclude soft skills (communication, teamwork, leadership, interpersonal, etc.) from extracted `skills_required`. Only specific technical/domain skills are included.

**Scoring**
- **FR-024**: The scoring engine MUST be entirely deterministic Python with zero AI calls.
- **FR-025**: The scoring engine MUST compute four independent dimensions: Profile Fit (max 40 points), Urgency (max 30 points), Completeness (max 20 points), Opportunity Value (max 10 points), for a total of 0–100.
- **FR-026**: Opportunities where the student's CGPA falls below the opportunity's minimum MUST be flagged `is_ineligible: true` but MUST still appear in output sorted below all eligible opportunities.
- **FR-027**: The system MUST assign urgency badge labels: RED (≤ 7 days), YELLOW (8–30 days), GREEN (> 30 days), ROLLING (rolling admissions), NO_DEADLINE (no deadline found), EXPIRED (deadline in the past).
- **FR-028**: Expired opportunities MUST appear at the bottom of the ranked list with an "EXPIRED" badge and a zero urgency score.
- **FR-029**: Rolling admissions MUST receive a non-zero urgency score (specifically: 8/30) to avoid unfair ranking penalty.
- **FR-030**: Tied scores MUST be broken deterministically: first by days_left ascending, then alphabetically by title.
- **FR-031**: Remote opportunities (location_type = "remote") MUST receive full location compatibility score for any student regardless of the student's stated location preference.
- **FR-032**: Borderline CGPA matches (student CGPA within 0.2 below requirement) MUST receive a partial score (5/10) with a "borderline" warning, rather than zero.

**Output and Checklist**
- **FR-033**: The system MUST generate 2–3 action checklist bullets per opportunity in exactly one batch AI call after all scoring is finalized. The AI MUST NOT alter ranking or scoring.
- **FR-034**: The system MUST provide a deterministic fallback checklist built from structured fields (link, deadline, documents) whenever the checklist AI call fails.
- **FR-035**: Evidence strings MUST be generated deterministically from scoring logic — NOT by AI — and MUST cite actual extracted values (e.g., "CGPA eligible: your 3.3 meets the 2.8 minimum").
- **FR-036**: The final response MUST include: ranked opportunities list (each with score, score breakdown, evidence strings, checklist, urgency badge), filtered-out list (with rejection reasons), total emails input, opportunities found count, and processing time.

**Demo Mode**
- **FR-037**: The system MUST include a "Load Demo" mode that pre-populates 5 emails and a student profile and displays pre-computed ranked results instantly, requiring zero API calls.

**API Budget**
- **FR-038**: The system MUST complete all AI processing in exactly 3 API calls: Call 1 (batch classification), Call 2 (batch extraction of opportunities only), Call 3 (batch checklists). No per-email loops are permitted.

### Key Entities

- **RawEmail**: Normalized email object created at ingestion. Carries id, subject, sender, body, raw_text, source (paste/file), char_count. Immutable after creation.
- **ClassificationResult**: Binary verdict per email from the classification AI. Carries email_id, is_opportunity, category, confidence, reject_reason.
- **OpportunityObject**: Rich structured object per opportunity email after extraction. Carries all parsed fields needed for scoring: deadline info, eligibility constraints, documents, contact, compensation, location, and raw evidence text.
- **StudentProfile**: Structured student data collected via the form. Carries academic status (degree, semester, CGPA), preferences (skills, preferred types, location, financial need), and past experience (display only).
- **ScoredOpportunity**: Combines OpportunityObject with scoring outputs: total_score, four dimension scores, evidence list, urgency badge, is_ineligible flag, days_left.
- **RankedOutput**: Final output unit per opportunity. Adds rank, action checklist, and score breakdown to ScoredOpportunity.
- **FinalResponse**: The complete response returned to the frontend. Carries ranked_opportunities, filtered_out, student_profile summary, total_emails_input, opportunities_found, processing_time_ms.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A student can submit a batch of 5–15 emails and receive a fully ranked priority list within 30 seconds of submission under normal network conditions.
- **SC-002**: Given 10 emails (4 real opportunities, 6 noise), the system correctly identifies at least 3 of the 4 real opportunities and correctly rejects at least 5 of the 6 noise emails (≥ 75% precision and recall on classification).
- **SC-003**: Given an email with a stated CGPA requirement higher than the student's CGPA, the opportunity appears in output with a visible warning — it is never silently omitted.
- **SC-004**: If any single AI call fails, the user still receives a complete ranked list (using fallback data where needed) — no error page, no empty output.
- **SC-005**: In demo mode, the full ranked output is displayed in under 2 seconds without any external API calls.
- **SC-006**: A student can identify the top-priority opportunity and understand the reason for its ranking (via evidence strings) within 30 seconds of viewing the output, without reading any documentation.
- **SC-007**: The scoring engine produces identical output for identical inputs on every run (100% determinism — zero randomness in scoring).
- **SC-008**: Zero hallucinated application links appear in any ranked output — all displayed links are validated as present verbatim in the original email.
- **SC-009**: All edge cases documented in the Edge Cases section above have defined, tested handling paths that result in continued processing or a graceful degradation, not a crash.
- **SC-010**: A first-time user can complete a full demo run (paste emails + fill profile + view results) in under 5 minutes without any guidance.

---

## Assumptions

- Students are university-enrolled; system is designed primarily for a South Asian (Pakistani) context but handles any English-language opportunity email.
- All email input is in English. Non-English emails may produce unreliable extraction but will not crash the system.
- The AI provider supports structured JSON output mode. If not, the system retries once with explicit JSON formatting instructions in the prompt before falling back.
- The student profile is filled once per session; no account, login, or data persistence is required for this prototype.
- The "past experience" field in the profile is collected for display context only and is NOT parsed or matched algorithmically in this version.
- The UI is a single-page web application; mobile responsiveness is out of scope for this MVP.
- Emails where the entire opportunity content is inside a PDF attachment (no body text) are out of scope — they are skipped with a warning.
- The scoring dimension weights (Profile Fit 40%, Urgency 30%, Completeness 20%, Opportunity Value 10%) are fixed and not user-configurable in this version.
- All deadlines are interpreted in Pakistan Standard Time (PST, UTC+5) unless an explicit timezone is stated in the email.
- "Financial need required" on an opportunity is checked against the student's boolean profile flag — no income verification is performed by the system.
- The maximum score an expired opportunity can receive is its profile_fit + completeness + value scores only (urgency = 0), ensuring it always ranks below any non-expired eligible opportunity.
- The system is scoped to exactly 3 AI calls per submission regardless of email count. This is a hard architectural constraint, not a soft guideline.
- AI provider is assumed to be Gemini 2.0 Flash or Claude 3 Haiku/Sonnet — models that support JSON mode and have sufficient context windows for 15-email batches.
