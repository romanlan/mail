import re
import subprocess
from datetime import datetime
import datetime as dt


class Header:
    """获取邮件头并分析"""

    def __init__(self, email, openfile):
        self.__email = email
        self.__openfile = openfile
        self.__openfile.write('开始处理\n')

    def parsecheck(self, parsestr, parseemail):
        if parsestr in parseemail:
            return parseemail[parsestr]

    def get_header_to(self):
        header_to = self.__email.parsed_email['To']
        self.__openfile.write('To: ' + str(header_to) + '\n')
        return header_to

    def get_header_from(self):
        header_from = self.__email.parsed_email['From']
        self.__openfile.write('From: ' + str(header_from) + '\n')
        return header_from

    def get_header_sender(self):
        header_sender = self.parsecheck('Sender', self.__email.parsed_email['HeadersMap'])
        self.__openfile.write('Sender: ' + str(header_sender) + '\n')
        if isinstance(header_sender, list):
            self.__openfile.write('sender 数量不是一个,可能存在伪造。\n')
            return None
        return header_sender

    def get_header_replyto(self):
        header_replyto = self.parsecheck('REPLY-TO', self.__email.parsed_email['HeadersMap'])
        # header_replyto = self.__email.parsed_email['HeadersMap']['REPLY-TO']
        self.__openfile.write('REPLY_TO: ' + str(header_replyto) + '\n')
        return header_replyto

    def get_header_date(self):
        header_date = self.__email.parsed_email['HeadersMap']['Date']
        self.__openfile.write('Date: ' + str(header_date) + '\n')
        if isinstance(header_date, list):
            self.__openfile.write('Date 数量不是一个,可能存在伪造。\n')
            return None
        return header_date

    def get_header_DKIMsignature(self):
        header_DKIMsignature = self.__email.parsed_email['HeadersMap']['DKIM-Signature']
        self.__openfile.write('DKIM-Signature: ' + str(header_DKIMsignature) + '\n')
        return header_DKIMsignature

    def get_header_messageid(self):
        header_messageid = self.__email.parsed_email['HeadersMap']['Message-ID']
        self.__openfile.write('Message-ID: ' + str(header_messageid) + '\n')
        return header_messageid

    def get_header_receiveds(self):
        header_receiveds = self.__email.parsed_email['HeadersMap']['Received']
        if isinstance(header_receiveds, list):
            for i in range(0, len(header_receiveds)):
                self.__openfile.write('Received[' + str(i) + ']: ' + str(header_receiveds[i]) + '\n')
        else:
            self.__openfile.write('Received: ' + str(header_receiveds + '\n'))
        return header_receiveds

    def get_received_date(self, received):
        return received.split(';')[1]

    def compare_from_replyto(self):
        mailfrom = self.get_header_from()
        replyto = self.get_header_replyto()
        if mailfrom is not None and replyto is not None:
            find_mailfrom = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", mailfrom)
            find_replyto = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", replyto)
            if find_mailfrom != find_replyto:
                self.__openfile.write('发件人与回复人不一致，可能存在伪造。\n')
            else:
                self.__openfile.write('发件人与回复人一致，正常。\n')

    def compare_from_sender(self):
        mailfrom = self.get_header_from()
        sender = self.get_header_sender()
        if mailfrom is not None and sender is not None:
            find_mailfrom = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", mailfrom)
            find_sender = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", sender)
            if find_mailfrom != find_sender:
                self.__openfile.write('显示发件人与实际发件人不一致，可能存在伪造。\n')
            else:
                self.__openfile.write('显示发件人与实际发件人一致，正常。\n')

    def date_to_unix(self, date):
        timezonestr = date[25:]
        GMT_FORMAT = '%a, %d %b %Y %H:%M:%S ' + timezonestr
        unix_time = datetime.strptime(date, GMT_FORMAT).replace(tzinfo=dt.timezone.utc).timestamp()
        return unix_time

    def receiveddate_to_unix(self, receiveddate):
        timezonestr = receiveddate[26:]
        GMT_FORMAT = ' %a, %d %b %Y %H:%M:%S' + timezonestr
        unix_time = datetime.strptime(receiveddate, GMT_FORMAT).replace(tzinfo=dt.timezone.utc).timestamp()
        return unix_time

    def compare_received_date(self):
        header_receiveds = self.get_header_receiveds()
        date = self.get_header_date()
        if header_receiveds is not None and date is not None and isinstance(header_receiveds, list):
            for i in range(0, len(header_receiveds)):
                if self.receiveddate_to_unix(self.get_received_date(header_receiveds[i])) < self.date_to_unix(date):
                    self.__openfile.write('received[' + str(i) + ']时间小于date时间，可能存在伪造。\n')
                    return -1
                    # 第一个是最新的
                else:
                    for j in range(0, i - 1):
                        if self.receiveddate_to_unix(self.get_received_date(header_receiveds[i])) < \
                                self.receiveddate_to_unix(self.get_received_date(header_receiveds[j])):
                            self.__openfile.write(
                                'received[' + str(i) + ']时间小于' + 'received[' + str(i) + ']，可能存在伪造。\n')
                            return -1
                    self.__openfile.write('received[' + str(i) + ']时间正常。\n')
        elif header_receiveds is not None and date is not None:
            if self.receiveddate_to_unix(self.get_received_date(header_receiveds)) < self.date_to_unix(date):
                self.__openfile.write('received时间小于date时间，可能存在伪造。\n')
            else:
                self.__openfile.write('received时间正常。\n')

    def get_com(self, ip):
        lookup_result = subprocess.Popen("nslookup {}".format(ip),
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0]
        return lookup_result

    def compare_ip_com(self):
        reveives = self.get_header_receiveds()
        if isinstance(reveives, list):
            for r in reveives:
                i = reveives.index(r)
                ip_list = r.split(' ')
                com1 = ip_list[1]
                com2 = ip_list[2].replace('(', ' ').strip()
                if com2 == '':
                    com2 = 'None'
                self.__openfile.write('域名： ' + com1 + ' ' + com2 + '\n')
                ip = ip_list[3].replace('[', ' ').replace(']', ' ').replace(')', ' ').strip()
                self.__openfile.write('ip： ' + ip + '\n')
                print(ip)
                lookup_result = self.get_com(ip)
                response = lookup_result.decode("GBK").replace('\r\n', ' ')
                self.__openfile.write('ip查询结果为: \n' + response+ '\n')
                if com1 in str(lookup_result) or com2 in str(lookup_result):
                    self.__openfile.write('received[' + str(i) + ']ip与域名一致。\n')
                else:
                    self.__openfile.write('received[' + str(i) + ']ip与域名不符。\n')
        else:
            ip_list = reveives.split(' ')
            com1 = ip_list[1]
            com2 = ip_list[2].replace('(', ' ').strip()
            self.__openfile.write('域名： ' + com1 + ' ' + com2 + '\n')
            ip = ip_list[3].replace('[', ' ').replace(']', ' ').replace(')', ' ').strip()
            self.__openfile.write('ip： ' + ip + '\n')
            print(ip)
            lookup_result = self.get_com(ip)
            response = lookup_result.decode("GBK").replace('\r\n', ' ')
            self.__openfile.write('ip查询结果为: \n' + response + '\n')
            if com1 in str(lookup_result) or com2 in str(lookup_result):
                self.__openfile.write('received ip与域名一致。\n')
            else:
                self.__openfile.write('received ip与域名不符。\n')

    def compare(self):
        self.compare_from_replyto()
        self.compare_from_sender()
        self.compare_received_date()
        self.compare_ip_com()
