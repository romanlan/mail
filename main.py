#!/usr/bin/python
import re
# coding=gbk
import subprocess
from datetime import datetime
import datetime as dt
import parse_emails
import os


import parse_header


def open_file():
    save_filename = str(datetime.now().timestamp()) + 'output.txt'
    openfile = open(save_filename, 'a')
    return openfile


def emails_parse(pathin, openfile):
    email = parse_emails.EmailParser(pathin, max_depth=3, parse_only_headers=False)
    email.parse()
    header = parse_header.Header(email, openfile)
    header.compare()


def get_files(pathin):
    emlnum = 0
    openfile = open_file()
    for filepath, dirnames, filenames in os.walk(pathin):
        for filename in filenames:
            if filename.endswith('.eml'):
                emlnum = emlnum + 1
                name = os.path.join(filepath, filename)
                openfile.write('邮件名称: ' + name + '\n')
                emails_parse(name, openfile)
                openfile.write('\n')
    openfile.write('邮件总数: ' + str(emlnum) + '\n')
    openfile.close()


if __name__ == '__main__':
    path = 'D:\study\paper\email\\tets'
    ip = subprocess.Popen("nslookup {}".format('123.126.97.2'),
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0]
    response = ip.decode("GBK")
    response1 = re.findall("名称:.*\r\n", response)
    #res_list = response1.split(" ")
    #row_ip = res_list[2].split()[:-1]
    GMT_FORMAT = '%a, %d %b %Y %H:%M:%S +0800'
    str2 = 'Fri, 22 Jul 2022 16:26:55 +0800'
    time = datetime.strptime(str2, GMT_FORMAT)
    unix_time = time.timestamp()
    str1 = 'Fri, 22 Jul 2022 8:26:55 +0000 (cst)'
    timezonestr = str1[25:]
    GMT_FORMAT1 = '%a, %d %b %Y %H:%M:%S ' + timezonestr
    time1 = datetime.strptime(str1, GMT_FORMAT1).replace(tzinfo=dt.timezone.utc)
    unix_time1 = time1.timestamp()
    get_files(path)
