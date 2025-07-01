🌟 PURPOSE
We are building a three-agent chat workflow that delivers a single-session **cognitive-reframing** intervention for users with **Avoidant Personality Disorder (APD)**.  
Your task is to gather **thorough, evidence-based background material** (max ≈ 15 000 words per agent) that will be injected into their system prompts to maximise therapeutic fidelity, cultural sensitivity, and safety.

────────────────────────────────────────────────
A. PROBLEM CONTEXT  (share with all researchers)
────────────────────────────────────────────────
• APD clients struggle with chronic shame, social withdrawal, and rigid negative self-beliefs.  
• We offer a short chat that:  
  1) collects a distressing automatic thought;  
  2) detects its cognitive distortion;  
  3) produces a balanced reframe + ≤ 10 min action step;  
  4) exports an anonymised PDF summary.  
• The system has three specialised agents:

  1️⃣ **Info-Collector** – gathers trigger, thought, emotion (plus optional extras) in ≤ 4 turns using trauma-informed interviewing.  
  2️⃣ **Reframer** – applies a distortion playbook to craft the balanced thought & action; measures confidence shift; ensures crisis escalation.  
  3️⃣ **PDF-Summariser** – turns session data into a clean report (header → input snapshot → analysis → micro-action & confidence shift → checklist).

────────────────────────────────────────────────
B. RESEARCH GOALS  (deliver separately per agent)
────────────────────────────────────────────────
For **each agent** produce a *research packet* (≤ 15 000 words) that covers:

1. **Clinical theory** – APD-specific findings, CBT adaptation guidelines, any transdiagnostic data relevant to automatic thoughts, shame, avoidance.  
2. **Best-practice scripts / phrases** – validated wording for validation, Socratic probes, cultural humility, crisis wording.  
3. **Safety & ethics** – recommended guard-rails, legal notes (EU + Spain), hotline accuracy, data-privacy tips.  
4. **Diversity considerations** – language tone, pronouns, collectivist vs individualist values, neurodivergence.  
5. **Measurement snippets** – evidence for confidence-shift metrics, distress-delta cut-offs, PDF feedback value.  
6. **High-grade references** – RCTs, meta-analyses, NICE / APA / WHO guidelines, Beck Institute materials, trauma-informed care manuals.  
7. **Practical templates** – tables, micro-action menus, rubric check-lists, pie-chart examples, continuum scaling examples.

────────────────────────────────────────────────
C. QUICK-CLIP TASKS  (divide & conquer)
────────────────────────────────────────────────
**Clip 1 → Info-Collector**  
• Search phrases: “avoidant personality interviewing,” “trauma-informed intake scripts,” “CBT APD validation statements.”  
• Target: 20–30 verbatim lines that model *warm-validation + concise open questions* for APD users.  

**Clip 2 → Reframer**  
• Search phrases: “CBT cognitive restructuring APD,” “probability re-rating efficacy,” “confidence scaling in single-session CBT.”  
• Target: 10 distortion-matched micro-actions tested in APD or social-anxiety samples, plus 10 balanced-thought exemplars ≤ 40 words each.

(*If there is bandwidth, create a third clip for Summariser: “digital after-visit summaries for psychotherapy”*).

────────────────────────────────────────────────
D. OUTPUT & FORMAT
────────────────────────────────────────────────
• Produce **one Markdown file per agent** named:  
  `research_info-collector.md`, `research_reframer.md`, `research_pdf-summariser.md`.  
• Within each file, organise with Level-2 headings (`##`) that mirror Sections 1-7 above.  
• Include inline citations in [Author YYYY] format and append a “References” list.  
• If you quote > 50 words from any source, add a short note on copyright status.  
• Bullet lists over paragraphs whenever possible for easy prompt injection.

────────────────────────────────────────────────
E. COLLABORATION & VERSION CONTROL
────────────────────────────────────────────────
• Each researcher works in a separate doc, then merges via Git or shared drive.  
• Use “NOTE TO PROMPT-WRITERS:” comments to flag especially injection-ready snippets.  
• Timebox: first draft packets in 3 days, final peer-review in 5 days.

────────────────────────────────────────────────
F. DELIVERABLE CHECKLIST
────────────────────────────────────────────────
[ ] Three Markdown research packets (≤ 15 k words each)  
[ ] Two quick-clips (Info-Collector & Reframer) with ready-to-paste lines  
[ ] Master reference list (APA 7th or [preferred style])  
[ ] Change-log of any ethical red-flags discovered  


=============
Root ─ SequentialAgent ───────────────────────────────────────────────────────────────
│
├─ 1️⃣ LoopAgent   (Agente-1  – diálogo libre con el usuario)
│      • max_iterations = N₁
│      • stop_condition = cond_1(state, events)
│
├─ 2️⃣ LlmAgent    (Agente-2  – parser ⇒ JSON)
│      • output_key = "parsed"
│
├─ 3️⃣ LoopAgent   (Agente-3  – diálogo de análisis + búsquedas web)
│      • max_iterations = N₃
│      • stop_condition = cond_3(state, events)
│      • reads   state["parsed"]
│      • writes  state["analysis"], state["web_lookups"]
│      │
│      └── LlmAgent "AnalystLLM"
│            • tools = [ WebSearchTool ]   ← nueva habilidad
│            • llama `web_search(query)` cuando necesita datos externos
│
└─ 4️⃣ ToolAgent   (Agente-4  – PDF + artefacto)
       • reads  state["conv_raw"],
                 state["analysis"],
                 state["web_lookups"]      ← ahora también cita fuentes
       • save_artifact()  →  GCS URL

Look, this is the diagram of the different agents (as initially proposed for the refraiming poc), you will see that there are missing components, please complete the components needed to be able to successfully run the workflow e2e with the same high standards as you have had until now. For instance, the parser llm agent is missing, but that's only an example. Identify and implement all misssing components to successfully run a session with adk web and then to be able to deploy to cloud run.

By the way, please find below some of the changes made by one of the other LLMs that were not explicitly mentioned and that I had to guide. I am providing them to you so you do not make any assumptions that contradict them.

# Changes Performed 

1. **Added Agent Instruction Keys to Settings Class**
   - Added four new settings to the `Settings` class in `base.py`:
     - `analysis_agent_instruction_key`: "reframe-agent-adk-instructions"
     - `collect_agent_instruction_key`: "intake-agent-adk-instructions"
     - `parser_agent_instruction_key`: "intake-parser-agent-adk-instructions"
     - `synthesis_agent_instruction_key`: "synthesis-agent-adk-instructions"
   - **Purpose**: Centralizes all prompt keys in the Settings class for easier management and consistency across the application.

2. **Updated Collector Agent (collect_llm.py)**
   - Changed hardcoded model name from "gemini-2." to `Settings.google_ai_model`
   - Replaced hardcoded instruction with `prompt_manager.fetch_prompt(Settings.collect_agent_instruction_key)`
   - **Purpose**: Removes hardcoded values and uses centralized configuration, enabling easier updates and maintenance.

3. **Updated Parser Agent (parser.py)**
   - Changed model from hardcoded "gemini-1.5-pro" to `Settings.google_ai_model`
   - Replaced hardcoded instruction with `prompt_manager.fetch_prompt(Settings.parser_agent_instruction_key)`
   - **Purpose**: Standardizes model usage across agents and moves prompt content to the prompt management system.

4. **Added Future Integration Notes to PDF Agent (pdf_agent.py)**
   - Added commented imports and code for future LLM integration
   - **Purpose**: Prepares the PDF agent for future enhancement with LLM capabilities using the synthesis prompt key.

These changes improve the codebase by:
1. Centralizing configuration in the Settings class
2. Removing hardcoded values from agent implementations
3. Making the system more maintainable and consistent
4. Enabling prompt management through the existing prompt_manager system
5. Providing a clear path for future PDF agent enhancement with LLM capabilities
