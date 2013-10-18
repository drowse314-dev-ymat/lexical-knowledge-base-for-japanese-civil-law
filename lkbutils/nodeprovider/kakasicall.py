# encoding: utf-8

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

def kakasi_series(targets, to_set=CharSet.ascii, stdin=None):
    targets = list(targets)
    procs = []
    procs.append(kakasi(targets.pop(), to_set, stdin=stdin))
    for target in targets:
        proc = kakasi(target, to_set, stdin=procs[-1].stdout)
        procs.append(proc)
    return procs

def romanize(text,
             targets=(CharSet.kanji, CharSet.katakana, CharSet.hiragana),
             encoding='utf-8'):
    """Romanize text."""
    echo_text = echo(text)
    init_iconv = iconv(encoding, 'euc-jp', stdin=echo_text.stdout)
    kakasi_procs = kakasi_series(targets, stdin=init_iconv.stdout)
    fin_iconv = iconv('euc-jp', encoding, kakasi_procs[-1].stdout)

    echo_text.stdout.close()
    init_iconv.stdout.close()
    for kakasi in kakasi_procs:
        kakasi.stdout.close()
    output = fin_iconv.communicate()[0]
    return output.strip()
