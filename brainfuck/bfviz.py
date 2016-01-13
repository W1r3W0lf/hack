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


def record_execute(code,
                   split_mem_change=False,
                   split_output=False):
    """Executes brainfuck code and records states.

    State is encoded as a 4 tuple of pointer, memory area, instruction
    pointer and output so far produced. One such tuple is added to the
    return value for each instruction executed.

    If split_mem_change is set, an additional state frame is added
    after instruction pointer is moved but before memory or pointer is
    updated for instructions that modify pointer or memory.

    If split_output is set, same thing but when output's written.
    """

    p, mem, ip, out = 0, [0], -1, []

    states = []
    while True:
        states.append((p, mem[:], ip, out[:]))

        ip += 1
        if ip >= len(code):
            break

        if split_mem_change and code[ip] in ('<', '>', ',', '+', '-'):
            states.append((p, mem[:], ip, out[:]))
        if split_output and code[ip] == '.':
            states.append((p, mem[:], ip, out[:]))

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
    states.append((p, mem[:], -1, out[:]))

    return states


def render_code(code, ip, font, csize):
    im = Image.new('RGBA', (len(code) * csize[0], int(csize[1] * 1.5)),
                   (255, 255, 255, 255))
    draw = ImageDraw.Draw(im)
    for i, c in enumerate(code):
        draw.text((csize[0] * i, 0), c, font=font,
                  fill=(0 if i != ip else 255, 0, 0, 255))
    del draw
    return im


def render_mem(mem, p, mem_len, font, csize):
    mem = mem + [0] * (mem_len - len(mem))
    width = font.getsize("mem: " + " ".join("%d" % x for x in mem))[0]
    im = Image.new('RGBA', (width, int(csize[1] * 1.5)),
                   (255, 255, 255, 255))
    draw = ImageDraw.Draw(im)

    draw.text((0, 0), "mem:", font=font, fill=(0, 0, 0, 255))
    xoff = font.getsize("mem: ")[0]
    for i, x in enumerate(mem + [0] * (mem_len - len(mem))):
        fill = 0, 0, 0, 255
        if i == p and mem_len > 1:
            fill = 255, 0, 0, 255
        text = "%d " % x
        draw.text((xoff, 0), text, font=font, fill=fill)
        xoff += font.getsize(text)[0]
    del draw
    return im


def render_out(out, font, csize):
    text = "out: " + " ".join("%d" % x for x in out)
    im = Image.new('RGBA', (font.getsize(text)[0], int(csize[1] * 1.5)),
                   (255, 255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.text((0, 0), text, font=font, fill=(0, 0, 0, 255))
    del draw
    return im


def render_state(code, state, mem_len, out_len, font, csize):
    sp, smem, sip, sout = state

    im_code = render_code(code, sip, font, csize)
    im_mem = render_mem(smem, sp, mem_len, font, csize)
    im_out = render_out(sout, font, csize)

    size = (max(im_code.size[0], im_mem.size[0]),
            im_code.size[1] + im_mem.size[1] + im_out.size[1])

    im = Image.new('RGBA', size, (255, 255, 255, 255))
    im.paste(im_code, (0, 0))
    im.paste(im_mem, (0, im_code.size[1]))
    im.paste(im_out, (0, im_code.size[1] + im_mem.size[1]))

    return im


def render(code, states, max_width=640):
    mem_len = max(len(mem) for _, mem, __, ___ in states)
    code_len = sum(len(c) for c in code)
    out_len = max(len(out) for _, __, ___, out in states)

    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    char_sizes = map(font.getsize,
                     [',', '.', '[', ']', '<', '>', '+', '-'] +
                     map(chr, range(ord('0'), ord('9') + 1)))
    csize = (max(cs[0] for cs in char_sizes),
             max(cs[1] for cs in char_sizes))

    for i, s in enumerate(states):
        frame = render_state(code, s, mem_len, out_len, font, csize)
        frame.save(open("viz_%04d.png" % i, "w"), "PNG")


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s <source>\n" % sys.argv[0])
        return 1

    code = tokenize(open(sys.argv[1]).read().strip())

    render(code, record_execute(code, True, True))

    return 0

if __name__ == "__main__":
    sys.exit(main())
