import os
import glob
from pypdf import PdfReader

pdf_files = sorted(glob.glob("inbound/*.pdf"))
with open("pdf_summary.txt", "w", encoding="utf-8") as out:
    for f in pdf_files:
        reader = PdfReader(f)
        out.write("====== " + os.path.basename(f) + " ======\n")
        text = ""
        for page in reader.pages[:1]: # read first page only
            text += page.extract_text()
        
        # We only need the top 1000 characters which usually contain the month and summary
        out.write(text[:800] + "\n")
        out.write("-" * 40 + "\n")
