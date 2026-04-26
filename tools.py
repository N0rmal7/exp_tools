#!/usr/bin/env python3
"""
自动生成 pwntools 利用框架脚本（支持 checksec ./filename 直接检测）
支持可选引入 ctypes 和 LibcSearcher 库，支持自定义输出文件名（自动避免重名）
用法：
    python make_exp.py <漏洞程序名>
    或者直接运行后交互输入程序名
"""

import os
import sys
import subprocess
import re

def get_arch_from_checksec(binary_path):
    """
    执行 checksec ./binary，捕获 stdout/stderr 并解析架构
    返回 'i386' 或 'amd64'
    """
    try:
        result = subprocess.run(
            ['checksec', binary_path],
            capture_output=True,
            text=True,
            check=False
        )
    except FileNotFoundError:
        print("[-] 未找到 checksec 命令，请先安装 (apt install binutils)")
        sys.exit(1)

    combined_output = result.stdout + "\n" + result.stderr
    print("[DEBUG] checksec 输出:")
    print(combined_output)
    
    pattern = r'Arch:\s*([a-zA-Z0-9]+)-'
    for line in combined_output.splitlines():
        if 'Arch' in line:
            match = re.search(pattern, line)
            if match:
                arch = match.group(1)
                if arch == 'amd64':
                    return 'amd64'
                elif arch == 'i386':
                    return 'i386'
                else:
                    print(f"[-] 未知架构: {arch}")
                    sys.exit(1)
    
    for line in combined_output.splitlines():
        if 'Arch' in line:
            parts = line.split(':')
            if len(parts) >= 2:
                arch_part = parts[1].strip().split('-')[0]
                if arch_part == 'amd64':
                    return 'amd64'
                elif arch_part == 'i386':
                    return 'i386'
    
    print("[-] 未能从 checksec 输出中解析到架构信息")
    print("请手动检查 checksec 是否能正常输出架构行")
    sys.exit(1)

def ask_yes_no(question):
    while True:
        answer = input(question + " (y/n): ").strip().lower()
        if answer in ('y', 'yes'):
            return True
        elif answer in ('n', 'no', ''):
            return False
        else:
            print("请输入 y 或 n")

def ask_output_filename(default_name):
    """询问输出文件名，支持直接回车使用默认名；若文件已存在则循环要求重新输入"""
    while True:
        user_input = input(f"请输入 exp 文件名 (直接回车使用 {default_name}): ").strip()
        if not user_input:
            filename = default_name
        else:
            filename = user_input
            if not filename.endswith('.py'):
                filename += '.py'
        
        if os.path.exists(filename):
            print(f"存在同名文件: {filename}，请重新输入。")
            continue
        else:
            return filename

def generate_exploit_script(binary_name, arch, use_ctypes, use_libcsearcher):
    imports = ["from pwn import *"]
    if use_ctypes:
        imports.append("from ctypes import *")
    if use_libcsearcher:
        imports.append("from LibcSearcher import *")
    
    import_section = "\n".join(imports)
    
    return f'''{import_section}

context(os='linux', arch='{arch}', log_level='debug')
p = process('./{binary_name}')
#p = remote()
elf = ELF('./{binary_name}')
#libc = ELF('./libc.so.6')
'''

def main():
    if len(sys.argv) >= 2:
        binary = sys.argv[1]
    else:
        binary = input("请输入漏洞程序文件名 (当前目录下): ").strip()

    if not binary:
        print("[-] 文件名不能为空")
        sys.exit(1)

    if not os.path.isfile(binary):
        print(f"[-] 文件不存在: {binary}")
        sys.exit(1)

    os.chmod(binary, 0o755)
    print(f"[+] 已添加执行权限: {binary}")

    arch = get_arch_from_checksec(binary)
    print(f"[+] 检测到架构: {arch}")

    use_ctypes = ask_yes_no("是否使用 ctypes 库？")
    use_libcsearcher = ask_yes_no("是否使用 LibcSearcher 库？")

    default_out = f"{binary}_exp.py"
    out_file = ask_output_filename(default_out)

    content = generate_exploit_script(binary, arch, use_ctypes, use_libcsearcher)
    with open(out_file, 'w') as f:
        f.write(content)
    os.chmod(out_file, 0o644)

    print(f"[+] 已生成利用框架: {out_file}")
    print("\n--- 脚本内容预览 ---")
    print(content)

if __name__ == '__main__':
    main()