# AnimeDownloader

AnimeDownloader(ADL)

![img](https://i.imgur.com/pkHFupn.gif)

快速下載動畫的小工具

## Installation

主程式下載 : [AnimeDownloader(ADL) v1.2](https://github.com/md9830415/AnimeDownloader/releases)

## Getting Started

1. 開啟**AnimeDownloader\(ADL\)主程式**

2. 到 momovod 選擇想下載的動畫頁面, 像是 https://www.momovod.com/vod-detail-id-61424.html

3. 在輸入中貼上頁面網址, 並輸入需要的參數, 按下Enert

4. 完成後, 檔案會存在**AnimeDownload**資料夾中

*注意: chromedriver.exe為必要檔案，請勿任意刪除*

```

@params:
url          -[Required] : myself-bbs url, like: https://www.momovod.com/vod-detail-id-61424.html
start        -[Optional] : start index
end          -[Optional] : end index
threadNum    -[Optional] : multiThread threadNum


Example:

Download all :
> https://www.momovod.com/vod-detail-id-61424.html

Download episode 3 to 7 :
> https://www.momovod.com/vod-detail-id-61424.html start=2 end=6

Just download episode 3 :
> https://www.momovod.com/vod-detail-id-61424.html start=2 end=2

Note: indexing start with 0


Advanced setting:

Change threadNum (default=64) :
> https://www.momovod.com/vod-detail-id-61424.html threadNum=128

```