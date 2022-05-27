from typing import List


def uint(n: str | int | List[bool] | List[int] | bytes | None) -> int:
    val: int = 0
    match n:
        case str():
            n = n.replace(' ', '')
            try:
                val = int(n, 2)
            except:
                try:
                    val = int(n, 10)
                except:
                    try:
                        val = int(n, 16)
                    except:
                        raise ValueError(
                            "The string in argument n is not an integer")
            return val
        case [*_data] if all(isinstance(i, bool) for i in _data):
            a = [1 if v else 0 for v in _data]
            for v in a:
                val <<= 1
                val |= v
            return val
        case [*_data] if all(isinstance(i, int) for i in _data):
            a = [1 if v > 0 else 0 for v in _data]
            for v in a:
                val <<= 1
                val |= v
            return val
        case int():
            return n
        case bytes():
            for i in n:
                val <<= 8
                val += i
            return val
        case None:
            return 0
        case _:
            raise ValueError(f"Invalid type passed in argument n({type(n)})")


def byteFormat(n: int, format: str = "$n$", mode: str = 'h') -> str:
    n = uint(n)
    if mode.lower() != 'b' and mode.lower() != 'h':
        mode = 'h'
    st = format.find('$')
    en = format[st+1:].find('$')+st+1

    r = format[st+1:en]

    size = -1
    arg = ''
    if r.find(':') != -1:
        try:
            size = int(r[r.find(':')+1:])
        except:
            arg = r[r.find(':')+1:]

    n = bin(n)[2:] if mode == 'b' else hex(n)[2:].upper()
    if mode == 'b' and arg == 'c':
        if len(n) % 8 != 0:
            size = (len(n)+8)-(len(n) % 8)
    if mode == 'h' and arg == 'c':
        if len(n) % 2 != 0:
            size = (len(n)+1)
    if size != -1:
        n = (('0'*size)+n)[-size:]
    return format[:st]+n+format[en+1:]


def itoil(n: int, complete: int | None = None) -> List[int]:
    n = uint(n)
    r = []
    while(n > 0):
        r.append(n & 1)
        n >>= 1
    r.reverse()
    if complete is None or complete==len(r):
        if len(r)==0:
            return [False]
        else:
            return r
    elif complete<len(r):
        return r[-complete:]
    else:
        return ([0]*(complete-len(r)))+r


def itobl(n: int, complete: int | None = None) -> List[bool]:
    n = uint(n)
    return [False if v <= 0 else True for v in itoil(n,complete)]


def itob(n: int) -> bytes:
    n = uint(n)
    r = []
    while(n > 0):
        r.append(n & 0xFF)
        n >>= 8
    r.reverse()
    return bytes(r) if len(r) != 0 else bytes([0])


def bit_size(n: int) -> int:
    n = uint(n)
    return sum((1 for v in itoil(n)))


def bit_append(a: int, b: int) -> int:
    a = uint(a)
    b = uint(b)
    return (a << bit_size(b)) | b


def bit_reverse(n: int) -> int:
    n = uint(n)
    r = itoil(n)
    r.reverse()
    return uint(n)


def bit_sub(n: int, start: int | None = None, end: int | None = None) -> int:
    n = uint(n)
    return (uint(itoil(n)[start:end]))


def bit_get(n: int, index: int = 0) -> int:
    n = uint(n)
    return itoil(n,index+1)


def bit_set(n: int, index: int = 0, v: bool | int | None = 1) -> int:
    n = uint(n)
    match v:
        case int():
            a = itoil(n)
            a[index] = v
            return uint(a)
        case True:
            return bit_set(n, index, 1)
        case False:
            return bit_set(n, index, 0)
        case None:
            return bit_set(n, index, 0)
        case _:
            return bit_set(n, index, uint(v))


def bit_chop(n: int, allsize: int, section_size: int, end: int) -> int:
    rest = allsize-end
    return (n & (uint((section_size)*'1') << rest)) >> rest


def bit_mask(size: int) -> int:
    return ((1 << size)-1)


def bit_negate(n: int) -> int:
    n = uint(n)
    n = itobl(n)
    return uint([not v for v in n])
