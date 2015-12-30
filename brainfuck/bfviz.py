#!/usr/bin/python
#
# Creates a visualization of the execution of a Brainfuck program.
#
# Path of Brainfuck program accepted as command line argument. Input
# for program is read from stdin.
#
# The visualization is written to a series of frames from viz_0000.png
# up to at most viz_9999.png. These can be converted to a GIF89
# animation using imagemagick:
#        convert -delay 80 -loop 0 viz_*.png viz.gif
#

import sys
import re
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageSequence

FONT_PATH = "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"
FONT_SIZE = 20

def tokenize(code):
    return [t for t in re.compile(r'([,.[\]+-<>])').split(code)
            if len(t) > 0]

def scan(code, i, direction):
    depth = 1
    while depth:
        i += direction
        if code[i] == '[':
            depth += direction
        elif code[i] == ']':
            depth -= direction
    return i

def record_execute(code):
    p, mem, ip, out = 0, [0], -1, []

    states = []
    while True:
        states.append((p, mem[:], ip, out[:]))

        ip += 1
        if ip >= len(code):
            break

        if code[ip] == '>':
            p += 1
            if p >= len(mem):
                mem.append(0)
        elif code[ip] == '<':
            p -= 1
        elif code[ip] == '.':
            out.append(mem[p])
        elif code[ip] == ',':
            mem[p] = ord(sys.stdin.read(1))
        elif code[ip] == '+':
            mem[p] = (mem[p] + 1) % 256
        elif code[ip] == '-':
            mem[p] = (mem[p] + 255) % 256
        elif code[ip] == '[':
            if mem[p] == 0:
                states.append((p, mem[:], ip, out[:]))
                ip = scan(code, ip, 1)
        elif code[ip] == ']':
            if mem[p] != 0:
                states.append((p, mem[:], ip, out[:]))
                ip = scan(code, ip, -1)

    return states

def render(code, states):
    mem_len = max(len(mem) for _, mem, __, ___ in states)
    code_len = sum(len(c) for c in code)
    out_len = max(len(out) for _, __, ___, out in states)

    code_off = [0]
    for c in code:
        code_off.append(code_off[-1] + len(c))

    for p, mem, ip, out in states:
        print (''.join(code) + " " +
               ' '.join("%2x" % x for x in mem) + "  0" * (mem_len - len(mem)))
        print (" " * ip + ("^" if p >= 0 else "") + " " * (code_len - ip - 1) +
               " " + "   " * p + " ^")

    print mem_len, code_len

def render_state(code, state, mem_len, out_len, font, csize, size):

    im = Image.new('RGBA', size, (255, 255, 255, 255))
    draw = ImageDraw.Draw(im)

    sp, smem, sip, sout = state

    for i, c in enumerate(code):
        xy = (i * csize[0], 0)
        fill = 0 if i != sip else 255, 0, 0, 255

        draw.text(xy, c, font=font, fill=fill)

    for i, x in enumerate(smem + [0] * (mem_len - len(smem))):
        xy = (i * csize[0] * 4, csize[1])
        fill = 0 if i != sp else 255, 0, 0, 255

        draw.text(xy, "%3d" % x, font=font, fill=fill)

    del draw
    return im

def render(code, states, max_width=640):
    mem_len = max(len(mem) for _, mem, __, ___ in states)
    code_len = sum(len(c) for c in code)
    out_len = max(len(out) for _, __, ___, out in states)

    font = ImageFont.truetype(FONT_PATH, 20)

    char_sizes = map(font.getsize,
                     [',', '.', '[', ']', '<', '>', '+', '-'] +
                     map(chr, range(ord('0'), ord('9') + 1)))
    csize = (max(cs[0] for cs in char_sizes),
             max(cs[1] for cs in char_sizes))

    for i, s in enumerate(states):
        frame = render_state(code, s, mem_len, out_len, font, csize, (640, 480))
        frame.save(open("viz_%04d.png" % i, "w"), "PNG")


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s <source>\n" % sys.argv[0])
        return 1

    code = tokenize(open(sys.argv[1]).read().strip())

    render(code, record_execute(code))

    return 0

if __name__ == "__main__":
    sys.exit(main())
