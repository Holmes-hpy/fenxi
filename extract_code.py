import re
import requests

# 下载SKILL.md
url = "https://raw.githubusercontent.com/simonlin1212/a-stock-data/main/SKILL.md"
response = requests.get(url)
content = response.text

# 提取所有Python代码块
pattern = r'```python\n(.*?)\n```'
matches = re.findall(pattern, content, re.DOTALL)

# 合并所有代码块
combined_code = '\n\n' + '='*80 + '\n\n'.join(matches)

# 保存到文件
with open('a_stock_data_core.py', 'w', encoding='utf-8') as f:
    f.write('"""\nA股数据核心功能模块\n从 a-stock-data SKILL.md 自动生成\n"""\n\n')
    f.write(combined_code)

print(f"成功提取 {len(matches)} 个Python代码块")
print(f"文件已保存到 a_stock_data_core.py")
