"""Search committed experiment reports without invoking inference."""
import argparse,json,pathlib
def search(root,query):
    root=pathlib.Path(root)
    terms=query.casefold().split()
    results=[]
    for f in sorted((root/'results').glob('*/*/report.md')):
        if f.is_symlink() or not f.is_file(): continue
        body=f.read_text(errors='replace')
        if all(t in body.casefold() for t in terms):
            results.append({'issue':f.parts[-3],'attempt':f.parts[-2],'path':str(f.relative_to(root)),'excerpt':body[:1000]})
    return results
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('checkout');p.add_argument('query');a=p.parse_args()
    print(json.dumps(search(a.checkout,a.query),indent=2))
