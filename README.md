# AnimeDownloader
AnimeDownloader(ADL)


快速下載 myself-bbs.com 動畫的小工具

## Installation

主程式下載 : [AnimeDownloader(ADL)](https://github.com/md9830415/AnimeDownloader/releases)

## Getting Started

1. 開啟**AnimeDownloader\(ADL\)主程式**

2. 到 myself-bbs.com 選擇想下載的動畫頁面, 像是 https://myself-bbs.com/thread-44659-1-1.html

3. 在輸入中貼上頁面網址, 並輸入需要的參數, 按下Enert

4. 完成後, 檔案會存在**AnimeDownload**資料夾中

```
@params:
url          -[Required] : myself-bbs url, like: https://myself-bbs.com/thread-44659-1-1.html
start        -[Optional] : start index
end          -[Optional] : end index
image_res    -[Optional] : image resolution
downloadMode -[Optional] : multiThread || singleThread
threadNum    -[Optional] : multiThread threadNum
autoRetry    -[Optional] : when file incomplete, retrying downloads

Download all :
> https://myself-bbs.com/thread-44659-1-1.html

Download episode 3 to 7 :
> https://myself-bbs.com/thread-44659-1-1.html start=3 end=7

Just download episode 3 :
> https://myself-bbs.com/thread-44659-1-1.html start=3 end=3

Note: indexing start with 0

Change image resolution to 360p (default=1080):
> https://myself-bbs.com/thread-44659-1-1.html image_res=360

Download episode 3 to 7 (720p)
> https://myself-bbs.com/thread-44659-1-1.html start=3 end=7 image_res=720

Advanced setting:

Change download mode to multiThread or singlethread (default=multiThread) :
> https://myself-bbs.com/thread-44659-1-1.html downloadMode=singleThread

Change threadNum (default=20) :
> https://myself-bbs.com/thread-44659-1-1.html threadNum=30

Enable/Disable autoRetry (default=False) :
> https://myself-bbs.com/thread-44659-1-1.html autoRetry=True
```

