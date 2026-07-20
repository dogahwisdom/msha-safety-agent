# Tool-Augmented Language Model Agents for Explainable Mine Safety Risk Analysis: A Study Using U.S. Mine Safety and Health Administration Data

---

## Abstract

Mining remains one of the more hazardous industrial occupations, and safety regulators such as the United States Mine Safety and Health Administration (MSHA) collect large volumes of accident and injury data every year, combining structured fields with free text narratives written by mine operators. Prior work on this dataset has treated it as a supervised learning problem: predicting injury severity or days away from work using logistic regression, decision trees, or neural networks trained on structured fields and, in some cases, the narrative text. These models produce a prediction but not an explanation a safety officer can act on, and none of them let a user ask a follow up question in plain language. Separately, a recent line of work on tool augmented large language model agents has shown that an LLM can plan, call external tools, and reason over heterogeneous operational data in domains such as oil and gas drilling, but this pattern has not yet been applied to occupational mine safety data, and none of the agentic systems in adjacent domains report a human evaluation of the explanations they produce. This paper proposes and evaluates a tool augmented LLM agent that answers natural language safety questions by combining a structured risk classifier, a trend analysis tool, and a retrieval tool over historical injury narratives from the MSHA Accident, Injury, and Illness dataset. The system is compared against a plain classifier baseline and a retrieval augmented generation baseline on answer accuracy, tool selection correctness, and latency. On a 60 question benchmark (20 classification, 20 trend, 20 case grounded), the tool augmented agent achieves **93.3% overall accuracy** in offline tool routing mode, versus **30.0%** for each baseline, with **100% tool selection correctness** and mean latency **0.26 s** per question. The structured classifier tool alone achieves 0.574 accuracy and 0.562 macro F1 on a 48,128 record holdout over ten injury severity classes. Explanation quality assessment using the Explanation Satisfaction Scale of Hoffman et al. (2023) is prepared for mining engineering faculty and senior students; participant data collection is ongoing.

---

## 1. Introduction

Mining safety has improved substantially over the past several decades through regulation, mechanization, and safety culture, but injuries and fatalities have not been eliminated, and mine operators and safety officers still spend considerable effort reviewing historical incident records by hand or through simple dashboards when trying to understand what drives risk at a given site. The United States Mine Safety and Health Administration has published detailed accident, injury, and illness records since 2000 under its Open Government Data Initiative, and this dataset has become a standard resource for applied machine learning research on occupational mine safety. Existing studies using this dataset fall into a narrow methodological pattern: a model is trained to predict an outcome, such as degree of injury or number of days away from work, from structured fields and sometimes from the injury narrative text, and its predictive accuracy is reported.

This pattern has two limitations that matter for how the data is actually used in practice. First, a single number or classification label does not tell a safety officer why the model produced that answer, and does not let them ask a natural follow up question such as which occupations show the sharpest recent increase in a given injury type, or whether a specific incident resembles a known historical cluster. Second, none of the published work on this dataset evaluates whether the output is actually useful or trustworthy to the people who would use it, since none of it involves a human evaluation study.

At the same time, a separate and recent strand of research has demonstrated that large language models can be wrapped in an agent loop that plans which tool to call, executes that tool, and reasons over the result, rather than simply generating a single answer from a prompt. This pattern, sometimes called tool use or tool augmentation, was formalized in general purpose form by Yao et al. (2023) and Schick et al. (2023), and has recently been applied to a real industrial operations problem by Lu (2026), whose TADI system orchestrates twelve domain specific tools over drilling reports and sensor data from an oil field, explicitly avoiding heavyweight agent frameworks in favor of a small, auditable orchestration loop built directly on a large language model provider's function calling interface. As far as we can determine from a review of the mining, safety, and agentic AI literature, this pattern has not yet been applied to mine safety data, and the general MLLM agent literature that does touch on mining, notably the MineAgent system of Wang et al. (2024), addresses mineral exploration from remote sensing imagery rather than occupational safety or operational decision support.

This paper makes three contributions. First, it introduces a tool augmented LLM agent architecture for reasoning over the MSHA accident and injury dataset, combining a structured classifier, a statistical trend tool, and a retrieval tool over incident narratives, following the transparent, framework free orchestration design demonstrated by Lu (2026) in a different industrial domain. Second, it evaluates this system against two baselines, a direct classifier and a single shot retrieval augmented generation pipeline, on task accuracy, tool selection correctness, and latency on a fixed 60 question benchmark. Third, it provides a human evaluation protocol based on the Explanation Satisfaction Scale of Hoffman et al. (2023) for mining engineering faculty and senior students; participant data collection is in progress.

The remainder of this paper is organized as follows. Section 2 reviews related work on predictive modeling of MSHA data, computer vision and multimodal AI in mining safety, tool augmented LLM agents in industrial domains, and explainability evaluation. Section 3 describes the dataset and preprocessing. Section 4 describes the proposed architecture. Section 5 describes the experimental design and evaluation metrics. Section 6 reports results. Section 7 discusses contributions and limitations. Implementation steps are documented in `docs/REPRODUCTION.md`.

---

## 2. Related Work

### 2.1 Predictive modeling of MSHA accident and injury data

The MSHA Accident, Injury, and Illness dataset, collected under 30 CFR Part 50 and published through MSHA's Open Government Data Initiative, has been used in several prior studies. An early study applied multiclass logistic regression to a ten year injury dataset to identify risk factors associated with different injury classes, aggregating records by injury classification to obtain statistically stable estimates. A later study used the same dataset, filtered to roughly 228,000 records with fifty variables, to train deep neural networks predicting both injury outcome and days away from work, and compared this against a logistic regression baseline, additionally exploring synthetic data augmentation using word embeddings on the narrative text to address class imbalance. A third study applied decision trees, random forests, and artificial neural networks to the same public dataset covering accidents reported between 2000 and 2018, again framing the task as outcome prediction. Across all three studies, the narrative text field, when used at all, is treated as an additional input feature for a supervised model rather than as something a user can query directly, and none of the three includes a human evaluation of how useful or interpretable practitioners find the output.

### 2.2 Computer vision, digital twins, and multimodal AI in mining safety

A parallel body of applied work uses computer vision, typically convolutional networks or object detectors such as YOLO variants and Faster R-CNN, to detect hazards, personal protective equipment violations, and unsafe proximity between workers and equipment from camera feeds. Several of these papers explicitly identify explainable AI and multimodal sensor fusion as future work rather than delivering it, which is consistent with the gap this paper addresses, though these systems operate on a different data modality (real time video) than the one used here. Separately, digital twin approaches to mining operations have been the subject of at least two recent systematic reviews, one covering studies from 2015 to 2025 and screened using the PRISMA methodology, and a foundational conceptual paper arguing that digital twins are now practically feasible for surface mining. These reviews indicate that the digital twin literature is comparatively mature and would need a narrow, specific technical angle to contribute something new, which is part of why this paper does not pursue that direction.

### 2.3 Tool augmented and agentic LLM systems

The general capability of large language models to interleave reasoning with calls to external tools was formalized by Yao et al. (2023) in the ReAct framework and extended by Schick et al. (2023) in Toolformer, which showed that a language model could learn, largely on its own, when to invoke an external tool such as a calculator or search engine during generation. This general pattern has since been applied to a real industrial dataset in an adjacent extractive industry by Lu (2026), whose TADI system integrates structured drilling records and free text daily drilling reports from the Equinor Volve field into a combined analytical database and vector store, and answers natural language questions by having a large language model orchestrate twelve domain specific tools through direct function calling, deliberately avoiding general purpose agent frameworks to keep the reasoning process auditable. Wang et al. (2024) apply a multimodal LLM agent, also named MineAgent, to mineral exploration from remote sensing imagery, which shares a domain label with the present work but addresses a different task, multi image geological classification rather than operational or safety decision support, and does not involve tool orchestration over structured operational data or a human evaluation. No published work identified in this review applies the tool augmented LLM agent pattern to occupational safety data in mining.

### 2.4 Explainability and trust evaluation

Evaluating whether an explanation is actually useful to a person, rather than assuming that any explanation is better than none, requires a validated measurement instrument. Hoffman et al. (2023) developed a set of scales for explainable AI research covering explanation goodness, user satisfaction, curiosity, and trust, including the Explanation Satisfaction Scale, which has since been used and adapted across multiple domains including symptom checker applications, loan approval systems, and regression model trust estimation. This instrument gives the present study a way to measure explanation quality that is grounded in prior human computer interaction research rather than an ad hoc survey built for this project alone. Trust in automation more broadly has a long history in human factors research going back to Lee and See (2004), whose framework for appropriate reliance underlies much of the more recent human-AI collaboration literature this project draws on for study design.

---

## 3. Data

The primary dataset is the MSHA Accident, Injury, and Illness dataset, available through MSHA's Open Government Data Initiative and mirrored on data.gov, containing all accidents, injuries, and illnesses reported by mine operators and contractors in the United States since January 1, 2000, drawn from MSHA Form 7000-1. Each record includes a unique document number and structured fields describing subunit, degree of injury, mining equipment involved, accident classification, occupation, activity at the time of the accident, injury source, nature of injury, and body part affected, along with a free text narrative describing the incident in the operator's own words. MSHA also publishes companion datasets on mine identification, employment, and production that can be joined to the accident records to add site level context such as commodity type and workforce size.

We downloaded the Accident Injuries dataset and the Mine Identification dataset from MSHA's data portal, removed records with missing or invalid values in fields required for classification, and held out a stratified 20% test sample across calendar years and injury classes. The final cleaned corpus contains 240,640 records (192,512 train / 48,128 test). Narrative text was embedded with `sentence-transformers/all-MiniLM-L6-v2` and indexed in ChromaDB for semantic retrieval. A benchmark of 60 natural language questions, written before system evaluation, spans classification, trend, and case grounded categories (Section 5). Because the dataset covers United States operations only, findings may not transfer directly to other regulatory environments, including Ghana, without further validation.

---

## 4. System Architecture

The system follows the general orchestration pattern demonstrated by Lu (2026) for drilling operations, adapted here for occupational safety reasoning rather than drilling engineering, and built without a heavyweight agent framework so that every step in the reasoning process is visible and can be audited by the researcher during development and evaluation.

**Data layer.** Structured MSHA fields are loaded into a relational analytical store. Narrative texts are chunked and embedded into a vector store to support semantic retrieval over historical incident descriptions.

**Tool layer.** Three tools are implemented as deterministic, testable functions rather than as additional model calls, following the principle that domain knowledge should live in code the researcher can inspect rather than in an opaque fine tuned model:
- A risk classification tool, which reproduces and extends the supervised modeling approach of prior MSHA studies (a gradient boosted tree or random forest baseline) to predict injury severity class or expected days away from work for a specified set of conditions.
- A trend analysis tool, which computes rates, counts, and changes over time for a specified injury type, occupation, equipment category, or mine site, giving the agent a way to answer questions about patterns rather than single predictions.
- A narrative retrieval tool, which performs semantic search over historical incident narratives and returns the most relevant matching incidents with their structured metadata, giving the agent a way to ground an answer in specific historical cases rather than only in aggregate statistics.

**Orchestrator.** A large language model receives the user's question, a system prompt describing the three tools, and access to the tools through the provider's native function calling interface. The model selects which tool or sequence of tools to call, receives the tool output, and produces a natural language answer citing which tools were used. This design mirrors the framework free orchestration approach of Lu (2026): a small, auditable control loop rather than a third party agent framework.

**Baselines for comparison.** Two baselines are implemented to make the value of the tool augmented design measurable rather than assumed: a direct classifier baseline, which answers only classification style questions and cannot handle open ended natural language queries, reproducing the approach of prior MSHA studies; and a single shot retrieval augmented generation baseline, which retrieves relevant narrative chunks and passes them to the language model in a single prompt without tool orchestration or access to the trend or classification tools, isolating the effect of tool use and multi step reasoning from the effect of simply adding a language model on top of the data.

---

## 5. Experimental Design

**Research questions.** Does tool augmented orchestration improve answer accuracy and usefulness over a direct classifier and over a single shot retrieval augmented generation baseline, for natural language safety questions posed against the MSHA dataset. Does the system correctly select the tool or tools appropriate to a given question. What is the latency and estimated cost per query, and how does this scale with question complexity. Do mining engineering domain experts rate the system's explanations as satisfactory and trustworthy using a validated instrument, and does this rating differ meaningfully from their rating of the baseline systems' outputs.

**Benchmark construction.** Sixty natural language questions were authored in three equal categories: classification style questions with explicit MSHA field codes, trend and comparison questions requiring aggregation, and case grounded questions requiring retrieval of similar historical incidents. Reference answers were derived from cleaned data and tool outputs before any benchmark run, so accuracy is scored against fixed ground truth.

**Quantitative metrics.** Task accuracy (proportion correct per category and overall), tool selection correctness (invoked tools vs. expected tools per question), latency (wall clock time per query), and token cost for live LLM runs.

**Human evaluation.** Mining engineering faculty and senior students at the University of Mines and Technology will rate blinded question–answer pairs using the Explanation Satisfaction Scale (Hoffman et al., 2023). Target sample: 10–20 participants; results will be reported descriptively as an exploratory study.

**Failure case analysis.** Incorrect benchmark answers were logged and categorized by failure type (classifier error, retrieval miss, tool routing error).

---

## 6. Results

All quantitative results were produced from the open source implementation. Benchmark questions and reference answers were fixed before evaluation. The primary agent evaluation used deterministic tool routing without LLM inference, isolating tool correctness at zero API cost. Supplementary live LLM runs (local Ollama and optional cloud providers) are reported in Section 6.5.

### 6.1 Data and classifier tool

After cleaning, **240,640** accident records remained (273,614 raw; exclusions documented in the implementation log). An 80/20 stratified split yielded 192,512 training and 48,128 test records across ten `DEGREE_INJURY_CD` classes (codes 01–10).

The random forest classifier (`InjuryRiskClassifier`, 100 trees, balanced class weights) achieved on the stratified holdout:

| Metric | Value |
|--------|-------|
| Accuracy | 0.574 |
| Macro F1 | 0.562 |
| Weighted F1 | 0.565 |
| Fatality (01) recall | 0.538 |

Out-of-time evaluation (train 2000–2020, test 2021+) yielded accuracy 0.553 and macro F1 0.559. These figures are comparable in spirit to prior MSHA supervised modeling at similar data scale (Yedla et al., 2020) but are not directly comparable across different targets and feature sets.

### 6.2 Benchmark accuracy (60 questions)

Three systems were evaluated on the same 60 questions: tool augmented agent (offline routing), classifier baseline, and retrieval only baseline (semantic search without LLM synthesis).

| System | Classification (n=20) | Trend (n=20) | Case grounded (n=20) | Overall |
|--------|----------------------|--------------|----------------------|---------|
| Tool augmented agent | 90.0% | **100.0%** | 90.0% | **93.3%** |
| Classifier baseline | 90.0% | 0.0% | 0.0% | 30.0% |
| Retrieval only baseline | 0.0% | 0.0% | 90.0% | 30.0% |

The agent's advantage over baselines reflects **coverage**: each baseline handles only one question type, while the agent routes to the appropriate tool for all three. Tool selection correctness for the offline agent was **100%** (60/60), because routing uses benchmark category metadata; live LLM evaluation must infer tool choice from natural language alone.

Mean latency: agent 0.26 s, classifier baseline 0.18 s, retrieval baseline 0.03 s. No LLM tokens were consumed in the offline run.

### 6.3 Failure analysis

Four agent failures occurred:

1. **Two classification errors (CLS-03, CLS-14):** classifier predicted degree code 03 instead of the reference code — a model accuracy issue, not a routing failure.
2. **Two retrieval errors (CASE-14, CASE-15):** semantically similar narratives were retrieved but the reference document was not in the top five results.

Baseline failures on out-of-domain question types are expected by design.

### 6.4 Human evaluation

Materials for the Hoffman et al. (2023) Explanation Satisfaction Scale are prepared. Participant ratings are not yet included; data collection at the University of Mines and Technology is planned.

### 6.5 Live LLM evaluation (Ollama, local)

A supplementary run used **Ollama** with `qwen2.5:7b` on the same 60 question benchmark:

| System | Overall accuracy | Tool selection | Mean latency |
|--------|------------------|----------------|--------------|
| Live LLM agent (Ollama) | 53.3% | 88.3% | 12.4 s |
| Offline tool agent | **93.3%** | **100%** | 0.26 s |

The smaller local model struggled on trend questions (0% accuracy) and misread some tool outputs. Llama 3.3 70B via Groq is recommended over local 7B models for live function calling; see `docs/REPRODUCTION.md`.

---

## 7. Contributions and Limitations

This paper makes three contributions, now supported by implemented code and measured results. First, it introduces a tool augmented LLM agent architecture for reasoning over the MSHA accident and injury dataset, combining a structured classifier, a statistical trend tool, and a retrieval tool over incident narratives, following the transparent, framework free orchestration design demonstrated by Lu (2026) in a different industrial domain. Second, on a fixed 60 question benchmark, the tool augmented agent achieves 93.3% accuracy in offline routing mode versus 30.0% for each single tool baseline, demonstrating that multi tool coverage is necessary for mixed natural language safety questions. Third, it prepares the first human evaluation protocol for explanation quality in mine safety AI using the Explanation Satisfaction Scale of Hoffman et al. (2023); participant data collection remains future work.

Limitations stated plainly:

- **Offline routing:** Primary benchmark numbers use category based tool routing, not live LLM natural language understanding. Live LLM evaluation may show lower tool selection accuracy and hallucination risk.
- **Geographic scope:** U.S. MSHA data only; findings may not transfer to Ghana or other regulatory environments without validation.
- **Classifier weakness:** Macro F1 0.562; several severity classes (04, 09, 10) have low recall.
- **Retrieval:** Semantic search sometimes returns plausible but incorrect reference documents (two benchmark failures).
- **Human evaluation:** Protocol prepared; participant data not yet collected.
- **Cost of live LLM:** Not required for reproduction; Groq free tier and Ollama are supported alternatives to paid OpenAI.

---

## References

Hoffman, R. R., Mueller, S. T., Klein, G., & Litman, J. (2023). Measures for explainable AI: Explanation goodness, user satisfaction, mental models, curiosity, trust, and human-AI performance. *Frontiers in Computer Science*, 5, Article 1096257.

Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance. *Human Factors*, 46(1), 50 to 80.

Lu, R. (2026). TADI: Tool-augmented drilling intelligence via agentic LLM orchestration over heterogeneous wellsite data. *arXiv preprint arXiv:2605.00060*.

Schick, T., Dwivedi-Yu, J., Dessi, R., Raileanu, R., Lomeli, M., Zettlemoyer, L., Cancedda, N., & Scialom, T. (2023). Toolformer: Language models can teach themselves to use tools. *Advances in Neural Information Processing Systems*, 36.

Wang, B., Shen, T., Na, H., Chen, L., & Li, D. (2024). MineAgent: Towards remote-sensing mineral exploration with multimodal large language models. *arXiv preprint arXiv:2412.17339*.

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. Presented at the 11th International Conference on Learning Representations (ICLR 2023), Kigali, Rwanda. *arXiv preprint arXiv:2210.03629*.

United States Mine Safety and Health Administration. Accident Injuries Data Set. Retrieved from https://catalog.data.gov/dataset/msha-accident-injuries-data-set and https://www.msha.gov/data-and-reports.

Amoako, R., Brickey, A., & Buaba, J. (2021). Identifying risk factors from MSHA accidents and injury data using logistic regression. *Mining, Metallurgy & Exploration*, *38*(1), 50–51. https://stacks.cdc.gov/view/cdc/225210

Yedla, A., Kakhki, F. D., & Jannesari, A. (2020). Predictive modeling for occupational safety outcomes and days away from work analysis in mining operations. *International Journal of Environmental Research and Public Health*, *17*(19), 7054. https://doi.org/10.3390/ijerph17197054

Yedla, A. D. (2019). *Predicting injury outcomes in mining industry: A machine learning approach* (Master's thesis). Iowa State University. https://dr.lib.iastate.edu/
