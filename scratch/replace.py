import glob
import os

files = glob.glob('D:/ViTai/src/vitai/*.py')
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace references
    new_content = content.replace('vitrans.', 'vitai.')
    new_content = new_content.replace('from vitrans', 'from vitai')
    new_content = new_content.replace('import vitrans', 'import vitai')
    new_content = new_content.replace('ViTrans', 'ViTai')
    new_content = new_content.replace('vitrans', 'vitai')
    
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
