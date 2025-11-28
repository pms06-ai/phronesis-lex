import os
import re
import csv

# Configuration
ROOT_DIR = r"C:\Users\pstep\OneDrive\Desktop\THE CASE"
OUTPUT_FILE = r"C:\Users\pstep\phronesis-lex\Phronesis\DOCUMENT_ATTRIBUTION_LOG.md"

# Known Parties/Authors (Regex patterns)
# Order matters: specific full names first, then aliases
AUTHORS = {
    "Samantha Stephen": [r"Samantha Stephen", r"SJS", r"Samantha Seamark", r"Mother", r"1st Respondent", r"First Respondent"],
    "Paul Stephen": [r"Paul Stephen", r"PS", r"Father", r"2nd Respondent", r"Second Respondent", r"Step-Father"],
    "Mandy Seamark": [r"Mandy Seamark", r"Mandy", r"MS", r"MGM", r"Grandmother", r"Maternal Grandmother"],
    "Joshua Dunmore": [r"Joshua Dunmore", r"Josh", r"JD", r"Father", r"Applicant"],
    "Gary Dunmore": [r"Gary Dunmore", r"Gary", r"PGF", r"Paternal Grandfather"],
    "Fran Balmford (SW)": [r"Fran Balmford", r"Fran"],
    "Sophie Bradley (SW)": [r"Sophie Bradley", r"Sophie"],
    "Dr. Hunnisett (Expert)": [r"Hunnisett", r"Dr H"],
    "Police / MCU": [r"Police", r"MG11", r"MCU", r"Constable", r"DC ", r"PC ", r"DS ", r"Incident Report"],
    "Children's Guardian": [r"Guardian", r"Cafcass"],
    "Legal (Solicitors)": [r"Oslers", r"Copleys", r"Atkins Dellow", r"Lucy Ardern", r"Tim Colbran"],
    "School / Education": [r"School", r"Teacher", r"EHCP", r"Report"],
    "Medical / Health": [r"Medical", r"Health", r"Doctor", r"NHS", r"Clinic", r"Hospital"],
}

IGNORE_DIRS = [".git", ".cursor", "node_modules"]
IGNORE_FILES = ["desktop.ini", ".DS_Store"]

def identify_author(filename):
    # Check against known authors
    for author, patterns in AUTHORS.items():
        for pattern in patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return author
    return "Unattributed / General"

def determine_type(filename):
    filename = filename.lower()
    if "statement" in filename or "stmt" in filename or "mg11" in filename:
        return "Statement"
    if "email" in filename or "correspondence" in filename:
        return "Email/Correspondence"
    if "report" in filename or "assessment" in filename:
        return "Report/Assessment"
    if "order" in filename or "application" in filename or "c2" in filename:
        return "Court Order/App"
    if "interview" in filename:
        return "Interview Record"
    if "note" in filename:
        return "Note/Record"
    return "Evidence/Other"

def scan_and_attribute(root_path):
    print(f"Scanning {root_path}...")
    attribution_map = {}

    for root, dirs, files in os.walk(root_path):
        # Skip ignored dirs
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES:
                continue
                
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, root_path)
            
            author = identify_author(file)
            doc_type = determine_type(file)
            
            if author not in attribution_map:
                attribution_map[author] = []
            
            attribution_map[author].append({
                "File": file,
                "Path": rel_path,
                "Type": doc_type
            })
            
    return attribution_map

def generate_markdown(attribution_map):
    md = "# Document Attribution Log\n\n"
    md += "**Generated:** " + os.popen("date /t").read().strip() + "\n\n"
    
    # Sort authors: Specific people first, then General
    sorted_authors = sorted(attribution_map.keys())
    if "Unattributed / General" in sorted_authors:
        sorted_authors.remove("Unattributed / General")
        sorted_authors.append("Unattributed / General")

    for author in sorted_authors:
        files = attribution_map[author]
        md += f"## 👤 {author} ({len(files)} files)\n\n"
        md += "| Type | Document Name | Location |\n"
        md += "| :--- | :--- | :--- |\n"
        
        # Sort by Type then Name
        sorted_files = sorted(files, key=lambda x: (x['Type'], x['File']))
        
        for item in sorted_files:
            # Shorten path for display
            short_path = item['Path']
            if len(short_path) > 50:
                short_path = "..." + short_path[-47:]
            
            md += f"| **{item['Type']}** | {item['File']} | `{short_path}` |\n"
        
        md += "\n"
        
    return md

if __name__ == "__main__":
    data = scan_and_attribute(ROOT_DIR)
    report = generate_markdown(data)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"Attribution log written to: {OUTPUT_FILE}")

