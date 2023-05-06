import requests
import time
import re
import execjs
import json
import random
from lxml import etree
"""
host = 'https://www.mafengwo.cn/'
"""


class SendRequest:
    """基本请求模板，待完善"""
    def __init__(self):
        self.url = ''
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        }
        self.cookies = {}
        self.data = {}
        self.page = 1
        self.session = requests.session()

    @property
    def UGetRequest(self):
        response = self.session.get(url=self.url, headers=self.headers, cookies=self.cookies)
        time.sleep(random.randint(1,3))
        return response

    @UGetRequest.setter
    def UGetRequest(self, kwargs: dict):
        if kwargs.get('url'):
            self.url = kwargs.get('url')
        if kwargs.get('referer'):
            self.headers['referer'] = kwargs.get('referer')

    @property
    def UPostRequest(self):
        response = self.session.post(url=self.url, headers=self.headers, cookies=self.cookies, data=self.data)
        return response

    @UPostRequest.setter
    def UPostRequest(self, kwargs: dict):
        if kwargs.get('url'):
            self.url = kwargs.get('url')
        if kwargs.get('referer'):
            self.headers['referer'] = kwargs.get('referer')


class DataDeal(SendRequest):
    def getIndexData(self):
        """主页处理"""
        daytime = str(int(time.time()*1000))
        self.UGetRequest = {'url': 'https://pagelet.mafengwo.cn/note/pagelet/recommendNoteApi?params={"type":0,"objid":0,"page":%s,"ajax":1,"retina":1}&_=%s' % (self.page, daytime),
                            'referer': 'https://www.mafengwo.cn/'}  # 防盗链
        response = self.UGetRequest
        text_html = response.json().get('data').get('html')
        # with open('mfw.html', 'w', encoding='utf-8')as f:
        #     f.write(text_html)
        tree = etree.HTML(text_html)
        url_list = tree.xpath('//*[@id="_j_tn_content"]/div[1]/div/div[1]/a/@href')
        url_list = ['https://www.mafengwo.cn' + url for url in url_list]    # 拼接出完整的游记详情页URL地址
        return url_list

    def getFirstCookie(self):
        """获取第一次返回的Cookie"""
        response = self.UGetRequest
        status_code = response.status_code  # 返回状态码
        res_data = response.content.decode()
        if status_code == 200:  # 判断状态码如果为200则证明没有二次跳转，这种情况发生在第一篇游记请求成功之后
            return response
        __jsluid_s = response.cookies.get('__jsluid_s')
        res_jscode = re.findall('<script>document\.cookie=(.*?)location\.href=location\.pathname\+location\.search</script>',res_data)[0][:-1]  # 提取出第一次返回的js代码
        res_jscode = execjs.eval(res_jscode)    # 执行第一次获取的js代码生成第一次cookie
        __jsl_clearance_s = res_jscode.split(';')[0]
        k, v = __jsl_clearance_s.split('=')
        # 添加cookie
        self.cookies[k] = v
        self.cookies['__jsluid_s'] = __jsluid_s

    def getSecCookie(self):
        """获取第二次返回的cookie"""
        response = self.UGetRequest
        sec_jscode = response.content.decode()
        go_data = re.findall('}};go\((.*?)\)</script>', sec_jscode)[0]  # 提取出js代码中需要传递的参数
        dic_data = json.loads(go_data)
        data = {'ha': 'sha256', 'tn': '__jsl_clearance_s', 'vt': '3600', 'wt': '1500'}
        bts = dic_data.get('bts')
        chars = dic_data.get('chars')
        ct = dic_data.get('ct')
        data['bts'] = bts
        data['chars'] = chars
        data['ct'] = ct
        location_jscode = open('jscode.js', encoding='utf-8').read()    # 此处打开的代码为第二次请求返回的JS代码，该JS代码就是用于生成第二次cookie的
        js_res = execjs.compile(location_jscode)
        __jsl_clearance_s = js_res.call('go', data)[0]
        self.cookies['__jsl_clearance_s'] = __jsl_clearance_s

    def detailDeal(self):
        url_list = self.getIndexData()  # 获取到一页的游记
        for url in url_list:    # 遍历游记列表
            self.UGetRequest = {'url': url, 'rederer': ''}
            FckResponse = self.getFirstCookie()
            if not FckResponse:     # 判断获取第一次cookie时是发生跳转还是响应成功，响应成功则证明是获取到了游记内容，此情况发生于第一次访问成功之后
                # 如果没有响应成功，则证明需要我们进一步获取第二次的cookie再次请求
                while 1:
                    try:
                        self.getSecCookie()
                        response = self.UGetRequest
                        text_html = response.content.decode()
                        tree = etree.HTML(text_html)
                        print(tree.xpath('//*[@id="_j_cover_box"]/div[3]/div[2]/div/h1/text()')[0])
                        break
                    except Exception as e:
                        print(e)
                        continue
            else:
                text_html = FckResponse.content.decode()
                tree = etree.HTML(text_html)
                print(tree.xpath('//*[@id="_j_cover_box"]/div[3]/div[2]/div/h1/text()')[0])


if __name__ == '__main__':
    indexdeal = DataDeal()
    indexdeal.detailDeal()