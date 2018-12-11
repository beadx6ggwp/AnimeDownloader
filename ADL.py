import requests
from bs4 import BeautifulSoup
import time
import sys
import os
import re
import queue
import threading
from functools import cmp_to_key  # 轉換sorted的cmp to key
import shutil
from colorama import Fore, Back, Style, init
init()


downloadPath = 'AnimeDownload'
welcome = """
More info: https://github.com/md9830415/AnimeDownloader
     _          _                                             
    / \   _ __ (_)_ __ ___   ___                              
   / _ \ | '_ \| | '_ ` _ \ / _ \                             
  / ___ \| | | | | | | | | |  __/                             
 /_/  _\_\_| |_|_|_| |_| |_|\___|                 _           
     |  _ \  _____      ___ __ | | ___   __ _  __| | ___ _ __ 
     | | | |/ _ \ \ /\ / / '_ \| |/ _ \ / _` |/ _` |/ _ \ '__|
     | |_| | (_) \ V  V /| | | | | (_) | (_| | (_| |  __/ |   
     |____/ \___/ \_/\_/ |_| |_|_|\___/ \__,_|\__,_|\___|_|   

"""

doc = """
> argument(url [, start='num', end='num', image_res='num', downloadMode='mode', threadNum='num', autoRetry='boolean'])
---------------------------------------------------------------------------------------------
@params:
url          -[Required] : myself-bbs url, like: https://myself-bbs.com/thread-44659-1-1.html
start        -[Optional] : start index
end          -[Optional] : end index
image_res    -[Optional] : image resolution
threadNum    -[Optional] : multiThread threadNum
autoRetry    -[Optional] : when file incomplete, retrying downloads
---------------------------------------------------------------------------------------------
Example:

Download all :
> https://myself-bbs.com/thread-44659-1-1.html

Download 3 ~ 7 :
> https://myself-bbs.com/thread-44659-1-1.html start=3 end=7

change image resolution to 360, 480, 720, 1080 :
> https://myself-bbs.com/thread-44659-1-1.html image_res=360
"""


def main(arg):
    print(welcome)
    # direct exe
    while len(arg) == 1:
        print('Input arguments(split with whitespace\' \', or help):')
        inputs = input('> ')
        if inputs.find('help') != -1 and len(inputs) < 10:
            print(doc)
            continue
        try:
            in_arg = inputs.split(' ')
            url = in_arg[0]

            data = {}
            if len(in_arg) > 1:
                for item in in_arg[1:]:
                    s = item.split('=')
                    data[s[0]] = s[1]

            downloadAnime(url, **data)
            os.system('pause')
            return
        except Exception as e:
            print(e)
            print('[InputError] Please retry')

    # use command
    if arg[1].find('help') != -1 and len(arg[1]) < 10:
        print(doc)
        return

    url = arg[1]
    if len(arg) > 2:
        del arg[0:2]
        data = {}
        for item in arg:
            s = item.split('=')
            data[s[0]] = s[1]
        # print(arg)
        # print(data)
        downloadAnime(url, **data)
    # downloadAnime('http://myself-bbs.com/thread-44659-1-1.html',start=0, end=1)

# option: AnimePage ImageResolution
# [ConnectionError] : 該影片的host無法連接
# [RequestError] : 該影片的請求無法得到正確回應


def downloadAnime(url, start=0, end=999, image_res=1080, threadNum=20, autoRetry=False):
    print('連接中...')
    animeContent = getAnimeContent(url)

    image_res = int(image_res)
    threadNum = int(threadNum)
    # select downloads range
    length = len(animeContent['videoRequest'])
    start = abs(int(start))
    end = min(int(end), len(animeContent['videoRequest']))

    animeContent['eptitle'] = animeContent['eptitle'][start:end+1]
    animeContent['videoRequest'] = animeContent['videoRequest'][start:end+1]

    eplist = animeContent['eptitle']
    videolist = animeContent['videoRequest']
    playlist = ['%s, %s' % (k, v) for k, v in zip(eplist, videolist)]
    print('取得下載資料:\n%s' % '\n'.join(playlist))
    print('準備下載 Mode-%s thread :' % threadNum)

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
        # 篩選解析度
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

                download_result = multiThread_download(hosturl,
                                                       file_name=filename,
                                                       directory=directory,
                                                       threadNum=threadNum)
                if download_result or not autoRetry:
                    break
                # 如果下載失敗，就再繼續下個host
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



# getVideoContent(url)
# @parm
# url:
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

# -------------------------------------------------------------------------
# multiThread function


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
def download(href, jobstatus=None, headers=None, file_name=None, directory='', chunk_size=1024):
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
            # chunk_size = 1024  # 單次請求最大值
            totle_length = int(totle_length)  # 內容大小
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    if not jobstatus == None:
                        jobstatus['count'] += len(chunk)
                    f.write(chunk)

    response.close()
    return


def download_tasksDispatch(url, jobstatus, file_name='', directory='', threadNum=20):
    startTime = time.time()

    partPath = 'part'
    if directory != '':
        partPath = directory + '\\' + partPath

    if not os.path.exists(partPath):
        os.makedirs(partPath)
    #
    sindex = url.find('//') + 2
    eindex = url.find('.com') + 4

    start_heradr = {
        'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
        'Referer': 'http://v.myself-bbs.com/',
        'Host': url[sindex:eindex],
        'Range': 'bytes=0-'
    }
    test_res = requests.get(url, start_heradr, stream=True)
    test_res.close()


    threads = []
    taskQueue = queue.Queue()

    # 先分派任務
    total = int(test_res.headers.get('content-length'))
    jobstatus['total'] = total
    # total = 5000000
    start_part = 0
    part_time = total // max(threadNum - 1, 1)

    # print('檔案大小:%d, 分割%d, 每份%d' % (total, threadNum, part_time))
    for i in range(threadNum):  # threadNum-0
        header = start_heradr.copy()
        s = 'bytes={}-{}'
        # Range : start<= x <= end
        header['Range'] = s.format(start_part,
                                   start_part + part_time-1)  
        if i == threadNum - 1:
            header['Range'] = s.format(start_part, '')

        start_part += part_time
        taskQueue.put({
            'index': i,
            'header': header
        })

    downloadTime = time.time()

    # 啟用執行序
    for i in range(0, threadNum):
        t = threading.Thread(target=thread_download, args=(
            taskQueue, jobstatus, url, partPath))
        t.start()
        threads.append(t)

    # 等待全部完成
    for t in threads:
        t.join()
    jobstatus['isDone'] = True

    endTime = time.time()

    # 完成後將part檔案合併為mp4
    merge_folderFile(partPath, newFileName=file_name, directory=directory)

    # 並將part檔案刪除
    shutil.rmtree(partPath)

    # print("完成下載, Time cost: %s\n" % (endTime - startTime))


def merge_folderFile(path, newFileName=None, directory=''):
    # 合併檔案
    if newFileName == None:
        newFileName = '%s.mp4' % int(time.time())

    newpath = newFileName
    if directory != '':
        newpath = directory+'\\'+newFileName

    files = os.listdir(path)

    def func(a, b): return (int(a.split('_')[1]) - int(b.split('_')[1]))
    files.sort(key=cmp_to_key(func))

    with open(newpath, 'ab') as result:
        for file in files:
            with open(path+'\\'+file, 'rb') as part_file:
                result.write(part_file.read())
        pass


def thread_download(taskQueue, jobstatus, url, directory):
    while not taskQueue.empty():
        task = taskQueue.get_nowait()
        download(url,
                 headers=task['header'],
                 file_name='part_%d' % task['index'],
                 directory=directory,
                 jobstatus=jobstatus)


def showStatus(jobstatus):
    while True:
        dl = jobstatus['count']
        totle_length = jobstatus['total']
        speed = (dl/2**20) / ((time.time() - jobstatus['startTime']))
        text = '{0:>5.2f}/{1:.2f} MB |{2:>5.2f} MB/s'.format(dl / (2**20),
                                                             totle_length / (2**20), speed)
        printProgressBar(dl, totle_length, prefix='Progress',
                         suffix=text, length=40)

        # 這個延遲是為了在下載任務剛完成，主執行續還沒執行到jobstatus['isDone']=True時，有一段時間差
        # 在這之前這會多跑好幾次isDone，所以用一個小延遲來等待主執行續設定isDone=True
        time.sleep(0.01)
        if jobstatus['isDone']:
            break


def multiThread_download(url, file_name='', directory='', threadNum=20):
    jobstatus = {
        'isDone': False,
        'count': 0,
        'total': 0.0001,
        'startTime': time.time()-0.1
    }

    print('[{}]'.format(file_name))

    spinner = threading.Thread(target=showStatus, args=(jobstatus,))
    # print('spinner object:', spinner)
    spinner.start()

    download_tasksDispatch(url, jobstatus,
                           file_name=file_name, directory=directory, threadNum=threadNum)
    spinner.join()

    if jobstatus['count'] != jobstatus['total']:
        print('[Incomplete download] : %s, %d/%d' %
              (file_name, jobstatus['count'], jobstatus['total']))
        return False
    return True


# main
if __name__ == '__main__':
    main(sys.argv)
