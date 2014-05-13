#!/usr/bin/env python
# encoding: utf-8
import urllib2
import urllib
import json
import re
from HTMLParser import HTMLParser
from lib.command.Command import UserInput
from util import Util
from util.log import *
from lib.model import Callback


class translate_callback(Callback.Callback):

    base_url = "http://fanyi.youdao.com/openapi.do"

    def callback(self, cmd, msg):
        if Util.empty_str(msg):
            cancel_flag = u"取消"
            finish_flag = u"完成"
            self._home.publish_msg(
                cmd
                , u"请输入内容, 输入\"%s\"或\"%s\"结束:" % (finish_flag, cancel_flag)
                , cmd_type="input"
            )
            msg = UserInput(self._home).waitForInput(
                                                    finish=finish_flag,
                                                    cancel=cancel_flag)
        if msg is None:
            self._home.publish_msg(cmd, u"无翻译内容")
        elif len(msg) > 200:
            self._home.publish_msg(cmd, u"翻译内容过长（<200字）")
        else:
            try:
                values = {
                    "keyfrom":"11111testt111", 
                    "key":"2125866912",
                    "type":"data",
                    "doctype":"json",
                    "version":"1.1",
                    "q":msg.encode("utf-8")
                }
                url = translate_callback.base_url + "?" + urllib.urlencode(values)
                res = urllib2.urlopen(url).read()
                res = " ".join(json.loads(res)["translation"])
                self._home.publish_msg(cmd, u"翻译结果:\n" + res)
            except Exception, ex:
                ERROR("request error:", ex)
                self._home.publish_msg(cmd, u"翻译失败")
                return True
        return True


class baidu_wiki_callback(Callback.Callback):
    base_url = "http://wapbaike.baidu.com"

    def searchWiki(self, word, time=10):
        value = {"word": word.encode("utf-8")}
        url = baidu_wiki_callback.base_url + \
                "/search?" + urllib.urlencode(value)
        try:
            response = urllib2.urlopen(url, timeout=time)
            html = response.read().encode("utf-8")
            response.close()

            real_url = None
            content = None
            m = re.compile(r"URL=(.+)'>").search(html)
            if m:
                real_url = m.group(1)
            else:
                return None, None
            real_url = real_url[:real_url.index("?")]
            if not real_url is None:
                url = baidu_wiki_callback.base_url + real_url
                response = urllib2.urlopen(url, timeout=time)
                html = response.read()
                response.close()
                m = re.compile(
                    r'<p class="summary"><p>(.+)<div class="card-info">',
                    re.DOTALL
                ).search(html)
                if m:
                    content = m.group(1)
                    return Util.strip_tags(content), url
                else:
                    return None, None
        except Exception, ex:
            ERROR("wiki error: ", ex)
            return None, None

    def callback(self, cmd, msg):
        if Util.empty_str(msg):
            cancel_flag = u"取消"
            finish_flag = u"完成"
            self._home.publish_msg(
                cmd
                , u"请输入内容, 输入\"%s\"或\"%s\"结束:" % (finish_flag, cancel_flag)
                , cmd_type="input"
            )
            msg = UserInput(self._home).waitForInput(
                                                    finish=finish_flag,
                                                    cancel=cancel_flag)
        if not msg is None:
            self._home.publish_msg(cmd, u"正在搜索...")
            res, url = self.searchWiki(msg)
            if res is None:
                self._home.publish_msg(cmd, u"无百科内容")
            else:
                res = res.decode("utf-8")
                if len(res) > 140:
                    res = res[:140]
                msg = u"百度百科:\n    %s...\n%s" \
                        % (res, url)
                self._home.publish_msg(cmd, msg)
        else:
            self._home.publish_msg(cmd, u"无百科内容")
        return True


class cal_callback(Callback.Callback):

    _ops = {
            u'加':'+',
            u'减':'-',
            u'乘':'*',
            u'除':'/',
            u'+':'+',
            u'-':'-',
            u'*':'*',
            u'/':'/',
            u'(':'(',
            u'（':'(',
            u')':')',
            u'）':')',
            }

    def _parse_tokens(self, src):
        tokens = []
        cur_t = u''
        for term in src:
            if term in cal_callback._ops:
                if cur_t != u'':
                    tokens.append(cur_t)
                    cur_t = u''
                tokens.append(term)
            else:
                cur_t += term
        if cur_t != u'':
            tokens.append(cur_t)
        return tokens

    def _parse_expression(self, tokens):
        expression = u''
        for token in tokens:
            if token in cal_callback._ops:
                expression += cal_callback._ops[token]
            else:
                num = Util.cn2dig(token)
                if num is None:
                    return None
                expression += str(num)
        res = None
        INFO("expression: " + expression)
        try:
            res = eval(expression)
        except Exception, ex:
            ERROR("cal expression error:", ex)
        return res

    def callback(self, cmd, msg):
        if Util.empty_str(msg):
            cancel_flag = u"取消"
            finish_flag = u"完成"
            self._home.publish_msg(
                cmd
                , u"请输入公式, 输入\"%s\"或\"%s\"结束:" % (finish_flag, cancel_flag)
                , cmd_type="input"
            )
            msg = UserInput(self._home).waitForInput(
                                                    finish=finish_flag,
                                                    cancel=cancel_flag)
        if msg is None:
            self._home.publish_msg(cmd, u"无公式内容")
        else:
            tokens = self._parse_tokens(msg)
            if not tokens is None:
                res = self._parse_expression(tokens)
                if not res is None:
                    self._home.publish_msg(cmd, u"%s = %s" % (msg, str(res)))
                    return True, res
                else:
                    self._home.publish_msg(cmd, u"计算出错")
                    return True, None
            else:
                self._home.publish_msg(cmd, u"格式有误")
        return True, None
