import re
import glob

files = glob.glob('src/services/*.py')

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # We want to find:
    #         except Exception as e:
    #             import logging
    # logging.info(f"...")
    # And fix the indentation of import logging and logging.info
    
    # The error is that `import logging\nlogging.info` was inserted verbatim without indentation matching.
    # Let's fix this by finding lines that start with "import logging" with wrong indentation and matching their previous line.
    
    with open(f, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
    changed = False
    for i in range(1, len(lines)):
        if lines[i].startswith('import logging') or lines[i].lstrip().startswith('import logging'):
            # Check previous line to copy its exact leading whitespace + 4 spaces
            prev_line = lines[i-1]
            if prev_line.strip() == '':
                continue
                
            match = re.match(r'^([ \t]+)', prev_line)
            if match:
                base_indent = match.group(1)
                
                # If the previous line is "except Exception as e:", we need one more level of indent
                if prev_line.strip().startswith('except ') or prev_line.strip().startswith('else:') or prev_line.strip().startswith('try:'):
                    target_indent = base_indent + '    '
                else:
                    target_indent = base_indent
                
                # Fix the current line
                if lines[i] != target_indent + lines[i].lstrip():
                    lines[i] = target_indent + lines[i].lstrip()
                    changed = True
                    
                # Fix the next line if it's logging.info
                if i+1 < len(lines) and lines[i+1].lstrip().startswith('logging.info'):
                    if lines[i+1] != target_indent + lines[i+1].lstrip():
                        lines[i+1] = target_indent + lines[i+1].lstrip()
                        changed = True

    if changed:
        with open(f, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        print(f"Fixed {f}")
