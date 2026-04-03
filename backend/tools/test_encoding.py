from urllib.parse import quote

filenames = [
    "заявление_TST-1.docx",
    "smeta_МЕН-5.docx",
    "expenses_export.csv",
    "BLANK_ШКОЛА-2.docx"
]

for fn in filenames:
    encoded = quote(fn)
    print(f"Original: {fn}")
    print(f"Encoded:  {encoded}")
    print(f"Header:   filename*=utf-8''{encoded}")
    print("-" * 20)
