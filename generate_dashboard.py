import os
import html
import markdown
import datetime
import re
from pypdf import PdfReader

# Configuration
ROOT_DIR = r"C:\Users\pstep\OneDrive\Desktop\THE CASE"
OUTPUT_FILE = os.path.join(ROOT_DIR, "index.html")
REPORTS_DIR = r"C:\Users\pstep\phronesis-lex\Phronesis" # Where I wrote the MD files

# Styles (CSS)
CSS = """
<style>
    :root { --primary: #2c3e50; --secondary: #34495e; --accent: #3498db; --light: #ecf0f1; }
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background: #f4f7f6; }
    header { background: var(--primary); color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
    h1 { margin: 0; font-size: 1.5rem; }
    nav { background: var(--secondary); padding: 0.5rem 2rem; position: sticky; top: 0; z-index: 100; }
    nav a { color: white; text-decoration: none; margin-right: 1.5rem; font-weight: 500; }
    nav a:hover { color: var(--accent); }
    .container { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }
    .card { background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); padding: 1.5rem; margin-bottom: 2rem; }
    .card h2 { border-bottom: 2px solid var(--light); padding-bottom: 0.5rem; margin-top: 0; color: var(--primary); }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }
    .file-link { display: block; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; text-decoration: none; color: var(--primary); transition: background 0.2s; }
    .file-link:hover { background: var(--light); border-color: var(--accent); }
    .file-meta { font-size: 0.85rem; color: #7f8c8d; display: block; margin-top: 0.25rem; }
    .tag { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: bold; margin-right: 0.5rem; }
    .tag-new { background: #e74c3c; color: white; }
    .tag-master { background: #27ae60; color: white; }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    th, td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #ddd; }
    th { background-color: var(--light); font-weight: 600; }
    tr:hover { background-color: #f1f1f1; }
    .search-box { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 1rem; font-size: 1rem; }
    footer { text-align: center; padding: 2rem; color: #7f8c8d; font-size: 0.9rem; }
    
    /* Attribution Section Styles */
    .attribution-container { display: flex; gap: 1rem; }
    .attribution-sidebar { width: 250px; flex-shrink: 0; background: white; padding: 1rem; border-radius: 8px; height: fit-content; position: sticky; top: 80px; }
    .attribution-content { flex-grow: 1; }
    .author-filter { display: block; padding: 0.5rem; margin-bottom: 0.5rem; background: var(--light); border-radius: 4px; cursor: pointer; text-decoration: none; color: var(--primary); }
    .author-filter:hover, .author-filter.active { background: var(--accent); color: white; }
    .author-section { display: none; }
    .author-section.active { display: block; animation: fadeIn 0.3s; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
"""

JS = """
<script>
function filterTable(filterValue) {
    const table = document.getElementById('indexTable');
    if (!table) return;
    const query = (filterValue || '').toUpperCase();
    const rows = table.getElementsByTagName('tr');
    for (let i = 0; i < rows.length; i++) {
        const firstCell = rows[i].getElementsByTagName('td')[0];
        if (!firstCell) continue;
        const txtValue = firstCell.textContent || firstCell.innerText || '';
        rows[i].style.display = txtValue.toUpperCase().includes(query) ? '' : 'none';
    }
}

function showAuthor(authorId) {
    const sections = document.querySelectorAll('.author-section');
    sections.forEach(section => {
        section.classList.toggle('active', section.id === `author-${authorId}`);
    });

    const filters = document.querySelectorAll('.author-filter');
    filters.forEach(filter => {
        filter.classList.toggle('active', filter.dataset.author === authorId);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const filters = document.querySelectorAll('.author-filter');
    if (filters.length) {
        filters.forEach(filter => {
            filter.addEventListener('click', () => {
                const authorId = filter.dataset.author;
                if (authorId) {
                    showAuthor(authorId);
                }
            });
        });
        showAuthor(filters[0].dataset.author);
    }

    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', () => filterTable(searchInput.value));
    }
});
</script>
"""


def safe_text(value: str) -> str:
    """HTML-escape helper that also handles None gracefully."""
    return html.escape(value or "")


def to_web_path(path: str) -> str:
    """Convert OS-specific paths to web-friendly forward-slash paths."""
    return path.replace("\\", "/")

def get_file_info(path):
    try:
        stats = os.stat(path)
        dt = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
        size_mb = stats.st_size / (1024 * 1024)
        return f"{dt} | {size_mb:.2f} MB"
    except:
        return "Unknown"

def generate_index_section():
    master_path = os.path.join(ROOT_DIR, "00_MASTER_BUNDLE")
    if not os.path.isdir(master_path):
        return ""

    links = []
    for file in sorted(os.listdir(master_path)):
        full_path = os.path.join(master_path, file)
        if not os.path.isfile(full_path) or not file.lower().endswith(".pdf"):
            continue
        rel_path = to_web_path(os.path.relpath(full_path, ROOT_DIR))
        meta = get_file_info(full_path)
        links.append(
            f'''                <a href="{rel_path}" class="file-link" target="_blank">
                    <span class="tag tag-master">BUNDLE</span>
                    <strong>{safe_text(file)}</strong>
                    <span class="file-meta">{meta}</span>
                </a>'''
        )

    if not links:
        return ""

    links_markup = "\n".join(links)
    return f"""
        <div class="card" id="master-bundle">
            <h2>📂 Master Bundle (00_MASTER_BUNDLE)</h2>
            <div class="grid">
{links_markup}
            </div>
        </div>
    """

def generate_inbox_section():
    inbox_path = os.path.join(ROOT_DIR, "11_NEW_INBOX")
    if not os.path.isdir(inbox_path):
        return ""

    entries = []
    files = sorted(
        (f for f in os.listdir(inbox_path) if not f.startswith(".")),
        key=lambda x: os.path.getmtime(os.path.join(inbox_path, x)),
        reverse=True
    )

    for file in files:
        full_path = os.path.join(inbox_path, file)
        if not os.path.isfile(full_path):
            continue
        rel_path = to_web_path(os.path.relpath(full_path, ROOT_DIR))
        meta = get_file_info(full_path)
        entries.append(
            f'''                <a href="{rel_path}" class="file-link" target="_blank">
                    <span class="tag tag-new">NEW</span>
                    <strong>{safe_text(file)}</strong>
                    <span class="file-meta">{meta}</span>
                </a>'''
        )

    if not entries:
        return ""

    entries_markup = "\n".join(entries)
    return f"""
        <div class="card" id="new-inbox">
            <h2>📥 New Evidence Inbox (11_NEW_INBOX)</h2>
            <p>Files processed from "New folder" are located here.</p>
            <div class="grid">
{entries_markup}
            </div>
        </div>
    """

def parse_attribution_log():
    """Parses the markdown log into structured data for the HTML view"""
    log_path = os.path.join(REPORTS_DIR, "DOCUMENT_ATTRIBUTION_LOG.md")
    if not os.path.exists(log_path):
        return {}
        
    authors = {}
    current_author = None
    
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        # Detect Author Header: ## 👤 Name (Count)
        if line.startswith("## 👤"):
            # Extract name
            match = re.search(r"## 👤 (.*?) \(", line)
            if match:
                current_author = match.group(1).strip()
                authors[current_author] = []
        
        # Detect Table Row: | **Type** | File | Path |
        elif line.startswith("| **") and current_author:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 3:
                doc_type = parts[0].replace("**", "")
                filename = parts[1]
                path_raw = parts[2].replace("`", "")
                
                # Fix path - sometimes MD truncates or formats weirdly
                # We'll try to make it a valid link if it looks like a path
                if "..." in path_raw:
                    # Can't link truncated paths easily, just show name
                    pass 
                
                authors[current_author].append({
                    "type": doc_type,
                    "file": filename,
                    "path": path_raw
                })
                
    return authors

def generate_attribution_section():
    authors_data = parse_attribution_log()
    if not authors_data:
        return ""
        
    sidebar_links = []
    content_sections = []
    
    for author, docs in authors_data.items():
        safe_id = re.sub(r'\W+', '', author).lower()
        sidebar_links.append(
            f'''                <div class="author-filter" data-author="{safe_id}">
                    {safe_text(author)} <span style="float:right; opacity:0.6">{len(docs)}</span>
                </div>'''
        )
        
        rows = []
        for doc in docs:
            rows.append(
                f'''                            <tr>
                                <td><span class="tag">{safe_text(doc.get("type", ""))}</span></td>
                                <td>{safe_text(doc.get("file", ""))}</td>
                            </tr>'''
            )
        if not rows:
            rows.append("                            <tr><td colspan=\"2\">No documents recorded.</td></tr>")
        
        rows_markup = "\n".join(rows)
        content_sections.append(
            f'''                <div id="author-{safe_id}" class="author-section">
                    <h3>Documents Attributed to: {safe_text(author)}</h3>
                    <table>
                        <thead><tr><th>Type</th><th>Document</th></tr></thead>
                        <tbody>
{rows_markup}
                        </tbody>
                    </table>
                </div>'''
        )
    
    sidebar_markup = "\n".join(sidebar_links)
    content_markup = "\n".join(content_sections)
    
    return f"""
        <div class="card" id="attribution">
            <h2>👥 Document Attribution & Parsing</h2>
            <p>Documents automatically linked to specific parties based on content analysis.</p>
            <div class="attribution-container">
                <div class="attribution-sidebar">
                    <h3>👤 Parties</h3>
{sidebar_markup}
                </div>
                <div class="attribution-content">
{content_markup}
                </div>
            </div>
        </div>
    """

def convert_markdown_reports():
    reports = [
        "CASE_QA_REPORT.md",
        "PARTIES_AND_ROLES.md",
        "EMAIL_COMMUNICATIONS_LOG.md",
        "POLICE_WITNESS_ANALYSIS.md",
        "NEW_FILES_ANALYSIS.md",
        "DOCUMENT_ATTRIBUTION_LOG.md"
    ]
    
    sections = []
    for report in reports:
        path = os.path.join(REPORTS_DIR, report)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                md_content = f.read()
                html_content = markdown.markdown(md_content, extensions=['tables'])
                sections.append(
                    f'''            <details>
                <summary style="cursor:pointer; padding:1rem; background:#eee; margin-bottom:0.5rem; font-weight:bold;">
                    {safe_text(report)}
                </summary>
                <div style="padding:1rem; border:1px solid #eee;">{html_content}</div>
            </details>'''
                )
    
    if not sections:
        return ""
    
    sections_markup = "\n".join(sections)
    return f"""
        <div class="card" id="analysis">
            <h2>📊 AI Analysis Reports</h2>
{sections_markup}
        </div>
    """

def extract_index_pdf_content():
    # Attempt to extract the Index PDF text to make it searchable
    index_path = os.path.join(ROOT_DIR, "00_MASTER_BUNDLE", "00_INDEX.pdf")
    rows = []
    
    if os.path.exists(index_path):
        try:
            reader = PdfReader(index_path)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    lines = text.split('\n')
                    for line in lines:
                        if len(line.strip()) > 5:
                            # Try to parse Page Number if at end of line
                            parts = line.rsplit(' ', 1)
                            page_ref = parts[-1] if len(parts) > 1 and (parts[-1].startswith('A') or parts[-1].startswith('B') or parts[-1].isdigit()) else ""
                            content = parts[0] if len(parts) > 1 else line
                            
                            rows.append(
                                f'''                        <tr>
                                <td>{safe_text(content.strip())}</td>
                                <td>{safe_text(page_ref)}</td>
                                <td>Page {i+1}</td>
                            </tr>'''
                            )
        except Exception as e:
            rows = [f"                        <tr><td colspan='3'>Error reading Index PDF: {safe_text(str(e))}</td></tr>"]
    
    if rows:
        rows_markup = "\n".join(rows)
        return f"""
        <div class="card" id="searchable-index">
            <h2>🔍 Searchable Case Index</h2>
            <input type="text" id="searchInput" class="search-box" placeholder="Search for documents in the Master Index...">
            <div style="max-height: 500px; overflow-y: auto;">
                <table id="indexTable">
                    <thead><tr><th>Document Description</th><th>Bundle Ref</th><th>PDF Page</th></tr></thead>
                    <tbody>
{rows_markup}
                    </tbody>
                </table>
            </div>
        </div>
        """
    return ""

def main():
    print("Generating Dashboard...")
    
    sections = [
        ("master-bundle", "Master Bundle", generate_index_section()),
        ("new-inbox", "New Evidence", generate_inbox_section()),
        ("attribution", "Attribution", generate_attribution_section()),
        ("searchable-index", "Search Index", extract_index_pdf_content()),
        ("analysis", "AI Reports", convert_markdown_reports()),
    ]
    
    nav_links = []
    content_blocks = []
    for anchor, label, block in sections:
        if block and block.strip():
            nav_links.append(f'            <a href="#{anchor}">{label}</a>')
            content_blocks.append(block)
    
    nav_html = "\n".join(nav_links)
    body_content = "\n".join(content_blocks)
    
    content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Legal Case Dashboard</title>
        {CSS}
    </head>
    <body>
        <header>
            <h1>⚖️ Legal Case Dashboard</h1>
            <span>Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
        </header>
        
        <nav>
{nav_html}
        </nav>

        <div class="container">
{body_content}
        </div>

        <footer>
            <p>Generated by Phronesis AI for Legal Case Management.</p>
        </footer>
        {JS}
    </body>
    </html>
    """
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Dashboard created at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()