import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0"
}
response = requests.get(url='https://movie.douban.com/top250', headers=headers)
if response.ok:
    print(response.text)
else:
    print("请求失败...")
