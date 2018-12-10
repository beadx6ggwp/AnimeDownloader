import requests
import time
import sys
import os
import queue
import threading
from functools import cmp_to_key  # 轉換sorted的cmp to key
import shutil
from colorama import Fore, Back, Style, init
init()

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
            # print(file_name, totle_length)
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    if not jobstatus == None:
                        jobstatus['count'] += len(chunk)
                    f.write(chunk)

    response.close()

    return


def download_tasksDispatch(url, jobstatus, file_name='', directory='',threadNum=20):
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
    start_time = 0

    taskQueue = queue.Queue()

    # 先分派任務
    total = int(test_res.headers.get('content-length'))
    jobstatus['total'] = total
    # total = 5000000
    part_time = total // (threadNum - 1)
    # part_time = total // (threadNum)

    # print('檔案大小:%d, 分割%d, 每份%d' % (total, threadNum, part_time))
    for i in range(threadNum):  # threadNum-0
        header = {
            'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
            'Referer': 'http://v.myself-bbs.com/',
            'Range': 'bytes=0-'
        }
        s = 'bytes={}-{}'
        header['Range'] = s.format(
            start_time, start_time+part_time-1)  # start<= x <= end
        if i == threadNum-1:
            header['Range'] = s.format(start_time, '')

        start_time += part_time
        taskQueue.put({
            'index': i,
            'header': header
        })

    downloadTime = time.time()

    # 依序執行
    for i in range(0, threadNum):
        t = threading.Thread(target=thread_download, args=(
            taskQueue, jobstatus, url, partPath))
        t.start()
        threads.append(t)

    # 等待全部完成
    for t in threads:
        t.join()

    endTime = time.time()

    # 完成後將part檔案合併為mp4
    merge_folderFile(partPath, newFileName=file_name, directory=directory)

    # 完成後將part檔案刪除
    shutil.rmtree(partPath)

    jobstatus['isDone'] = True
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
        # print('index:%d Current Thread Name %s' %
        #       (task['index'], threading.currentThread().name))

        download(url,
                 headers=task['header'],
                 file_name='part_%d' % task['index'],
                 directory=directory,
                 jobstatus=jobstatus)


def printThreadProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='#'):
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


def showStatus(jobstatus):
    while True:
        dl = jobstatus['count']
        totle_length = jobstatus['total']
        speed = (dl/2**20) / ((time.time() - jobstatus['startTime']))
        text = '{0:>5.2f}/{1:.2f} MB |{2:>5.2f} MB/s'.format(dl / (2**20),
                                                             totle_length / (2**20), speed)
        printThreadProgressBar(
            dl, totle_length, prefix='Progress', suffix=text, length=40)
        if jobstatus['isDone']:
            print()
            break


def multiThread_download(url, file_name='', directory='',threadNum=20):
    jobstatus = {
        'isDone': False,
        'count': 0,
        'total': 0.0001,
        'startTime': time.time()-0.1
    }

    spinner = threading.Thread(target=showStatus, args=(jobstatus,))
    # print('spinner object:', spinner)
    print('[{}]'.format(file_name))
    spinner.start()

    download_tasksDispatch(url, jobstatus,
                           file_name=file_name, directory=directory,threadNum=threadNum)
    spinner.join()
    if jobstatus['count'] != jobstatus['total']:
        print('Download error,please retry : %s' % file_name)
        return False
    return True


# multiThread_download('http://v17.myself-bbs.com/' +
#                      '44659/009_360P.mp4?m=JLrFP6ViTUXIWsxHeqsp9Q&e=1544376616', file_name='fuckeeeyou.mp4', directory='test2')
