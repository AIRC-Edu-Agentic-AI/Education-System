import os

paths = [
    r'C:\src\flutter\bin\internal\update_engine_version.ps1',
    r'D:\flutter\bin\internal\update_engine_version.ps1',
]

for p in paths:
    if os.path.exists(p):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                content = f.read()
            
            target = 'git -C "$flutterRoot" ls-files bin/internal/engine.version'
            replacement = 'Test-Path "$flutterRoot/bin/internal/engine.version"'
            
            if target in content:
                content = content.replace(target, replacement)
                with open(p, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Patched: {p}")
            else:
                print(f"Target not found or already patched in: {p}")
        except Exception as e:
            print(f"Error patching {p}: {e}")

print("Flutter engine patcher finished.")
