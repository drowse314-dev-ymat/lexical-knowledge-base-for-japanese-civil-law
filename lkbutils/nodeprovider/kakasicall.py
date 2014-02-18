# encoding: utf-8

import re
import subprocess
import collections


kakasi_charset_identifiers = {
    'ascii': 'a',
    'jisroman': 'j',
    'graphic': 'g',
    'kana': 'k',
    'kigou': 'E',
    'katakana': 'K',
    'hiragana': 'H',
    'kanji': 'J',
}

CharSet = collections.namedtuple(
    'KakasiCharSet',
    sorted(kakasi_charset_identifiers.keys()),
)(
    *[
        kakasi_charset_identifiers[key] for key
        in sorted(kakasi_charset_identifiers.keys())
    ]
)

# Valid sets for romanization destination.
roman_sets = [
    CharSet.ascii, CharSet.jisroman,
]
# Valid conversion order for romanization.
conversion_order = [
    CharSet.katakana, CharSet.hiragana,
    CharSet.kanji, CharSet.hiragana, CharSet.katakana,
]


def echo(text):
    p = subprocess.Popen(
        ['echo', text],
        stdout=subprocess.PIPE,
    )
    return p

def iconv(from_code, to_code, stdin=None):
    p = subprocess.Popen(
        [
            'iconv',
            '-f', from_code,
            '-t', to_code,
        ],
        stdin=stdin, stdout=subprocess.PIPE,
    )
    return p

def kakasi(from_set, to_set, stdin=None):
    p = subprocess.Popen(
        [
            'kakasi',
            '-' + from_set + to_set,
        ],
        stdin=stdin, stdout=subprocess.PIPE,
    )
    return p

def kakasi_romanize_series(to_set=CharSet.ascii, stdin=None):
    if to_set not in roman_sets:
        raise ValueError('invalid destination: "{}"'.format(to_set))
    procs = []
    prev_stdin = stdin

    order = conversion_order[:]
    order.append(to_set)
    for from_set, to_set in zip(order, order[1:]):
        proc = kakasi(from_set, to_set, stdin=prev_stdin)
        procs.append(proc)
        prev_stdin = proc.stdout

    return procs

def romanize(text, encoding='utf-8'):
    """Romanize text."""
    echo_text = echo(text)
    init_iconv = iconv(encoding, 'euc-jp', stdin=echo_text.stdout)
    kakasi_romanize_procs = kakasi_romanize_series(stdin=init_iconv.stdout)
    fin_iconv = iconv('euc-jp', encoding, kakasi_romanize_procs[-1].stdout)

    echo_text.stdout.close()
    init_iconv.stdout.close()
    for kakasi in kakasi_romanize_procs:
        kakasi.stdout.close()
    output = fin_iconv.communicate()[0]
    return _prettify(output)

def _prettify(kakasi_output):
    kakasi_output = kakasi_output.strip()
    kakasi_output = _handle_euphonic(kakasi_output)
    return kakasi_output

re_euphonic_repr = re.compile(u'(.)[\'\^]')
def _handle_euphonic(kakasi_output):
    return re_euphonic_repr.sub(u'\\1\\1', kakasi_output)
