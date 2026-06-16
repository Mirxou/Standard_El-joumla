import re

f1 = 'src/ai/predictive_analytics_platform.py'
with open(f1, 'r', encoding='utf-8') as f:
    content = f.read()

new_content, n = re.subn(r'^\s*except:\s*(?:#.*)?$', lambda m: m.group(0).replace('except:', 'except Exception:'), content, flags=re.MULTILINE)
if n > 0:
    with open(f1, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'Fixed {n} bare except(s) in {f1}')

f2 = 'src/ai/multi_agent_coordinator.py'
with open(f2, 'r', encoding='utf-8') as f:
    content2 = f.read()

new_content2 = re.sub(r'\bprint\((f?[\"\'][^\n]+)\)', r'self.logger.info(\1)', content2)
if new_content2 != content2:
    with open(f2, 'w', encoding='utf-8') as f:
        f.write(new_content2)
    print(f'Replaced prints with logger in {f2}')
