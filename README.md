# SUPHRA Recommendation Generator
A tool to extract, upload, and maintain productivity and health recommendations from scientific papers. Each LLM-generated recommendation source information from [Semantic Scholar API](https://www.semanticscholar.org/product/api) will be assigned.


<img src="assets/screenshot_extraction_frame.png" width="100%" align="center"> GUI Screenshot


## 📖How to use
**1. Set up keys.**
To generate recommendations you necessarily need to add an [OpenAi API key](https://openai.com/index/openai-api/), since OpenAi´s GPT models are the only supported models so far. A [Semantic Scholar API](https://www.semanticscholar.org/product/api) is also required for usage.
To set up your keys just fill in `.env` like it is done in [.env.template](/.env.template).

**2. Set up URL to your Database**
Fill in the DATABASE_URL field in your `.env` following [SQLAlchemy's convention](https://docs.sqlalchemy.org/en/20/core/engines.html#:~:text=various%20backends%20available.-,Database%20URLs%C2%B6,-The%20create_engine()).

**3. Feed your papers.** 
To hand in your scientific papers just select them via the drag-and-drop field in the 'Extraction' view. It is recommended to not upload too many documents at once since you will probably lose track of them. Start with 1-2 papers to see how it works.

**4. Choose a model.** The only model that is currently supported is OpenAIs GPT-4o-mini. Depending on requirements, more models will be added. Be sure to provide the required keys for the chosen model.

**5. Generate!** Click on *Generate Recommendations* and the model will analyze what you have given towards it. 

## 📅 Output Table
| **Field** | **Describtion** |
|-----------|-----------------|
| short_desc | A short describtion of the recommended tip. |
| long_desc | A more informative version of the tip which also introduces the reader to the study from which the tip comes from. |
| goal | What should be achieved when the tip is excuded? Possible values: `augment`(should be mentioned when improving on something), `prevent`(should be mentioned when avoiding negative impact), `recover`(should be mentioned when restoring personal resources), `maintain`(Preserving current levels of performance, well-being, or resources to ensure stability and consistency) | 
| activity_type | What is the key characteric of the tip to execute the tip? Possible values: `creative`, `exercise`, `cognitive`, `relax`, `social`, `time management`, `nutrition` |
| categories | Possible values: `work`, `success`, `productivity`, `performance`, `focus`, `time management`, `happiness`, `mental`, `active reflection`, `awareness`, `well-being`, `health`, `fitness`, `social` |
| concerns | Concerns for which the tip could be helpful. Possible values: `goal-setting`(Defining Goals and tracking progress toward them), `self-motivation`(finding internal motivation to work on tasks), `self-direction`(Taking initiative and making independent decisions to guide your work and priorities), `self-discipline`(maintaining consistent effort and control over impulses to achieve tasks and goals), `focus`(concentrating on tasks while minimizing distractions and interruptions), `mindeset`(Developing attitudes and beliefs that support resilience and growth), `time management`(organizing and allocating time effectively to complete tasks and meet deadlines), `procrastination`(overcoming delays andavoidance in starting and completing tasks), `stress management`(coping with and reducing stess to maintain productivity and well-being), `mental-health`(promoting emotional and psychological well-being to support overall performance), `work-life balance`(balancing professional and personal responsibilities for a fulfilling lifestyle), `sleep quality`(improving the quality and consistency of sleep to enhance energy and focus) |
| daytime | When should the tip ideally be executed? Possible values: `morning`(tips that may influence the day ahead. e.g. mindset, motivation), `noon`(tips that are relevant for the second part of the day), `evening`(tips that are relevant when the day's work is done), `end of day`(tips that are relevant to finish the day, e.g. conclude about the day), `any`(if it doesnt matter) |
| wekkdays | For which type of days is the tip relevant? Possible values: `workdays`, `weekend`, `week start`, `end of workweek`, `public holiday`, `any`(if it doesnt matter) |
| season | In which season should the tip ideally be executed? Possible values: `any`, `spring`, `summer`, `autumn`, `winter`, `holiday season`(starting in late November and lasting until the begin of January), `summer vacation` |
| is_outdoor | Is the tip most probably executed outdoors? outdoor: `TRUE`;  indoor: `FALSE`  |
| is_advanced | Is the tip executable for users with low health literacy? yes: `TRUE`; no: `FALSE` |
| gender | Is the tip relevant for anybody or only for a specific gender? (e.g. regarding menstrual cycle or menopause) Possible values: `male`, `female`, `any` |
| src_title | Title of the regarding paper. (SemanticScholar) |
| src_pub_year | Publication year of the regarding paper. (SemanticScholar) |
| src_pub_type | Specifies categories of scholarly works. Possible values: see `publicationTypes` on [SemanticScholarAPI](https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data/operation/get_graph_paper_relevance_search) |
| src_field_of_study | Specifies the subject areas in which the paper is located. Possible values: see `fieldsOfStudy` on [SemanticScholarAPI](https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data/operation/get_graph_paper_relevance_search) |
| src_doi | Paper's DOI |
| src_hyperlink | URL to paper's SemanticScholar entry. |
| src_pub_venue | Venue the paper was published in. |
| src_citations | Number of citations of the paper. |
| src_cit_influential | Number of 'highly influential' citations of the paper. (see [What are highly influential citations?](https://www.semanticscholar.org/faq/influential-citations)) |
| created_at | Timestamp that will be set by the database. It therefore contains the time of the upload to the database, not the time of creation by the model. |
| modified_at | Timestamp of last modification in the database. |
| risk | `NOT YET IMPLEMENTED` |
| is_approved | `NOT YET IMPLEMENTED` |

The prompt that is used for the generation is based on [this instructions text](./data/instructions/paper_to_rec_inst.txt). To keep a clear output structure function calling is used (see *tools* in [generate.py](./tip_generator/)).
