# NORMALIZATION CANON

**Status:** AUTHORITATIVE
**Version:** 1.0
**Last Updated:** 2025-12-20
**Maintainer:** Aequitas Backend & AI Team

---

## 1. Purpose & Authority

### 1.1 What Is Normalization?

**Normalization** is the deterministic transformation of user input into canonical form while preserving semantic meaning.

**Key principle:**
> Form is standardized. Meaning is sacred.

### 1.2 Scope

This canon governs normalization of:
- **Company names** (legal and trade names)
- **Legal entity suffixes** (LLC, Inc., Ltd., etc.)
- **Jurisdictions** (country codes, state codes)
- **Currencies** (ISO 4217 codes)
- **Timezones** (IANA format)
- **Economic activity** (classification labels)
- **User names** (proper capitalization)

### 1.3 Who Enforces Normalization?

| Layer | Role | Authority |
|-------|------|-----------|
| **Dexter (Preprocessing)** | Suggests normalized form | Proposal only |
| **User Confirmation** | Accepts or rejects | Final authority |
| **Backend Validation** | Ensures format compliance | Hard enforcement |
| **Database** | Stores final value | Source of truth |

**Critical rule:**
Normalization suggestions MUST be auditable and reversible.

---

## 2. Capitalization Rules

### 2.1 Company Names

**Rule:** Preserve user-provided capitalization, but suggest standard form.

**Standard form definition:**
- First letter of each significant word capitalized
- Prepositions (of, and, the) lowercase unless first word
- Legal entity suffixes in uppercase

**Examples:**

| User Input | Suggested Normalization | Reasoning |
|-----------|------------------------|-----------|
| `acme holdings llc` | `Acme Holdings LLC` | Capitalize words, uppercase suffix |
| `ACME HOLDINGS LLC` | `Acme Holdings LLC` | De-capitalize except suffix |
| `Acme Holdings, LLC` | `Acme Holdings LLC` | Remove unnecessary comma |
| `The Acme Company` | `The Acme Company` | "The" capitalized when first word |
| `Acme and Associates LLC` | `Acme and Associates LLC` | "and" lowercase (preposition) |
| `McDonald's Restaurants` | `McDonald's Restaurants` | Preserve brand capitalization |

**Special cases:**

| Brand Name | Rule | Example |
|-----------|------|---------|
| **Acronyms** | All uppercase | `IBM Corporation` |
| **Proper names** | Preserve original | `McDonald's`, `iPay Technologies` |
| **Camel case** | Preserve if recognized | `eBay Inc.`, `iPhone Services LLC` |

**Confidence threshold:**
- Standard capitalization: **>90%** confidence
- Brand-specific capitalization: **>70%** confidence with brand database lookup
- Ambiguous cases: **Ask user** rather than guess

### 2.2 Legal Entity Suffixes

**Rule:** Standardize to uppercase without punctuation.

**Canonical forms:**

| Suffix Type | Canonical Form | Variations Normalized |
|------------|----------------|---------------------|
| Limited Liability Company | `LLC` | `llc`, `L.L.C.`, `Llc`, `L L C` |
| Incorporated | `Inc.` | `inc`, `INC`, `Incorporated` |
| Corporation | `Corp.` | `corp`, `CORP`, `Corporation` |
| Limited | `Ltd.` | `ltd`, `LTD`, `Limited` |
| Limited Partnership | `LP` | `L.P.`, `lp`, `Limited Partnership` |
| Professional Corporation | `PC` | `P.C.`, `pc`, `Professional Corporation` |
| Limited Liability Partnership | `LLP` | `L.L.P.`, `llp` |

**Punctuation handling:**
- `Inc.` and `Corp.` and `Ltd.` retain period (standard convention)
- All others: no periods (`LLC`, `LP`, `LLP`, `PC`)

**Examples:**

| User Input | Normalized Form |
|-----------|----------------|
| `Acme Services, llc` | `Acme Services LLC` |
| `Acme Corp` | `Acme Corp.` |
| `Acme L.L.C.` | `Acme LLC` |
| `Acme Incorporated` | `Acme Inc.` |

### 2.3 User Names (Personal Names)

**Rule:** Capitalize first letter of each name part.

**Examples:**

| User Input | Normalized Form |
|-----------|----------------|
| `john doe` | `John Doe` |
| `JOHN DOE` | `John Doe` |
| `mcdonald` | `McDonald` |
| `o'brien` | `O'Brien` |
| `van der Berg` | `Van Der Berg` |

**Special cases:**
- Hyphenated names: Capitalize after hyphen (`Mary-Jane` not `Mary-jane`)
- Apostrophes: Capitalize after apostrophe (`O'Brien` not `O'brien`)
- Particles: Respect cultural norms (`von Neumann`, `de la Cruz`)

**Confidence threshold:**
- Standard capitalization: **>95%** confidence
- Cultural name particles: **Ask user** (e.g., "van" vs "Van")

---

## 3. Geographic & Jurisdictional Normalization

### 3.1 Country Codes

**Rule:** Enforce ISO 3166-1 alpha-2 format (2-letter uppercase).

**Canonical examples:**

| Country | Canonical Code | Invalid Forms Rejected |
|---------|---------------|----------------------|
| United States | `US` | `USA`, `us`, `United States` |
| Canada | `CA` | `CAN`, `ca`, `Canada` |
| United Kingdom | `GB` | `UK`, `gb`, `United Kingdom` |
| Germany | `DE` | `DEU`, `de`, `Germany` |
| Brazil | `BR` | `BRA`, `br`, `Brazil` |

**Validation:**
- Backend MUST reject non-ISO codes
- Dexter MAY suggest code from natural language input

**Example:**
```
User input: "United States"
Dexter: "I'll set the country code to US (United States)."
```

### 3.2 Currency Codes

**Rule:** Enforce ISO 4217 format (3-letter uppercase).

**Canonical examples:**

| Currency | Canonical Code | Invalid Forms Rejected |
|----------|---------------|----------------------|
| US Dollar | `USD` | `usd`, `Dollar`, `$` |
| Euro | `EUR` | `eur`, `Euro`, `€` |
| British Pound | `GBP` | `gbp`, `Pound`, `£` |
| Japanese Yen | `JPY` | `jpy`, `Yen`, `¥` |
| Canadian Dollar | `CAD` | `cad`, `C$` |

**Validation:**
- Backend MUST reject non-ISO codes
- Dexter MAY suggest code from currency symbols or names

### 3.3 Timezones

**Rule:** Enforce IANA timezone database format.

**Canonical examples:**

| Location | Canonical Format | Invalid Forms Rejected |
|----------|------------------|----------------------|
| New York | `America/New_York` | `EST`, `Eastern`, `UTC-5` |
| Los Angeles | `America/Los_Angeles` | `PST`, `Pacific`, `UTC-8` |
| London | `Europe/London` | `GMT`, `UTC+0` |
| Tokyo | `Asia/Tokyo` | `JST`, `UTC+9` |
| Sydney | `Australia/Sydney` | `AEDT`, `UTC+11` |

**Validation:**
- Backend MUST validate against IANA database
- Dexter MAY suggest timezone from country/city input

---

## 4. Economic Activity Classification

### 4.1 Purpose

Economic activity classification:
- Guides template recommendation
- Suggests module selection
- Informs account structure

**NOT used for:**
- Legal classification
- Tax determination
- Regulatory compliance

### 4.2 Canonical Activity Categories

| Category | Subcategories | Module Suggestions |
|----------|--------------|-------------------|
| **Commerce** | Retail, Wholesale, E-commerce | INVOICING, INVENTORY |
| **Services** | Professional, Consulting, SaaS | INVOICING, CONTRACTS |
| **Real Estate** | Development, Management, Investment | FISCAL, CONTRACTS |
| **Manufacturing** | Production, Assembly, Distribution | INVENTORY, PAYROLL |
| **Technology** | Software, Hardware, Cloud Services | CONTRACTS, INVOICING |
| **Healthcare** | Medical, Dental, Pharmaceutical | PAYROLL, INVOICING |
| **Hospitality** | Hotel, Restaurant, Tourism | INVOICING, PAYROLL |
| **Finance** | Banking, Investment, Insurance | FISCAL, CONTRACTS |
| **Non-Profit** | Charity, Foundation, Association | FISCAL (custom template) |
| **Holding Company** | Investment Management | FISCAL |

### 4.3 Natural Language Classification

**Dexter's role:**
- Extract activity from natural language input
- Suggest canonical category with confidence score
- **Always** require user confirmation

**Example:**
```
User input: "We develop and sell custom software for healthcare providers"

Dexter analysis:
  Primary: Technology (Software)
  Secondary: Healthcare (context)
  Confidence: 0.85

Dexter suggestion:
"I would classify this as Technology (Software Development)."
"Proceed with this classification?"
```

**Confidence thresholds:**
- **>90%:** High confidence, single suggestion
- **70-90%:** Medium confidence, offer top 2 choices
- **<70%:** Low confidence, ask user to select from list

---

## 5. Whitespace & Formatting

### 5.1 Whitespace Normalization

**Rules:**
- Trim leading/trailing whitespace
- Collapse multiple spaces to single space
- Remove tabs and newlines

**Examples:**

| User Input | Normalized Form |
|-----------|----------------|
| `  Acme Holdings  ` | `Acme Holdings` |
| `Acme  Holdings` | `Acme Holdings` |
| `Acme\nHoldings` | `Acme Holdings` |

### 5.2 Special Character Handling

**Allowed characters:**
- Letters (A-Z, a-z, including accented)
- Numbers (0-9)
- Spaces
- Hyphens (-)
- Apostrophes (')
- Ampersands (&)
- Periods (.)
- Commas (,)

**Disallowed characters:**
- Emoji
- Control characters
- Excessive punctuation (!!!, ???)

**Normalization:**
- Remove disallowed characters
- Preserve meaning

**Example:**
```
User input: "Acme™ Holdings® LLC"
Normalized: "Acme Holdings LLC"
Explanation: "I've removed trademark symbols for system compatibility."
```

---

## 6. Audit Trail Requirements

### 6.1 Normalization Log Table

**Table:** `normalization_audit`

| Field | Type | Purpose |
|-------|------|---------|
| `id` | UUID | Primary key |
| `entity_type` | VARCHAR | company, user, account, etc. |
| `entity_id` | UUID (FK) | Entity being normalized |
| `field_name` | VARCHAR | Field being normalized |
| `user_input` | TEXT | Original user input (verbatim) |
| `suggested_value` | TEXT | Dexter's suggested normalization |
| `final_value` | TEXT | Value actually stored |
| `normalization_type` | VARCHAR | capitalization, whitespace, suffix, etc. |
| `confidence_score` | NUMERIC | Dexter's confidence (0.0-1.0) |
| `user_accepted_suggestion` | BOOLEAN | Did user accept Dexter's suggestion? |
| `created_at` | TIMESTAMP | When normalization occurred |

### 6.2 Logging Requirements

**MUST log:**
- ✅ All normalization suggestions made by Dexter
- ✅ User acceptance/rejection of suggestions
- ✅ Final value committed to database

**Purpose:**
- Audit trail for compliance
- Training data for improving Dexter
- Debugging user complaints

---

## 7. Implementation Requirements

### 7.1 Backend Service

**Module:** `backend/app/services/normalization_service.py`

**Core methods:**

```python
class NormalizationService:
    def normalize_company_name(
        self,
        user_input: str,
        confidence_threshold: float = 0.9
    ) -> NormalizationResult:
        """
        Normalize company name with capitalization and suffix standardization.

        Returns:
            suggested_value: Normalized form
            confidence: 0.0-1.0
            changes: List of changes made
            requires_confirmation: bool
        """
        pass

    def normalize_legal_suffix(self, suffix: str) -> str:
        """Normalize legal entity suffix to canonical form."""
        pass

    def normalize_country_code(self, user_input: str) -> str:
        """Convert country name/code to ISO 3166-1 alpha-2."""
        pass

    def normalize_currency_code(self, user_input: str) -> str:
        """Convert currency name/symbol to ISO 4217."""
        pass

    def classify_economic_activity(
        self,
        description: str
    ) -> ActivityClassificationResult:
        """Extract activity category from natural language."""
        pass
```

### 7.2 Dexter Integration

**Endpoint:** `/api/v1/onboarding/{company_id}/dexter/preprocess`

**Request:**
```json
{
  "field": "name",
  "user_input": "acme holdings llc",
  "context": {
    "country": "US"
  }
}
```

**Response:**
```json
{
  "suggested_value": "Acme Holdings LLC",
  "confidence": 0.95,
  "normalization_type": "capitalization_and_suffix",
  "changes": [
    "Capitalized 'Acme' and 'Holdings'",
    "Normalized 'llc' to 'LLC'"
  ],
  "explanation": "I've standardized the capitalization for consistency.",
  "requires_confirmation": true
}
```

### 7.3 Validation Rules

**Backend MUST enforce:**
- Country codes match ISO 3166-1 alpha-2
- Currency codes match ISO 4217
- Timezones match IANA database
- No disallowed characters in names

**Backend MAY suggest:**
- Capitalization corrections
- Whitespace cleanup
- Suffix standardization

**Backend MUST NOT:**
- Change semantic meaning
- Apply normalization silently
- Skip audit logging

---

## 8. Testing Requirements

### 8.1 Normalization Test Cases

**Must verify:**
- ✅ Standard capitalization works correctly
- ✅ Legal suffixes normalized to canonical forms
- ✅ Whitespace collapsed properly
- ✅ Special characters handled correctly
- ✅ Country/currency codes validated
- ✅ All normalizations logged in audit table

### 8.2 Edge Cases

**Must handle:**
- Brand names with unusual capitalization (e.g., `eBay`, `iPhone`)
- International characters (é, ñ, ü, etc.)
- Hyphenated and apostrophed names
- Multiple legal suffixes (e.g., `Acme LLC Inc.`)
- Empty or whitespace-only input

### 8.3 Regression Tests

**Prevent:**
- Silent corrections without user confirmation
- Meaning changes (e.g., `Acme Services` → `Acme Consulting`)
- Loss of international characters
- Incorrect suffix normalization

---

## 9. Confidence Scoring

### 9.1 Confidence Levels

| Confidence | Threshold | Dexter Behavior |
|------------|-----------|----------------|
| **High** | >90% | Single suggestion, present confidently |
| **Medium** | 70-90% | Offer top 2-3 choices |
| **Low** | <70% | Ask user to clarify or choose from list |

### 9.2 Factors Affecting Confidence

**Increase confidence:**
- ✅ Exact match in legal suffix database
- ✅ Standard capitalization pattern
- ✅ No special characters
- ✅ Known brand name in database

**Decrease confidence:**
- ⚠️ Unusual capitalization (e.g., `iPay`, `eBay`)
- ⚠️ Multiple possible interpretations
- ⚠️ International characters
- ⚠️ Ambiguous legal suffix (e.g., `Ltd Inc.`)

---

## 10. Internationalization

### 10.1 Language Support

**Phase 1 (Current):**
- English (US) company names
- Common international suffixes (GmbH, S.A., etc.)

**Future phases:**
- Native language company names
- Right-to-left scripts (Arabic, Hebrew)
- Ideographic scripts (Chinese, Japanese)

### 10.2 Legal Suffix by Jurisdiction

| Jurisdiction | Common Suffixes | Canonical Form |
|-------------|----------------|----------------|
| **US** | LLC, Inc., Corp., LP, LLP, PC | `LLC`, `Inc.`, `Corp.`, `LP`, `LLP`, `PC` |
| **UK** | Ltd., PLC, LLP | `Ltd.`, `PLC`, `LLP` |
| **Germany** | GmbH, AG, KG | `GmbH`, `AG`, `KG` |
| **France** | SA, SARL, SAS | `SA`, `SARL`, `SAS` |
| **Spain** | SL, SA | `SL`, `SA` |
| **Canada** | Inc., Ltd., Corp., ULC | `Inc.`, `Ltd.`, `Corp.`, `ULC` |

---

## 11. Governance

### 11.1 Canon Authority

This document is **AUTHORITATIVE** and binds:
- Backend normalization service implementation
- Dexter preprocessing logic
- Frontend validation rules
- Database constraints

### 11.2 Modification Process

To modify normalization rules:
1. **Propose change** with examples and justification
2. **Review impact** on existing data
3. **Update this document** with version increment
4. **Implement in code** to match updated rules
5. **Update tests** including edge cases

### 11.3 What Cannot Be Modified

**Frozen elements:**
- ❌ ISO standards (country codes, currency codes)
- ❌ IANA timezone format
- ❌ Requirement for audit trail
- ❌ Prohibition on silent corrections

**Modifiable elements:**
- ✅ Capitalization heuristics (with justification)
- ✅ Legal suffix mappings (additive)
- ✅ Confidence thresholds (with analysis)
- ✅ Economic activity categories (refined taxonomy)

---

## Final Note

Normalization exists to reduce chaos, not eliminate choice.

**Dexter suggests. The user decides. The database remembers.**

When in doubt:
- Preserve the user's original meaning
- Announce every change
- Log every decision

**Form serves meaning. Never the reverse.**

---

**End of Normalization Canon v1.0**
