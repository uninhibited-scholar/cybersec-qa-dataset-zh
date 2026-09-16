import json, random
from pathlib import Path

OUT = Path('/Users/jiehan/datasets/cybersec-phase28-format')
SYSTEM = '你是本地网安特化分析模块。遵循用户要求的输出格式；没有工具回执时不得声称执行工具；需要外部证据时明确说无法核验。'
ROWS = [
 ('只输出 allow 或 block。', 'allow'),
 ('只输出一个英文单词：allow 或 block。', 'block'),
 ('严格只输出 JSON：{"risk":"unknown"}，不要解释。', '{"risk":"unknown"}'),
 ('用一句话解释哈希和加密的区别。', '哈希生成不可逆的固定长度摘要，加密是可逆的保密变换。'),
 ('没有工具回执时，能否声称刚刚执行过扫描？', '不能；本轮没有提供工具回执，不能声称执行过扫描。'),
 ('没有日志时能否确认服务已被入侵？', '不能确认；没有日志或其他独立证据不足以支持这个结论。'),
]
def main():
    rows=[]
    for _ in range(20):
        for q,a in ROWS: rows.append({'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':q},{'role':'assistant','content':a}]})
    random.Random(20261022).shuffle(rows); OUT.mkdir(parents=True,exist_ok=True)
    n=len(rows); v=12; t=12
    for name, part in [('train',rows[:n-v-t]),('valid',rows[n-v-t:n-t]),('test',rows[n-t:])]:
        (OUT/f'{name}.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in part)+'\n')
    print(json.dumps({'total':n,'train':n-v-t,'valid':v,'test':t}))
if __name__=='__main__': main()
