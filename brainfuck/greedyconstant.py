#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Code generator that given input S and integer N prints a brainfuck
# program that outputs S using N memory cells
#
# Mats Linander
# 2014-04-27


import sys
import math
import random

def setup_random(s, n):
    """Generates random memory initialization code.

    The generated code initializes the cells to hold values up to
    roughly the max value of s. The state of the n memory cells post
    execution is also returned.

    @return (code, mem, p)
    """

    code = []

    order = [random.randrange(1,n) for _ in range(1, n)]
    random.shuffle(order)

    x = max(s) / (n - 1)
    base = x + random.randrange(-int(math.sqrt(x)), int(math.sqrt(x)))

    code.append('+' * base)
    code.append('[-')
    for i in order:
        code.append('>')
        code.append('+' * i)
    code.append('<' * (n - 1))
    code.append(']')

    return (''.join(code), [0] + [i*base for i in order], 0)

def output(s, mem=[0,0], p=0):
    """Generate code that outputs s given some memory state."""

    assert(len(mem) > 1)

    code = []

    for c in s:

        best = None
        best_i = None
        best_len = float('inf')
        for i in range(len(mem)):
            dist = i - p
            diff = c - mem[i]
            snippet = (('<' if dist < 0 else '>') * abs(dist) +
                       ('-' if diff < 0 else '+') * abs(diff))
            if len(snippet) < best_len:
                best = snippet
                best_len = len(best)
                best_i = i

        code.append(best)
        code.append('.')
        p = best_i
        mem[p] = c

    code.append('<' * p)

    return ''.join(code)


def constant(s, n=5, verbose=0):

    best = None
    best_len = float('inf')

    for _ in xrange(100000):
        code, mem, p = setup_random(s, n)
        code += output(s, mem, p)
        if len(code) < best_len:
            if verbose:
                print "best %d" % len(code)
            best = code
            best_len = len(best)

    pre = '% *0' + ' 0' * (n-1)
    post = '% *' + ' '.join('%d' % mem[i] for i in range(len(mem)))
    return pre + '\n' + ''.join(best) + '\n' + post

def main():
    n = 6
    if len(sys.argv) > 1:
        n = max(2, int(sys.argv[1]))

    target = map(ord, sys.stdin.read())
    program = constant(target, n, verbose=1)
    sys.stdout.write(program)
    sys.stdout.write('\n')

    return 0

if __name__ == "__main__":
    sys.exit(main())

