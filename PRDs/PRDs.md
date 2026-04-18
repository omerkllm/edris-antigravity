We'll design a robust, production‑grade logic flow that can realistically be coded in six hours. The focus is on **modularity, deterministic scoring, and explainability**—not just throwing prompts at an LLM and hoping for the best. You'll get:

- A detailed feature breakdown with clear boundaries.
- A logical pipeline that never leaves room for "maybe" outputs.
- A fast, battle‑tested tech stack mapped to real‑world engineering patterns (Gmail, LinkedIn, Zapier).
- A concrete example showing exactly how an email becomes a ranked action item.

---

## 1. Detailed Feature Set (What the System Actually Does)

| Feature Group | Feature | Description | Why It's Non‑Negotiable |
|---------------|---------|-------------|--------------------------|
| **Ingestion** | Multi‑format input | Accept pasted raw email text or `.eml`/`.txt` file upload (max 15 emails). | Hackathon judges will demo with copy‑paste or a few files. |
| | Student profile form | Structured fields only: Degree, Semester, CGPA, Skills (list), Interests (list), Preferred Types (list), Financial Need (bool), Location Pref (string), Past Exp (list). | **Determinism** – no free‑text parsing of the profile avoids ambiguity. |
| **Opportunity Detection** | Binary classification (Opportunity / Not Opportunity) | Uses a small, fine‑tuned classifier or a prompt‑based LLM with strict JSON output. Rejects: newsletters, "thank you" emails, spam, internal memos. | Prevents false positives from flooding the ranking list. |
| **Information Extraction** | Structured field extraction | From each opportunity email, extract: `deadline` (ISO date), `eligibility_criteria` (list of strings), `required_documents` (list), `application_link`, `contact_email`, `opportunity_type` (enum), `location_requirement`, `stipend_info` (if any). | Machine‑readable data feeds the scoring engine. |
| **Normalization** | Date parsing & standardization | Convert "next Friday", "March 15", "15/03/2026" into a unified `YYYY-MM-DD` format. | Ranking by urgency requires comparable timestamps. |
| **Profile Matching** | Skill/Interest overlap scoring | Compute Jaccard similarity or simple keyword intersection between student `skills`/`interests` and extracted eligibility text. | Determines "fit". |
| | Academic requirement checking | Parse CGPA thresholds (e.g., "minimum 3.0 GPA") and compare with student CGPA. Return `fit_academic: true/false`. | Hard filter; non‑fit opportunities get lower priority. |
| | Location preference matching | Compare extracted location requirement (e.g., "must be in Lahore") with student location pref. | |
| **Scoring Engine** | Three‑factor deterministic score | `Score = (w1 * Urgency) + (w2 * Fit) + (w3 * Completeness)` where:<br>‑ **Urgency** = days until deadline (linear decay)<br>‑ **Fit** = weighted sum of skill match, GPA match, location match, type match<br>‑ **Completeness** = % of required fields successfully extracted | Explainable ranking – every point can be traced back to data. |
| **Ranking & Explanation** | Priority list with evidence | For each opportunity, show: title, deadline, why it ranks here (e.g., "High urgency – deadline in 3 days; Strong fit – matches 4/5 skills; Missing application link lowers completeness."). | Builds trust; meets "evidence‑backed" requirement. |
| **Action Checklist** | Per‑opportunity next steps | Auto‑generated based on missing info or extracted requirements: "Prepare updated resume", "Ask professor for LOR", "Submit via link by Mar 20". | Actionable output – not just a list. |

---

## 2. Logical Pipeline (No Broken Steps)

```
[Email Batch (text)] 
      │
      ▼
┌─────────────────────────────────────────┐
│  Preprocessing & De‑duplication         │
│  - Clean HTML, extract plain text       │
│  - Remove duplicate email bodies        │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│  Opportunity Classifier                 │
│  (Small LLM call with JSON schema)      │
│  Output: { "is_opportunity": bool,      │
│            "confidence": float }        │
└─────────────────────────────────────────┘
      │ (only opportunities pass)
      ▼
┌─────────────────────────────────────────┐
│  Structured Extractor                   │
│  (Single LLM call per email with        │
│   strict JSON output format)            │
│  Returns fields like deadline,          │
│  eligibility list, documents, link      │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│  Normalization & Validation             │
│  - Parse dates to ISO                   │
│  - Validate email format for contact    │
│  - Clean document list (remove dupes)   │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│  Profile Matcher (Deterministic)        │
│  - Skill overlap score                  │
│  - CGPA threshold check                 │
│  - Location compatibility               │
│  - Type preference weight               │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│  Scoring & Ranking Engine               │
│  - Urgency = 1 / (days_until_deadline+1)│
│  - Fit = weighted average of above      │
│  - Completeness = fields_present/total  │
│  - Final Score = 0.5*Urg + 0.3*Fit +    │
│                  0.2*Completeness       │
│  - Sort descending, keep top N          │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│  Explanation & Checklist Generator      │
│  - Template‑based reason strings        │
│  - Action items derived from            │
│    missing docs / deadline proximity    │
└─────────────────────────────────────────┘
      │
      ▼
  [Ranked Opportunity Dashboard]
```

**Why this logic is unbroken:**
- The classifier prevents garbage from entering the extractor.
- Extractor output is forced into a JSON schema – no free text parsing downstream.
- Scoring uses only **already‑structured** data, so it's 100% deterministic.
- Explanation strings are generated from the same structured data, not hallucinated.

---

## 3. Fast Architecture & Tech Stack (6‑Hour MVP)

We need speed of development without sacrificing reliability. The stack mirrors how **Zapier** handles email parsing (trigger + action) and how **LinkedIn** scores job recommendations (offline feature store + online scoring).

| Component | Technology Choice | Why It's Fast & Solid |
|-----------|-------------------|------------------------|
| **Frontend** | **Streamlit** | Single Python file for UI. File upload, form inputs, and table display in minutes. No React/Flask overhead. |
| **Backend API** | **FastAPI** (optional if Streamlit direct) | If you need separate backend, FastAPI gives async support and auto‑docs. But Streamlit can call Python functions directly – even faster. |
| **AI Processing** | **OpenAI GPT‑4o mini** or **Claude 3 Haiku** | Small, fast, cheap models with **Structured Outputs** (JSON mode). One prompt for classification, another for extraction. **Cost:** <$0.001 per email. |
| **Alternative (offline)** | **Local BERT + regex fallback** | If internet is unreliable, use a small `distilbert‑base‑uncased` fine‑tuned on opportunity emails (can be done pre‑hackathon) + date parser `dateparser`. |
| **Data Validation** | **Pydantic** | Define schemas for extracted data. Automatically validates LLM output – if invalid, fallback to retry prompt. |
| **Scoring Engine** | **Pure Python + Pandas** | Lightweight; pandas DataFrame for bulk scoring in one go. |
| **Deployment** | **Streamlit Cloud / Hugging Face Spaces** | Free, instant deploy from GitHub. Judges can play with live demo. |

### Real‑World Mapping

- **Gmail's Smart Inbox Categorization:** Uses a lightweight classifier to separate "Promotions" from "Primary". We do the same but for "Opportunity" vs "Noise".
- **LinkedIn Job Matching:** Computes a score based on skill match, location, and seniority. Our scoring engine is a simplified, explainable version of that.
- **Zapier's Email Parser:** Allows users to forward emails and extract fields using templates. Our LLM‑based extractor replaces the need for user‑defined templates, making it more flexible for a hackathon.

---

## 4. Concrete Example Walkthrough

### Input: Student Profile
```
Degree: BS Computer Science
Semester: 6th
CGPA: 3.4
Skills: ["Python", "Machine Learning", "Data Analysis", "SQL"]
Interests: ["AI", "Data Science"]
Preferred Types: ["Internship", "Scholarship"]
Financial Need: True
Location Preference: "Lahore"
Past Experience: "2-month research internship"
```

### Input: One Email (Raw Text)
```
Subject: FAST NUCES AI Lab Summer Internship 2026

Dear Students,

The AI Lab at FAST NUCES Lahore is offering a 6-week summer internship.
Eligibility: BS students 5th semester or above, CGPA >= 3.2.
Required skills: Python, basic ML concepts.
Deadline: April 30, 2026.
Apply at: https://lhr.nu.edu.pk/ai-internship
Contact: ai.lab@nu.edu.pk

Regards,
AI Lab Coordinator
```

### Step‑by‑Step Execution

**1. Classifier** → `{"is_opportunity": true}`

**2. Extractor (JSON output)** →
```json
{
  "opportunity_type": "internship",
  "deadline": "2026-04-30",
  "eligibility_criteria": [
    "BS students 5th semester or above",
    "CGPA >= 3.2",
    "Skills: Python, basic ML concepts"
  ],
  "required_documents": [],
  "application_link": "https://lhr.nu.edu.pk/ai-internship",
  "contact_email": "ai.lab@nu.edu.pk",
  "location_requirement": "Lahore"
}
```

**3. Profile Matcher**
- Skill overlap: `["Python", "Machine Learning"]` → 2/2 matched, score 1.0
- CGPA: student 3.4 >= 3.2 → true
- Location: student prefers Lahore, requirement is Lahore → match
- Type: internship in preferred list → match
- **Fit Score** = 0.95

**4. Scoring Engine**
- Urgency: deadline in 12 days (as of April 18) → `1/(12+1)=0.0769` (normalized to 0‑1 scale: actually we'd scale relative to other emails; assume max urgency is 7 days, so this gets a good score)
- Completeness: 5/6 fields present → 0.83
- **Final Score** = 0.5*0.8 + 0.3*0.95 + 0.2*0.83 = 0.851 → ranks high.

**5. Explanation & Checklist**
- **Why #1:** "Deadline in 12 days – act soon; Perfect skill match (Python/ML); Matches location preference."
- **Action Checklist:**
  - Prepare updated resume highlighting Python and ML projects.
  - Submit application via provided link before April 30.
  - Email ai.lab@nu.edu.k if any questions.

This entire flow is **transparent, auditable, and can be built in an afternoon** if you leverage structured LLM outputs and a simple Python backend.

---

## 5. Implementation Roadmap for 6 Hours

| Hour | Task | Deliverable |
|------|------|-------------|
| 0‑1 | Set up Streamlit app with file upload and profile form. Create Pydantic schemas. | Basic UI skeleton. |
| 1‑2 | Integrate LLM calls for classification and extraction (use OpenAI/Claude with JSON mode). Build fallback parser with `dateparser`. | Pipeline works for 1 email. |
| 2‑3 | Implement profile matcher and scoring engine. Write unit tests with sample data. | Scoring function returns consistent numbers. |
| 3‑4 | Build ranking table and explanation generator. Display checklist per selected opportunity. | UI shows ranked list. |
| 4‑5 | Add batch processing for up to 15 emails. Handle edge cases (no deadline, missing fields). | Robust demo flow. |
| 5‑6 | Polish UI, write clear instructions, prepare demo narrative. Deploy to Streamlit Cloud. | Ready for judges. |

This architecture is deliberately **modest**—no vector databases, no complex RAG. It relies on the strength of modern small LLMs for parsing and clean deterministic code for ranking. It's exactly what you need to **win a hackathon** with a working, explainable product.

---

### Edge Cases
Absolutely. A critical review of edge cases is essential to ensure the system doesn't fail silently or produce misleading rankings. Below is a comprehensive, component‑by‑component breakdown of **everything that can go wrong** with the proposed schema‑driven, LLM‑powered approach.

I'll categorize edge cases by severity: **🔴 Critical (breaks ranking/logic)** , **🟡 Moderate (degrades user experience)** , and **🟢 Minor (annoyances)** .

---

## 1. Email Ingestion & Preprocessing

| Edge Case | Severity | Example | Why It Breaks the System |
|-----------|----------|---------|--------------------------|
| **HTML‑only emails without plaintext fallback** | 🔴 | An email containing only a poster image with text embedded. | LLM receives empty string or meaningless `alt` text. No opportunity detected even if obvious to human. |
| **Emails with attachments but no body text** | 🔴 | A forwarded email where the actual content is in a PDF attachment. | System only scans body text; misses the entire opportunity. |
| **Multi‑part emails with quoted replies** | 🟡 | A long email chain where the opportunity is at the top, but 10 replies with "Thanks!" follow. | LLM may get confused and extract details from the wrong part (e.g., an old signature). |
| **Character encoding issues** | 🟡 | Email contains `â€™` instead of apostrophes due to wrong charset. | LLM usually handles this, but structured extraction of names/links may fail if garbled. |
| **Forwarded email with `>` prefixes** | 🟡 | Each line starts with `> ` from forwarding. | LLM may still parse, but confidence drops; date formats inside quotes may be mis‑read. |
| **Duplicate emails (same opportunity, different subject)** | 🔴 | Student receives both a department email and a forwarded version from a friend. | The system will treat them as two separate opportunities, artificially inflating the list and possibly ranking both. **Must deduplicate by content hash or link.** |

---

## 2. Opportunity Classification

| Edge Case | Severity | Example | Why It Breaks the System |
|-----------|----------|---------|--------------------------|
| **False negative: Genuine opportunity phrased casually** | 🔴 | "Hey folks, we have some funds left for conference travel, first come first served." | No explicit "opportunity" keywords; LLM may classify as `is_opportunity: false`. Student misses out. |
| **False positive: Event announcement with no call to action** | 🟡 | "Join us for a webinar on AI Ethics this Friday." | Classifier says yes, extractor finds a "deadline" (the webinar date). System ranks it as an opportunity, wasting student's time. |
| **Ambiguous opportunities: "Volunteer to help with event"** | 🟡 | Unpaid, no clear benefit. Is it an opportunity? | Student profile might prefer "Internship/Scholarship". Volunteer work may be irrelevant but still technically an "opportunity". |
| **Spam that mimics opportunity language** | 🟡 | "Congratulations! You are selected for a $5,000 scholarship! Click here to claim." | Classifier may mark `true`, extractor finds a fake link, system ranks it high. **Trust is destroyed.** Needs a spam‑confidence filter. |
| **Internal university administrative emails** | 🟡 | "Course registration deadline extended to April 25." | Not a career/academic advancement opportunity, but contains a deadline and eligibility. Will be mis‑ranked. |

---

## 3. Information Extraction (LLM with JSON Schema)

This is the **most brittle** component. LLMs are powerful but not deterministic.

| Edge Case | Severity | Example | Why It Breaks the System |
|-----------|----------|---------|--------------------------|
| **Deadline expressed in relative terms** | 🔴 | "Apply within the next two weeks" (email sent March 1). | Without the original send date (not always in email body), the system cannot compute an ISO date. Extracted `deadline` will be `null` or a hallucination. |
| **Multiple deadlines in one email** | 🔴 | "Early decision: March 1. Regular decision: April 15." | The JSON schema expects a single `deadline` field. LLM may pick one arbitrarily, or output an array that breaks the Pydantic model. |
| **No deadline mentioned** | 🔴 | "Rolling admissions until positions are filled." | `deadline` becomes `null`. Urgency score = 0. Opportunity sinks to bottom even if it's perfect for the student. **Rolling deadlines need special handling.** |
| **Eligibility criteria with "or" conditions** | 🟡 | "Must have 3.5 CGPA **or** 2 years of relevant experience." | Parser extracts a list of strings: `["3.5 CGPA", "2 years experience"]`. The matching logic treats them as **AND** (both required), incorrectly filtering out qualified students. |
| **Eligibility listed as "must NOT have"** | 🟡 | "Not open to final year students." | Extracted as string, but the logic only checks for *presence* of requirements, not negations. Final‑year student gets a false match. |
| **Required documents buried in paragraph** | 🟡 | "Please ensure you have an updated CV." | LLM may not extract "CV" because it's not in a bullet list. Completeness score drops incorrectly. |
| **Hallucinated application links** | 🔴 | LLM sees "apply on our portal" and invents `https://portal.example.com/apply`. | Student clicks dead link; trust erodes. **Must validate URLs are actually present in email text.** |
| **Contact email mis‑extracted** | 🟡 | Email signature: "Dr. A. Khan, Director" with `khan@uni.edu`. LLM extracts `director@uni.edu`. | Minor, but checklist may reference wrong contact. |
| **Opportunity type ambiguity** | 🟡 | "Summer Research Program" – is it an internship, fellowship, or volunteer? | Affects profile matching (student preferred type). LLM picks one arbitrarily. |
| **Stipend / financial info extraction** | 🟢 | "Stipend: PKR 25,000/month" vs "Funded: Yes". | Not critical for ranking but useful. LLM may fail to capture if not a numeric value. |
| **Date formats from different locales** | 🔴 | "15/03/2026" (dd/mm/yyyy) vs "03/15/2026" (mm/dd/yyyy). | `dateparser` may interpret `03/04/2026` as March 4 or April 3 depending on locale. **Must enforce YYYY-MM-DD output from LLM.** |

---

## 4. Profile Matching & Scoring Engine

| Edge Case | Severity | Example | Why It Breaks the System |
|-----------|----------|---------|--------------------------|
| **CGPA threshold with different scales** | 🔴 | Student profile: 3.4/4.0. Opportunity: "Minimum 60% marks." | No conversion logic. Match fails completely. |
| **Skill matching: synonym mismatch** | 🟡 | Student skill: "ML". Opportunity: "machine learning experience". | Exact string match fails; overlap score = 0 despite perfect semantic match. |
| **Skill matching: "basic Python" vs "expert Python"** | 🟢 | Student is expert, but opportunity only needs basic. | Overlap score counts both as "Python", which is acceptable but doesn't differentiate proficiency. |
| **Location preference: "Lahore" vs "Remote"** | 🔴 | Student pref: "Lahore". Opportunity: "Remote (Pakistan)". | Strict string match fails; location score = 0. Student misses a perfectly suitable remote role. |
| **Financial need flag not used** | 🟡 | Student indicates `financial_need: true`. Opportunity is unpaid. | Current scoring doesn't penalize unpaid opportunities. Paid opportunities should get a boost. |
| **Semester mismatch: "5th semester and above"** | 🟡 | Student is 4th semester but has exceptional skills. | Hard filter says "not eligible". No nuance. Could be a missed opportunity. |
| **Urgency scoring for very near deadlines** | 🟡 | Deadline is **today**. Score formula gives it maximum urgency. | Good. But what if deadline is **past**? System must filter out expired opportunities before ranking. |
| **Opportunities with no deadline (rolling)** | 🔴 | `deadline: null`. Urgency score = 0. | Perfect‑fit opportunity sinks to bottom. **Rolling opportunities need a default medium urgency or a separate bucket.** |
| **Completeness score penalizes sparse emails** | 🟡 | A legitimate opportunity email contains only a link and a deadline. | Completeness = 2/6 fields → score 0.33. Drops ranking even though it's real. Should weight fields by importance. |

---

## 5. Ranking & Explanation Generation

| Edge Case | Severity | Example | Why It Breaks the System |
|-----------|----------|---------|--------------------------|
| **Ties in final score** | 🟢 | Two opportunities with identical score. | Ranking order arbitrary. Not critical but needs a tie‑breaker (e.g., deadline then title). |
| **Explanation says "Missing application link" when it's in text** | 🔴 | Extraction failed to capture link. Explanation blames email, not system. | User thinks opportunity is incomplete when it's actually fine. **Explanation must reflect extraction confidence.** |
| **Checklist generation for items student already has** | 🟢 | "Prepare resume" even though student uploaded it. | Annoying but harmless. |
| **Action checklist for opportunities with no deadline** | 🟡 | System says "Apply soon" – too vague. | Could instead say "Rolling admissions – apply early to secure spot." |

---

## 6. 6‑Hour MVP‑Specific Edge Cases

| Edge Case | Severity | Example | Why It Matters for the Hackathon |
|-----------|----------|---------|----------------------------------|
| **LLM API rate limits / cost overrun** | 🔴 | 15 emails × 2 LLM calls = 30 calls. Judge runs demo 10 times → 300 calls, hits free tier limit. | System hangs or shows error during judging. **Must implement local fallback or cache results.** |
| **Internet outage during demo** | 🔴 | LLM API unreachable. | **Must have a pre‑computed offline demo mode** with 5 static emails already processed. |
| **Large email body exceeds LLM context window** | 🟡 | Email with a 50‑page PDF as base64 inline. | Token limit exceeded. **Need truncation strategy** (e.g., first 2000 characters). |
| **User pastes non‑email text (e.g., WhatsApp message)** | 🟢 | "Hey, there's an internship at XYZ." | Classifier may still work; extractor may struggle. Acceptable for MVP. |

---

## 7. Summary Table: Critical Failures That Must Be Addressed

| Critical Failure | Mitigation Strategy (for 6‑Hour Build) |
|------------------|----------------------------------------|
| **No plaintext fallback for HTML emails** | Use `beautifulsoup4` to extract text from HTML body. |
| **Relative deadlines without send date** | Ask user to provide email received date OR default to current date with warning. |
| **Multiple deadlines** | Modify schema to accept `deadlines: list[DeadlineObject]`; pick earliest or allow user to choose. |
| **Rolling admissions (no deadline)** | Assign a default urgency factor (e.g., 0.5) instead of 0. |
| **Hallucinated links** | Validate that extracted URL exists as substring in original email. If not, set to `null`. |
| **Duplicate opportunities** | Compute SHA‑256 hash of normalized content or application link to deduplicate. |
| **CGPA scale mismatch** | Add a simple conversion mapping: `{"4.0": 100, "10.0": 100}` and normalize to percentage. |
| **Location "Remote" not matching "Lahore"** | Expand location check: if student pref is "Lahore" and opp location contains "Remote" or "Online", consider it a partial match. |

---

## Final Thought

The architecture is **sound for a 6‑hour prototype** *provided* the critical edge cases above are acknowledged and handled with explicit fallbacks. No system is perfect, but **transparency** (showing confidence scores or warning icons) will win judges' trust even when extraction fails. The key is to **fail gracefully and never silently mislead the student**.


---

We'll walk through the entire 8‑layer pipeline using a **single concrete example email** so you can see exactly how data transforms at each stage. By the end, you'll have a complete blueprint for implementation.

I'll use this sample email (raw text) as our test case:

```
Subject: Google STEP Internship 2026 – Apply Now

Dear Student,

Google is excited to announce the STEP (Student Training in Engineering Program) internship for Summer 2026.
Eligibility:
- Currently enrolled in a Bachelor's program (2nd year or above)
- CGPA of 3.5 or higher
- Experience with Python and at least one other programming language

Application Deadline: April 26, 2026
Required Documents: Resume/CV, unofficial transcript
Apply online at: https://careers.google.com/students/step
For questions, contact step-interns@google.com

Best,
Google University Programs
```

And a matching student profile:

```json
{
  "name": "Ali Khan",
  "degree": "BS Computer Science",
  "semester": 6,
  "cgpa": 3.7,
  "skills": ["Python", "Machine Learning", "SQL", "Data Analysis"],
  "interests": ["AI", "Software Engineering"],
  "preferred_types": ["internship", "scholarship"],
  "financial_need": false,
  "location_preference": "Lahore",
  "past_experience": "2-month research internship"
}
```

---

## Layer 1: Input Ingestion

**Purpose:** Accept raw emails and student profile from the user.

**What happens:**
- User either pastes raw email text into a `<textarea>` or uploads `.eml` / `.txt` files.
- User fills out a structured HTML form for the student profile.
- Backend receives both as `multipart/form-data` or JSON.

**Input:**
- `email_text` (string) or `email_file` (bytes)
- `student_profile` (JSON)

**Processing:**
- If file uploaded, read contents as string.
- For multiple files, accumulate into a list.
- Store student profile as Python dict.

**Output (data state):**
```python
emails_raw = [
    "Subject: Google STEP Internship 2026 – Apply Now\n\nDear Student,\n\nGoogle is excited to announce..."
]
student_profile = {
    "degree": "BS Computer Science",
    "semester": 6,
    "cgpa": 3.7,
    "skills": ["Python", "Machine Learning", "SQL", "Data Analysis"],
    ...
}
```

---

## Layer 2: Preprocessing & Deduplication

**Purpose:** Clean email text, remove duplicates, and prepare for LLM ingestion.

**Input:** `List[str]` of raw email strings.

**Processing Steps:**

1. **Parse `.eml` if needed:** Use Python's `email` library to extract the plain text body. If no `text/plain`, fallback to stripping HTML from `text/html` with BeautifulSoup.
2. **HTML stripping:** `BeautifulSoup(html_content, "html.parser").get_text()`.
3. **Normalize whitespace:** Collapse multiple newlines/spaces into single spaces.
4. **Deduplicate by content hash:**
   - Compute SHA‑256 hash of normalized, lowercase text.
   - Keep only the first occurrence of each hash.
5. **Truncate to 2000 characters:** Keep the beginning (opportunity details are always near the top).

**Example for our email:**

Raw text after HTML strip (already plain):
```
Subject: Google STEP Internship 2026 – Apply Now

Dear Student,

Google is excited to announce the STEP (Student Training in Engineering Program) internship for Summer 2026.
Eligibility:
- Currently enrolled in a Bachelor's program (2nd year or above)
- CGPA of 3.5 or higher
- Experience with Python and at least one other programming language

Application Deadline: April 26, 2026
Required Documents: Resume/CV, unofficial transcript
Apply online at: https://careers.google.com/students/step
For questions, contact step-interns@google.com

Best,
Google University Programs
```

SHA‑256 hash: `7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069`

Truncated to 2000 chars (this email is short, so no change).

**Output (data state):**
```python
preprocessed_emails = [
    {
        "id": "email_0",
        "original_text": "Subject: Google STEP... (full text)",
        "truncated_text": "Subject: Google STEP... (same, under 2000)",
        "hash": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
    }
]
```

---

## Layer 3: AI Batch Processing (Single Gemini Call)

**Purpose:** Use one LLM call to classify and extract structured data from all emails simultaneously.

**Input:** List of truncated email texts + student profile (for context in prompt).

**Processing:**

- Construct a system prompt that includes:
  - Today's date (for relative date conversion).
  - Strict JSON output schema (Pydantic model).
  - Instructions to process **all** emails in one response array.
- Call Gemini 2.0 Flash with `temperature=0.1`.
- Receive JSON array.
- Validate with Pydantic; retry once on failure.

**Prompt Snippet (abbreviated):**
```
Today's date: 2026-04-18

For each of the following emails, determine if it contains a genuine academic/career opportunity.
If yes, extract the fields according to the JSON schema below.
Return a JSON array with one object per email.

Emails:
[0]: Subject: Google STEP Internship 2026 – Apply Now ...

Schema: { "is_opportunity": bool, "opportunity_type": "...", "deadline_iso": "YYYY-MM-DD", ... }
```

**Gemini Response (for our single email):**
```json
[
  {
    "is_opportunity": true,
    "confidence": 0.98,
    "opportunity_type": "internship",
    "title": "Google STEP Internship 2026",
    "deadline_iso": "2026-04-26",
    "eligibility_criteria": [
      "Enrolled in Bachelor's program (2nd year or above)",
      "CGPA >= 3.5",
      "Experience with Python",
      "Experience with at least one other programming language"
    ],
    "required_documents": ["Resume/CV", "unofficial transcript"],
    "application_link": "https://careers.google.com/students/step",
    "contact_email": "step-interns@google.com",
    "location_requirement": null,
    "stipend_info": null
  }
]
```

**Output (data state):** List of Pydantic `OpportunityExtraction` objects.

---

## Layer 4: Normalization & Validation

**Purpose:** Guard against LLM hallucinations, validate dates, and filter out expired/invalid opportunities.

**Input:** LLM output JSON + original email text.

**Processing per opportunity:**

1. **Hallucination guard for `application_link`:**
   ```python
   if extraction.application_link and extraction.application_link not in original_text:
       extraction.application_link = None  # Hallucinated
   ```
2. **Date validation:**
   - Parse `deadline_iso` with `datetime.fromisoformat()`.
   - Compute `days_until = (deadline - today).days`.
   - If `days_until < 0` → drop opportunity (expired).
3. **Rolling deadline flag:** If `deadline_iso` is `None`, set `is_rolling = True`.
4. **Normalize eligibility list:** Remove duplicates, strip whitespace.

**Example check:**
- Link `https://careers.google.com/students/step` appears verbatim in original email → valid.
- Deadline 2026-04-26 is 8 days in the future → keep.

**Output (data state):**
```python
validated_opportunities = [
    {
        "title": "Google STEP Internship 2026",
        "type": "internship",
        "deadline": date(2026, 4, 26),
        "days_until": 8,
        "is_rolling": False,
        "eligibility": ["Enrolled in Bachelor's program...", "CGPA >= 3.5", "Experience with Python", ...],
        "required_docs": ["Resume/CV", "unofficial transcript"],
        "link": "https://careers.google.com/students/step",
        "contact": "step-interns@google.com",
        "location": None,
        "original_text": "..."
    }
]
```

---

## Layer 5: Profile Matching

**Purpose:** Compute how well the opportunity fits the student's profile using deterministic rules.

**Input:** Validated opportunity + student profile.

**Sub‑scores:**

| Component | Calculation | Example Value |
|-----------|-------------|---------------|
| **Skill Score** | Tokenize student skills and eligibility text. Compute Jaccard similarity: `intersection / max(len(A), len(B))` | Student skills: `["python", "machine learning", "sql", "data analysis"]`<br>Eligibility tokens: `["experience", "python", "programming", "language"]`<br>Intersection: `{"python"}` → size 1<br>`max(4,4)=4` → score = 0.25 |
| **Location Score** | If opp location contains "remote"/"online" → 0.7<br>Else if opp location matches student pref (case‑insensitive) → 1.0<br>Else → 0.0 | Opp location is `null` → 0.0 |
| **CGPA Fit** | Detect scale: if threshold > 4.0, assume percentage. Convert student CGPA if needed. Binary match. | Eligibility: "CGPA >= 3.5". Student 3.7/4.0 → meets → 1.0 |
| **Type Preference** | If `opportunity_type` in student's preferred types → 1.0, else 0.5 | Student prefers `["internship", "scholarship"]`. Opp type `internship` → 1.0 |

**Fit Score (weighted):**
```
fit = 0.5*skill + 0.2*location + 0.2*cgpa + 0.1*type
    = 0.5*0.25 + 0.2*0.0 + 0.2*1.0 + 0.1*1.0
    = 0.125 + 0.0 + 0.2 + 0.1 = 0.425
```

**Output:** `fit_score = 0.425` (on 0–1 scale).

---

## Layer 6: Scoring Engine

**Purpose:** Combine urgency, fit, and completeness into a final rankable score.

**Input:** Fit score, deadline info, extracted fields completeness.

**Calculations:**

| Component | Formula | Example |
|-----------|---------|---------|
| **Urgency** | If `is_rolling`: `0.5`<br>Else: `1 / (1 + days_until/30)` | `1 / (1 + 8/30) = 1 / 1.2667 = 0.789` |
| **Completeness** | `count_non_null_fields / total_fields` (exclude optional fields like stipend) | Fields present: type, title, deadline, eligibility, docs, link, contact (7). Total 7 → 1.0 |
| **Final Score** | `0.5*urgency + 0.3*fit + 0.2*completeness` | `0.5*0.789 + 0.3*0.425 + 0.2*1.0 = 0.3945 + 0.1275 + 0.2 = 0.722` |

**Tie‑break:** If scores equal, sort by `days_until` ascending (more urgent first), then alphabetically by title.

**Output:**
```python
ranked_opportunity = {
    ...,
    "urgency": 0.789,
    "fit": 0.425,
    "completeness": 1.0,
    "final_score": 0.722,
    "rank": 1
}
```

---

## Layer 7: Explanation & Checklist Generator

**Purpose:** Turn the numeric scores into human‑readable justification and actionable steps.

**Input:** Ranked opportunity + student profile.

**Template Example (Python f‑string):**
```python
explanation = f"Ranked #{rank} — deadline in {days_until} days and {matched_skills} of your skills match eligibility."

evidence = [
    f"Skills matched: {', '.join(matched_list)} ({len(matched)} of {len(student_skills)} skills)",
    f"CGPA: your {student_cgpa} meets the {cgpa_threshold} minimum threshold",
    f"Deadline: {deadline.strftime('%B %d, %Y')} ({days_until} days)",
    f"Application link: {'verified in email body' if link else 'not provided'}"
]

checklist = []
if required_docs:
    checklist.append(f"Prepare: {', '.join(required_docs)}")
if link:
    checklist.append(f"Apply at: {link}")
if days_until <= 7:
    checklist.append(f"⚠️ Deadline in {days_until} days — submit today!")
else:
    checklist.append(f"Deadline: {deadline.strftime('%B %d')} — set a reminder")
```

**Example Output:**
```
Explanation: Ranked #1 — deadline in 8 days and 1 of your skills (Python) match eligibility.

Evidence:
- Skills matched: Python (1 of 4 skills)
- CGPA: your 3.7 meets the 3.5 minimum threshold
- Deadline: April 26, 2026 (8 days)
- Application link: verified in email body

Checklist:
- Prepare: Resume/CV, unofficial transcript
- Apply at: https://careers.google.com/students/step
- Deadline: April 26 — set a reminder
```

---

## Layer 8: Ranked Output UI

**Purpose:** Display the final ranked list as interactive cards in the browser.

**Backend (FastAPI):**
- Endpoint `POST /process` returns JSON with all ranked opportunities and summary stats.
```json
{
  "opportunities": [
    {
      "rank": 1,
      "title": "Google STEP Internship 2026",
      "score": 0.722,
      "explanation": "Ranked #1 — deadline in 8 days and 1 of your skills (Python) match eligibility.",
      "evidence": [...],
      "checklist": [...]
    }
  ],
  "stats": {
    "total_emails": 15,
    "opportunities_found": 3,
    "spam_filtered": 2
  }
}
```

**Frontend (Vanilla JS):**
- `fetch('/process', { method: 'POST', body: formData })`
- Loop through `opportunities` array and build HTML cards.
- Inject into DOM.

**UI Card (Visual Representation):**
```
┌─────────────────────────────────────────────────────────┐
│ #1 Google STEP Internship 2026                Score: 0.89│
│ Ranked #1 — deadline in 8 days and 2 of your skills...   │
├─────────────────────────────────────────────────────────┤
│ Evidence                                                 │
│ • Skills matched: Python, Machine Learning (2 of 5)      │
│ • CGPA: your 3.7 meets the 3.5 minimum threshold         │
│ • Deadline: April 26, 2026 (8 days)                      │
│ • Application link: verified in email body               │
├─────────────────────────────────────────────────────────┤
│ Action Checklist                                         │
│ 1. Prepare: updated CV, unofficial transcript            │
│ 2. Apply at: careers.google.com/students/step            │
│ 3. Deadline: April 26, 2026 — set a reminder now         │
└─────────────────────────────────────────────────────────┘
```

---

## Complete End‑to‑End Example Summary Table

| Layer | Input State | Output State |
|-------|-------------|--------------|
| L1 | User paste/file + form | Raw email string, student profile dict |
| L2 | Raw email string | Cleaned, deduped, truncated text (2000 chars) |
| L3 | Truncated text batch | Gemini JSON: is_opportunity, fields |
| L4 | Gemini JSON + original text | Validated fields, hallucination‑free, expired removed |
| L5 | Validated opp + profile | Fit score (0.425) |
| L6 | Fit + deadline + completeness | Final score (0.722), rank |
| L7 | Ranked opp + profile | Explanation string, evidence list, checklist |
| L8 | Ranked list JSON | Rendered HTML cards in browser |

This layered approach ensures every transformation is deterministic, auditable, and ready to code in a 6‑hour hackathon. If you need the exact prompt text or Pydantic models, I can provide those next.