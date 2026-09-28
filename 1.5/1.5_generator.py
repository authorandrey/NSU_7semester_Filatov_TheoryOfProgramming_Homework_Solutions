"""Generate a multitape machine description for adding a constant."""

import sys


def generate_mt(k, m):
    """Generate a multitape machine description for adding k in base m."""
    digits = []
    temp = k
    if temp == 0:
        digits = [0]
    else:
        while temp > 0:
            digits.append(temp % m)
            temp //= m
    L = len(digits)  # noqa: N806
    k_digits = digits

    lines = []
    alphabet = ["#"] + [str(i) for i in range(m)]
    lines.append(f"alphabet = [{', '.join(alphabet)}]\n")
    lines.append("tapes = [ right ]\n")
    lines.append("START:")
    lines.append("\t# -> #R Add_0_0")

    for i in range(L):
        carries = [0] if i == 0 else [0, 1]
        for carry in carries:
            state = f"Add_{i}_{carry}"
            lines.append(f"{state}:")
            for d in range(m):
                sum_val = d + k_digits[i] + carry
                write_digit = sum_val % m
                new_carry = sum_val // m
                if i + 1 < L:
                    next_state = f"Add_{i+1}_{new_carry}"
                else:
                    next_state = "STOP" if new_carry == 0 else "Inc"
                lines.append(f"\t{d} -> {write_digit}R {next_state}")
            if i == 0:
                lines.append("\t# -> #H STOP")
            else:
                sum_val = k_digits[i] + carry
                write_digit = sum_val % m
                new_carry = sum_val // m
                if i + 1 < L:
                    next_state = f"Add_{i+1}_{new_carry}"
                else:
                    next_state = "STOP" if new_carry == 0 else "WriteOne"
                lines.append(f"\t# -> {write_digit}R {next_state}")

    lines.append("Inc:")
    for d in range(m - 1):
        lines.append(f"\t{d} -> {d+1}H STOP")
    lines.append(f"\t{m-1} -> 0R Inc")
    lines.append("\t# -> 1H STOP")
    lines.append("WriteOne:")
    lines.append("\t# -> 1H STOP")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) > 3:
        k = int(sys.argv[1])
        m = int(sys.argv[2])
        filename = sys.argv[3]
        with open(filename, "w", encoding="utf-8") as f:
            f.write(generate_mt(k, m))
    else:
        k = int(input("Input constant k to add: "))
        m = int(input("Input base m: "))
        print(generate_mt(k, m))