import os
from datetime import datetime

OUTPUT_DIR = "."
out_path = os.path.join(OUTPUT_DIR, "index.html")

def main():
    html = f"""<!doctype html>
<html lang="no">
<head>
  <meta charset="utf-8">
  <title>Testside – Strand postliste</title>
</head>
<body>
  <h1>Hei verden 👋</h1>
  <p>Denne siden ble generert {datetime.now().strftime("%Y-%m-%d %H:%M")}.</p>
</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Skrev test index.html til {out_path}")

if __name__ == "__main__":
    main()
