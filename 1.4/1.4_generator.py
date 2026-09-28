"""Generate a Turing machine description for adding k."""


def generate_mt(k):
    """Return a Turing machine description that adds k to its input."""
    bits = []
    temp = k
    while temp > 0:
        bits.append(temp & 1)
        temp >>= 1
    if not bits:
        bits = [0]
    L = len(bits)  # noqa: N806
    k_bits = bits

    lines = []
    lines.append(
        f"// This programm adds {k} to the inputted word of the number "
        "in inversed binary format."
    )
    lines.append("alphabet = [#, 0, 1]\n")
    lines.append("tapes = [ right ]\n")
    lines.append("START:")
    lines.append("\t# -> #R Add_0_0")

    for i in range(L):
        carries = [0] if i == 0 else [0, 1]
        for carry in carries:
            state = f"Add_{i}_{carry}"
            lines.append(f"{state}:")
            sum0 = 0 + k_bits[i] + carry
            w0 = sum0 % 2
            nc0 = sum0 // 2
            if i + 1 < L:
                next0 = f"Add_{i+1}_{nc0}"
            else:
                next0 = "STOP" if nc0 == 0 else "Inc"
            lines.append(f"\t0 -> {w0}R {next0}")
            sum1 = 1 + k_bits[i] + carry
            w1 = sum1 % 2
            nc1 = sum1 // 2
            if i + 1 < L:
                next1 = f"Add_{i+1}_{nc1}"
            else:
                next1 = "STOP" if nc1 == 0 else "Inc"
            lines.append(f"\t1 -> {w1}R {next1}")
            if i == 0:
                lines.append("\t# -> #H STOP")
            else:
                sum_hash = k_bits[i] + carry
                wh = sum_hash % 2
                nch = sum_hash // 2
                if i + 1 < L:
                    next_hash = f"Add_{i+1}_{nch}"
                else:
                    next_hash = "STOP" if nch == 0 else "WriteOne"
                lines.append(f"\t# -> {wh}R {next_hash}")

    lines.append("Inc:")
    lines.append("\t0 -> 1H STOP")
    lines.append("\t1 -> 0R Inc")
    lines.append("\t# -> 1H STOP")
    # WriteOne
    lines.append("WriteOne:")
    lines.append("\t# -> 1H STOP")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        k = int(sys.argv[1])
        filename = sys.argv[2]
        with open(filename, "w", encoding="utf-8") as f:
            f.write(generate_mt(k))
    else:
        k = int(input("Input k: "))
        print(generate_mt(k))
