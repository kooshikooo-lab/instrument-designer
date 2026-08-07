with open('C:/Users/Admin/Desktop/instrument-designer/backend/optimization/selector.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines, 1):
    if i == 226:
        # def evaluate - add 4 spaces
        new_lines.append('    ' + line)
    elif i == 264:
        # def optimize - add 4 spaces
        new_lines.append('    ' + line)
    else:
        new_lines.append(line)

with open('C:/Users/Admin/Desktop/instrument-designer/backend/optimization/selector.py', 'w') as f:
    f.writelines(new_lines)
print('Done')