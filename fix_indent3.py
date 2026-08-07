with open('C:/Users/Admin/Desktop/instrument-designer/backend/optimization/selector.py', 'r') as f:
    content = f.read()

lines = content.split('\n')
new_lines = []

for i, line in enumerate(content.split('\n'), 1):
    # Lines 226-262: evaluate method (needs 4 spaces added to def, body already at 8 spaces)
    # Line 226: def evaluate... (currently at col 0, needs 4 spaces)
    # Lines 227-262: method body at 8 spaces (correct)
    # Line 264: def optimize... at col 0, needs 4 spaces
    # Lines 265-470: method body at 12 spaces, needs 8 spaces
    # Line 473: OptimizerFactory class - stop indenting
    
    if i == 226:
        # def evaluate line - add 4 spaces
        new_lines.append('    ' + line)
    elif 227 <= i <= 262:
        # evaluate method body - already at 8 spaces, keep as is
        new_lines.append(line)
    elif i == 264:
        # def optimize line - add 4 spaces
        new_lines.append('    ' + line)
    elif 265 <= i <= 470:
        # optimize method body - currently at 12 spaces, needs to be 8 spaces
        # Remove 4 leading spaces
        if line.startswith('            '):
            new_lines.append(line[4:])
        elif line.startswith('        '):
            new_lines.append(line)
        else:
            new_lines.append(line)
    elif i >= 473:
        # After TwoPhaseOptimizer class - no indentation
        new_lines.append(line)
    else:
        new_lines.append(line)

with open('C:/Users/Admin/Desktop/instrument-designer/backend/optimization/selector.py', 'w') as f:
    f.write('\n'.join(new_lines))
print('Done')