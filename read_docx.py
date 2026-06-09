import zipfile
import xml.etree.ElementTree as ET
import sys

def read_docx(file_path):
    try:
        with zipfile.ZipFile(file_path) as docx:
            tree = ET.fromstring(docx.read('word/document.xml'))
            namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            texts = [node.text for node in tree.findall('.//w:t', namespaces) if node.text]
            return ' '.join(texts)
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    file_path = sys.argv[1]
    with open("proposal_text.txt", "w", encoding="utf-8") as f:
        f.write(read_docx(file_path))
