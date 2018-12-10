import requests


def download_video(video_link):
    response = requests.get(video_link, stream=True)
    print(response.headers)
    file_name = 'test.mp4'

    chunk_size = 1024 # 单次请求最大值
    content_size = int(response.headers['content-length']) # 内容体总大小
    print("Downloading file:%s" % file_name)
    progress = ProgressBar(file_name, total=content_size,
                        unit="KB", chunk_size=chunk_size, run_status="正在下载", fin_status="下载完成")
    # download started
    # maybe can use byte to hex to check data?
    with open(file_name, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
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
        # 【名称】状态 进度 单位 分割线 总数 单位
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

download_video("http://v25.myself-bbs.com/44624/010_480P.mp4?m=qNt4SlHWI9nxSpCqDJXAyw&e=1544098700")