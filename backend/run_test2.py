import subprocess
result = subprocess.run(['python', r'C:\Users\Admin\Desktop\Woodwind design automation\woodwind-designer\backend\run_test.py'], capture_output=True, text=True, timeout=600, cwd=r'C:\Users\Admin\Desktop\Woodwind design automation\woodwind-designer\backend')
print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
print("Return code:", result.returncode)