import requests

url = 'https://q5.itc.cn/q_70/images01/20241024/df7b31acc6b5452ea936d0d2ffe776cc.jpeg'
res = requests.get(url)
# print(res.content)
with open('../../../练习/2.jpg', 'wb') as f:
    f.write(res.content)
