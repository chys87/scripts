#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:ts=8 sts=4 sw=4 expandtab ft=python

#
# Copyright (c) 2013, 2017, chys <admin@CHYS.INFO>
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

import argparse
from collections import namedtuple
import configparser
import getopt
import os
import sys
import unicodedata


CONFIG_FILE = 'salary-calc.conf'


class Tax:
    __slots__ = '_exempt', '_table'

    Item = namedtuple('Item', 'lo pp deduct')

    def __init__(self, config):
        '''创建对象，从配置文件中读取税率信息
        '''
        self._exempt = None
        self._table = []

        last_pp = 0
        last_deduct = 0

        try:
            for (key, value) in config.items('tax'):
                if key == 'exempt':
                    self._exempt = float(value)
                else:
                    try:
                        lo, pp = [float(v) for v in value.split()]
                    except ValueError:
                        sys.exit('配置文件错误: {}'.format(value))

                    deduct = lo * (pp - last_pp) / 100 + last_deduct
                    self._table.append(self.Item(lo, pp, deduct))
                    last_pp = pp
                    last_deduct = deduct

            if not self._exempt:
                sys.exit('未指定免税额')
        except configparser.NoSectionError:
            sys.exit('配置文件中找不到个人所得税信息')
        except configparser.Error:
            sys.exit('配置文件错误')

    def calc(self, salary, year_end=False):
        '''计算个人所得税，salary为计税额
        '''
        if year_end:
            tax_reference = salary / 12
            exempt = 0
        else:
            tax_reference = salary
            exempt = self._exempt

        tax = 0
        if salary <= exempt:
            return tax
        salary -= exempt

        # [i].lo < tax_reference <= [j].lo
        table = self._table
        i = 0
        j = len(table)
        while j - i > 1:
            m = (i + j) // 2
            if table[m].lo < tax_reference:
                i = m
            else:
                j = m

        item = table[i]

        # 年终奖：速算扣除数不乘以12（神奇的中国税务！）
        return salary * item.pp / 100 - item.deduct


class SocialSecurity:
    __slots__ = '_items',

    Item = namedtuple('Item',
                      'name employee_percent employer_percent upper lower')

    def __init__(self, config, city):
        '''创建对象，从配置文件中读取城市信息
        '''
        try:
            self._items = []
            for (name, data) in config.items(city):
                try:
                    employee_percent, employer_percent, \
                        upper, lower = \
                        [float(v) for v in data.split()]
                except ValueError:
                    sys.exit('配置文件错误: {} = {}'.format(name, data))
                self._items.append(self.Item(
                    name, employee_percent, employer_percent, upper, lower))
        except configparser.NoSectionError:
            sys.exit('配置文件中找不到城市“{}”'.format(city))
        except configparser.Error:
            sys.exit('配置文件错误')

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
    parser = argparse.ArgumentParser(
        description='个人所得税、社保计算器',
        epilog='''与网上多数计算器相比，本计算器有以下特点：
(1) 考虑社保缴纳上限；
(2) 考虑实际工资与社保缴纳基数不一致的问题；
(3) 通过配置文件自行设置各项缴纳比例；
(4) 支持年终奖计算。

配置文件 salary-calc.conf 放在本程序同一目录下，数据自行添加修改。
格式参见示例配置文件注释''',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-c', '--city',
                        help='城市 (默认城市可在配置文件中指定)')
    parser.add_argument('-y', '--year-end', action='store_true', default=False,
                        help='按年终奖计算')
    parser.add_argument('salary', type=float, help='税前工资')
    parser.add_argument('security_base', type=float, nargs='?',
                        help='社保基数')
    args = parser.parse_args()

    city = args.city
    salary = args.salary
    security_base = args.security_base or salary
    year_end = args.year_end

    config = configparser.RawConfigParser()
    for config_file in _get_config_files():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config.readfp(f)
                break
        except FileNotFoundError:
            pass
    else:
        sys.exit('找不到配置文件: {}'.format(CONFIG_FILE))

    if not city:
        try:
            city = config.get('security', 'city')
        except configparser.Error:
            sys.exit('未指定城市')

    if year_end:
        security = []
    else:
        security = SocialSecurity(config, city).calc(security_base)
    security_employee_sum = sum(a for (_, a, _) in security)
    security_employer_sum = sum(a for (_, _, a) in security)
    security_sum = security_employee_sum + security_employer_sum
    taxable = salary - security_employee_sum
    tax = Tax(config).calc(taxable, year_end=year_end)

    if not year_end:
        print('== 所在城市 ==')
        print(city)
        print()

    print('== 税前工资 ==')
    print('{:.2f}'.format(salary))
    print()

    if not year_end:
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
    if not year_end:
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
