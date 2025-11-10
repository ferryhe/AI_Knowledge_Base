# IAA AI Knowledge Base

IAA AI materials live under `Knowledge_Base_MarkDown/`, each with a Markdown source and companion image folder. Entries below follow the requested section labels so readers can quickly scan the title, upload date, publish date, and summary. Links jump to the Markdown files inside `Knowledge_Base_MarkDown/`.

## Repository Layout
- `Knowledge_Base_MarkDown/` - curated Markdown documents plus `*_assets/` folders for inline images.
- `AI_Agent/` - Retrieval-Augmented Generation utilities (CLI, Streamlit UI, Open WebUI pipeline) that index the Markdown corpus.
- `AI_Agent/knowledge_base.*` - generated FAISS index + metadata created by `scripts/build_index.py`.
- `.gitignore` keeps API keys, indexes, and the virtual environment out of version control.

## Updating the Catalog
1. Drop the new `document.md` into `Knowledge_Base_MarkDown/` and keep supporting images in a sibling `document_assets/` directory so relative links continue to work.
2. Add the entry to the catalog table below (title, upload date, publish date, and short summary).
3. Rebuild the search index so the AI assistant sees the changes:
   ```powershell
   cd AI_Agent
   python .\scripts\build_index.py --source ..\Knowledge_Base_MarkDown
   ```
4. Share the refreshed FAISS + metadata files (`AI_Agent/knowledge_base.faiss`, `AI_Agent/knowledge_base.meta.pkl`) with anyone else running the agent.

## Querying with the Agent
- Quick-start instructions, environment variables, and troubleshooting live in `AI_Agent/README.md`.
- For a fast CLI query on Windows PowerShell:
  ```powershell
  cd AI_Agent
  .\.venv\Scripts\python.exe .\scripts\ask.py "Summarize the AI governance framework"
  ```
- Launch the optional UI with `streamlit run streamlit_app.py` after setting `OPENAI_API_KEY` and rebuilding the index.

## Validating the Agent
- Run the smoke test whenever you change `AI_Agent/scripts/` or the indexing workflow:
  ```powershell
  cd AI_Agent
  pytest tests/test_smoke.py
  ```
- The test suite uses deterministic dummy embeddings, so it finishes quickly and does not require `OPENAI_API_KEY` or internet access. This guards against regressions in chunking, metadata serialization, and retrieval.

## Catalog

### AI Agents & Actuarial Enablement
- **[Title]** [AI Agents & Actuarial Enablement](Knowledge_Base_MarkDown/202505_Webinar_AI_Agents_Actuarial_Enablement.md)
- **[Upload Date]** 2025-11-08
- **[Publish Date]** 2025-05-12
- **[Summary]** Navigating the next frontier of actuarial productivity; Episode 2 of the IAA Data Analytics Webinar Series with an AI agent team showcase, live demo, and suggested next steps.

### Machine Learning in Reserving
- **[Title]** [Machine Learning in Reserving](Knowledge_Base_MarkDown/202507_Webinar_Machine_Learning_in_Reserving.md)
- **[Upload Date]** 2025-11-08
- **[Publish Date]** 2025-07-14
- **[Summary]** Introduction and recent developments from the IFoA Machine Learning in Reserving Working Party, covering neural networks, interpretability tooling, and reserving case studies.

### Artificial Intelligence Governance - Comparing AI Regulatory Guidance Among Countries
- **[Title]** [Artificial Intelligence Governance - Comparing AI Regulatory Guidance Among Countries](Knowledge_Base_MarkDown/202511_Artificial_Intelligence_Governance_Comparing_AI_Regulatory_Guidance_Among_Countries.md)
- **[Upload Date]** 2025-11-08
- **[Publish Date]** 2025-11
- **[Summary]** Supporting document to the comparison chart that summarizes national regulatory frameworks, key governance elements, and planned follow-up from the AITF governance workstream.

### Documentation of Artificial Intelligence Models
- **[Title]** [Documentation of Artificial Intelligence Models](Knowledge_Base_MarkDown/202507_Documentation_of_Artificial_Intelligence_Models.md)
- **[Upload Date]** 2025-11-08
- **[Publish Date]** 2025-07
- **[Summary]** Consultation draft prepared by the IAA AI Task Force outlining documentation goals, structural components, and accountability for AI models.

### Artificial Intelligence Governance Framework
- **[Title]** [Artificial Intelligence Governance Framework](Knowledge_Base_MarkDown/202507_Artificial_Intelligence_Governance_Framework.md)
- **[Upload Date]** 2025-11-08
- **[Publish Date]** 2025-07
- **[Summary]** Comprehensive governance framework for AI actuarial work describing roles, lifecycle controls, validation, and training expectations.

### Testing of Artificial Intelligence Models
- **[Title]** [Testing of Artificial Intelligence Models](Knowledge_Base_MarkDown/202507_Testing_of_Artificial_Intelligence_Models.md)
- **[Upload Date]** 2025-11-08
- **[Publish Date]** 2025-07
- **[Summary]** Consultation draft focused on trustworthy AI testing: objective setting, data preparation, key trust metrics, and continuous monitoring practices.

### Public Consultation on Draft Application Paper on the Supervision of Artificial Intelligence
- **[Title]** [Public Consultation on Draft Application Paper on the Supervision of Artificial Intelligence](Knowledge_Base_MarkDown/202502_Public_Consultation_on_Draft_Application_Paper_on_the_Supervision_of_AI.md)
- **[Upload Date]** 2025-11-08
- **[Publish Date]** 2025-02-17
- **[Summary]** IAA's response to the IAIS consultation, providing overall feedback plus section-by-section comments and edits.

### Statement of Intent (SOI) for IAA Activities on Artificial Intelligence (AI)
- **[Title]** [Statement of Intent (SOI) for IAA Activities on Artificial Intelligence (AI)](Knowledge_Base_MarkDown/202312_Statement_of_Intent_for_IAA_Activities_on_AI.md)
- **[Upload Date]** 2025-11-08
- **[Publish Date]** 2023-12-14
- **[Summary]** Executive Committee-approved SOI describing objectives, motivations, workplan, and the establishment of the AI Task Force.

---

When adding new material, keep the `document.md` + `document_assets/` pairing inside `Knowledge_Base_MarkDown/` so images continue to render in Markdown viewers without additional configuration.
