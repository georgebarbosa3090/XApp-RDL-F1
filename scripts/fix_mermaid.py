import os
import re

def check_mermaid_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    mermaid_blocks = re.findall(r'```mermaid(.*?)```', content, flags=re.DOTALL)
    modified = False
    new_content = content

    for block in mermaid_blocks:
        new_block = block
        
        def quote_label(m):
            arrow = m.group(1)
            label = m.group(2).strip()
            # If label has parentheses or special chars and is not quoted
            if ('(' in label or ')' in label or '/' in label or '&' in label) and not (label.startswith('"') and label.endswith('"')):
                return f'{arrow}|"{label}"|'
            return m.group(0)

        # Match arrows with labels: -->|label|, -.->|label|, ==|label|==>, etc.
        new_block = re.sub(r'([\-=\.]{1,3}>?)\|([^\|\n]+)\|', quote_label, new_block)
        if new_block != block:
            new_content = new_content.replace(block, new_block)
            modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed Mermaid in: {filepath}")

if __name__ == "__main__":
    for base_dir in ['.', '../iqos-xapp-rdl-phase2']:
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
                if any(skip in root for skip in ['.git', '.venv', '__pycache__', '.pytest_cache']):
                    continue
                for file in files:
                    if file.endswith('.md'):
                        check_mermaid_file(os.path.join(root, file))
