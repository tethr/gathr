"""
Stolen shamelessly from Karl (http://karlproject.org).
"""
import os
import re

_convert_to_dashes = re.compile(r"""[\s/:"']""") # ' damn you emacs
_safe_char_check = re.compile(r"[\w.-]+$")
_reduce_dashes = re.compile(r"-{2,}")

_ascii_mapping = {
    # This is pulled from plone.i18n.normalizer.  It is a partial mapping
    # of Unicode characters that look similar to ASCII letters.  Non-ASCII
    # characters not listed here will be encoded in hexadecimal.

    # Latin characters with accents, etc.
    138 : 's', 140 : 'O', 142 : 'z', 154 : 's', 156 : 'o', 158 : 'z',
    159 : 'Y', 192 : 'A', 193 : 'A', 194 : 'A', 195 : 'a', 196 : 'AE',
    197 : 'Aa', 198 : 'AE', 199 : 'C', 200 : 'E', 201 : 'E', 202 : 'E',
    203 : 'E', 204 : 'I', 205 : 'I', 206 : 'I', 207 : 'I', 208 : 'Th',
    209 : 'N', 210 : 'O', 211 : 'O', 212 : 'O', 213 : 'O', 214 : 'OE',
    215 : 'x', 216 : 'O', 217 : 'U', 218 : 'U', 219 : 'U', 220 : 'UE',
    222 : 'th', 221 : 'Y', 223 : 'ss', 224 : 'a', 225 : 'a', 226 : 'a',
    227 : 'a', 228 : 'ae', 229 : 'aa', 230 : 'ae', 231 : 'c',
    232 : 'e', 233 : 'e', 234 : 'e', 235 : 'e', 236 : 'i', 237 : 'i',
    238 : 'i', 239 : 'i', 240 : 'th', 241 : 'n', 242 : 'o', 243 : 'o',
    244 : 'o', 245 : 'o', 246 : 'oe', 248 : 'oe', 249 : 'u', 250 : 'u',
    251 : 'u', 252 : 'ue', 253 : 'y', 254 : 'Th', 255 : 'y' ,
    # Turkish
    286 : 'G', 287 : 'g', 304 : 'I', 305 : 'i', 350 : 'S', 351 : 's',
    # Polish
    321 : 'L', 322 : 'l',
    # French
    339: 'oe',
    # Greek
    902: 'A', 904: 'E', 905: 'H', 906: 'I', 908: 'O', 910: 'Y', 911: 'O',
    912: 'i', 913: 'A', 914: 'B', 915: 'G', 916: 'D', 917: 'E', 918: 'Z',
    919: 'I', 920: 'Th', 921: 'I', 922: 'K', 923: 'L', 924: 'M', 925: 'N',
    926: 'Ks', 927: 'O', 928: 'P', 929: 'R', 931: 'S', 932: 'T', 933: 'Y',
    934: 'F', 935: 'Ch', 936: 'Ps', 937: 'O', 938: 'I', 939: 'Y', 940: 'a',
    941: 'e', 942: 'i', 943: 'i', 944: 'y', 945: 'a', 946: 'b', 947: 'g',
    948: 'd', 949: 'e', 950: 'z', 951: 'i', 952: 'th', 953: 'i', 954: 'k',
    955: 'l', 956: 'm', 957: 'n', 958: 'ks', 959: 'o', 960: 'p', 961: 'r',
    962: 's', 963: 's', 964: 't', 965: 'y', 966: 'f', 967:'ch', 968: 'ps',
    969: 'o', 970: 'i', 971: 'y', 972: 'o', 973: 'y', 974: 'o',
    # Russian
    1081 : 'i', 1049 : 'I', 1094 : 'c', 1062 : 'C',
    1091 : 'u', 1059 : 'U', 1082 : 'k', 1050 : 'K',
    1077 : 'e', 1045 : 'E', 1085 : 'n', 1053 : 'N',
    1075 : 'g', 1043 : 'G', 1096 : 'sh', 1064 : 'SH',
    1097 : 'sch', 1065 : 'SCH', 1079 : 'z', 1047 : 'Z',
    1093 : 'h', 1061 : 'H', 1098 : '', 1066 : '',
    1092 : 'f', 1060 : 'F', 1099 : 'y', 1067 : 'Y',
    1074 : 'v', 1042 : 'V', 1072 : 'a', 1040 : 'A',
    1087 : 'p', 1055 : 'P', 1088 : 'r', 1056 : 'R',
    1086 : 'o', 1054 : 'O', 1083 : 'l', 1051 : 'L',
    1076 : 'd', 1044 : 'D', 1078 : 'zh', 1046 : 'ZH',
    1101 : 'e', 1069 : 'E', 1103 : 'ya', 1071 : 'YA',
    1095 : 'ch', 1063 : 'CH', 1089 : 's', 1057 : 'S',
    1084 : 'm', 1052 : 'M', 1080 : 'i', 1048 : 'I',
    1090 : 't', 1058 : 'T', 1100 : '', 1068 : '',
    1073 : 'b', 1041 : 'B', 1102 : 'yu', 1070 : 'YU',
    1105 : 'yo', 1025 : 'YO',
}

def _encode_name(name):
    """Encode the Unicode characters in a name"""
    res = []
    for c in name:
        if _safe_char_check.match(c):
            res.append(c)
            continue
        n = ord(c)
        if n < 128:
            # Discard ASCII symbols like '?', '$', etc.
            continue
        encoded = _ascii_mapping.get(n)
        if not encoded:
            encoded = '-%x-' % n
        res.append(encoded)
    return ''.join(res)


def make_name(context, title, raise_error=True):
    """Make a correct __name__ that is unique in the context"""
    name = _convert_to_dashes.sub("-", title)
    if not _safe_char_check.match(name):
        name = _encode_name(name)
    name = _reduce_dashes.sub("-", name)

    if not name and raise_error:
        raise ValueError('The name must not be empty')

    # Make sure the name is unique in the context
    if name in context and raise_error:
        fmt = "The name '%s' already exists in folder '%s'"
        msg = fmt % (name, context.__name__)
        raise ValueError(msg)
    else:
        return name


def make_unique_name(context, title):
    """Make a correct __name__ that is unique in the context.

    Try until an empty name is found (or be debunked by a
    conflict error).
    """
    unique_name, postfix = make_unique_name_and_postfix(context, title)
    return unique_name


def make_unique_name_and_postfix(context, title):
    """Make a correct __name__ that is unique in the context.
    Also return the postfix that can be used to modulate the
    title and filename of the file objects.

    Try until an empty name is found (or be debunked by a
    conflict error).
    """

    postfix = ''
    dashpostfix = ''
    counter = 1

    base, ext = os.path.splitext(title)

    while True:
        try:
            unique_name = make_name(context, base + dashpostfix + ext)
            break
        except ValueError:
            postfix = '%i' % (counter, )
            dashpostfix = '-' + postfix
            counter += 1
            # This could actually cause all our
            # processes hang forever :)

    return unique_name, postfix
