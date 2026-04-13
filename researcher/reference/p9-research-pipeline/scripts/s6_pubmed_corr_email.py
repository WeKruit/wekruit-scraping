"""
S6: PubMed Corresponding Author Email
Uses Biopython E-Utilities to fetch article XML and extract corresponding author emails.

Usage:
  python scripts/s6_pubmed_corr_email.py --query "deep learning" --max-results 500
"""
import argparse, json, os, re, sys, time, xml.etree.ElementTree as ET
from pathlib import Path

import requests
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR, NCBI_API_KEY, NCBI_EMAIL

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')


def search_pmids(query: str, max_results=500) -> list[str]:
    params = {"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"}
    if NCBI_API_KEY: params["api_key"] = NCBI_API_KEY
    r = requests.get(f"{EUTILS_BASE}/esearch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("esearchresult", {}).get("idlist", [])


def fetch_article_xml(pmids: list[str]) -> str:
    params = {"db": "pubmed", "id": ",".join(pmids), "rettype": "xml"}
    if NCBI_API_KEY: params["api_key"] = NCBI_API_KEY
    r = requests.get(f"{EUTILS_BASE}/efetch.fcgi", params=params, timeout=60)
    r.raise_for_status()
    return r.text


def extract_corr_emails(xml_text: str) -> list[dict]:
    results = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return results
    for article in root.findall(".//PubmedArticle"):
        pmid_el = article.find(".//PMID")
        pmid = pmid_el.text if pmid_el is not None else None
        title_el = article.find(".//ArticleTitle")
        title = title_el.text if title_el is not None else ""
        # Find emails in author affiliations
        emails = set()
        for aff in article.findall(".//AffiliationInfo/Affiliation"):
            if aff.text:
                emails.update(EMAIL_RE.findall(aff.text))
        for email_el in article.findall(".//Author/AffiliationInfo/Identifier[@Source='email']"):
            if email_el.text:
                emails.add(email_el.text)
        # Also check article-level
        for el in article.iter():
            if el.tag == "Email" and el.text:
                emails.add(el.text)

        # Extract authors
        authors = []
        for auth in article.findall(".//Author"):
            last = (auth.find("LastName") or type('',(),{'text':''})()).text or ""
            first = (auth.find("ForeName") or type('',(),{'text':''})()).text or ""
            if last:
                authors.append(f"{first} {last}".strip())

        if emails:
            results.append({
                "pmid": pmid, "title": title,
                "authors": authors, "corr_emails": list(emails),
                "source": "pubmed_corr"
            })
    return results


def main():
    parser = argparse.ArgumentParser(description="S6: PubMed corresponding author email")
    parser.add_argument("--query", type=str, default="artificial intelligence", help="PubMed search query")
    parser.add_argument("--max-results", type=int, default=500)
    parser.add_argument("--output", type=str, default=f"{DATA_DIR}/pubmed_emails.jsonl")
    args = parser.parse_args()

    print(f"[S6] PubMed search: '{args.query}'")
    pmids = search_pmids(args.query, args.max_results)
    print(f"  Found {len(pmids)} PMIDs")

    all_results = []
    batch_size = 50
    delay = 0.34 if NCBI_API_KEY else 1.0
    for i in tqdm(range(0, len(pmids), batch_size), desc="Fetching XML"):
        batch = pmids[i:i+batch_size]
        xml = fetch_article_xml(batch)
        all_results.extend(extract_corr_emails(xml))
        time.sleep(delay)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[S6] Found emails in {len(all_results)} articles → {args.output}")


if __name__ == "__main__":
    main()
