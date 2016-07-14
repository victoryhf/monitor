#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import re
import sys
reload(sys)
sys.setdefaultencoding('utf8')

#告警列表
alert = []   

#锁定主目录
DIR = '/opt/oracle/apache/htdocs/panoramic/'

def getIdIp(name, id):
    '''根据节点名及sourceid生成对应IP，返回字符串'''
    with open(DIR + 'config/tab.conf') as f:
        tab_conf = f.read()
        tab_conf = re.findall('\[.*\][A-Z0-9\n=,.:]*', tab_conf)
    if name == 'mas':
        conf = tab_conf[6]
    elif name == 'aps':
        conf = tab_conf[7]
    t = conf.split('\n')[1].split('=')[1].split(',')
    a = conf.split('\n')[2].split('=')[1].split(',')
    b = conf.split('\n')[3].split('=')[1].split(',')
    id_ip = {}
    for i in t:
        id_ip[i.split(':')[0]] = i.split(':')[1]
    for i in a:
        id_ip[i.split(':')[0]] = i.split(':')[1]
    for i in b:
        id_ip[i.split(':')[0]] = i.split(':')[1]
    return id_ip[id]

def getNodeIp(name, unit=None):
    '''根据节点名称生成该节点在TAB的IP分布列表，返回IP列表'''
    with open(DIR + 'config/tab.conf') as f:
        tab_conf = f.read()
        tab_conf = re.findall('\[.*\][A-Z0-9\n=,.:]*', tab_conf)
    nodes = ['vpos', 'mgw', 'posp', 'internal', 'mbp', 'tais', 'mas', 'aps', 'cups_cp', 'cups_cnp', 'cups_kj', 'icbc_sh_kj', 'abc_sz_kj']
    if name == 'pos_machine':
        conf = tab_conf[2]
    else:
        for i in range(len(nodes)):
            if name == nodes[i]:
                conf = tab_conf[i]
                break
    if name in ['mas', 'aps']:
        t = [ i.split(':')[1] for i in conf.split('\n')[1].split('=')[1].split(',') ]
        a = [ i.split(':')[1] for i in conf.split('\n')[2].split('=')[1].split(',') ]
        b = [ i.split(':')[1] for i in conf.split('\n')[3].split('=')[1].split(',') ]
    elif name in ['pos_machine', 'vpos', 'mgw', 'posp', 'internal', 'mbp', 'tais']:
        t = conf.split('\n')[1].split('=')[1].split(',')
        a = conf.split('\n')[2].split('=')[1].split(',')
        b = conf.split('\n')[3].split('=')[1].split(',')
    else:
        all = conf.split('\n')[1].split('=')[1].split(',')
    if unit == 't':
        return t
    elif unit == 'a':
        return a
    elif unit == 'b':
        return b
    else:
        return all

def log_process(name, unit, node_log):
    '''根据节点名称、机组名称及日志名称处理该日志，使log只包含该机组的日志'''
    log = []
    ip = getNodeIp(name, unit)
    for i in range(1, len(node_log)):
        for j in range(len(ip)):
            if ip[j] == re.findall('[0-9]{1,3}\.[0-9]{1,3}', node_log[i].split('=')[0])[1]:
                log.append(re.search('[0-9]{1,3}\.[0-9]{1,3}=.*', node_log[i]).group(0))
    log.append(name)
    return log

def getNodeLog(name, unit):
    '''根据节点名称及所在机组生成对应日志，返回日志列表'''
    with open(DIR + 'datas/splunk.data') as f:
        raw_log = f.read()
    #按节点名称将日志拆分成多个字符串并放入列表
    raw_log = [ i.rstrip('\n') for i in re.findall('\[.*\][0-9\n=:.]*', raw_log) ]
    nodes = ['pos_machine', 'vpos', 'posp', 'mgw', 'internal', 'mbp', 'tais', 'mas', 'aps']
    for i in range(len(nodes)):
        if name == nodes[i]:
            node_log = raw_log[i]
            node_log = [ node_log.split('\n')[i] for i in range(len(node_log.split('\n'))) ]
            if unit == 't':
                log =log_process(name, 't', node_log)
            elif unit == 'a':
                log =log_process(name, 'a', node_log)
            else:
                log = log_process(name, 'b', node_log)
            break
    #没数据的IP统一设为0
    ip = getNodeIp(name, unit)
    for i in log[:-1]:
        for j in ip:
            if j == i.split('=')[0]:
                ip.remove(j)
    for i in ip:
        if name == 'tais':
            log.insert(-1, i+'=0:0:0')
        elif name == 'pos_machine':
            log.insert(-1, i+'=0')
        else:
            log.insert(-1, i+'=0:0')
    return log

def getNodeData(name, node):
    '''根据节点名称及所在机组生成关键字字典，返回列表'''
    with open(DIR + 'datas/splunk.data') as f:
        time = f.readline().rstrip().split(' ')[1]
    log = getNodeLog(name, node)
    #len(log)-1是因为log包含name字符串
    data = [ {} for i in range(len(log) - 1) ]
    for i in range(len(data)):
        if name == 'pos_machine':
            data[i]['name'] = 'POS机'
            data[i]['ip'] = log[i].split('=')[0]
            data[i]['time'] = time
            data[i]['flush'] = int(log[i].split('=')[1].split(':')[0])
            data[i]['type'] = 'Queue监控'
        elif name == 'mgw':
            data[i]['name'] = log[-1]
            data[i]['ip'] = log[i].split('=')[0]
            data[i]['time'] = time
            if log[i].split('=')[1].split(':')[0] == '':
                data[i]['request'] = 0
            else:
                data[i]['request'] = int(log[i].split('=')[1].split(':')[0])
            if log[i].split('=')[1].split(':')[1] == '':
                data[i]['response'] = 0
            else:
                data[i]['response'] = int(log[i].split('=')[1].split(':')[1])
            data[i]['type'] = 'Queue监控'
        else:
            data[i]['name'] = log[-1]
            data[i]['ip'] = log[i].split('=')[0]
            data[i]['time'] = time
            if log[i].split('=')[1].split(':')[0] == '':
                data[i]['request'] = 0
            else:
                data[i]['request'] = int(log[i].split('=')[1].split(':')[0])
            if log[i].split('=')[1].split(':')[1] == '':
                data[i]['response'] = 0
            else:
                data[i]['response'] = int(log[i].split('=')[1].split(':')[1])
            if name == 'tais':
                if log[i].split('=')[1].split(':')[2] == '':
                    data[i]['forward'] = 0
                else:
                    data[i]['forward'] = int(log[i].split('=')[1].split(':')[2])
            data[i]['type'] = 'Queue监控'
    for i in range(len(data)):
        #total ips
        if name == 'tais':
            total_request = total_response = total_forward = 0
            for j in range(len(data)):
                total_request += int(data[j]['request'])
                total_response += int(data[j]['response'])
                total_forward += int(data[j]['forward'])
            data[i]['differ'] = total_request - total_response - total_forward
            if (total_request - total_response - total_forward) >= 60 or (total_response + total_forward - total_request) >= 60:
                data[i]['alarm'] = 'critical'
            elif (total_request - total_response - total_forward) >= 45 or (total_response + total_forward - total_request) >= 45:
                data[i]['alarm'] = 'warning'
            else:
                data[i]['alarm'] = 'normal'
            data[i]['total_request'] = total_request
            data[i]['total_response'] = total_response
            data[i]['total_forward'] = total_forward
            data[i]['num'] = 'total'
        #total ips
        elif name == 'mas':
            total_request = total_response = 0
            for j in range(len(data)):
                total_request += int(data[j]['request'])
                total_response += int(data[j]['response'])
            data[i]['differ'] = total_request - total_response 
            if (total_request - total_response) >= 60 or (total_response - total_request) >= 60:
                data[i]['alarm'] = 'critical'
            elif (total_request - total_response) >= 45 or (total_response - total_request) >= 45:
                data[i]['alarm'] = 'warning'
            else:
                data[i]['alarm'] = 'normal'
            data[i]['total_request'] = total_request
            data[i]['total_response'] = total_response
            data[i]['num'] = 'total'
        #total ips
        elif name == 'pos_machine':
            total_flush = 0
            for j in range(len(data)):
                total_flush += int(data[j]['flush'])
            if total_flush >= 20:
                data[i]['alarm'] = 'critical'
            elif total_flush >= 10:
                data[i]['alarm'] = 'warning'
            else:
                data[i]['alarm'] = 'normal'
            data[i]['total_flush'] = total_flush
            data[i]['num'] = 'total'
        #single IP
        elif name == 'mgw':
            request = int(data[i]['request'])
            response = int(data[i]['response'])
            data[i]['differ'] = request - response
            if (request - response) >= 20 or (response - request) >= 20:
                data[i]['alarm'] = 'critical'
            elif (request - response) >= 10 or (response - request) >= 10:
                data[i]['alarm'] = 'warning'
            else:
                data[i]['alarm'] = 'normal'
            data[i]['num'] = 'single'
        #single IP
        else:
            request = int(data[i]['request'])
            response = int(data[i]['response'])
            data[i]['differ'] = request - response
            if (request - response) >= 30 or (response - request) >= 30:
                data[i]['alarm'] = 'critical'
            elif (request - response) >= 20 or (response - request) >= 20:
                data[i]['alarm'] = 'warning'
            else:
                data[i]['alarm'] = 'normal'
            data[i]['num'] = 'single'
    return data


def getNodePic(name):
    '''根据报警情况返回对应图片'''
    data = getNodeData(name, 't')
    data.extend(getNodeData(name, 'a'))
    data.extend(getNodeData(name, 'b'))
    number_critical = number_warning = 0
    #total ips
    if name in ['pos_machine', 'tais', 'mas']:
        for i in range(len(data)):
            if data[i]['alarm'] == 'critical':
                number_critical += 1
            elif data[i]['alarm'] == 'warning':
                number_warning += 1
        if number_critical >= 1:
            return './static/images/' + name + '_critical.jpg'
        elif number_warning >= 1:
            return './static/images/' + name + '_warning.jpg'
        else:
            return './static/images/' + name + '_normal.jpg'
    #single ips
    else:
        for i in range(len(data)):
            if data[i]['alarm'] == 'critical':
                number_critical += 1
            elif data[i]['alarm'] == 'warning':
                number_warning += 1
        if number_critical >= 2:
            return './static/images/' + name + '_critical.jpg'
        elif number_critical == 1 or number_warning >= 2:
            return './static/images/' + name + '_warning.jpg'
        else:
            return './static/images/' + name + '_normal.jpg'

def getBgwLog(name):
    '''根据bgw名称返回日志，返回列表'''
    with open(DIR + 'datas/bgw.data') as f:
        raw_log = f.read()
    raw_log = [ i.rstrip('\n') for i in re.findall('\[.*\][0-9\n=:.]*', raw_log) ]
    nodes = ['cups_cp', 'cups_cnp', 'cups_kj', 'icbc_sh_kj', 'abc_sz_kj']
    for i in range(len(nodes)):
        if name == nodes[i]:
            log = raw_log[i]
            log = [ log.split('\n')[i] for i in range(len(log.split('\n'))) ] 
            if len(log) > 2:
                log[1] = re.search('[0-9]{1,3}\.[0-9]{1,3}=[0-9]*:[0-9]*', log[1]).group(0)
                log[2] = re.search('[0-9]{1,3}\.[0-9]{1,3}=[0-9]*:[0-9]*', log[2]).group(0)
            elif len(log) > 1:
                log[1] = re.search('[0-9]{1,3}\.[0-9]{1,3}=[0-9]*:[0-9]*', log[1]).group(0)
            break
    ip = getNodeIp(name)
    for i in log[1:]:
        for j in ip:
            if j == i.split('=')[0]:
                ip.remove(j)
    for i in ip:
        log.append(i+'=0:0')
    #将专线名移至列表最后
    bgw_name = log[0][1:-1]
    log = log[1:]
    log.append(bgw_name)
    return log

def getBgwData(name):
    '''根据bgw名称生成关键字字典，返回列表'''
    with open(DIR + 'datas/bgw.data') as f:
        time = f.readline().rstrip().split(' ')[1]
    log = getBgwLog(name)
    data = [ {} for i in range(len(log)-1) ]
    for i in range(len(data)):
        data[i]['ip'] = log[i].split('=')[0]
        data[i]['name'] = log[-1]
        data[i]['time'] = time
        if log[i].split('=')[1].split(':')[0] == '':
            data[i]['request'] = 0
        else:
            data[i]['request'] = int(log[i].split('=')[1].split(':')[0])
        if log[i].split('=')[1].split(':')[1] == '':
            data[i]['response'] = 0
        else:
            data[i]['response'] = int(log[i].split('=')[1].split(':')[1])
        data[i]['num'] = 'single'
        data[i]['type'] = 'Queue监控'
        data[i]['differ'] = data[i]['request'] - data[i]['response']
        if (data[i]['request'] - data[i]['response']) >= 45 or (data[i]['response'] - data[i]['request']) >= 45:
            data[i]['alarm'] = 'critical'
        elif (data[i]['request'] - data[i]['response']) >= 30 or (data[i]['response'] - data[i]['request']) >= 30:
            data[i]['alarm'] = 'warning'
        else:
            data[i]['alarm'] = 'normal'
    return data

def returnPic(name, color, data):
    for i in data:
        if i['alarm'] == 'critical':
            return './static/images/' + name + '_critical.jpg'
        elif i['alarm'] == 'warning':
            color = 'warning'
    if color == 'normal':            
        return './static/images/' + name + '_normal.jpg'
    elif color == 'warning':
        return './static/images/' + name + '_warning.jpg'

def getBgwPic(name):
    '''根据bgw报警情况返回图片'''
    color = 'normal'
    data = getBgwData(name)
    if getSlaData(name):
    	data.extend(getSlaData(name))
    return returnPic(name, color, data)
	    
def getBankPic(name):
    '''根据银行名称返回银行对应图形'''
    bank = []
    color = 'normal'
    if name == 'cups':
        bank = getBgwData('cups_cp')
        bank.extend(getBgwData('cups_cnp'))
        bank.extend(getBgwData('cups_kj'))
        if getSlaData('cups_cp'):
            bank.extend(getSlaData('cups_cp'))
        if getSlaData('cups_cnp'):
            bank.extend(getSlaData('cups_cnp'))
        return returnPic(name, color , bank)
    elif name == 'icbc':
        bank = getBgwData('icbc_sh_kj')
        if getSlaData('icbc_sh_kj'):
            bank.extend(getSlaData('icbc_sh_kj'))
        return returnPic(name, color , bank)
    elif name == 'ccb':
        return returnPic(name, color , bank)
    elif name == 'abc':
        bank = getBgwData('abc_sz_kj')
        if getSlaData('abc_sz_kj'):
            bank.extend(getSlaData('abc_sz_kj'))
        return returnPic(name, color , bank)
    elif name == 'boc':
        return returnPic(name, color , bank)

def getSlaLog(name):
    '''根据名称返回日志，返回列表'''
    log = []
    with open(DIR + 'datas/sla.data') as f:
        raw_log = f.read()
    raw_log = [ i.rstrip('\n') for i in re.findall('\[.*\][a-zA-Z0-9\n=.%]*', raw_log) ]
    #nodes = ['cups_cp', 'cups_cnp', 'icbc_sh_kj', 'abc_sz_kj']
    nodes = ['cups_cp', 'cups_cnp', 'icbc_sh_kj', 'abc_sz_kj', 'mas', 'aps']
    for i in range(len(nodes)):
        if name == nodes[i]:
            log = raw_log[i]
            log = log.split('\n')
    #避免多行垃圾日志
    if name in ['cups_cp', 'cups_cnp', 'icbc_sh_kj', 'abc_sz_kj']:
        log = log[:2]
    else:
        log = log[:5]
    return log

def getSlaData(name):
    '''根据名称生成关键字字典，返回列表'''
    with open(DIR + 'datas/sla.data') as f:
        time = f.readline().rstrip().split(' ')[1]
    log = getSlaLog(name)
    data = [{} for i in range(len(log) - 1)]
    if name in ['mas', 'aps']:
        for i in range(len(data)):
            data[i]['name'] = name
            data[i]['time'] = time
            data[i]['num'] = 'single'
            data[i]['type'] = 'Sla监控'
            data[i]['ip'] = getIdIp(name, log[i+1].split('=')[0])
            data[i]['sla'] = log[i+1].split('=')[1]
        for i in range(len(data)):
            if float(data[i]['sla'].split('%')[0]) >= 10:
                data[i]['alarm'] = 'critical'
            elif float(data[i]['sla'].split('%')[0]) >= 5:
                data[i]['alarm'] = 'warning'
            else:
                data[i]['alarm'] = 'normal'
    else:
        for i in range(len(data)):
            data[i]['name'] = log[0][1:-1]
            data[i]['time'] = time
            data[i]['num'] = 'total'
            if log[i+1].split('=')[1] == 'N':
                data[i]['sla'] = 0
            else:
                data[i]['sla'] = log[i+1].split('=')[1]
            data[i]['type'] = 'Sla监控'
        for i in range(len(data)):
            if float(data[i]['sla']) >= 3:
                data[i]['alarm'] = 'critical'
            elif float(data[i]['sla']) >= 1.5:
                data[i]['alarm'] = 'warning'
            else:
                data[i]['alarm'] = 'normal'
    return data

def getSlaPic(name):
    '''根据Sla报警情况返回图片'''
    #bgw与bank之间的线条
    if name == 'bgw':
        color = 'normal'
        for i in ['cups_cp', 'cups_cnp', 'icbc_sh_kj', 'abc_sz_kj']:
            if getSlaData(i):
                if getSlaData(i)[0]['alarm'] == 'critical':
                    color = 'critical'
                elif getSlaData(i)[0]['alarm'] == 'warning':
                    color = 'warning'
        if color == 'normal':
            return './static/images/arrow_normal.jpg'
        elif color == 'warning':
            return './static/images/arrow_warning.jpg'
        else:
            return './static/images/arrow_critical.jpg' 
    else:
        data = getSlaData(name)
    if data:
        #the number of clour
        number_critical = number_warning = 0
        if name in ['mas', 'aps']:
            for i in range(len(data)):
                if data[i]['alarm'] == 'critical':
                    number_critical += 1
                elif data[i]['alarm'] == 'warning':
                    number_warning += 1
            if number_critical >= 2:
                return './static/images/arrow_' + name + '_critical.jpg'
            elif number_critical == 1 or number_warning >= 2:
                return './static/images/arrow_' + name + '_warning.jpg'
            else:
                return './static/images/arrow_' + name + '_normal.jpg'
        else:
            if data[0]['alarm'] == 'critical':
                return './static/images/arrow_bgw_critical.jpg'
            elif data[0]['alarm'] == 'warning':
                return './static/images/arrow_bgw_warning.jpg'
            else:
                return './static/images/arrow_bgw_normal.jpg'
    else:
        if name in ['mas', 'aps']:
            return './static/images/arrow_' + name + '_normal.jpg'
        else:
            return './static/images/arrow_bgw_normal.jpg'

def getAlert():
    '''获取所有异常数据'''
    log = []
    alert = []
    for i in ['t', 'a', 'b']:
        #total ip
        log.append(getNodeData('pos_machine', i)[0])
        log.extend(getNodeData('vpos', i))
        log.extend(getNodeData('mgw', i))
        log.extend(getNodeData('posp', i))
        log.extend(getNodeData('internal', i))
        log.extend(getNodeData('mbp', i))
        #total ip
        log.append(getNodeData('tais', i)[0])
        log.append(getNodeData('mas', i)[0])
        log.extend(getNodeData('aps', i))
    for i in ['cups_cp', 'cups_cnp', 'cups_kj', 'icbc_sh_kj', 'abc_sz_kj']:
        log.extend(getBgwData(i))
    for i in ['mas', 'aps', 'cups_cp', 'cups_cnp', 'icbc_sh_kj', 'abc_sz_kj']:
        log.extend(getSlaData(i))
    for i in log:
        if i['alarm'] == 'warning':
            alert.append(i)
    for i in log:
        if i['alarm'] == 'critical':
            alert.append(i)
    return alert

def processAlert():
    '''保证报警信息为10行'''
    global alert
    new_alert = getAlert()
    if alert == []:
        #无报警记录且无新的报警
        if new_alert == []:
            for i in range(10):
                alert.append({'name': '', 'no': '', 'ip': '', 'alarm': 'null', 'request': '', 'num': 'single', 'time': '', 'type': '', 'response': ''})
            for i in range(len(alert)):
                alert[i]['no'] = i+1
            alerts = []
            for i in range(5):
                alerts.append([alert[i], alert[i+5]])
            return alerts
        #无报警记录且有新的报警
        else:
            line = len(alert)+len(new_alert) - 10
            #新报警超过10行
            if line > 0:
                for i in range(line):
                    alert.pop()
                for i in range(len(new_alert)):
                    alert.insert(0, new_alert[i])
                for i in range(len(alert)):
                    alert[i]['no'] = i+1
            #新报警不超过10行
            else:
                for i in range(len(new_alert)):
                    alert.insert(0, new_alert[i])
                for i in range(10-len(alert)):
                    alert.append({'name': '', 'no': '', 'ip': '', 'alarm': 'null', 'request': '', 'num': 'single', 'time': '', 'type': '', 'response': ''})
                for i in range(len(alert)):
                    alert[i]['no'] = i+1
            alerts = []
            for i in range(5):
                alerts.append([alert[i], alert[i+5]])
            return alerts
    else:
        #有报警记录且无新的报警
        if new_alert == []:
            alerts = []
            for i in range(5):
                alerts.append([alert[i], alert[i+5]])
            return alerts
        #有报警记录且有新的报警
        else:
            #新报警是相同报警忽略 
            if new_alert[-1]['name'] == alert[0]['name'] and new_alert[-1]['time'] == alert[0]['time'] and new_alert[-1]['type'] == alert[0]['type']:
                alerts = []
                for i in range(5):
                    alerts.append([alert[i], alert[i+5]])
                return alerts
            #新报警是不同报警
            else:
                line = len(alert)+len(new_alert) - 10
                for i in range(line):
                    alert.pop()
                for i in range(len(new_alert)):
                    alert.insert(0, new_alert[i])
                for i in range(len(alert)):
                    alert[i]['no'] = i+1
                alerts = []
                for i in range(5):
                    alerts.append([alert[i], alert[i+5]])
                return alerts

def getSumData(name, node):
    '''根据名称及节点返回综合SLA报警数据后的数据'''
    sladata = getSlaData(name)
    nodedata = getNodeData(name, node)
    for i in sladata:
        for j in nodedata:
            if i['ip'] == j['ip']:
                if i['alarm'] == 'critical':
                    j['alarm'] = 'critical'
                elif i['alarm'] == 'warning':
                    if j['alarm'] == 'normal':
                        j['alarm'] = 'warning'
    return nodedata

if __name__ == '__main__':
    print getAlert()
