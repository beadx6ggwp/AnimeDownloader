import requests
from bs4 import BeautifulSoup
import time
import sys
import os
import re
from colorama import Fore, Back, Style, init
from threadDownload import multiThread_download
init()


downloadPath = 'download'
doc = """
> argument(url [, start='num', end='num', image_res='num', downloadMode='mode', threadNum='num'])
---------------------------------------------------------------------------------------------
url          -[Required] : myself-bbs url, like: https://myself-bbs.com/thread-44659-1-1.html
start        -[Optional] : start index
end          -[Optional] : end index
image_res    -[Optional] : image resolution
downloadMode -[Optional] : multiThread || singleThread
threadNum    -[Optional] : multiThread threadNum
---------------------------------------------------------------------------------------------
Example:

Download all :
> main.py https://myself-bbs.com/thread-44659-1-1.html

Download 3 ~ 7 :
> main.py https://myself-bbs.com/thread-44659-1-1.html start=3 end=7

change image resolution to 360, 480, 720, 1080 :
> main.py https://myself-bbs.com/thread-44659-1-1.html image_res=360
"""


def main(arg):
    if len(arg) == 1:
        print('No arg, press help?')
        return

    if arg[1].find('help') != -1:
        print(doc)

    url = arg[1]
    if len(arg) > 2:
        del arg[0:2]
        data = {}
        for item in arg:
            s = item.split('=')
            data[s[0]] = s[1]
        print(arg)
        print(data)
        downloadAnime(url, **data)
    # downloadAnime('http://myself-bbs.com/thread-44659-1-1.html',start=0, end=1)

# option: AnimePage ImageResolution
# [ConnectionError] : 該影片的host無法連接
# [RequestError] : 該影片的請求無法得到正確回應


def downloadAnime(url, start=0, end=999, image_res=360, downloadMode='multiThread', threadNum=20):
    print('連接中...')
    animeContent = getAnimeContent(url)

    # select downloads range
    length = len(animeContent['videoRequest'])
    start = abs(int(start))
    end = min(int(end), len(animeContent['videoRequest']))

    del animeContent['eptitle'][end+1:]
    del animeContent['eptitle'][0: start]
    del animeContent['videoRequest'][end+1:]
    del animeContent['videoRequest'][0: start]

    eplist = animeContent['eptitle']
    videolist = animeContent['videoRequest']
    playlist = ['%s, %s' % (k, v) for k, v in zip(eplist, videolist)]
    print('取得下載資料:\n%s' % '\n'.join(playlist))
    print('準備下載:')

    pattern = r'[\\/:*?"<>|]'

    s = '{}\\{}'
    folderName = re.sub(pattern, ' ', animeContent['animeTitle'])
    directory = s.format(downloadPath, folderName)
    if not os.path.exists(directory):
        os.makedirs(directory)

    header = {
        'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
        'Host': 'v1.myself-bbs.com',
        'Referer': 'http://v.myself-bbs.com/',
        'Range': 'bytes=0-'
    }
    for eptitle, title in zip(animeContent['eptitle'], animeContent['videoRequest']):
        videoContent = getVideoContent(title)
        if videoContent == None:
            # 無法取得影片播放資料
            continue

        # [1080:url/name.mp4?qwjeoi]
        videoResolution = list(videoContent['video'])[-1]  # 預設最低畫質
        # 塞選解析度
        match = [k for k in videoContent['video']
                 if int(k[0]) <= image_res]
        if len(match) > 0:
            videoResolution = match[0]

        vs = videoResolution[1]
        fileType = vs[vs.find('.'): vs.find('?')]
        resolution = videoResolution[0]
        titleName = re.sub(pattern, ' ', eptitle)
        s = '{} ({}p){}'
        filename = s.format(titleName, resolution, fileType)

        # request error test
        # videoContent['host'][0] = 'http://davidhsu666.com/'+videoResolution
        # videoContent['host'] = ['http://davidhsu666.com/']
        # videoContent['host'] = ['http://davidhsu6676.com/']

        # 挑選可行的host, 目前是假設連得上都算正常，失敗就找list的下一個
        hosturl = ''
        testurl = ''
        for h in videoContent['host']:
            header['Host'] = h[h.find('http:')+5:].strip('/')
            testurl = '{}{}'.format(h, videoResolution[1])
            try:
                test = requests.get(testurl, headers=header,
                                    stream=True, timeout=10)
                test.close()
                if test.status_code != 206:  # Partial Content
                    continue
                hosturl = testurl

                print('Host:%s' % header['Host'])

                download_result = False
                if downloadMode == 'multiThread':
                    download_result = multiThread_download(hosturl,
                                                           file_name=filename,
                                                           directory=directory,
                                                           threadNum=threadNum)
                elif downloadMode == 'singleThread':
                    download_result = download_video(hosturl,
                                                     headers=header,
                                                     file_name=filename,
                                                     directory=directory)
                if download_result:
                    break
                # 如果下載失敗，就在繼續下個host
            except Exception as e:
                print('[ConnectionError]:%s\n' % h)
                continue
        if hosturl == '':
            print('[RequestError] %s\n' % (testurl))
            continue

    print('-' * 20)
    print("[OK] All videos downloaded!!!")


def getAnimeContent(url):
    data = {}

    # get full page
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    animeTitle = soup.find('a', attrs={
        'href': url.split('/')[-1]
    })
    animeTitle = animeTitle.text.split(u'【')[0]

    # main_list = soup.find_all('ul', class_="main_list")
    main_list = soup.find_all('a', string=u'站內')  # request url
    ep_list = soup.select('ul.main_list > li > a')  # episode title

    data['animeTitle'] = animeTitle
    data['videoRequest'] = [k['data-href'].strip('\r') for k in main_list]

    def query_ep(x): return x.parent.parent.parent.find('a').text
    data['eptitle'] = [query_ep(k) for k in main_list]
    return data

# header, 取得video list, image_resolution
# video
#   360	    44665/001_360P.mp4?m=agEy6298kDgCTYUmZEeu-w&e=1544111776
#   480	    44665/001_480P.mp4?m=uTFIoQkj6LzJ9K62Mslpbg&e=1544111776
#   720	    44665/001_720P.mp4?m=qsXdKoqHkL8jFmn_2_RlKQ&e=1544111776
#   1080    44665/001_1080P.mp4?m=tqMc76s-RRgqsJU3Z8JDmA&e=1544111776
# host
#   0	http://v2.myself-bbs.com/
#   1	http://v9.myself-bbs.com/
#   2	http://v24.myself-bbs.com/

# mySelf會檢查Referer來擋request, 所以要偽裝一個正當來源
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Range


def getVideoContent(sourceUrl):
    # http://v.myself-bbs.com/api/files/index/44665/001/
    # http://v.myself-bbs.com/api/files/index/animeID/number/
    targetUrl = 'http://v.myself-bbs.com/api/files/index'

    temp = str(sourceUrl).split('/')
    animeID = temp[-2]
    number = temp[-1]
    header_videoData = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': sourceUrl,
        'Host': 'v.myself-bbs.com',

    }

    s = '{}/{}/{}'
    requestUrl = s.format(targetUrl, animeID, number)

    # 這裡的請求可能也會出錯 error 502 Bad Gateway
    r = requests.get(requestUrl, headers=header_videoData)
    if r.status_code != 200:
        return None
    data = r.json()

    items = data['video'].items()

    videoUrl = {}
    items_sorted = sorted(items, key=lambda x: int(x[0]), reverse=True)
    for k, v in items_sorted:
        videoUrl[k] = v

    return {
        'video': items_sorted,
        'host': data['host'],
        'animeID': animeID,
        'number': number
    }


# get request header
# Accept:video/webm,video/ogg,video/*;q…q=0.7,audio/*;q=0.6,*/*;q=0.5
# Accept-Language:zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3
# Connection:keep-alive
# Cookie:__cfduid=d09727e56811e0697a64894a682d5d5051544095407
# DNT:1
# Host:v1.myself-bbs.com
# Range:bytes=0-
# Referer:http://v.myself-bbs.com/
# User-Agent:Mozilla/5.0 (Windows NT 10.0; …) Gecko/20100101 Firefox/63.0

# http://docs.python-requests.org/en/master/api/#requests.Response
def download_video(href, headers=None, file_name=None, directory=''):
    if file_name == None:
        file_name = '{}.mp4'.format(int(time.time()))
    path = directory+'\\'+file_name

    response = requests.get(href, headers=headers, stream=True)
    # response.close()

    # download started
    with open(path, 'wb') as f:
        totle_length = response.headers.get('content-length')
        if totle_length == None:
            f.write(response.content)
        else:
            chunk_size = 1024  # 單次請求最大值
            totle_length = int(totle_length)  # 內容大小
            startTime = Now()
            dl = 0
            print('[{}]'.format(file_name))
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    dl += len(chunk)
                    speed = (dl/2**20) / ((Now() - startTime + 0.0001))
                    text = '{0:>5.2f}/{1:.2f} MB |{2:>5.2f} MB/s'.format(
                        dl / (2**20), totle_length / (2**20), speed)
                    printProgressBar(
                        dl, totle_length, prefix='Progress', suffix=text, length=40)

    response.close()

    return True


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='#'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(('{0} |{1}|{2:>'+str(4 + decimals) + 's}% |{3}').format(prefix,
                                                                  bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        sys.stdout.write('\x1b[K')
        print(('{0} |{1}|{2:>'+str(4 + decimals) + 's}% | {3}').format(prefix,
                                                                       bar, percent, 'Done!'), end='\r')
        print()


def Now(): return time.time()


if __name__ == '__main__':
    main(sys.argv)
    # downloadFile('http://v25.myself-bbs.com/44624/001_360P.mp4?m=KcRLtU2qq2qj6Kuu_qtS8A&e=1544200797', '')
    # download_video(
    #     "http://v25.myself-bbs.com/44624/001_360P.mp4?m=KcRLtU2qq2qj6Kuu_qtS8A&e=1544200797", 'test.mp4')
# download_video("http://v1.myself-bbs.com/44665/001_1080P.mp4?m=tqMc76s-RRgqsJU3Z8JDmA&e=1544111776",'test.mp4')
