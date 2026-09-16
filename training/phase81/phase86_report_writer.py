import json, os, tempfile
def write_json_atomic(path, data):
    d=os.path.dirname(path) or '.'
    fd,tmp=tempfile.mkstemp(prefix='.report-',dir=d,text=True)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
        with open(tmp,encoding='utf-8') as f: json.load(f)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
