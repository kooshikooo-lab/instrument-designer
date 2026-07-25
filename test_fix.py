with open(r'C:\instrument-designer\backend\tmm_acoustics.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# Fix indentation for methods from line 455 to 697 (class end)
# Methods should have 4 spaces for def, 8 for body
# Currently they have 0 or 4 for def, 4 or 8 for body

fixed_lines = []
for i, line in enumerate(lines):
    # Lines 455-697 (0-indexed: 454-696)
    if 454 <= i <= 696:
        stripped = line.lstrip()
        if stripped:
            # Check if it's a method definition or body
            # Method definitions should have 4 spaces, body 8
            if line.startswith('def ') or line.startswith('@'):
                # Method decorator or def - should be 4 spaces
                if not line.startswith(' ' * 4):
                    line = '    ' + line.lstrip()
            elif line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                # Body line that lost indentation
                # But don't re-indent comments or empty lines
                if not line.startswith('#') and line.strip():
                    line = '    ' + line
    fixed_lines.append(line)
else:
    fixed_lines.append(line)

new_content = '\n'.join(fixed_lines)

with open(r'C:\instrument-designer\backend\tmm_acoustics.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Fixed indentation")