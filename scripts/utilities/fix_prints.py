import re

files = ['src/models/currency.py', 'src/models/payment.py', 'src/models/product.py', 'src/models/sale.py']
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # replace print(f"...") with self.logger.error(f"...")
    if 'self.logger' in content:
        new_content = re.sub(r'\bprint\((f?[\"\'][^\n]+)\)', r'self.logger.error(\1)', content)
    else:
        new_content = re.sub(r'\bprint\((f?[\"\'][^\n]+)\)', r'logger.error(\1)', content)
        
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f'Replaced prints in {f}')
