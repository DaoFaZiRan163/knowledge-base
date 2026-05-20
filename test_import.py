import sys
print('Python version:', sys.version)
try:
    from unstructured.partition.auto import partition
    print('unstructured OK')
except Exception as e:
    print('unstructured error:', e)
try:
    from pypdf import PdfReader
    print('pypdf OK')
except Exception as e:
    print('pypdf error:', e)