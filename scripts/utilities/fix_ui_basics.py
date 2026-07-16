import glob
import re

files = glob.glob('src/ui/**/*.py', recursive=True) + glob.glob('src/ui/*.py')
files = list(set(files))

count_bare = 0
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    new_content, n = re.subn(r'^(\s*)except:\s*(?:#.*)?$', r'\1except Exception as e:', content, flags=re.MULTILINE)
    
    if n > 0:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        count_bare += n

print(f'Fixed {count_bare} bare excepts.')

# We will just comment out the prints in the UI layer. Prints in UI are 99% debug artifacts.
# This avoids IndentationError and F821.
count_print = 0
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if 'print(' in content:
        lines = content.split('\n')
        changed = False
        for i in range(len(lines)):
            if re.search(r'^\s*print\(', lines[i]):
                lines[i] = lines[i].replace('print(', '# print(')
                count_print += 1
                changed = True
        
        if changed:
            with open(f, 'w', encoding='utf-8') as file:
                file.write('\n'.join(lines))

print(f'Commented out {count_print} prints.')
