import requests

def download_file(url):
    local_filename = "ttt"
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                print('ok')
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    return local_filename

download_file("http://v12.myself-bbs.com/44624/010_480P.mp4?m=TAs5EFv0ADFx7cTrvpyHUA&e=1544083351")

print("done!!!!!!!!!!!!!!!!!!!")