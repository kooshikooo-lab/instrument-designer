import re

with open('C:/Users/Admin/Desktop/instrument-designer/backend/optimization/selector.py', 'r') as f:
    content = f.read()

lines = content.split('\n')
new_lines = []
in_class = False

for line in content.split('\n'):
    stripped = line.lstrip()
    
    # Detect class definition
    if stripped.startswith('class TwoPhaseOptimizer('):
        in_class = True
        new_lines.append(line)
        continue
    
    if in_class:
        # Check if we've left the class (next class or function at module level)
        if stripped and not line.startswith(' ') and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith('def ') and not line.startswith('    ') and not line.startswith('        ') and not line.startswith('            ') and not line.startswith('                ') and not line.startswith('                    ') and not line.startswith('                        ') and not line.startswith('                            ') and not line.startswith('                                ') and not line.startswith('                                    '):
            # Check if this is a new class or function at module level
            if stripped.startswith('class ') or stripped.startswith('def ') or stripped.startswith('@'):
                in_class = False
        
        if in_class:
            # Add 4 spaces to the beginning if the line has content
            if stripped:
                new_lines.append('    ' + line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)
    
    # Detect class start
    if stripped.startswith('class TwoPhaseOptimizer('):
        in_class = True

result = '\n'.join(new_lines)
with open('C:/Users/Admin/Desktop/instrument-designer/backend/optimization/selector.py', 'w') as f:
    f.write('\n'.join(new_lines))
print('Done')