# Data sources: Police Complaints Knowledge Base

The vector store in `chroma_db/` (collection `police_complaints`) is built from the 10 files in `data/`.
**These are condensed summary notes prepared for a retrieval practice corpus**, not official texts.
Each file states this itself and names the material it was based on. Answers must not be presented
as the official judgment, statute or government reply.

| # | File (format) | Topic | Original source named in the file |
|---|---|---|---|
| 01 | `01_lalita_kumari_fir_guidelines.pdf` (PDF) | Lalita Kumari v. Govt. of U.P.: FIR registration is mandatory for cognizable offences | Supreme Court of India, Constitution Bench, (2014) 2 SCC 1, as reported by LiveLaw |
| 02 | `02_prakash_singh_police_reform_directives.pdf` (PDF) | Prakash Singh v. Union of India: the seven police-reform directives | Supreme Court of India, (2006) 8 SCC 1; Commonwealth Human Rights Initiative (CHRI) summary |
| 03 | `03_nhrc_spot_enquiry_handbook_notes.pdf` (PDF) | NHRC spot enquiries into complaints against police | NHRC, *Handbook on Spot Enquiries* (2014), nhrc.nic.in |
| 04 | `04_nhrc_custodial_death_reporting.html` (HTML) | NHRC rules for reporting custodial deaths | nhrc.nic.in (node/107220, node/118087); NHRC press release of 28 May 2025 |
| 05 | `05_police_complaints_authority_india.html` (HTML) | Police Complaints Authorities in Indian States/UTs | Wikipedia, "Police Complaints Authority (India)" (CC BY-SA 4.0) |
| 06 | `06_dk_basu_arrest_guidelines.html` (HTML) | D.K. Basu v. State of West Bengal: the 11 arrest and detention guidelines | Supreme Court of India, (1997) 1 SCC 416; case summaries from LegalFly and CaseMine |
| 07 | `07_bnss_section_173_fir.md` (Markdown) | Section 173 BNSS, 2023: information in cognizable cases, e-FIR | Lexibal commentary on s.173 BNSS; Vidhi Centre for Legal Policy note on the e-FIR |
| 08 | `08_zero_fir_sop.md` (Markdown) | Zero FIR and e-Zero FIR SOP | Legal Service India; LiveLaw; MHA/PIB material as reported by Vajiram & Ravi and Anantam IAS |
| 09 | `09_first_information_report_basics.txt` (TXT) | FIR basics for citizens | Wikipedia, "First information report" (CC BY-SA 4.0), plus general explainers |
| 10 | `10_lok_sabha_q2277_police_complaints_authority.txt` (TXT) | Lok Sabha Unstarred Q. 2277 (27.03.2012) on Police Complaints Authorities | Parliament Digital Library, eparlib.nic.in, document 117961 |

## How each chunk points back to its source

Every vector in Chroma has this metadata, so the backend can cite answers:

| Key | Example |
|---|---|
| `source` | `01_lalita_kumari_fir_guidelines.pdf` |
| `title` | `Lalita Kumari v. Government of Uttar Pradesh - Mandatory Registration of FIR` |
| `section` | `Holding` |
| `page`, `page_end` | `1`, `1` (PDFs only) |
| `chunk_index`, `tokens` | `2`, `231` |
| `citation` | `Lalita Kumari v. ... — Holding (p. 1) [01_lalita_kumari_fir_guidelines.pdf]` |

Chunk IDs look like `01-lalita-kumari-fir-guidelines-002` (`<file slug>-<chunk number>`).

## Licensing note

Files 05 and 09 are paraphrased from Wikipedia (CC BY-SA 4.0), so attribution applies if they are shown
publicly. File 06 notes that rights to the original case summaries stay with their authors. Before the
corpus is used beyond the hackathon, check reuse terms for the summaries the other files are based on.
