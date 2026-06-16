import glob
import re

def fix_bare_excepts():
    files = glob.glob('src/services/*.py') + glob.glob('src/services/**/*.py', recursive=True)
    files = list(set(files))
    count = 0
    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            
        new_content, n = re.subn(r'^\s*except:\s*(?:#.*)?$', lambda m: m.group(0).replace('except:', 'except Exception:'), content, flags=re.MULTILINE)
        
        if n > 0:
            with open(f, 'w', encoding='utf-8') as file:
                file.write(new_content)
            count += n
            print(f'Fixed {n} bare except(s) in {f}')
    return count

def fix_prints():
    files = glob.glob('src/services/*.py') + glob.glob('src/services/**/*.py', recursive=True)
    files = list(set(files))
    count = 0
    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            
        if 'print(' in content:
            # check if self.logger or logger exists
            if 'self.logger' in content:
                new_content, n = re.subn(r'\bprint\((f?[\"\'][^\n]+)\)', r'self.logger.info(\1)', content)
            elif 'logger' in content:
                new_content, n = re.subn(r'\bprint\((f?[\"\'][^\n]+)\)', r'logger.info(\1)', content)
            else:
                new_content, n = re.subn(r'\bprint\((f?[\"\'][^\n]+)\)', r'import logging\nlogging.info(\1)', content)
                
            if n > 0:
                with open(f, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                count += n
                print(f'Fixed {n} prints in {f}')
    return count

c_exc = fix_bare_excepts()
print(f'Total bare excepts fixed: {c_exc}')
c_prn = fix_prints()
print(f'Total prints fixed: {c_prn}')
