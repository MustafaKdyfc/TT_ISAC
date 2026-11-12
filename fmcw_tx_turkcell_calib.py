#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 FMCW CHIRP YAYINI — DIZI KALIBRASYONU ICIN KAYNAK  (N321, 3530 MHz / 100 MHz)
===============================================================================
 HEDEF BANT (spektrum analizoru ile olculdu):
   kanal  3480 .. 3580 MHz  -> merkez 3530 MHz, genislik 100 MHz
   isgal  3480.86 .. 3579.14 MHz  (273 RB x 12 x 30 kHz = 98.28 MHz)
   guard  845 kHz her kenarda (TS 38.104 Tablo 5.3.3-1)
 Chirp'in kapsamasi gereken yer ISGAL EDILEN banttir; guard band bostur ama
 supurme onu da asarsa zarari yok (kalibrasyon oran oldugu icin sadece o
 binlerde SNR dusuk kalir ve agirlikli LS onlara zaten az agirlik verir).
 Kaynak: taha_berkay_2/fmcw_tx.py  (O DOSYA DEGISTIRILMEDI; bu bagimsiz kopya
 Turkcell bandina ve 100 MHz'e uyarlandi.)

 BU DOSYA SADECE YAYIN YAPAR. Icinde HICBIR ALICI KODU YOKTUR.
 Alicinin tamami esas kodda:  4rx_1tx_konum_backproj_v1_turkcell.py --wcal

 NEDEN AYRI: X410 oturumu TEK olmak ZORUNDA. Iki ayri prosesin alici acmasi
 kalibrasyonu bozar (ZBX'te LO export yok; her acilista kanal fazlari rastgele
 oturur). Bu yuzden alici bir kez, esas kodda acilir; bu dosya sadece chirp'i
 yayar ve alicinin ne yaptigindan haberi yoktur.

 KULLANIM — IKI TERMINAL
 -----------------------
   Terminal 1 (esas kod, alici):
     python3 4rx_1tx_konum_backproj_v1_turkcell.py --wcal --range 120 \
             --key signal_key.npz --step 20 --mti
     ... "SPLITTER'I TAK ve TX'i baslat" diye bekler ...

   Terminal 2 (bu dosya, verici):
     python3 fmcw_tx_turkcell_calib.py
     ... yayin baslar, Ctrl+C'ye kadar surer ...

   Sonra Terminal 1'de ENTER -> kalibrasyon alinir -> "SPLITTER'I CIKAR" der
   -> Terminal 2'de Ctrl+C -> Terminal 1'de ENTER -> olcum ayni oturumda surer.

 *** DONANIM GUVENLIGI — OKUMADAN CALISTIRMA ***
 ------------------------------------------------
   N321 TX tam kazancta ~+20 dBm verir. 4 yollu splitter -6 dB -> X410 girisine
   ~+14 dBm. ZBX'in hasar esigi ~+10 dBm, normal calisma seviyesi ~-15 dBm.
   DOGRUDAN BAGLARSAN ALICIYI YAKARSIN.
     * TX_GAIN varsayilani 0 dB (fmcw_tx.py'de 40 idi) — bilerek dusuk
     * yola SABIT ZAYIFLATICI koy (30 dB onerilir)
     * seviyeyi esas kod olcup raporlar; kirpma varsa kalibrasyonu REDDEDER

 100 MHz — "SUPURME" ILE "DUZ BANT" AYNI SEY DEGIL
 --------------------------------------------------
   Orijinal fmcw_tx.py Hamming penceresi kullaniyordu: -3 dB duz bant supurmenin
   ~%38'i. 100 MHz DUZ bant icin ~262 MHz supurmek gerekirdi ve o, X410'un
   122.88 MHz'lik penceresine SIGMAZ (katlanir, kalibrasyonu bozar).

   Gerek de yok: kalibrasyon bir ORAN islemidir,
       H_k(f) = <S_k conj(S_0)> / <|S_0|^2>
   ve chirp'in kendi spektral sekli pay ile paydada AYNI oldugu icin TAM OLARAK
   sadelesir. Duzluk degil, her frekansta yeterli SNR gerekir. Bu yuzden burada
   Hamming yerine hafif Tukey (alpha=0.15) ve 110 MHz supurme var:
   3475..3585 MHz -> kanalin (3480..3580) tamamini ~5 MHz kenar payiyla kapsar
   ve alicinin penceresine (3468.6..3591.4) sigar.

 Durdurmak icin: Ctrl+C.  Kilitli kalirsa: python3 fmcw_tx_turkcell_calib.py --stop
===============================================================================
"""

import argparse
import os
import sys
import time

import numpy as np

try:
    import uhd
    _HAVE_UHD = True
except ImportError:
    _HAVE_UHD = False


# ═══════════════════════════════════════════════════════════════════
#  AYARLAR
# ═══════════════════════════════════════════════════════════════════
DEVICE_ARGS = "addr=192.168.12.10"   # N321
CHANNEL     = 0                      # RF0
TX_ANTENNA  = "TX/RX"
REPLAY_BLOCK  = "0/Replay#0"
REPLAY_PORT   = 0
REPLAY_OFFSET = 0

CENTER_FREQ = 3489.60e6      # [Hz] alicinin tune edildigi frekansla AYNI olmali
#CENTER_FREQ = 3352.26e6   
SWEEP_BW    = 110e6       # [Hz] supurulen bant (alici penceresi 122.88 MHz)
CHIRP_DUR   = 100e-6      # [s]  chirp periyodu -> PRF = 10 kHz
TAPER_ALPHA = 0.15        # Tukey alpha (Hamming DEGIL — yukaridaki nota bak)
SAMPLE_RATE = 245.76e6    # [Hz] master clock ile ayni -> DUC interpolasyonu 1
TX_GAIN     = 55.0         # [dB] BILEREK DUSUK. Zayiflatici olmadan artirma.
AMPLITUDE   = 0.7         # tepe genlik (0-1), DAC tepe payi

# Hedef kanal — chirp'in kapsamasi gereken bant (sadece raporlama icin)
CARRIER_BW_HZ = 100e6            # nominal kanal genisligi
GUARD_BAND_HZ = 845e3            # TS 38.104 Tablo 5.3.3-1 (100 MHz @ 30 kHz)
OCC_BW_HZ     = 273 * 12 * 30e3  # 98.28 MHz — ISGAL EDILEN (RB'den turetildi)
BAND_LO = CENTER_FREQ - CARRIER_BW_HZ / 2      # 3480 MHz, kanal kenari
BAND_HI = CENTER_FREQ + CARRIER_BW_HZ / 2      # 3580 MHz
OCC_LO  = CENTER_FREQ - OCC_BW_HZ / 2          # 3480.86 MHz, isgal kenari
OCC_HI  = CENTER_FREQ + OCC_BW_HZ / 2          # 3579.14 MHz


# ═══════════════════════════════════════════════════════════════════
#  DALGA FORMU
# ═══════════════════════════════════════════════════════════════════
def tukey(n, alpha):
    """Tukey (koseli kosinus) penceresi. alpha=0 -> dikdortgen, 1 -> Hann."""
    if alpha <= 0:
        return np.ones(n)
    w = np.ones(n)
    nt = int(np.floor(alpha * (n - 1) / 2.0)) + 1
    if nt < 2:
        return w
    ramp = 0.5 * (1 - np.cos(np.pi * np.arange(nt) / (nt - 1)))
    w[:nt] = ramp
    w[n - nt:] = ramp[::-1]
    return w


def make_chirp(rate, bw, duration, amplitude, alpha, word_size=8):
    """Merkezi DC'de olan lineer up-chirp. Doner (sig, period, slope).

    Ornek sayisi Replay blogunun bellek kelimesine tam bolunur (sc16 -> 2
    ornek/kelime)."""
    n = int(round(rate * duration))
    samps_per_word = max(1, word_size // 4)
    n -= n % samps_per_word
    if n < 16:
        raise ValueError(f"Chirp cok kisa: {n} ornek. --chirp-dur artir.")
    period = n / rate
    slope = bw / period
    t = np.arange(n) / rate - period / 2.0
    sig = np.exp(1j * 2.0 * np.pi * 0.5 * slope * t ** 2) * tukey(n, alpha)
    sig /= np.max(np.abs(sig))
    sig *= amplitude
    return sig.astype(np.complex64), period, slope


def chirp_report(chirp, rate, fc, bw):
    """Spektrumu olcup hedef bandi gercekten kapsadigini yazar. Doner bool."""
    n = len(chirp)
    nfft = 4 * int(2 ** np.ceil(np.log2(n)))
    spec = np.abs(np.fft.fftshift(np.fft.fft(chirp, nfft)))
    spec = 20.0 * np.log10(spec / spec.max() + 1e-15)
    freq = np.fft.fftshift(np.fft.fftfreq(nfft, 1 / rate))
    print(f"  supurme     : {bw/1e6:.2f} MHz  "
          f"({(fc - bw/2)/1e6:.2f} -> {(fc + bw/2)/1e6:.2f} MHz)")
    for lvl in (-3.0, -6.0, -10.0):
        idx = np.flatnonzero(spec >= lvl)
        w = (freq[idx[-1]] - freq[idx[0]]) / 1e6 if idx.size else 0.0
        print(f"  {lvl:+5.0f} dB bant : {w:6.2f} MHz")
    print(f"  hedef kanal : {BAND_LO/1e6:.2f} .. {BAND_HI/1e6:.2f} MHz "
          f"(isgal {OCC_LO/1e6:.2f} .. {OCC_HI/1e6:.2f}, guard "
          f"{GUARD_BAND_HZ/1e3:.0f} kHz)")
    ok = True
    for name, f_abs in (("isgal alt", OCC_LO), ("isgal ust", OCC_HI)):
        off = f_abs - fc
        if abs(off) > rate / 2:
            print(f"  [UYARI] kanalin {name} kenari ({f_abs/1e6:.0f} MHz) "
                  f"ornekleme bandinin disinda.")
            ok = False
            continue
        i = int(np.argmin(np.abs(freq - off)))
        span = max(1, nfft // 400)
        droop = float(np.median(spec[max(0, i - span):i + span + 1]))
        bad = droop < -10.0
        ok = ok and not bad
        print(f"  kanal {name} kenari ({f_abs/1e6:.0f} MHz): {droop:+.1f} dB"
              + ("   <- ZAYIF, --sweep genislet" if bad else ""))
    return ok


def plot_waveform(chirp, rate, fc, bw, period, png_path, gui=True):
    """Yayina baslamadan once dalga formunu ciz (zaman + spektrum)."""
    import matplotlib
    if not gui:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = len(chirp)
    nfft = 4 * int(2 ** np.ceil(np.log2(n)))
    spec = np.abs(np.fft.fftshift(np.fft.fft(chirp, nfft)))
    spec = 20 * np.log10(spec / spec.max() + 1e-15)
    fmhz = (fc + np.fft.fftshift(np.fft.fftfreq(nfft, 1 / rate))) / 1e6
    t_us = np.arange(n) / rate * 1e6

    fig, ax = plt.subplots(2, 1, figsize=(12, 7), constrained_layout=True)
    fig.suptitle(f"KALIBRASYON CHIRP'I — {fc/1e6:.1f} MHz, supurme {bw/1e6:.0f} MHz, "
                 f"periyot {period*1e6:.0f} us", fontweight="bold")
    ax[0].plot(t_us, chirp.real, lw=0.7, color="#00BFFF", label="I")
    ax[0].plot(t_us, np.abs(chirp), lw=1.0, color="#FF1744", label="zarf (Tukey)")
    ax[0].set_xlabel("zaman [us]"); ax[0].set_ylabel("genlik")
    ax[0].set_title("zaman", loc="left"); ax[0].grid(alpha=0.3); ax[0].legend(fontsize=8)
    ax[1].plot(fmhz, spec, lw=0.8, color="#00E676")
    for f_abs, lbl in ((BAND_LO, "kanal kenari"), (BAND_HI, None)):
        ax[1].axvline(f_abs / 1e6, color="#FFEB3B", ls=":", lw=1.4, label=lbl)
    for f_abs, lbl in ((OCC_LO, "isgal kenari (273 RB)"), (OCC_HI, None)):
        ax[1].axvline(f_abs / 1e6, color="#FF9100", ls="--", lw=1.1, label=lbl)
    ax[1].set_xlim(fmhz[0], fmhz[-1]); ax[1].set_ylim(-60, 3)
    ax[1].set_xlabel("frekans [MHz]"); ax[1].set_ylabel("dB")
    ax[1].set_title("spektrum — TURUNCU cizgiler arasi DOLU olmali", loc="left")
    ax[1].grid(alpha=0.3); ax[1].legend(fontsize=8)
    fig.savefig(png_path, dpi=110)
    print(f"  grafik      : {png_path}")
    if gui:
        print("  (pencereyi kapatinca yayin baslar)")
        plt.show()
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════
#  RFNoC:  TxStreamer -> Replay(DRAM) -> DUC -> Radio
# ═══════════════════════════════════════════════════════════════════
def setup_graph(args):
    graph = uhd.rfnoc.RfnocGraph(args.args)
    radio_id = f"0/Radio#{CHANNEL}"
    duc_id = f"0/DUC#{CHANNEL}"
    for blk in (radio_id, duc_id, REPLAY_BLOCK):
        if not graph.has_block(blk):
            raise RuntimeError(f"FPGA imajinda {blk} yok.")
    radio = uhd.rfnoc.RadioControl(graph.get_block(radio_id))
    duc = uhd.rfnoc.DucBlockControl(graph.get_block(duc_id))
    replay = uhd.rfnoc.ReplayBlockControl(graph.get_block(REPLAY_BLOCK))
    radio.set_tx_antenna(TX_ANTENNA, CHANNEL)
    radio.set_tx_frequency(args.freq, CHANNEL)
    radio.set_tx_gain(args.gain, CHANNEL)
    duc.set_input_rate(args.rate, CHANNEL)
    rate = duc.get_input_rate(CHANNEL)
    graph.connect(REPLAY_BLOCK, REPLAY_PORT, duc_id, CHANNEL)
    return graph, radio, duc, replay, rate


def upload_waveform(graph, replay, chirp):
    """Dalga formunu bir kez DRAM'e yazar. Sira onemli: once akis bagla ve
    commit et, SONRA record kur (commit blok ayarlarini sifirlar)."""
    num_bytes = len(chirp) * 4                   # DRAM'de sc16 -> 4 bayt/ornek
    word = replay.get_word_size()
    if num_bytes % word:
        raise RuntimeError(f"{num_bytes} bayt, {word} baytlik kelimeye bolunmuyor.")
    if num_bytes > replay.get_mem_size():
        raise RuntimeError("Dalga formu DRAM'e sigmiyor.")
    streamer = graph.create_tx_streamer(1, uhd.usrp.StreamArgs("fc32", "sc16"))
    graph.connect(streamer, 0, REPLAY_BLOCK, REPLAY_PORT)
    graph.commit()
    replay.set_record_type("sc16", REPLAY_PORT)
    replay.set_play_type("sc16", REPLAY_PORT)
    replay.record(REPLAY_OFFSET, num_bytes, REPLAY_PORT)
    while True:                                  # eski veriyi bosalt
        replay.record_restart(REPLAY_PORT)
        dl, fullness = time.time() + 0.25, 0
        while time.time() < dl:
            fullness = replay.get_record_fullness(REPLAY_PORT)
            if fullness:
                break
        if not fullness:
            break
    md = uhd.types.TXMetadata()
    md.start_of_burst = md.end_of_burst = True
    t0 = time.time()
    sent = streamer.send(chirp.reshape(1, -1), md, 5.0)
    if sent != len(chirp):
        raise RuntimeError(f"Yalnizca {sent}/{len(chirp)} ornek gonderilebildi.")
    while replay.get_record_fullness(REPLAY_PORT) < num_bytes:
        if time.time() - t0 > 5.0:
            raise RuntimeError("DRAM'e yazma zaman asimina ugradi.")
        time.sleep(0.005)
    print(f"  DRAM'e yuklendi: {num_bytes/1024:.1f} kB / {len(chirp)} ornek "
          f"({(time.time()-t0)*1e3:.0f} ms)")
    del streamer
    return num_bytes


def start_playback(replay, num_bytes):
    replay.config_play(REPLAY_OFFSET, num_bytes, REPLAY_PORT)
    cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    cmd.stream_now = True
    replay.issue_stream_cmd(cmd, REPLAY_PORT)


def stop_only(args):
    if not _HAVE_UHD:
        print("[HATA] uhd modulu yok."); sys.exit(1)
    graph = uhd.rfnoc.RfnocGraph(args.args)
    replay = uhd.rfnoc.ReplayBlockControl(graph.get_block(REPLAY_BLOCK))
    replay.stop(REPLAY_PORT)
    print("Yayin durduruldu.")


# ═══════════════════════════════════════════════════════════════════
#  SELF-TEST — donanimsiz dalga formu dogrulamasi
# ═══════════════════════════════════════════════════════════════════
def self_test(args):
    print("=" * 70)
    print(" SELF-TEST — chirp dalga formu (donanim gerekmez)")
    print("=" * 70)
    chirp, period, slope = make_chirp(args.rate, args.bw, args.chirp_dur,
                                      args.amplitude, args.taper)
    print(f"  ornek       : {len(chirp)}  periyot {period*1e6:.2f} us  "
          f"(PRF {1/period/1e3:.2f} kHz)")
    print(f"  egim        : {slope/1e12:.3f} MHz/us")
    print(f"  tepe genlik : {np.max(np.abs(chirp)):.3f} (DAC payi "
          f"{20*np.log10(np.max(np.abs(chirp))):.1f} dBFS)")
    ok = chirp_report(chirp, args.rate, args.freq, args.bw)

    # Alicinin penceresine sigiyor mu? Supurme 122.88 MHz'i asarsa katlanir.
    RX_FS = 122.88e6
    fits = args.bw < RX_FS - 4e6
    print(f"\n  alici penceresi {RX_FS/1e6:.2f} MHz -> supurme "
          f"{args.bw/1e6:.0f} MHz {'SIGIYOR' if fits else 'SIGMIYOR (katlanir!)'}")
    ok = ok and fits

    # Ornek sayisi Replay kelimesine bolunuyor mu (8 bayt = 2 ornek)?
    word_ok = (len(chirp) * 4) % 8 == 0
    print(f"  Replay kelime hizasi: {'OK' if word_ok else 'HATALI'}")
    ok = ok and word_ok

    print("\n" + "=" * 70)
    print(" SELF-TEST GECTI" if ok else " SELF-TEST KALDI")
    print("=" * 70)
    return ok


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════
def parse_args():
    p = argparse.ArgumentParser(
        description="Dizi kalibrasyonu icin FMCW chirp yayini (N321). "
                    "SADECE VERICI — alici esas koddadir.")
    p.add_argument("--args", default=DEVICE_ARGS, help="UHD cihaz argumanlari")
    p.add_argument("--freq", type=float, default=CENTER_FREQ,
                   help="merkez frekans [Hz] (alicininkiyle AYNI olmali)")
    p.add_argument("--rate", type=float, default=SAMPLE_RATE, help="ornekleme hizi [Hz]")
    p.add_argument("--bw", type=float, default=SWEEP_BW,
                   help="supurulen chirp bandi [Hz]")
    p.add_argument("--chirp-dur", type=float, default=CHIRP_DUR, dest="chirp_dur",
                   help="chirp suresi [s]")
    p.add_argument("--taper", type=float, default=TAPER_ALPHA,
                   help="Tukey alpha (0=dikdortgen, 1=Hann)")
    p.add_argument("--gain", type=float, default=TX_GAIN,
                   help=f"TX kazanci [dB] (varsayilan {TX_GAIN:.0f} — BILEREK "
                        f"DUSUK; zayiflatici olmadan artirma)")
    p.add_argument("--amplitude", type=float, default=AMPLITUDE,
                   help="tepe genlik (0-1)")
    p.add_argument("--self-test", action="store_true",
                   help="donanimsiz dalga formu dogrulamasi")
    p.add_argument("--no-plot", action="store_true", help="dalga formunu cizme")
    p.add_argument("--no-gui", action="store_true",
                   help="pencere acma (PNG yine kaydedilir)")
    p.add_argument("--stop", action="store_true",
                   help="takili kalan yayini kes ve cik")
    return p.parse_args()


def main():
    args = parse_args()
    if args.self_test:
        return 0 if self_test(args) else 1
    if args.stop:
        stop_only(args)
        return 0
    if not _HAVE_UHD:
        print("[HATA] uhd modulu yok. --self-test kullan.")
        return 1

    print("=" * 70)
    print(" KALIBRASYON CHIRP'I — N321")
    print("=" * 70)
    chirp, period, slope = make_chirp(args.rate, args.bw, args.chirp_dur,
                                      args.amplitude, args.taper)
    print(f"  periyot     : {period*1e6:.2f} us  (PRF {1/period/1e3:.2f} kHz), "
          f"{len(chirp)} ornek")
    print(f"  egim        : {slope/1e12:.3f} MHz/us")
    chirp_report(chirp, args.rate, args.freq, args.bw)
    if args.gain > 10.0:
        print(f"\n  [DIKKAT] TX kazanci {args.gain:.0f} dB. Splitter dogrudan "
              f"X410'a bagliysa ALICI HASAR GOREBILIR.")
        print(f"           Yola sabit zayiflatici (>=30 dB) koydugundan emin ol.")

    if not args.no_plot:
        png = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "kalibrasyon_chirp.png")
        try:
            plot_waveform(chirp, args.rate, args.freq, args.bw, period, png,
                          gui=not args.no_gui)
        except Exception as e:
            print(f"  [UYARI] grafik cizilemedi ({e})")

    graph, radio, duc, replay, rate = setup_graph(args)
    print(f"\n  TX          : {radio.get_tx_frequency(CHANNEL)/1e6:.3f} MHz, "
          f"{radio.get_tx_gain(CHANNEL):.1f} dB, {TX_ANTENNA}")
    print(f"  DUC girisi  : {rate/1e6:.3f} Msps")
    if abs(rate - args.rate) > 1.0:
        print(f"  [UYARI] istenen {args.rate/1e6:.3f} Msps elde edilemedi; "
              f"chirp {rate/1e6:.3f}'e gore yeniden uretiliyor.")
        chirp, period, slope = make_chirp(rate, args.bw, args.chirp_dur,
                                          args.amplitude, args.taper)
    num_bytes = upload_waveform(graph, replay, chirp)
    start_playback(replay, num_bytes)

    print("\n" + "*" * 70)
    print(" *  YAYIN ACIK — sonsuz dongu (DRAM)")
    print(" *")
    print(" *  Simdi esas kodun bulundugu terminalde ENTER'a bas.")
    print(" *  Kalibrasyon bitince orasi 'SPLITTER'I CIKAR' diyecek;")
    print(" *  O ZAMAN buraya donup Ctrl+C ile yayini kes.")
    print("*" * 70)
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n  Durduruluyor...")
    finally:
        try:
            replay.stop(REPLAY_PORT)
            print("  YAYIN KAPANDI")
        except Exception as e:
            print(f"  [UYARI] durdurulamadi ({e}); --stop dene.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
