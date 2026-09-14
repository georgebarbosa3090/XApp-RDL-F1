import os
import re
import sys

def is_comment_line(line, lang):
    s = line.strip()
    if not s:
        return False, ""
    
    # C/C++ preprocessor directives are NOT comments
    if lang in ['c', 'cpp', 'c++']:
        if s.startswith('#include') or s.startswith('#define') or s.startswith('#ifdef') or s.startswith('#ifndef') or s.startswith('#endif') or s.startswith('#pragma'):
            return False, ""
        if s.startswith('//'):
            return True, s[2:].strip()
        if s.startswith('/*') and s.endswith('*/'):
            return True, s[2:-2].strip()
        if s.startswith('/*'):
            return True, s[2:].strip()
        if s.startswith('*'):
            return True, s[1:].strip()
    
    # Shell / Python / YAML / Dockerfile / Conf
    if s.startswith('#'):
        # Shebang in scripts
        if s.startswith('#!/'):
            return False, ""
        return True, s[1:].strip()
    
    if s.startswith('//'):
        return True, s[2:].strip()
    
    return False, ""

def strip_inline_comment(line, lang):
    # If line has an inline comment (e.g., cmd # comment)
    # Be careful with quotes or URLs
    if lang in ['bash', 'sh', 'shell', 'zsh', 'powershell', 'ps1', '']:
        # Match ' # ' not in quotes
        m = re.search(r'^(.*?)(\s+#\s+.*)$', line)
        if m:
            code_part = m.group(1)
            comment_part = m.group(2)
            # Check quotes balance
            if code_part.count('"') % 2 == 0 and code_part.count("'") % 2 == 0:
                return code_part.rstrip(), comment_part.strip()[1:].strip()
    return line, ""

def clean_markdown_content(content):
    lines = content.splitlines()
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if stripped.startswith('```'):
            # Code block starts
            raw_fence = stripped
            lang = raw_fence[3:].strip().lower()
            
            # Skip mermaid and diff blocks
            if lang in ['mermaid', 'diff']:
                new_lines.append(line)
                i += 1
                while i < len(lines):
                    new_lines.append(lines[i])
                    if lines[i].strip().startswith('```'):
                        i += 1
                        break
                    i += 1
                continue
            
            # Collect all lines of this code block
            block_lines = []
            i += 1
            while i < len(lines):
                if lines[i].strip().startswith('```'):
                    break
                block_lines.append(lines[i])
                i += 1
            
            # i is now at closing ``` or EOF
            closing_fence = lines[i] if i < len(lines) else '```'
            if i < len(lines):
                i += 1  # consume closing ```
            
            # Process block_lines
            # We want to break down the block into segments:
            # - comments -> external markdown paragraphs / headers
            # - code lines -> separate clean ```lang ... ``` blocks
            
            segments = []
            current_code = []
            
            for b_line in block_lines:
                is_cmt, cmt_text = is_comment_line(b_line, lang)
                if is_cmt:
                    if current_code:
                        # Flush current code block if it has non-empty lines
                        if any(c.strip() for c in current_code):
                            segments.append(('code', list(current_code)))
                        current_code = []
                    # Add comment segment
                    if cmt_text:
                        segments.append(('comment', cmt_text))
                else:
                    clean_code, inline_cmt = strip_inline_comment(b_line, lang)
                    current_code.append(clean_code)
            
            if current_code and any(c.strip() for c in current_code):
                segments.append(('code', list(current_code)))
            
            # Now reconstruct the output for this block
            if not any(s[0] == 'comment' for s in segments):
                # No comments at all, keep original block structure (with inline comments stripped)
                new_lines.append(raw_fence)
                for b_line in block_lines:
                    clean_code, _ = strip_inline_comment(b_line, lang)
                    new_lines.append(clean_code)
                new_lines.append(closing_fence)
            else:
                # Reconstruct cleanly
                for seg_type, seg_content in segments:
                    if seg_type == 'comment':
                        # Format as external markdown text
                        # If comment starts with number (e.g. "1. Step" or "Opção 1:"), format cleanly
                        cmt = seg_content.strip()
                        if cmt.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '- ', '* ')):
                            new_lines.append(f"\n{cmt}")
                        elif cmt.endswith(':'):
                            new_lines.append(f"\n**{cmt}**")
                        else:
                            new_lines.append(f"\n* {cmt}:")
                    elif seg_type == 'code':
                        # Trim leading/trailing blank lines in code block
                        while seg_content and not seg_content[0].strip():
                            seg_content.pop(0)
                        while seg_content and not seg_content[-1].strip():
                            seg_content.pop()
                        if seg_content:
                            new_lines.append(raw_fence)
                            for c_line in seg_content:
                                new_lines.append(c_line)
                            new_lines.append(closing_fence)
        else:
            new_lines.append(line)
            i += 1
            
    return '\n'.join(new_lines) + '\n'

def process_repo(repo_path):
    print(f"Processing repository: {repo_path}")
    count = 0
    for root, dirs, files in os.walk(repo_path):
        if any(ign in root for ign in ['.git', 'node_modules', '.venv', '__pycache__', 'build']):
            continue
        for file in files:
            if file.endswith('.md'):
                fpath = os.path.join(root, file)
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    original = f.read()
                cleaned = clean_markdown_content(original)
                if cleaned != original:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(cleaned)
                    rel = os.path.relpath(fpath, repo_path)
                    print(f"  [CLEANED] {rel}")
                    count += 1
    print(f"Total files updated in {repo_path}: {count}")

if __name__ == '__main__':
    if sys.platform.startswith("linux"):
        repos = [
            "/mnt/c/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase1",
            "/mnt/c/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2"
        ]
    else:
        repos = [
            r"C:\Users\george.barbosa\.gemini\antigravity\scratch\iqos-xapp-rdl-phase1",
            r"C:\Users\george.barbosa\.gemini\antigravity\scratch\iqos-xapp-rdl-phase2"
        ]
    for r in repos:
        if os.path.exists(r):
            process_repo(r)
