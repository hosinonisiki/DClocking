import numpy as np
import scipy.signal as signal
import fixed

# Dedicated for 4th order IIR of parallel biquad structure with 4-sla
# Optimal range and precisions:
# b: Q3.24, a: Q2.25, interm: Q4.26 for both x and y

def golden_ratio_search(left, right, func, tol=1e-5):
    phi = (1 + np.sqrt(5)) / 2
    resphi = 2 - phi

    c = left + resphi * (right - left)
    d = right - resphi * (right - left)

    while abs(right - left) > tol:
        if func(c) < func(d):
            right = d
            d = c
            c = left + resphi * (right - left)
        else:
            left = c
            c = d
            d = right - resphi * (right - left)

    return (left + right) / 2

def partial_fraction_decomposition(b, a):
    # Perform partial fraction decomposition
    r, p, k = signal.residuez(b, a)
    return r, p, k

def combine_pole_pairs(r, p, k):
    b_0 = np.array([2 * np.real(r[0]), -2 * np.real(r[0] * np.conj(p[0])), 0])
    a_0 = np.array([1, -2 * np.real(p[0]), np.abs(p[0])**2])
    b_1 = np.array([2 * np.real(r[2]), -2 * np.real(r[2] * np.conj(p[2])), 0])
    a_1 = np.array([1, -2 * np.real(p[2]), np.abs(p[2])**2])
    return b_0, a_0, b_1, a_1, k

def balance_direct(b_0, a_0, b_1, a_1, k, strategy = "uniform"):
    # Absorb the gain k into the two biquads to balance the coefficients
    if strategy == "uniform":
        k_0 = k / 2
        k_1 = k / 2
    elif strategy == "min_max":
        def max_coef(k_0):
            k_1 = k - k_0
            return max(np.max(np.abs(b_0 + k_0 * a_0)), np.max(np.abs(b_1 + k_1 * a_1)))
        k_0 = golden_ratio_search(0, k, max_coef)
        k_1 = k - k_0
    elif strategy == "balanced_gain":
        gain_0 = np.sum(b_0) / np.sum(a_0)
        gain_1 = np.sum(b_1) / np.sum(a_1)
        k_0 = (k + gain_1 - gain_0) / 2
        k_1 = (k - gain_1 + gain_0) / 2
    elif strategy == "balanced_norm":
        def max_norm(k_0):
            k_1 = k - k_0
            return max(np.sum(np.abs(b_0 + k_0 * a_0)), np.sum(np.abs(b_1 + k_1 * a_1)))
        k_0 = golden_ratio_search(0, k, max_norm)
        k_1 = k - k_0
    elif strategy == "balanced_pole":
        w_0 = 1 - np.sqrt(np.abs(a_0[2]))
        w_1 = 1 - np.sqrt(np.abs(a_1[2]))
        k_0 = k * w_0 / (w_0 + w_1)
        k_1 = k - k_0
    else:
        raise ValueError("Unknown strategy")
    b_0 += k_0 * a_0
    b_1 += k_1 * a_1
    return b_0, a_0, b_1, a_1
    
def scatter_look_ahead(b_0, a_0, b_1, a_1):
    A = np.array([[1, 0, 0, 0, 0, 0],
                  [a_0[1], 1, 0, 0, 0, 0],
                  [a_0[2], a_0[1], 1, 0, 0, 0],
                  [0, 0, a_0[2], a_0[1], 1, 0],
                  [0, 0, 0, a_0[2], a_0[1], 1],
                  [0, 0, 0, 0, a_0[2], a_0[1]]])
    B = np.array([-a_0[1], -a_0[2], 0, 0, 0, 0])
    multiplier = np.linalg.solve(A, B)
    multiplier = np.concatenate(([1], multiplier))
    b_0 = np.convolve(b_0, multiplier)
    a_0 = np.convolve(a_0, multiplier)
    A = np.array([[1, 0, 0, 0, 0, 0],
                  [a_1[1], 1, 0, 0, 0, 0],
                  [a_1[2], a_1[1], 1, 0, 0, 0],
                  [0, 0, a_1[2], a_1[1], 1, 0],
                  [0, 0, 0, a_1[2], a_1[1], 1],
                  [0, 0, 0, 0, a_1[2], a_1[1]]])
    B = np.array([-a_1[1], -a_1[2], 0, 0, 0, 0])
    multiplier = np.linalg.solve(A, B)
    multiplier = np.concatenate(([1], multiplier))
    b_1 = np.convolve(b_1, multiplier)
    a_1 = np.convolve(a_1, multiplier)
    return b_0, a_0, b_1, a_1

def get_IIR_parameters(ftype, cutoff_frequency, sample_frequency):
    b, a = signal.iirfilter(4, cutoff_frequency / sample_frequency * 2, btype='lowpass', ftype=ftype, rs=80, rp = 0.05)

    r, p, k = partial_fraction_decomposition(b, a)
    b_0, a_0, b_1, a_1, k = combine_pole_pairs(r, p, k)
    match ftype:
        case "butter":
            strategy = "balanced_pole"
        case "ellip":
            strategy = "balanced_gain"
        case _:
            strategy = "balanced_norm"
    b_0, a_0, b_1, a_1 = balance_direct(b_0, a_0, b_1, a_1, k, strategy=strategy)
    b_0, a_0, b_1, a_1 = scatter_look_ahead(b_0, a_0, b_1, a_1)
    a_0[1:] = -a_0[1:]
    a_1[1:] = -a_1[1:]
    return b_0, a_0, b_1, a_1

# Just for testing
def print_IIR_parameters(b_0, a_0, b_1, a_1):
    for _, b in enumerate(b_0):
        quantized_b = fixed.fixed("Q3.24", b)
        print(f"b_0[{_}] = ", quantized_b)
    for _, a in enumerate(a_0):
        quantized_a = fixed.fixed("Q2.25", a)
        print(f"a_0[{_}] = ", quantized_a)
    for _, b in enumerate(b_1):
        quantized_b = fixed.fixed("Q3.24", b)
        print(f"b_1[{_}] = ", quantized_b)
    for _, a in enumerate(a_1):
        quantized_a = fixed.fixed("Q2.25", a)
        print(f"a_1[{_}] = ", quantized_a)

# Used to generate parameters in a VHDL testbench
def temp(b_0, a_0, b_1, a_1):
    high = 26
    low = 0
    for b in b_0:
        quantized_b = fixed.fixed("Q3.24", b)
        print(f"core_param_in({high} downto {low}) <= \"", quantized_b.__str__()[-35:-8], "\";", sep="")
        low += 32
        high += 32
    for a in a_0[4::4]:
        quantized_a = fixed.fixed("Q2.25", a)
        print(f"core_param_in({high} downto {low}) <= \"", quantized_a.__str__()[-35:-8], "\";", sep="")
        low += 32
        high += 32
    for b in b_1:
        quantized_b = fixed.fixed("Q3.24", b)
        print(f"core_param_in({high} downto {low}) <= \"", quantized_b.__str__()[-35:-8], "\";", sep="")
        low += 32
        high += 32
    for a in a_1[4::4]:
        quantized_a = fixed.fixed("Q2.25", a)
        print(f"core_param_in({high} downto {low}) <= \"", quantized_a.__str__()[-35:-8], "\";", sep="")
        low += 32
        high += 32