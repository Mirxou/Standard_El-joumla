import os

file_path = "src/ui/ai_service_ui.py"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "with self.db_manager.get_connection() as conn:" in line:
        indent = line[:line.find("with")]
        if "load_models" in "".join(lines[max(0, len(new_lines)-20):len(new_lines)]):
            new_lines.append(f"{indent}if not self.db_manager:\n")
            new_lines.append(f"{indent}    return\n")
        elif "delete_model" in "".join(lines[max(0, len(new_lines)-20):len(new_lines)]):
            new_lines.append(f"{indent}if not self.db_manager:\n")
            new_lines.append(f"{indent}    return\n")
        elif "get_quick_stats" in "".join(lines[max(0, len(new_lines)-20):len(new_lines)]):
            new_lines.append(f"{indent}if not self.db_manager:\n")
            new_lines.append(f"{indent}    return \"قاعدة البيانات غير متصلة\"\n")
        else:
            # Default guard
            new_lines.append(f"{indent}if not self.db_manager:\n")
            new_lines.append(f"{indent}    return\n")
        new_lines.append(line)
    else:
        new_lines.append(line)

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Applied guards to AIServiceUI")
