import requests
from bs4 import BeautifulSoup
import time


def main():
    downloadAnime('http://myself-bbs.com/thread-44703-1-1.html')
    print("fuck life")

# option: AnimePage ImageResolution


def downloadAnime(url):
    ImageResolution = 720

    # get full page
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    # main_list = soup.find_all('ul', class_="main_list")
    main_list = soup.find_all('a', string=u'站內')

    animeTitle = soup.find('a', attrs={
        'href': url.split('/')[-1]
    })
    animeTitle = animeTitle.text.split(u'【')[0]
    
    for title in main_list:
        videoContent = getVideoContent(title['data-href'])

        header = {
            'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
            'Host': 'v1.myself-bbs.com',
            'Referer': 'http://v.myself-bbs.com/',
            'Range': 'bytes=0-'
        }

        videoResolution = list(videoContent['video'].values())[-1] #預設最低畫質
        hosturl = ''

        # 塞選解析度
        for k, v in videoContent['video'].items():
            if int(k) <= ImageResolution:
                videoResolution = v
                break

        # 挑選可行的host, 目前是假設連得上都算正常，失敗就找list的下一個
        for h in videoContent['host']:
            header['Host'] = h[h.find('http:')+5:].strip('/')
            testurl = '{}{}'.format(h, videoResolution)
            try:
                test = requests.get(testurl, headers=header, stream=True, timeout=10)
                test.close()
                hosturl = testurl
                break
            except Exception as e:
                print(e)
                print('伺服器失效:%s' % h)
                continue
            pass
        print('準備下載:%s' % hosturl)
        download_video(hosturl, header=header)



# https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Range
def getVideoContent(sourceUrl):
    # http://v.myself-bbs.com/api/files/index/44665/001/
    # http://v.myself-bbs.com/api/files/index/animeID/number/
    targetUrl = 'http://v.myself-bbs.com/api/files/index'
    sourceUrl = sourceUrl.strip('\r')

    temp = str(sourceUrl).split('/')
    animeID = temp[-2]
    number = temp[-1]

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
    header_videoData = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': sourceUrl,
        'Host': 'v.myself-bbs.com',

    }

    s = '{}/{}/{}'
    requestUrl = s.format(targetUrl, animeID, number)

    r = requests.get(requestUrl, headers=header_videoData)
    data = r.json()

    items = data['video'].items()

    videoUrl = {}
    items_sorted = sorted(items, key=lambda x: int(x[0]), reverse=True)
    for k, v in items_sorted:
        videoUrl[k] = v

    return {
        'video': videoUrl,
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
def download_video(video_link, header=None, file_name=None):
    if file_name == None:
        file_name = '{}.mp4'.format(int(time.time()))

    response = requests.get(video_link, headers=header, stream=True)
    # response.close()
    # print(response.headers)
    chunk_size = 1024  # 單次請求最大值 1024
    content_size = int(response.headers['content-length'])  # 內容大小

    print("Downloading file:%s" % file_name)
    progress = ProgressBar(file_name, total=content_size,
                           unit="KB", chunk_size=chunk_size, run_status="正在下载", fin_status="下载完成")
    # download started
    # maybe can use byte to hex to check data?
    with open(file_name, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size*256):
            if chunk:
                f.write(chunk)
                progress.refresh(count=len(chunk))

    response.close()
    print("%s downloaded!\n" % file_name)

    print("All videos downloaded!")

    return


class ProgressBar(object):

    def __init__(self, title,
                 count=0.0,
                 run_status=None,
                 fin_status=None,
                 total=100.0,
                 unit='', sep='/',
                 chunk_size=1.0):
        super(ProgressBar, self).__init__()
        self.info = "【%s】%s %.2f %s %s %.2f %s"
        self.title = title
        self.total = total
        self.count = count
        self.chunk_size = chunk_size
        self.status = run_status or ""
        self.fin_status = fin_status or " " * len(self.status)
        self.unit = unit
        self.seq = sep

    def __get_info(self):
        # 【名稱】狀態 進度 單位 分割線 總數 單位
        _info = self.info % (self.title, self.status,
                             self.count/self.chunk_size, self.unit, self.seq, self.total/self.chunk_size, self.unit)
        return _info

    def refresh(self, count=1, status=None):
        self.count += count
        # if status is not None:
        self.status = status or self.status
        end_str = "\r"
        if self.count >= self.total:
            end_str = '\n'
            self.status = status or self.fin_status
        print(self.__get_info(), end=end_str)


if __name__ == '__main__':
    main()
    # download_video(
    #     "http://v25.myself-bbs.com/44624/001_720P.mp4?m=RBeqBmpKemHLkcpw3WMXug&e=1544112645", 'test.mp4')
# download_video("http://v1.myself-bbs.com/44665/001_1080P.mp4?m=tqMc76s-RRgqsJU3Z8JDmA&e=1544111776",'test.mp4')
