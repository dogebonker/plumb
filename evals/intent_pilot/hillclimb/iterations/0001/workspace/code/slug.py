def encode_project(project):
    # Governing rule (sources/decision.md): every character outside ASCII
    # a-z, A-Z, 0-9 becomes one dash per UTF-16 code unit, so an astral
    # character (code point above U+FFFF) becomes two dashes. No NFC
    # normalization is applied to the session path.
    out = []
    for ch in project:
        if ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ("0" <= ch <= "9"):
            out.append(ch)
        elif ord(ch) > 0xFFFF:
            out.append("--")
        else:
            out.append("-")
    return "".join(out)
