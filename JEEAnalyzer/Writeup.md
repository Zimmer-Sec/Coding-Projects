### Motivation: When provided with millions of PDF documents about a PDFile, I found it to be a waste of time to manually open, read, and assess pointless business emails in search of a golden nugget. The great American technology sector has developed a product (LLMs) to read and assess words (assign weights) in the blink of an eye. Why not integrate AI/LLMs with Python to streamline the scraping, analysis, and summarization process to find things that are of interest.  
#### [Source Code](https://github.com/Zimmer-Sec/Coding-Projects/JEEAnalyzer/Core.py)   

# Process Overview:
Understanding that LLMs (like ChatGPT) aren't able to just magically doing everything by telling it what to do from the prompt (i.e the full process of web scraping, querying, reading, and analyzing documents across the internet) is the starting point. We need to make a program to then create our optimized store of data that the LLM can parse through and link data between. The way I see this process flowing is as follows:
1. Data Ingestion & Pre‑Processing (take in millions of PDFs to normal text with metadata structures)
2. Chunking & metadata enrichment (use chunker.py module to turn raw text into LLM‑sized chunks with metadata)
3. Embeddings & vector store (use embedder.py to make scalable by allowing the LLM to target data chunks)
4. LLM Reading & Analysis (use llm_client.py | analysis_flows.py to implement LLM to read and think about data)
5. Orchestration (set up batch jobs, queues, fault tolerance, track token usage/etc.)
6. User Workflows ("use the processed data" > query, dashboards, exports)

# Stage 1: Data Ingestion & Pre-processing
- Needing to get a proof of concept done.
- Data sets 1, 2, and 3 are all scanned images. Data set 4 has the first true text-based PDF files that can be analyzed.
- Plan: Download/load, extract text page by page, normalize text, format and save as json.
- [x] Create directory structure for data, configuration, source scripts, requirements, testing and main python components
- [x] Label requirements in root directory
- [x] Label data, database, logging, extraction tool, and other settings under config
- [ ] Outline and create sqlite3 database to store json metadata.
- [ ] Create method for downloading and registering pdf docs from internet
- [ ] Create ways for user to use PyMuPDF, pdfplumber, PdfReader as methods to extract/normalize page metadata to database
- [ ] Use main.py to showcase a proof of concept against a single pdf document
