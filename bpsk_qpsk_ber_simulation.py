"""BPSK and QPSK over an AWGN channel: simulated BER compared with theory."""

import numpy as np
import matplotlib.pyplot as plt
from scipy.special import erfc

rng = np.random.default_rng(42)

NUM_BITS = 2_000_000
EBN0_DB = np.arange(0, 10)


def bpsk_modulate(bits):
    # 0 -> -1, 1 -> +1
    return 2 * bits - 1


def qpsk_modulate(bits):
    # two bits per symbol: first bit on I, second bit on Q, scaled so Es = 1
    pairs = bits.reshape(-1, 2)
    i = 2 * pairs[:, 0] - 1
    q = 2 * pairs[:, 1] - 1
    return (i + 1j * q) / np.sqrt(2)


def add_awgn(symbols, ebn0_db, bits_per_symbol):
    ebn0 = 10 ** (ebn0_db / 10)
    eb = 1.0 / bits_per_symbol          # Es is 1, so Eb = Es / bits per symbol
    n0 = eb / ebn0
    sigma = np.sqrt(n0 / 2)             # noise std per real dimension

    if np.iscomplexobj(symbols):
        noise = sigma * (rng.standard_normal(symbols.shape)
                         + 1j * rng.standard_normal(symbols.shape))
    else:
        noise = sigma * rng.standard_normal(symbols.shape)
    return symbols + noise


def bpsk_demodulate(received):
    return (received > 0).astype(int)


def qpsk_demodulate(received):
    bits_i = (received.real > 0).astype(int)
    bits_q = (received.imag > 0).astype(int)
    return np.column_stack((bits_i, bits_q)).ravel()


def theoretical_ber(ebn0_db):
    # same formula for BPSK and Gray-coded QPSK
    ebn0 = 10 ** (np.asarray(ebn0_db) / 10)
    return 0.5 * erfc(np.sqrt(ebn0))


def simulate():
    bits = rng.integers(0, 2, NUM_BITS)
    ber_bpsk, ber_qpsk = [], []

    for ebn0_db in EBN0_DB:
        rx = add_awgn(bpsk_modulate(bits), ebn0_db, bits_per_symbol=1)
        ber_bpsk.append(np.mean(bpsk_demodulate(rx) != bits))

        rx = add_awgn(qpsk_modulate(bits), ebn0_db, bits_per_symbol=2)
        ber_qpsk.append(np.mean(qpsk_demodulate(rx) != bits))

        print(f"Eb/N0 = {ebn0_db:2d} dB | BPSK BER = {ber_bpsk[-1]:.2e} "
              f"| QPSK BER = {ber_qpsk[-1]:.2e} "
              f"| Theory = {theoretical_ber(ebn0_db):.2e}")

    return np.array(ber_bpsk), np.array(ber_qpsk)


def plot_ber(ber_bpsk, ber_qpsk):
    fine = np.linspace(EBN0_DB[0], EBN0_DB[-1], 200)

    plt.figure(figsize=(7, 5))
    plt.semilogy(fine, theoretical_ber(fine), "k-", label="Theory (BPSK/QPSK)")
    plt.semilogy(EBN0_DB, ber_bpsk, "o", label="BPSK simulated")
    plt.semilogy(EBN0_DB, ber_qpsk, "x", label="QPSK simulated")
    plt.xlabel("Eb/N0 (dB)")
    plt.ylabel("Bit Error Rate (BER)")
    plt.title("BER vs Eb/N0 over an AWGN channel")
    plt.grid(True, which="both", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig("ber_curve.png", dpi=150)


def plot_constellations(ebn0_db=6, n=2000):
    bits = rng.integers(0, 2, 2 * n)
    bpsk_rx = add_awgn(bpsk_modulate(bits[:n]), ebn0_db, 1)
    qpsk_rx = add_awgn(qpsk_modulate(bits), ebn0_db, 2)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))

    axes[0].scatter(bpsk_rx, np.zeros_like(bpsk_rx), s=4, alpha=0.4)
    axes[0].axvline(0, color="r", ls="--")
    axes[0].set_title(f"BPSK received (Eb/N0 = {ebn0_db} dB)")
    axes[0].set_xlabel("In-phase")

    axes[1].scatter(qpsk_rx.real, qpsk_rx.imag, s=4, alpha=0.4)
    axes[1].axhline(0, color="r", ls="--")
    axes[1].axvline(0, color="r", ls="--")
    axes[1].set_title(f"QPSK received (Eb/N0 = {ebn0_db} dB)")
    axes[1].set_xlabel("In-phase")
    axes[1].set_ylabel("Quadrature")
    axes[1].set_aspect("equal")

    plt.tight_layout()
    plt.savefig("constellations.png", dpi=150)


if __name__ == "__main__":
    ber_b, ber_q = simulate()
    plot_ber(ber_b, ber_q)
    plot_constellations()
    plt.show()