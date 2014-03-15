#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:ts=8 sts=4 sw=4 expandtab ft=python

#
# Copyright (c) 2013, chys <admin@CHYS.INFO>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
#   Neither the name of chys <admin@CHYS.INFO> nor the names of other
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

'''个人所得税、社保计算器

用法: salary-calc.py [选项...] <月薪> [<社保缴纳基数>]

选项:
    -c <city>, --city=<city>  选择城市
                              (默认城市可在配置文件中指定)

与网上多数计算器相比，本计算器有以下特点：
(1) 考虑社保缴纳上限；
(2) 考虑实际工资与社保缴纳基数不一致的问题；
(3) 通过配置文件自行设置各项缴纳比例。

配置文件 salary-calc.conf 放在本程序同一目录下，数据自行添加修改。
格式参见示例配置文件注释
'''

import configparser
import getopt
import os
import sys
import unicodedata


CONFIG_FILE = 'salary-calc.conf'


def usage(code=0):
    print(__doc__)
    sys.exit(code)


def fatal(*args, **kargs):
    if 'file' not in kargs:
        kargs['file'] = sys.stderr
    print(*args, **kargs)
    sys.exit(1)


def parse_salary(s):
    try:
        r = float(s)
        if r > 0:
            return r
    except ValueError:
        pass
    fatal('无效的工资: {}'.format(s))


class Tax:
    class Item:
        pass

    def __init__(self, config):
        '''创建对象，从配置文件中读取税率信息
        '''
        self._exempt = None
        self._table = []
        try:
            for (key, value) in config.items('tax'):
                if key == 'exempt':
                    self._exempt = parse_salary(value)
                else:
                    try:
                        item = Tax.Item()
                        item.lo, item.hi, item.pp = \
                            [float(v) for v in value.split()]
                    except ValueError:
                        fatal('配置文件错误: {}'.format(value))
                    self._table.append(item)
            if not self._exempt:
                fatal('未指定免税额')
        except configparser.NoSectionError:
            fatal('配置文件中找不到个人所得税信息')
            sys.exit(1)
        except configparser.Error:
            fatal('配置文件错误')

    def calc(self, salary):
        '''计算个人所得税，salary为计税额
        '''
        tax = 0
        if salary <= self._exempt:
            return tax
        salary -= self._exempt
        for item in self._table:
            if salary > item.lo:
                tax += min(item.hi - item.lo, salary - item.lo) * \
                    item.pp / 100
        return tax


class SocialSecurity:
    class Item:
        pass

    def __init__(self, config, city):
        '''创建对象，从配置文件中读取城市信息
        '''
        try:
            self._items = []
            for (name, data) in config.items(city):
                try:
                    item = SocialSecurity.Item()
                    item.name = name
                    item.employee_percent, item.employer_percent, \
                        item.upper, item.lower = \
                        [float(v) for v in data.split()]
                    self._items.append(item)
                except ValueError:
                    fatal('配置文件错误: {} = {}'.format(name, data))
        except configparser.NoSectionError:
            fatal('配置文件中找不到城市“{}”'.format(city))
        except configparser.Error:
            fatal('配置文件错误')

    def calc(self, base):
        '''计算社保，base为缴纳基数

        返回值：[ ('项目', 个人额, 单位额), .... ]
        '''
        res = []
        for item in self._items:
            itembase = min(item.upper, max(item.lower, base))
            res.append((item.name,
                        itembase * item.employee_percent / 100,
                        itembase * item.employer_percent / 100))
        return res


def wcwidth(s):
    return len(s) + sum((unicodedata.east_asian_width(c) in 'WF') for c in s)


def txtl(s, wid):
    return s + ' ' * max(0, wid - wcwidth(s))


def txtr(s, wid):
    return ' ' * max(0, wid - wcwidth(s)) + s


def _get_config_files():
    '''Return a list of possible config file names.'''
    exe = __file__

    # Same dir as this script
    yield os.path.join(os.path.dirname(exe), CONFIG_FILE)

    # Perhaps this script is run through a symlink..
    if os.path.islink(exe):
        exe = os.path.realpath(exe)
        yield os.path.join(os.path.dirname(exe), CONFIG_FILE)


def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "hc:", ["help", "city="])
    except getopt.GetoptError as e:
        fatal(e)

    city = None
    for o, a in opts:
        if o in ('-h', '--help'):
            usage(0)
        elif o in ('-c', '--city'):
            city = a
        else:
            assert False, "Unhandled option."

    if len(args) not in (1, 2):
        usage(1)

    salary = parse_salary(args[0])
    if len(args) > 1:
        security_base = parse_salary(args[1])
    else:
        security_base = salary

    config = configparser.RawConfigParser()
    for config_file in _get_config_files():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config.readfp(f)
                break
        except IOError:
            pass
    else:
        fatal('找不到配置文件: {}'.format(CONFIG_FILE))

    if not city:
        try:
            city = config.get('security', 'city')
        except configparser.Error:
            fatal('未指定城市')

    security = SocialSecurity(config, city).calc(security_base)
    security_employee_sum = sum(a for (_, a, _) in security)
    security_employer_sum = sum(a for (_, _, a) in security)
    security_sum = security_employee_sum + security_employer_sum
    taxable = salary - security_employee_sum
    tax = Tax(config).calc(taxable)

    print('== 所在城市 ==')
    print(city)
    print()

    print('== 税前工资 ==')
    print('{:.2f}'.format(salary))
    print()

    print('== 社保 ==')
    print('{}{}{}{}'.format(txtl('社保项目', 20), txtr('个人缴存额', 15),
                            txtr('单位缴存额', 15), txtr('总计', 15)))
    for (name, employee, employer) in security:
        print('{}{:>15.2f}{:>15.2f}{:>15.2f}'.format(txtl(name, 20),
                                                     employee,
                                                     employer,
                                                     employee + employer))
    print('{}{:>15.2f}{:>15.2f}{:>15.2f}'.format(txtl('总和', 20),
                                                 security_employee_sum,
                                                 security_employer_sum,
                                                 security_sum))
    print()

    print('== 个人所得税 ==')
    print('{}{:>15.2f}'.format(txtl('扣除社保后工资', 20), taxable))
    print('{}{:>15.2f}'.format(txtl('个人所得税', 20), tax))
    print()
    print('== 结论 ==')
    print('{}{:>15.2f}'.format(txtl('税前工资', 20), salary))
    print('{}{:>15.2f}'.format(txtl('到手工资', 20), taxable - tax))
    print('{}{:>15.2f}'.format(txtl('单位总支出', 20),
                               salary + security_employer_sum))


if __name__ == '__main__':
    main()
