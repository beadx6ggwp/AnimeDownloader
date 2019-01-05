import requests
from bs4 import BeautifulSoup
import time
import sys
import os
import re
import threading
import queue
from functools import cmp_to_key  # 轉換sorted的cmp to key
import shutil
from colorama import Fore, Back, Style, init

import m3u8
from selenium import webdriver
from urllib.parse import quote
init()

# 先設定selenium的wevdriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless') # 啟動無頭模式
chrome_options.add_argument('--disable-gpu') # windowsd必須加入此行
chrome_options.add_argument("--log-level=3")  # fatal

browser = webdriver.Chrome(chrome_options=chrome_options)
os.system('cls') # 清掉webdriver的devTool

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
> argument(url [, start='num', end='num', threadNum='num'])
---------------------------------------------------------------------------------------------
@params:
url          -[Required] : momovod url, like: https://www.momovod.com/vod-detail-id-61424.html
start        -[Optional] : start index
end          -[Optional] : end index
threadNum    -[Optional] : multiThread threadNum
---------------------------------------------------------------------------------------------
Example:

Download all :
> https://myself-bbs.com/thread-44659-1-1.html

Download 3 ~ 7 :
> https://www.momovod.com/vod-detail-id-53951.html start=2 end=6
"""


momovodUrl = 'https://www.momovod.com'


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
        downloadAnime(url, **data)


def downloadAnime(url, start=0, end=9999, threadNum=64):
    print('連接中...')
    animeContent = getAnimeContent(url)
    threadNum = int(threadNum)
    # select downloads range
    start = abs(int(start))
    end = min(int(end), len(animeContent['videoRequest']))
    animeContent['eptitle'] = animeContent['eptitle'][start:end+1]
    animeContent['videoRequest'] = animeContent['videoRequest'][start:end+1]

    eplist = animeContent['eptitle']
    videolist = animeContent['videoRequest']
    playlist = ['%s, %s' % (k, v) for k, v in zip(eplist, videolist)]
    print(animeContent['animeTitle'])
    print('取得下載資料:\n%s' % '\n'.join(playlist))
    print('準備下載 Mode- %s thread :' % threadNum)

    pattern = r'[\\/:*?"<>|]' #win的檔名限制符號
    folderName = re.sub(pattern, ' ', animeContent['animeTitle'])

    directory = '{}\\{}'.format(downloadPath, folderName)
    partDir = directory + '\\' + 'part'

    if not os.path.exists(directory):
        os.makedirs(directory)

    for eptitle, epUrl in zip(animeContent['eptitle'], animeContent['videoRequest']):
        if not os.path.exists(partDir):
            os.makedirs(partDir)
        videoContent = getVideoContent(epUrl)
        titleName = re.sub(pattern, ' ', eptitle) + '.mp4'        

        print("download:%s"%titleName)
        download_m3u8(videoContent['videoUrl'],videoContent['header'], partDir,threadNum=threadNum)
        merge_folderFile(partDir, titleName, directory)
        shutil.rmtree(partDir)

    print('-' * 20)
    print("[OK] All videos downloaded!!!")

# 給定影集位置，回傳集數列表、連結與名稱
def getAnimeContent(url):
    data = {}

    # get full page
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    animeTitle = soup.find('h3', attrs={
        'itemprop': 'name'
    }).text

    main_list = soup.find_all('div', class_='playlist collapse')[0]
    ep_list = main_list.select('ul > li > a')
    ep_list = list(reversed(ep_list))
    # ep_list = sorted(ep_list, key=lambda x: x['title'])

    data['animeTitle'] = animeTitle
    data['videoRequest'] = [momovodUrl + k['href'] for k in ep_list]
    data['eptitle'] = [k['title'] for k in ep_list]
    return data

# 輸入每集url，回傳下載位置
def getVideoContent(sourceUrl):
    # 因為該網站透過AJAX載入資料，導致不易用requests
    browser.implicitly_wait(30) # seconds
    browser.get(sourceUrl)
    soup = BeautifulSoup(browser.page_source, "html.parser")
    
    iframe = soup.select('div.MacPlayer iframe')[1]
    url = iframe['src']
    startStr = 'url='
    endStr = '&title='
    m3u8Url = url[url.find(startStr) + len(startStr):url.find(endStr)]
    # 取得m3u8中真正的video檔案
    m3u8_obj = m3u8.load(m3u8Url)
    videoUrl = m3u8_obj.playlists[0].absolute_uri

    # 將原網址title部分做url encode，再重新取代原本url的title部分
    title = quote(url[url.find(endStr)+len(endStr):])
    newurl = url[:url.find(endStr)+len(endStr)] + title

    header = {
        'Accept': '*/*',
        'Referer': u'https:' + newurl,
        'Origin': u'https://www.momovod.com'
    }
    return {
        'videoUrl' : videoUrl,
        'header' : header
    }

def download_m3u8(m3u8data, header, directory='', threadNum=20):
    m3u8_obj = m3u8.load(m3u8data)

    jobstatus = {
        'isDone': False,
        'count': 0,
        'allep':len(m3u8_obj.files),
        'total': 0,
        'startTime': time.time()-0.1
    }

    spinner = threading.Thread(target=showStatus, args=(jobstatus,))
    spinner.start()

    taskQueue = queue.Queue()
    for file in m3u8_obj.segments:
        content = {
            'href' : file.absolute_uri,
            'filename' : file.absolute_uri.split('/')[-1],
            'header' : header,
            'directory' : directory
        }
        taskQueue.put(content)
    threads = []
    for i in range(0, threadNum):
        task = threading.Thread(target=thread_download, args=(taskQueue, jobstatus))
        task.start()
        threads.append(task)

    for task in threads:
        task.join()
    
    jobstatus['isDone'] = True
    spinner.join()

def thread_download(taskQueue, jobstatus):
    while not taskQueue.empty():
        job = taskQueue.get_nowait()
        
        download(job['href'],
                 headers=job['header'],
                 file_name=job['filename'],
                 directory=job['directory'],
                 jobstatus=jobstatus)
    pass

def showStatus(jobstatus):
    while True:
        nowep = jobstatus['count']
        allep = jobstatus['allep']
        nowdl = jobstatus['total']
        speed = (nowdl/2**20) / ((time.time() - jobstatus['startTime']))
        text = ' {0} / {1} | {2:>5.2f} MB |{3:>5.2f} MB/s'.format(nowep, allep, nowdl / (2**20), speed)
        printProgressBar(nowep, allep, prefix='Progress',
                         suffix=text, length=40)

        # 如果progressBar完成後有print()，就要啟用延遲
        # 這個延遲是為了在下載任務剛完成，主執行續還沒執行到jobstatus['isDone']=True時，有一段時間差
        # 在這之前這會多跑好幾次isDone，所以用一個小延遲來等待主執行續設定isDone=True
        if jobstatus['isDone']:
            print()
            break

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
        # print()


def Now(): return time.time()

# -------------------------------------------------------------------------
# multiThread function
def download(href, headers=None, jobstatus=None, file_name=None, directory='', chunk_size=1024):
    """
    download stream from url
    @params:
        href        - Required  : video url (str)
        headers     - Required  : request header (Dict)
        jobstatus   - Optional  : jobstatus (Dict)
        file_name   - Optional  : filename (Str)
        directory   - Optional  : file directory (Str)
        chunk_size  - Optional  : chunk_size (Int)
    """
    if file_name == None:
        file_name = '{}.mp4'.format(int(time.time()))

    path = directory+'\\'+file_name

    response = requests.get(href, headers=headers, stream=True)

    # download started
    if jobstatus != None:
        jobstatus['count'] += 1
    with open(path, 'wb') as f:
        totle_length = response.headers.get('content-length')
        if totle_length == None:
            f.write(response.content)
        else:
            # chunk_size = 1024  # 單次請求最大值
            totle_length = int(totle_length)  # 內容大小
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    if jobstatus != None:
                        jobstatus['total'] += len(chunk)
                    f.write(chunk)


    response.close()
    return


def merge_folderFile(path, newFileName=None, directory=''):
    # 合併檔案
    if newFileName == None:
        newFileName = '%s.mp4' % int(time.time())

    newpath = newFileName
    if directory != '':
        newpath = directory+'\\'+newFileName

    files = os.listdir(path)

    with open(newpath, 'ab') as result:
        for file in files:
            with open(path+'\\'+file, 'rb') as part_file:
                result.write(part_file.read())
        pass


# main
if __name__ == '__main__':
    # downloadAnime('https://www.momovod.com/vod-detail-id-61424.html', start=1, end=3)
    main(sys.argv)
