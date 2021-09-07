import sys
import re
import subprocess
from collections import OrderedDict
import string

class Transaction():
    account = ""
    date = ""
    memo = ""
    category = ""
    amount = ""
    balance = ""

def main(argv):
    file = argv[0]
    f = open(file, 'r')

    transactions = []

    for line in f:
        m = re.search('(D[0-9]{5}), (\d+/\d+/\d+), (.*), (.*), (.*), (.*)', line)
        if m:
            #[month,day,year] = [int(n) for n in string.split(m.group(2),'/')]
            #t.date = datetime.datetime(year, month, day, 14, 0, 0, 0)
            t = Transaction()
            t.account = m.group(1)
            t.date = m.group(2)
            t.memo = m.group(3)
            t.category = m.group(4)
            t.amount = str(m.group(5))
            t.balance = m.group(6)

            transactions.append(t)

    for t in transactions:
        #print t.account, t.date, t.memo, t.category, t.amount, t.balance
        subprocess.call(['python', '..\\..\\manage.py ', 'apply_transaction', t.account, t.date, t.memo, t.category, '--', t.amount, t.balance])

if __name__=='__main__':
    main(sys.argv[1:])
