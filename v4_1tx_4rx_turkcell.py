#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 BISTATIK KONUM KESTIRIMI  —  X410 4 KANAL VIVALDI DIZISI + BACKPROJECTION
===============================================================================
 Bu dosya BAGIMSIZDIR (donanim kurulumu, anahtar referansi, geometri,
 kalibrasyon ve goruntuleme burada). Eski dosyalar ELLENMEZ.

 3aug_radar/4rx_1tx_kdyf_80mhz_v1.py'den FARKI
 ---------------------------------------------
 Eski dosya MONOSTATIK menzil-ACI (broadside'a gore aci) veriyordu: TX ve RX
 yan yana varsayilir, cikti "kac metre / kac derece". Bu dosya BISTATIK KONUM
 verir: baz istasyonu (TX) ile X410 dizisi (RX) FARKLI yerlerde. Hedef,
 baz istasyonunun her saniyenin ilk ~80-100 ms'sinde yaydigi deterministik
 sinyali yansitir; X410'un 4 Vivaldi anteni bu yansimayi yakalar.

     yol:  TX (baz ist.)  ->  hedef  ->  RX_k (dizi elemani k)
     dogrudan yol (LOS):  TX -> RX_k   (her zaman var, en guclu, DURGUN)

 Bir hedef icin bistatik menzil  R(p) = |p-TX| + |p-RX_k|  sabit -> odaklari
 TX ve RX olan bir ELIPS. 4 elemanli dizi ayrica GELIS ACISINI (faz farki)
 cozer. Ikisi birlikte hedefi z=0 duzleminde TEK noktaya oturtur.
 BACKPROJECTION bu iki bilgiyi (gecikme elipsi + dizi fazi) koherent birlestirip
 z=0 duzleminde bir ISI HARITASI cizer; tepe = hedef konumu.

 QSFP
 ----
 Eski baglanti (1 GbE ethernet) 80-100 ms'lik pencereyi saniyede aktaramiyordu.
 QSFP (100 GbE) ile tam pencere her saniye rahatca aktarilir; bu yuzden
 LOC_WIN_MS varsayilani 100 ms. ADDR icindeki IP QSFP arayuzune gore
 AYARLANMALI (asagidaki nota bak).

 GEOMETRI (asagida sabitlerden GIRILIR — kendi olcumunle degistir)
 -----------------------------------------------------------------
   TX_POS      : baz istasyonu (x1,y1,z1>0)               [m]
   TX_N1       : baz ist. yayilim normali (z bileseni 0)  -> 3 dB huzme
   TX_BW3_DEG  : baz ist. -3 dB huzme genisligi (tam aci) [derece]
   ARRAY_POS   : dizi ORTA noktasi (x2,y2,z2)             [m]
   ARRAY_N2    : dizi normali (z bileseni 0)
   ARRAY_D_M   : elemanlar arasi mesafe (d < lambda/2 OLMALI, girilecek) [m]
   elemanlar   : ARRAY_N2'ye DIK, yatay (z=0) dogrultuda dizilir (4 eleman)

 KALIBRASYON (iki asama, --calib ile TEK komutta)
 ------------------------------------------------
   1) Ortami 30 s BOS olc  -> dogrudan yol + durgun yankilar = "arka plan".
      Ayrica dogrudan yol tepesi zaman capasi (n_dir) buradan bulunur;
      TX<->RX bilinmeyen donanim gecikmesini (HW offset) sogurur.
   2) Bilinen bir noktaya hedef koy, 30 s olc. Arka plan cikarilinca kalan
      hedef yankisindan 4 kanalin KOMPLEKS kazanci (genlik+faz) cozulur.
   Ikisi bir .npz'ye yazilir (arka plan + kanal cal + n_dir + geometri).

 KULLANIM
 --------
   python3 4rx_1tx_konum_backproj_v1.py --self-test          # donanimsiz dogrulama
   python3 4rx_1tx_konum_backproj_v1.py --learn              # (eski dosyayla ayni) anahtar ogren
   python3 4rx_1tx_konum_backproj_v1.py --calib 3.0 5.0 --key signal_key.npz
                                                #  hedef (x=3,y=5) -> arka plan+cal yazar
   python3 4rx_1tx_konum_backproj_v1.py --locate 120 --key signal_key.npz
                                                #  120 s canli backprojection isi haritasi
 Not: deterministik referans URETILMEZ, --learn ile OGRENILIR (--key zorunlu).
      Ticari sebeke PRS yayinlamaz; ogrenilen sey hucrenin SSB/SIB1 bolgesidir.

 TICARI BAZ ISTASYONU (bu dosyanin amaci) — AKIS
 ------------------------------------------------
   HEDEF TASIYICI (spektrum analizoru ile olculdu): n78 makro hucre
     kanal   3480 .. 3580 MHz   -> merkez 3530 MHz, genislik 100 MHz
     isgal   3480.86 .. 3579.14 MHz  (273 RB x 12 x 30 kHz = 98.28 MHz)
     guard   845 kHz her kenarda (TS 38.104 Tablo 5.3.3-1)
   Fs = 122.88 MHz penceresi (3468.6..3591.4 MHz) bunu ~12 MHz payla kapsar.
   Menzil cozunurlugu tam bantta c/(2B) = 1.53 m.

   0) --cells                          KOMSU BANT: 3460-3480 ayri gNB mi?
   1) --psd 5                          frekans/kazanc dogrula
   2) --cell                           PCI + isgal edilen bant + cozunurluk
   3) --learn 120 --learn-win 40       anahtar + bant + hucre -> signal_key.npz
      --learn-out yeni.npz             ...ayri dosyaya (eskisi KORUNUR)
      --keydiff eski.npz yeni.npz      iki anahtari karsilastir (DONANIMSIZ)
   4) --calib 30 --key signal_key.npz  BOS SAHA kalibrasyonu
   5) --range 120 --key ... --cal ...  menzil ispati
   6) --locate 300 --key ... --cal ... konum haritasi

 REFERANS SECIMI (--ref) — BU DOSYANIN ANA TASARIM KARARI
 --------------------------------------------------------
   Korelasyon bir KARSILASTIRMA islemidir: iki sinyal de ayni x(t)'yi farkli
   gecikmelerle tasiyorsa, x(t) denklemden duser ve geriye GECIKME FARKI kalir.
   Bize zaten hep o lazimdi (elips denklemi R_bi - D0 bir farktir). Dolayisiyla
   referansin ne oldugu bir SECIMDIR, zorunluluk degil:

   --ref key  (VARSAYILAN) — ogrenilmis anahtar
       * deterministik, SAKLANABILIR, alimdan alima TEKRAR EDER
       * bant, hucrede tutarli olan ICERIGE baglidir — "SSB = 7.2 MHz" DIYE
         VARSAYMA. Sahada olculdu (PCI 693): 33 MHz -> ~4 m. Muhtemelen
         CORESET0/PDCCH+SIB1 de tutarli (96 RB x 30 kHz = 34.6 MHz).
         load_key her calismada anahtarin GERCEK bandini basar; ona bak.
       * referans TEMIZ (hedef yankisi tasimaz) -> MTI ZORUNLU DEGIL
         -> DURGUN hedefler de gorunur (bos saha haritasi cikarilarak)

   --ref los / beam — dogrudan yolun kendisi (kanal 0 ya da TX'e huzme)
       * tasiyicinin TAM bandi (~100 MHz) -> ~1.5 m
       * ama referans kendi yankilarini tasir ve HER ALIMDA DEGISIR
         -> LOO MTI zorunlu -> SADECE HAREKETLI hedef
       * ortak donanim gecikmesi referansla iptal olur (LOS lag ~ 0)

   SIRADAKI ADIM (henuz yazilmadi): "recon" — referansi LOS'tan YENIDEN URETMEK.
   LOS'u OFDM demodule et, her altasiyiciyi en yakin takimyildiz noktasina
   yuvarla (bitleri COZMEYE gerek yok, sadece sembol lazim), yeniden module et.
   Sonuc hem deterministik hem ~100 MHz olur: 1.5 m + durgun hedef. Tekrar eden
   tek sey yine CIR olur, dalga formu degil — bu yuzden durgun ortam haritasi
   simdiden KORELASYON (CIR) domeninde saklaniyor; o gun dosya bicimi degismez.

 BOS SAHA KALIBRASYONU (--calib) — TEK ASAMA
 --------------------------------------------
   Saha BOSKEN olculur, hedef koymaya gerek yok. Tek gecisde:
     1) FREKANS BASINA equalizer  (asagi)
     2) DURGUN ORTAM haritasi     (dogrudan yol + binalar/zemin), CIR domeninde
     3) n_dir                     (dogrudan yol capasi; HW gecikmesi buraya gomulur)
   Canlida durgun harita cikarilinca geriye sahaya SONRADAN giren her sey kalir;
   hedefin hareketli OLMASI gerekmez. --cal verilmezse LOO MTI'ye dusulur ve
   yalnizca hareketli hedef gorunur.

 FREKANS BASINA EQUALIZER
 -------------------------
   Dort RX zincirinin genlik/fazi duz degildir (analog filtre, kablo boyu, ADC
   skew). TEK bir kompleks katsayi bunu telafi EDEMEZ. Bu yuzden her FFT bini
   icin ayri katsayi cikarilir:

       H_k(f) = <S_k conj(S_0)> / <|S_0|^2>              (LS kanal kestirimi)
       geometrik faz exp(-j2pi f_abs (D_k-D_0)/c) ANALITIK cikarilir
       kalan KISA FIR'a agirlikli en-kucuk-kareler ile oturtulur -> EQ taplari
       EQ_k(f) ~ g_k(f)/g_0(f)   (saf donanim uyumsuzlugu)

   * Kestirim LOS'un TAM BANDINDA (~100 MHz) yapilir — anahtar dar bile olsa.
     Sebebi: SSB genelde bant ortasinda DEGIL. Tek bant-ortalamasi katsayi
     SSB'nin durdugu yerde 10-15 derece yanlis olur; taplari tam banttan cikarip
     SSB'nin YERINDE degerlendirmek bunu duzeltir. (Bandin ICINDEKI egim SSB
     genisliginde kucuktur; asil kazanc genis bant referansa gecince gelir.)
   * Taplar olarak saklanir -> herhangi bir FFT izgarasinda TAM dogru
     degerlendirilir (eq_from_taps); WB izgarasi ile korelasyon izgarasi farkli.
   * Kapi yerine LS: bant sinirli H'nin IFFT'sini kesmek bant kenarinda birkac
     dB Gibbs dalgalanmasi birakiyor (olculdu). LS ayni tap sayisiyla bant
     ICINDE en iyi uyumu verir.
   * Canlida equalizer'in USTUNE her yakalamada skaler bir LOS self-cal
     uygulanir; o da bagimsiz LO'larin faz suruklenmesini alir.

   BU DOSYA SADECE ALICIDIR — hicbir sey YAYMAZ.
===============================================================================
"""

import argparse
import functools
import os
import sys
import numpy as np


# ═══════════════════════════════════════════════════════════════════
#  GPU HIZLANDIRMA  —  davranisi DEGISTIRMEZ, sadece hizlandirir
# ═══════════════════════════════════════════════════════════════════
# Profil (T1000 8GB, 100 ms yakalama): zamanin cogu FFT'de.
#     band_limit_sig  12.3M nokta  -> 1093 ms
#     ocal_accum_clean 1024 chirp  ->  602 ms
#     capture_loo      5 occasion  ->   63 ms
# Bunlar GPU'ya tasindi. GPU yoksa ya da GPU_ENABLE=False ise AYNI numpy
# yolu kosar — cikti degismez, sadece yavaslar.
#
# SAYISAL FARK: GPU ve CPU FFT'leri son bitlerde ayrisabilir (float32'de
# gorece ~1e-6). Olcum gurultusunun cok altinda ama BIREBIR ayni degil.
# Birebir tekrarlanabilirlik gerekiyorsa GPU_ENABLE=False yap.
_CP = None
_GPU_TRIED = False















# ===================================================================
#  YAPILANDIRMA  —  BUTUN PARAMETRELER BURADA
# ===================================================================
# Sahada degistirecegin her sey bu blokta. Asagisi sadece islev.
# Turetilmis olanlar (FS, N_FFT, SLOT_DUR_S ...) kendilerinden ONCE
# gelen degerlere baglidir; sirayi bozma.

# ═══════════════════════════════════════════════════════════════════
#  1) DONANIM PARAMETRELERI
# ═══════════════════════════════════════════════════════════════════
# master_clock_rate 245.76 MHz ZORUNLU (30 kHz izgarasina tam oturmasi icin).
#
# ADDR — QSFP NOTU:
#   Eski (yavas) 1 GbE baglantida 192.168.20.2 kullaniliyordu. QSFP (100 GbE)
#   arayuzu FARKLI bir IP'de olabilir (fabrika varsayilani cogu zaman
#   192.168.10.2). QSFP kablosunu taktiktan sonra:
#       uhd_find_devices
#   ciktisindaki addr ne ise ASAGIYA onu yaz. Yanlis IP -> baglanti hatasi.
#   recv_frame_size/num_recv_frames/recv_buff_size QSFP'nin yuksek hizini
#   besler; jumbo frame (MTU 9000) aciksa recv_frame_size 8000'e cikarilabilir.
# --- GPU ---
GPU_ENABLE   = True      # False -> her sey numpy ile (birebir tekrarlanabilir)
GPU_MIN_SIZE = 1 << 16   # bu boyutun altinda GPU'ya tasima masrafi kazanci yer
ADDR = ("addr=192.168.10.2,master_clock_rate=245.76e6,"
        "clock_source=gpsdo,time_source=gpsdo,"
        "recv_frame_size=8000,num_recv_frames=2048,"
        "recv_buff_size=1073741824")
# TASIYICI — n78 makro hucre.  SPEKTRUM ANALIZORU ILE OLCULDU: 3480..3580 MHz
#
#   kanal        : 3480 .. 3580 MHz   -> merkez 3530 MHz, genislik 100 MHz
#   SCS          : 30 kHz  (mu=1)
#   RB           : 273     (TS 38.104 Tablo 5.3.2-1: 100 MHz @ 30 kHz)
#   ISGAL        : 273 x 12 x 30 kHz = 98.28 MHz  -> 3480.86 .. 3579.14 MHz
#   GUARD BAND   : 845 kHz her kenarda (TS 38.104 Tablo 5.3.3-1)
#                  kontrol: 2 x 0.845 + 98.28 = 99.97 MHz ~ 100 MHz kanal
#
# KOMSU TASIYICI UYARISI: 3510'a tune edilmis onceki olcumde isgal 3460.8'den
# basliyordu — yani 3480'in ALTINDA da enerji var (baska bir blok). 3530
# penceresi (3468.6..3591.4) o komsunun ust kuyrugunu da icine alir ve
# _wb_band_edges ikisini TEK blok sayabilir (WB_GAP_MHZ=1 araligi kapatir).
# Bunun onune gecmek icin WB islerinde --bw 100 ver: merkeze simetrik
# 3480..3580 zorlanir, komsu disarida kalir.
#
# O olcumde SSB 3470.9 MHz'te bulunmustu; o da 3480.86'nin ALTINDA, yani
# KOMSUYA aitti. Bu yuzden o donemin signal_key.npz'i BU blogun anahtari
# DEGILDI ve 3530'da --learn tekrarlanmasi gerekiyordu.
#
# YAPILDI (2026-08-14 17:36, mevcut signal_key.npz): merkez 3530 MHz, PCI 918
# (N_ID_1=306, N_ID_2=0), SSB 3496.199 MHz — yani SSB artik isgal bandinin
# (3480.86..3579.14) ICINDE, komsuda degil. Anahtarin kendi bandi 17.34 MHz,
# tekrar periyodu 20 ms. Bu dosya ARTIK bu blogun anahtaridir.
# Yeni bir anahtarin eskisiyle ayni sinyal olup olmadigini --keydiff olcer;
# --learn asla mevcut dosyanin uzerine yazmaz (--learn-out / --force-key).
#
# CENTER_FREQ kanalin ORTASINA oturmali; --psd ciktisindaki "bant ortasi" ve
# "merkez kaymasi" satirlari bunu dogrular. Baska hucre icin --freq ile ez.
# SAHADA CIKARILDI (2026-08-19): telefonun ServiceMode ciktisi NR-ARFCN 632640
# veriyor; TS 38.104 5.4.2.1'e gore
#     F = 3000 MHz + 15 kHz * (632640 - 600000) = 3489.600 MHz
# CHBW 100 -> tasiyici 3439.6 .. 3539.6 MHz. Onceki 3530 MHz degeri
# tasiyicinin UST KENARINDAYDI (+40.4 MHz kayma) ve bant siniri (+-50 MHz)
# tasiyicinin alt 40 MHz'ini tamamen disarida birakiyordu.
# BUNUN OLCULEN BEDELI buyuktu:
#     LO 3530   -> deterministik bant 17.5 MHz, menzil 8.6 m, tekrar. 0.9316
#     LO 3489.6 -> deterministik bant 37.0 MHz, menzil 4.05 m, tekrar. 0.9962
#                  (120 yakalamada 0.9987)
# SSB de burada: GSCN 340 = 3489.60 MHz, PCI 168, i_SSB 1 (--ssbscan).
# Baska bir hucrede once --ssbscan calistir, cikan SS_REF'i --freq ile ver.
CENTER_FREQ   = 3489.6e6
CARRIER_BW_HZ = 100e6        # NOMINAL kanal genisligi
GUARD_BAND_HZ = 845e3        # TS 38.104 Tablo 5.3.3-1, 100 MHz @ 30 kHz SCS
OCC_BW_HZ     = 273 * 12 * 30e3   # 98.28 MHz — ISGAL EDILEN (RB'den turetildi)
RX_GAIN     = 25             # SAHADA OLCULDU: 25 dB'de doyma yok (~-20 dBFS).
RX_ANTENNA  = "RX1"          # ZBX RX-only port
# 100 MHz'lik tasiyici 122.88 MHz'lik pencereye SIGAR (kenarda ~12 MHz pay).
# Pay dar oldugu icin DDC'nin decim-2 yarim-bant suzgeci bandin EN DIS ~1-2 MHz'ini
# biraz yuvarlayabilir. Bunun tek etkisi olculen bandin (ve dolayisiyla menzil
# cozunurlugunun) birkac yuzde kotulesmesidir; --psd spektrumunda dogrudan
# gorulur. Kenarlar gercekten kirpiliyorsa DECIM=1 (Fs=245.76 MHz, suzgec yok)
# yapilabilir — N_FFT/CP/N_SLOT asagida Fs'ten turedigi icin kod calisir, bedeli
# 2 kat veri hizi ve 2 kat DRAM penceresidir.
DECIM = 2
FS    = 245.76e6 / DECIM     # 122.88 MHz
# ═══════════════════════════════════════════════════════════════════
#  2) NR TASIYICI IZGARASI
# ═══════════════════════════════════════════════════════════════════
# TICARI HUCRE: deterministik referans, --learn ile OGRENILEN SSB anahtaridir.
# PRS YOKTUR ve bu dosyada PRS ile ilgili hicbir sey yoktur — ticari sebeke
# PRS yayinlamaz (konumlandirma servisi acik degilse), dolayisiyla sentetik
# PRS sablonu tasimanin bir anlami yoktu.
#   TS 38.104 Tablo 5.3.2-1: 100 MHz @ 30 kHz SCS -> 273 RB (98.28 MHz isgal)
SCS_HZ        = 30e3
N_FFT         = int(FS / SCS_HZ)     # 4096  (4096 x 30 kHz = 122.88 MHz)
N_RB_CELL     = 273                  # 100 MHz @ 30 kHz -> 273 RB
PHASE_COMP    = True                 # OFDM sembolu kurarken faz telafisi
FRAME_OFFSET_S = 0.0
# Yakalama PPS'ten bu kadar sonra tetiklenir. ADVANCE_MS kadar da erken acilir,
# yani net "RX acilir: PPS +0 ms". Referans ani anahtarin kendi t0'idir.
PPS_OFFSET_S = FRAME_OFFSET_S + 1.0e-3
ADVANCE_MS   = 1.0
MARGIN_MS    = 1.0
MIN_LEAD_S   = 0.15
C_AIR = 299792458.0
NSYM_PER_SLOT = 14
NSC_PER_RB    = 12
# ═══════════════════════════════════════════════════════════════════
#  3) DIZI TOPOLOJISI (X410 4 KANAL)
# ═══════════════════════════════════════════════════════════════════
# X410: Radio#0 -> DB0 (ch 0,1),  Radio#1 -> DB1 (ch 2,3),  Replay 4 port.
# k=0..3 FIZIKSEL dizide soldan saga sirayla ayni olmali; kablo sirasi
# farkliysa RX_CHANS'i degistir (yoksa geometri/faz yanlis eslesir).
N_RX     = 4
RX_CHANS = [(0, 0), (0, 1), (1, 0), (1, 1)]     # (radyo_index, radyo_ici_kanal)
# ═══════════════════════════════════════════════════════════════════
#  3b) GEOMETRI  —  KENDI OLCUMUNLE DOLDUR (metre, ortak koordinat sistemi)
# ═══════════════════════════════════════════════════════════════════
# Koordinat sistemi: z=0 zemin duzlemi. Konumlar 3 elemanli (x,y,z).
#   * TX_POS  z bileseni > 0 (baz istasyonu yukarida).
#   * ARRAY_POS z bileseni: dizi ortasinin yuksekligi (su an 0 -> antenler z=0).
#   * TX_N1, ARRAY_N2 normallerinin z bileseni 0 (yatay yayilim/bakis).
#
# SAHA GEOMETRISI (x = DOGU, y = KUZEY, alici = haritanin 0,0)
# Sahada dogrulandi: baz istasyonu aliciya gore 55 m DOGU, 90 m KUZEY.
#   -> yatay mesafe 105.5 m, yon 31.4 derece (KUZEYDOGU)
# NOT: ilk verilen GPS ciftinde BOYLAMLAR yer degistirmisti (aliciya 29 27
# 30.79", TX'e 29 27 28.43" yazilmisti) ve TX bati tarafina dusuyordu. Tersi
# alininca +55.3 dogu / +92.9 kuzey cikiyor, yani sahadaki olcumle ayni.
# Burada sahada soylenen degerler esas alindi.
# Dizi yonunu ayarlamak icin: --rxdir  (kaydiricili canli harita)
TX_POS     = np.array([55.0, 90.0, 30.0])    # baz istasyonu (yukseklik TAHMINI)
# TX anten azimutu BILINMIYOR (operatorun sektor yonu bize kapali). Aliciya
# bakiyormus gibi alindi ama ONEMI YOK: USE_TX_PATTERN=False (bkz. asagisi).
TX_N1      = np.array([-0.5215, -0.8533, 0.0])   # 211.4 der (aliciya donuk)
TX_BW3_DEG = 65.0                          # baz ist. -3 dB huzme genisligi (tam aci)
ARRAY_POS  = np.array([0.0, 0.0, 1.0])     # dizi ORTA noktasi = haritanin (0,0)
ARRAY_N2   = np.array([+0.5215, +0.8533, 0.0])  # 31.4 der: TX'e dogru bakiyor
ARRAY_D_M  = 0.040                          # eleman araligi [m]  (d < lambda/2 OLMALI)
# Eleman dizilim yonunun isareti. Fiziksel kablo sirasi ters ise -1 yap
# (harita saga/sola aynalanmis cikiyorsa bu isareti cevir).
ARRAY_ORDER_SIGN = +1
# ═══════════════════════════════════════════════════════════════════
#  3c) BACKPROJECTION IZGARASI (z=0 duzlemi)
# ═══════════════════════════════════════════════════════════════════
# None -> TX ve ARRAY'i iceren kutu otomatik hesaplanir (kenar payi GRID_MARGIN_M).
# Elle sinirlamak istersen (xmin, xmax, ymin, ymax) metre olarak ver.
GRID_BOUNDS  = None
GRID_MARGIN_M = 20.0          # otomatik kutuda her kenara eklenen pay [m]
GRID_RES_M    = 0.10         # izgara adimi [m] (0.10 -> 10 cm hucre)
GRID_MAX_CELLS = 400         # eksen basina azami hucre (bellek/hiz siniri)
# TX huzmesi disindaki noktalari bastir (arka lob hayaletlerini kirar).
# False -> huzme agirligi uygulanmaz (izotropik TX varsay).
# DIKKAT: huzme YUMUSAK MASKE olarak uygulanir (huzme icinde DUZ=1, sadece
# disari bastirilir). Ham huzme kazancini goruntuyle carpmak, genis dizi
# lobunda tepeyi huzme merkezine dogru KAYDIRIR (konum hatasi). Maske bunu
# onler: gain >= TX_MASK_FLOOR olan her nokta esit agirlik alir.
# KAPALI: ticari hucrenin sektor azimutu bize kapali. Bilinmeyen bir yone gore
# maske uygulamak haritanin bir yarisini sebepsiz bastirir ve hedefi kaydirir.
USE_TX_PATTERN = False
TX_MASK_FLOOR  = 0.25        # bu kazancin (-6 dB) altindaki noktalar bastirilir
# Bistatik yol kaybini (~1/(R_tx*R_rx)^2) kismen telafi et ki uzak hedef de
# gorunsun. 0 = kapali (VARSAYILAN). DIKKAT: telafi uzak kose gurultusunu de
# yukseltir ve sahte tepe uretebilir; bu yuzden PATHLOSS_MAX ile siniri var ve
# varsayilan KAPALI. Sadece gercek uzak hedef kayboluyorsa 0.3-0.5 dene.
PATHLOSS_COMP = 0.0
PATHLOSS_MAX  = 6.0          # telafi carpani bu kati asamaz (kose patlamasini onler)
# DIKKAT: klasordeki mevcut konum_cal.npz ESKI bicimde bir SAHA dosyasidir
# (2026-08-03). Uzerine yazilmasin diye kalibrasyon ciktisi AYRI isimde.
CAL_FILE = "turkcell_cal.npz"
# ═══════════════════════════════════════════════════════════════════
#  3e) GENIS BANT (WB) + EQUALIZER PARAMETRELERI
# ═══════════════════════════════════════════════════════════════════
# KORELASYON REFERANSI — "key" | "los" | "beam"   (--ref ile secilir)
#   key  : ogrenilmis SSB anahtari. Deterministik, saklanabilir, TEKRAR EDER.
#          Bant SSB kadar (~7.2 MHz) -> menzil cozunurlugu ~20 m. Referans TEMIZ
#          oldugu icin DURGUN hedefler de gorunur (MTI zorunlu degil).  VARSAYILAN
#   los  : dogrudan yolun kendisi (kanal 0). Tasiyicinin tam bandi (~100 MHz) ->
#          ~1.5 m, ama referans kendi yankilarini tasir ve alimdan alima DEGISIR;
#          bu yuzden yalniz HAREKETLI hedef (LOO MTI zorunlu).
#   beam  : los ile ayni, referans 4 elemanin TX yonune huzmelenmesiyle kurulur.
# Not: "los"un tam bandini deterministik bir referansla birlestirmenin yolu
# referansi LOS'tan YENIDEN URETMEKTIR (OFDM demod -> takimyildiz karari ->
# yeniden modulasyon). Henuz yazilmadi; sirasi geldiginde buraya "recon" eklenir.
# VARSAYILAN "key" — SAHADA OLCULDU (bkz. key_determinism / --keycheck):
#   3480..3500 MHz : determinizm +2..+5 dB  -> her periyot AYNI (SSB/CORESET0/SIB1)
#   3500..3580 MHz : determinizm -31..-49 dB -> koherent ortalamada YOK OLUYOR
# Yani tasiyicinin 98 MHz'inde guc var ama sadece ~20 MHz'i TEKRAR EDIYOR;
# gerisi PDSCH kullanici trafigi ve her periyot farkli. "los" referansi o
# 98 MHz'in TAMAMINI kullanir, yani %80'i tekrar etmeyen icerik olur — bu
# yuzden sadece hareketli hedefte anlamlidir.
# Anahtar ise koherent ortalamadir: tekrar etmeyen her sey ortalamada sifira
# gider, geriye SADECE SABIT sinyaller kalir. Bedeli cozunurluk: ~20 MHz ->
# c/(2B) ~ 7.5 m. Bu, deterministik icerigin FIZIKSEL siniridir.
REF_SRC      = "key"
WB_MODE      = False         # REF_SRC'den turetilir; dogrudan elleme
# Korelasyon blogu. 2'nin kuvveti olmali (FFT). 131072 ornek = 1.067 ms @122.88.
# Frekans cozunurlugu FS/WB_NFFT = 937.5 Hz -> equalizer icin fazlasiyla ince.
WB_NFFT      = 1 << 17
# Yakalama basina islenecek blok sayisi. Her blok bagimsiz bir menzil profili
# uretir; LOO MTI bunlarin arasinda calisir (>=2 sart, >=8 onerilir).
WB_NBLK      = 16
# TDD: UL/bosluk bloklarini at — tepe bloktan bu kadar dB asagidakiler atlanir.
WB_BLK_DYN_DB = 12.0
WB_RMAX_M    = 400.0        # CIR'de tutulan azami FAZLA menzil [m]
WB_NEG_M     = 30.0         # LOS'tan ONCEKI pay [m] (referans kirliligi aynasi)
# Spektral beyazlatma ustu: 1.0 = tam beyazlatma (uyumsuz filtre; menzil yan
# lobu en dusuk), 0.0 = saf uyumlu filtre (SNR en yuksek, yan lob kotu).
# Guclu LOS'ta 1.0 dogru secim; hucre cok zayifsa 0.5 dene.
WB_WHITEN    = 1.0
WB_OCC_DB    = 6.0          # isgal esigi: gurultu tabani (%10 dilim) + bu kadar dB
WB_GAP_MHZ   = 1.0          # isgal maskesinde bu kadar genis bosluklar kapatilir
WB_TAPER     = 0.08         # bant kenari Tukey inisi (menzil yan lobunu kirar)
WB_BW_MHZ    = None         # None -> bant OLCULUR. Sayi verilirse merkeze
WB_REF       = "ch0"        # referans kanal: "ch0" (saglam) | "beam" (TX'e huzme)
# --- frekans basina equalizer ---
EQ_ON        = True         # False -> equalizer uygulanmaz (karsilastirma icin)
EQ_GATE_M    = 8.0          # LOS tapasi kapisi [m] (+-). Bunun disi = cevre
EQ_REG       = 0.10         # MMSE ters regularizasyonu (bant kenarinda gurultu
# ═══════════════════════════════════════════════════════════════════
#  4) NR ZAMAN IZGARASI (TS38.211 5.3.1) — eski dosyayla birebir
# ═══════════════════════════════════════════════════════════════════
MU              = 1
SLOTS_PER_SF    = 2 ** MU
SLOTS_PER_FRAME = 10 * SLOTS_PER_SF          # 20
SLOT_DUR_S      = 1e-3 / SLOTS_PER_SF        # 0.5 ms
_sc      = FS / (480000 * 4096)
CP_NORM  = int(round(144 * 64 * 2 ** (-MU) * _sc))                 # 288
CP_LONG  = int(round((144 * 64 * 2 ** (-MU) + 16 * 64) * _sc))     # 352
LONG_CP_SYMS_IN_SF = (0, 7 * 2 ** MU)
N_SLOT = int(round(SLOT_DUR_S * FS))         # 61440 ornek = 0.5 ms
LEARN_MIN_SEG = int(10e-6 * FS)
# NR'de izin verilen SSB periyotlari [ms]. Baskin periyot BUNLARIN arasindan
# secilir; keyfi bir sayi (ardisik farklarin medyani gibi) NR'de anlamsizdir.
SSB_PERIODS_MS = (5.0, 10.0, 20.0, 40.0, 80.0, 160.0)
# ═══════════════════════════════════════════════════════════════════
#  7b) OCCASION DILIMLEME + KORELASYON PLANI
# ═══════════════════════════════════════════════════════════════════
# Pencere ilk occasion'da acilir (ornek 0 = occasion 0). Anahtar TEK dalga
# formudur ve kendi periyoduyla (--step, tipik 20 ms) tekrar eder -> 1 sinif.
# Bir yakalamada DOGRUDAN YOL binindeki bastirma bu esigin USTUNDE kalirsa o
# yakalamada MTI calismamistir (sabit icerik iptal olmamis). Waterfall'da butun
# menzillere yayilan parlak yatay cizgi olarak gorunur. -10 dB = "en az bir
# mertebe bastirilmis olmali".
MTI_SUP_WARN_DB = -10.0
# Sonuc grafikleri dB yerine LINEER olcekte cizilsin mi (--linear).
# dB zayif yankiyi one cikarir; lineer ise gucu oldugu gibi gosterir ve
# tepenin arka plana gercek oranini gozle okumayi kolaylastirir.
PLOT_LINEAR  = False
LOC_WIN_MS   = 100.0        # yakalama penceresi [ms]  (ilk ~80-100 ms deterministik)
LOC_DUR_S    = 120          # canli calisma suresi [s]  (saniyede 1 yakalama)
CAL_SECONDS  = 30           # her kalibrasyon asamasi [s]
CAL_VERIFY_N = 5            # kalibrasyon sonrasi bastirma dogrulama yakalamasi
# Ogrenilmis anahtarin TEKRAR PERIYODU [ms]. None -> NR frame periyodu (10 ms).
# TICARI SEBEKEDE deterministik olan sey SSB'dir ve varsayilan SSB periyodu
# 20 ms'dir -> `--step 20` ver. Yanlis step, occasion'larin yarisini BOSA
# dusurur (LOO MTI ve koherent ortalama bozulur). Dogru degeri --learn ciktisi
# soyler (bulunan araliklarin PPS ofsetleri arasindaki fark).
KEY_STEP_MS  = None
KEY_STEP_SRC = "--step ile verildi"   # nereden geldigi (rapor icin)
DIR_WIN = 3          # dogrudan yol ana lobu icin +- ornek (alpha kestirimi)
# ═══════════════════════════════════════════════════════════════════
#  3f) BANT SINIRI — komsu hucreler ISLENMEZ ve GOSTERILMEZ
# ═══════════════════════════════════════════════════════════════════
# Pencere 122.88 MHz genis ama BIZIM kanalimiz 100 MHz. Kalan ~23 MHz'te
# KOMSU tasiyicilar ve DDC gecis bandindan katlanan (alias) enerji var.
# Sahada olculdu (3530 MHz, kazanc 30 ve 10'da AYNI sekil):
#     3468.6..3473.6 MHz  -9.7 dB   <- pencere kenari, komsu/alias
#     3479  ..3499   MHz  -1.4 dB   <- BIZIM kanalimizin guclu kismi
#     3581  ..3586   MHz -31.2 dB   <- kanal biter (beklenen ust kenar 3579.14)
#     3586  ..3591   MHz -14.6 dB   <- pencere kenari, komsu/alias
# Bunlar isleme girerse:
#   * isgal edilen bant "tum pencere" (122.85 MHz) cikar — olculdu
#   * equalizer komsunun (BASKA yonden gelen) sinyaliyle kestirilir -> aci kayar
#   * gurultu tabani yanlis hesaplanir
# Bu yuzden BUTUN bant kararlari kanalin ICINE kisitlanir. Kapatmak icin
# --fullband (sadece TESHIS amacli; olcum icin ACIK birak).
BAND_LIMIT_ON = True
BAND_LIMIT_TW_HZ = 0.5e6     # gecis bandi. GUARD_BAND_HZ (845 kHz) icinde kalir,
WB_MAXMEM_MB = 512           # spektrum onbellegi siniri (self_eq iki gecisi icin)
# ═══════════════════════════════════════════════════════════════════
#  7e) NR HUCRE KIMLIGI — PSS/SSS -> PCI (baz istasyonunun "anahtari")
# ═══════════════════════════════════════════════════════════════════
# "Baz istasyonunu dinle ve anahtarini cikar"in dogrulanabilir hali: SSB icindeki
# PSS (N_ID_2) ve SSS (N_ID_1) dizileri cozulup PCI = 3*N_ID_1 + N_ID_2 bulunur.
# Bu, korelasyona giren sinyalin GERCEKTEN bir NR hucresi oldugunu ve HANGI
# hucre oldugunu ispatlar; ayrica SSB'nin PPS'e gore zaman ofsetini ve tekrar
# periyodunu verir (--step / t_ref icin dogru deger).
# TS 38.211 7.4.2.2 (PSS) ve 7.4.2.3 (SSS).
SSB_NSC   = 240              # SSB'nin altasiyici sayisi
PSS_NSC   = 127              # PSS/SSS uzunlugu
PSS_SC0   = 56               # SSB icinde PSS/SSS'in baslangic altasiyicisi
CELL_WIN_MS = 22.0           # --cell arama penceresi [ms] (SSB periyodu <=20 ms)
# ═══════════════════════════════════════════════════════════════════
#  7g) STANDARDA GORE SSB / CORESET#0 / SIB1  +  IKI BANT KARSILASTIRMASI
# ═══════════════════════════════════════════════════════════════════
# SORU: spektrumda IKI blok var (3460-3480 ve 3480-3580). Bunlar iki AYRI baz
# istasyonu mu, yoksa TEK bir gNB'nin iki tasiyicisi mi?
#
# PSS/SSS tek basina yetmez: iki tasiyicinin PCI'si zaten farkli olabilir (ayni
# sitede bile her hucreye ayri PCI verilir). Ayirt eden sey FIZIKSEL katmandir:
#
#   1) PBCH DMRS  (TS 38.211 7.4.1.4.1) — PCI *ve* SSB huzme indisi i_SSB ile
#      tohumlanir. Korele olursa o blokta GERCEKTEN o PCI'ye ait bir hucre var
#      demektir; ayrica kac huzme yayinlandigini soyler.
#   2) FREKANS SAPMASI [ppb] — ayni RU'dan cikan iki tasiyici AYNI osilatoru
#      kullanir, dolayisiyla ppb'leri BIREBIR aynidir. Ayri gNB'ler GPS'e kilitli
#      olsa bile birkac ppb ayrisir. Iki blogu AYNI yakalamada (ayni LO ile)
#      olctugumuz icin bizim kendi hatamiz ortak mod olarak tamamen dusuyor.
#   3) CERCEVE ZAMANLAMASI — ayni RU: SSB anlari ayni ornekte. Ayri site: hem
#      kendi senkron hatasi hem de FARKLI yayilim gecikmesi kadar kayar.
#   4) CORESET#0 / SIB1 (TS 38.213 Tablo 13-4 + TS 38.211 7.4.1.3.1) — bagimsiz
#      bir hucre SIB1 yayinlamak ZORUNDADIR. Alt blokta CORESET#0 yoksa orasi
#      ayri bir hucre degil, baska bir tasiyicidir (ya da baska operatordur).
SSB_SYMS   = 4               # SSB: 4 OFDM sembolu (PSS,PBCH,SSS+PBCH,PBCH)
PBCH_DMRS_N = 144            # SSB basina PBCH DMRS RE sayisi (60+24+60)
L_MAX_FR1  = 8               # 3-6 GHz FR1: en fazla 8 SSB huzmesi -> i_SSB 0..7
CELLS_WIN_MS = 45.0          # --cells yakalama penceresi [ms]
CELLS_N_CAP  = 8             # blok basina yakalama sayisi. TEK yakalama YETMEZ:
# Spektrum analizoru ile gorulen iki blok. --cells bunlari karsilastirir.
CELLS_BAND_A = (3460e6, 3480e6)    # alt blok  — komsu mu, ayni gNB mi?
CELLS_BAND_B = (3480e6, 3580e6)    # bizim kanal
# TS 38.213 Tablo 13-4 — {SSB, PDCCH} SCS = {30, 30} kHz, FR1, asgari kanal
# genisligi 5/10 MHz (n78/100 MHz bu satira duser).
#   (mux deseni, N_RB^CORESET, N_symb^CORESET, offset [RB])
# offset = CORESET#0'in en kucuk RB'sinden SSB'nin en kucuk RB'sine mesafe.
CORESET0_TABLE_13_4 = [
    (1, 24, 2,  0), (1, 24, 2,  1), (1, 24, 2,  2), (1, 24, 2,  3), (1, 24, 2, 4),
    (1, 24, 3,  0), (1, 24, 3,  1), (1, 24, 3,  2), (1, 24, 3,  3), (1, 24, 3, 4),
    (1, 48, 1, 12), (1, 48, 1, 14), (1, 48, 1, 16),
    (1, 48, 2, 12), (1, 48, 2, 14), (1, 48, 2, 16),
]
CELLS_SPAN_FRAC = 0.80       # tek yakalamada guvenli kapsam. DDC yariband
DET_MIN_DB = -6.0            # bir dilimi "sabit" saymak icin asgari determinizm
# ══════════════════════════════════════════════════════════════════
#  7f) KABLOLU (SPLITTER) DIZI KALIBRASYONU  —  --wcal
# ══════════════════════════════════════════════════════════════════
# ACI (kanallar arasi genlik+faz) SADECE BURADAN GELIR.
#
# Chirp kaynagi AYRI BIR PROSESTE calisir (fmcw_tx_turkcell_calib.py, N321).
# Bu dosya onunla konusMAZ; sadece "hazir oldugunda ENTER'a bas" der. Boylece
# ALICI OTURUMU TEKTIR — iki ayri prosesin alici acmasi, ZBX'te LO export
# olmadigi icin kanal fazlarini rastgele yeniden oturtur ve kalibrasyonu bozar.
#
# NEDEN LOS'TAN DEGIL: LOS'tan kanal kalibrasyonu cikarmak, "dogrudan yol
# gercekten TX_POS yonunden geliyor" varsayimini aci olcumunun ICINE gomer.
# Varsayim yanlissa (NLOS, baskin yansima, TX konumu hatali) aci sessizce kayar
# ve hicbir yerde kendini belli etmez: olcum kendi varsayimini dogrular.
# Kabloda boyle dongusel bir bagimlilik yoktur — dort kanala giren sinyal
# FIZIKSEL OLARAK aynidir, olculen fark yalnizca donanimdir.
#
# Ayni yontem sahada saglam calisan eski kodda da izleniyor:
# 3aug_radar/4rx_1tx_kdyf_80mhz_v1.py:calib_run — "gNB/RU KAPALI olmali,
# yardimci TX dizinin tam karsisinda 0 derecede". Splitter, o yontemin kablolu
# hali; uzak alan ve cok yolluluk sartlarini da ortadan kaldirir.
#
# LOS'un bu dosyadaki TEK rolu, MENZIL SIFIR NOKTASIDIR (n_dir, kanal 0
# uzerinden okunur). Kanallar arasi hicbir sey LOS'tan alinmaz.
WCAL_FILE      = "kablolu_cal.npz"
WCAL_SECONDS   = 10          # kalibrasyon toplama suresi [s]
WCAL_NFFT      = 8 * 12288   # 98304 ornek = 800 us = 8 tam chirp periyodu
WCAL_OCC_DB    = 10.0        # isgal esigi: taban (%10 dilim) + bu kadar dB
WCAL_NG        = 8           # equalizer FIR yari-uzunlugu (+-65 ns kablo farki)
WCAL_COH_MIN   = 0.99        # kabloda beklenen koherans (havada 0.3-0.7)
WCAL_PEAK_MAX  = 0.85        # I ya da Q bunu gecerse KIRPMA
WCAL_PEAK_MIN  = 0.02        # bunun altinda sinyal cok zayif
# ── CHIRP AYIKLAMA — baz istasyonu ayni bantta yayin yaparken ────────
# SORUN: havadan kalibrasyonda hucre chirp ile AYNI bantta ve hep aciktir.
# Sahada olculdu: taban -22 dB (kabloda -59), koherans 0.69 (kabloda 0.999),
# yani chirp ile girisim neredeyse esit gucte.
#
# COZUM: chirp'i BIZ uretiyoruz, yani tam olarak biliyoruz. Iki kaldirac var:
#   1) UYUMLU FILTRE  — 100 us x 110 MHz -> TB carpimi 1.1e4 -> ~40 dB kazanc.
#      Chirp'in nerede basladigini bulmak icin kullanilir.
#   2) PERIYODA KATLAMA — chirp her 100 us'de AYNI gelir, hucrenin sinyali
#      gelmez. Periyoda katlayip KOHERENT ortalayinca chirp N kat, hucre
#      sqrt(N) kat buyur -> 10*log10(N) dB kazanc. 100 ms'lik yakalamada
#      1000 chirp var; 8 gruba bolunce grup basina ~21 dB.
# Gruplar ayri "blok" olarak birakilir ki koherans OLCULEBILSIN (tek blokta
# koherans hep 1 cikar, hicbir sey soylemez).
OCAL_CHIRP_DUR   = 100e-6    # fmcw_tx_turkcell_calib.py: CHIRP_DUR
OCAL_CHIRP_BW    = 110e6     # fmcw_tx_turkcell_calib.py: SWEEP_BW
OCAL_CHIRP_ALPHA = 0.15      # fmcw_tx_turkcell_calib.py: TAPER_ALPHA
OCAL_TX_RATE     = 245.76e6  # fmcw_tx_turkcell_calib.py: SAMPLE_RATE
OCAL_N_GRP       = 8         # katlamada grup sayisi (koherans icin >=4)
OCAL_CHUNK       = 256       # toplu FFT yigin boyutu (n_grp'nin kati olmali)
# ── HAVADAN (HORN) KALIBRASYON — 0 derece broadside ──────────────────
# NEDEN 0 DERECE: broadside'da dalga cephesi dizi eksenine DIKTIR, yani dort
# elemana yol uzunlugu esittir ve geometrik faz farki SIFIRDIR. Olculen faz
# farki tamamen DONANIMDAN gelir — splitter ile aynisi. Baska bir acidan
# basilirsa gercek bir faz rampasi olusur ve kalibrasyon onu "donanim" sanip
# soguruyor; o andan sonra butun acilar o kadar kayik cikar.
OCAL_MIN_RANGE_M = 3.0       # yakin alan egriligi icin asgari mesafe (asagi bak)
AUTO_WCAL_N  = 20            # kablolu kalibrasyon olcum sayisi (~20 s)
# ═══════════════════════════════════════════════════════════════════
#  9b) KANAL-BASINA MENZIL TANISI — arka plan cikarma + range ISPATI
# ═══════════════════════════════════════════════════════════════════
# Backprojection'a (aci + kalibrasyon) GECMEDEN once en temel seyi ispatla:
# HER KANALDA, arka plan cikarilinca dogrudan yol kayboluyor mu ve hedef
# beklenen bistatik menzilde bir tepe olarak beliriyor mu? Dort kanal AYRI
# AYRI cizilir. Hepsinde ayni menzilde tepe cikiyorsa arka plan cikarma ve
# range dogru demektir; sonra aci/kalibrasyona gecilebilir.
RANGE_RMAX_M = 60.0          # VARSAYILAN x ekseni ust siniri; --rmax ile ezilir
# ═══════════════════════════════════════════════════════════════════
#  10b) --psd — BANT TANISI (ogrenmeden ONCE calistir)
# ═══════════════════════════════════════════════════════════════════
# Ticari bir baz istasyonunu dinlemeye baslarken ilk soru "dogru frekansta
# miyim ve kazanc dogru mu?" — bu mod tek yakalamadan iki sey gosterir:
#   1) SPEKTRUM  : tasiyici gercekten burada mi, kenarlari nerede (isgal bandi)
#   2) ZAMAN     : pencere icinde gucun nasil degistigi -> TDD DL/UL deseni ve
#                  DL yayininin PPS'e gore NEREDE oldugu (--learn bunu bulacak)
# Kirpma (clipping) uyarisi RX_GAIN icin: tepe -6 dBFS'i gecmesin.
PSD_NFFT   = 4096
PSD_TBIN_S = 50e-6           # zaman profili bini
PSD_WIN_MS = 40.0            # varsayilan pencere (--learn-win ile ezilir)
# ═══════════════════════════════════════════════════════════════════
#  11) --learn — deterministik sinyali ogren (eski dosyayla ayni format)
# ═══════════════════════════════════════════════════════════════════
LEARN_N_DEF     = 120
LEARN_WIN_MS    = 40.0
LEARN_GAMMA_MIN = 0.5
LEARN_SMOOTH    = 129
LEARN_FILE      = "signal_key.npz"
# Bu kadar kisa bosluklarla ayrilmis tutarli araliklar TEK anahtar sayilir.
# 1 OFDM sembolu (30 kHz SCS) ~35.7 us -> bir sembolluk bosluk birlestirilir,
# HUZMELER arasi (daha genis) bosluklar birlestirilMEZ.
LEARN_MERGE_US  = 40.0
# Anahtarin AZAMI uzunlugu. Bir SSB 4 sembol = ~142.7 us (30 kHz SCS).
# NEDEN SINIR VAR: ticari hucre cok huzmeli (beam-swept) SSB burst set yayar;
# tutarli bolge 3-4 ms boyunca kesintisiz olabilir (8 huzme birden). Hepsini
# referans yapmak CAZIP ama YANLIS: hedefi tek huzme aydinlatiyorsa korelasyon
# tepesi o huzmenin enerjisiyle (E_j) buyur, gurultu ise TUM referansin
# enerjisiyle (E_top) -> SNR ~ E_j^2/E_top, yani tek huzme kullanmaktan KOTU.
# Ayrica occasion dilimine (N_SLOT) sigmaz. Bu yuzden en guclu TEK SSB alinir.
# Olculen (2026-08-06, PCI 693): anahtarin BANDI uzunluktan BAGIMSIZ 33.3 MHz;
# uzunluk yalnizca ENERJI ekliyor. 200->800 us +3.5 dB kazandiriyor ve yakalama
# basina maliyet 0.05 -> 0.22 s. Bu yuzden varsayilan 800 us.
# DIKKAT: eger bir hucrede deterministik olan SADECE SSB ise (bant 7.2 MHz
# cikar), uzun anahtar cok huzmeli burst set'i icine alir ve hedefi tek huzme
# aydinlatiyorsa SNR DUSER. O durumda --keymax 200 ile karsilastir; --range
# ciktisi hangisinin gercekte daha iyi oldugunu soyler.
LEARN_KEY_MAX_US = 800.0
# ═══════════════════════════════════════════════════════════════════
#  11b) --keydiff — IKI ANAHTARI KARSILASTIR
# ═══════════════════════════════════════════════════════════════════
# Anahtar iki sey tasir: baz istasyonunun YAYDIGI dalga formu ve onun bize
# gelirken gectigi KANAL. Ayni hucre ayni frekanstan iki kez ogrenilirse
# yayilan kisim AYNIDIR -> kalan fark KANALDIR. Bu mod once "gercekten ayni
# sinyal mi" (RF ayari/hucre/bant) diye sorar, sonra kalani kanal olarak olcer.
KEYDIFF_NFFT_MIN     = 4096
KEYDIFF_SLICE_MHZ    = 5.0    # bant profili dilim genisligi
KEYDIFF_RHO_SAME     = 0.70   # bu uzerinde "ayni dalga formu"
KEYDIFF_RHO_WEAK     = 0.30   # bu altinda "iliskisiz"
KEYDIFF_BIN_FLOOR_DB = -20.0  # anahtarin bandi: tepeden bu kadar asagisi
KEYDIFF_CIR_PEAKS    = 6      # raporlanan azami yol sayisi
KEYDIFF_CIR_FLOOR_DB = -20.0  # CIR tepesi sayilmak icin asgari seviye
# ═══════════════════════════════════════════════════════════════════
#  12) MAIN
# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════
#  10) GEOMETRI GIRISI — sorarak al, dosyaya yaz, bir daha sorma
# ═══════════════════════════════════════════════════════════════════
# Konum kestirimi GEOMETRI OLMADAN yapilamaz: bistatik menzil bir ELIPS,
# aci bir ISIN verir; (x,y) ikisinin kesisimidir. Elipsin odaklari TX ve RX,
# isinin baslangici RX ve sifir yonu dizinin normalidir. Yani TX/RX konumu ve
# dizinin baktigi yon bilinmeden menzil+aci bir noktaya donusmez.
GEOM_FILE = "geometri.json"


try:
    import uhd
    _HAVE_UHD = True
except ImportError:
    _HAVE_UHD = False




                             # Bunlar sadece BEKLENTI/uyari icindir; islenen
                             # bant her zaman OLCULUR (bkz. wb_setup / --bw).
                             # 40 ve 60'ta yaygin kirpma vardi ve koheransi
                             # bozuyordu; 10'da ise ~15 dB bosa gidiyordu.










                                            # gercek yon icin --rxdir










                            # simetrik bu genislik ZORLANIR (--bw)

                            # yankisi; equalizer'a KARISMAMALI.
                            # patlamasini onler; azami kazanc ~1/(2*EQ_REG))














_GRID_WARNED = False














# ═══════════════════════════════════════════════════════════════════
#  5) TS 38.211 5.2.1 — SOZDE RASGELE (Gold) DIZI
# ═══════════════════════════════════════════════════════════════════
# Butun NR referans sinyalleri (PBCH/PDCCH/PDSCH DMRS) bu diziden turer.
_GOLD_X1 = None                        # x1 c_init'ten BAGIMSIZ -> bir kez uret












# ALICI OTURUMU TEKTIR. Bir kez acilir, program boyunca ayni kalir.
# NEDEN: ZBX'te LO export desteklenmiyor (donanimda dogrulandi:
# "set_rx_lo_export_enabled is not supported on this radio"), dolayisiyla dort
# kanalin LO'su ayri kilitleniyor ve HER ACILISTA kanallar arasi faz RASTGELE
# oturuyor. Kablolu kalibrasyon tam olarak o fazlari olcer; ikinci bir oturum
# acilirsa olculen degerler gecersizlesir. Bu yuzden setup_x410 ikinci kez
# cagrilinca YENI oturum acmaz, mevcut olani dondurur.
_SESSION = None



















_CHAIN = False      # --auto zinciri: oturum bilerek tek sefer acilir, asamalar
                    # farkli pps_offset ister ve bu KAYMA ILE cozulur -> o
                    # durumda "oturum farkli parametrelerle acilmisti" uyarisi
                    # dogru degil, gurultu yapar.
















































# ═══════════════════════════════════════════════════════════════════
#  7d) GENIS BANT (WB) — LOS REFERANS KANALI + FREKANS BASINA EQUALIZER
# ═══════════════════════════════════════════════════════════════════
# Bu bolum dosyanin ASIL yenisi. Ogrenilmis dar bant anahtar yerine DOGRUDAN
# YOLU (LOS) referans alir; boylece cozunurluk anahtarin degil TASIYICININ
# bandiyla belirlenir. Ayrintili gerekce icin dosya basindaki "GENIS BANT (WB)
# MOD" ve "FREKANS BASINA EQUALIZER" bloklarina bak.
try:
    from scipy import fft as _sfft
    _FFT, _IFFT = _sfft.fft, _sfft.ifft
    _FFT_C = np.complex64                  # scipy tek duyarlikli calisir (2x hizli)
except Exception:                          # scipy yoksa numpy (her zaman float64)
    _FFT, _IFFT = np.fft.fft, np.fft.ifft
    _FFT_C = np.complex128








                             # yani isgal edilen spektruma DOKUNMAZ; sadece tuglali
                             # kesimin zaman-alani cinlamasini yumusatir.
























































                             # sahada her kosuda baska PCI cikti (731/341,
                             # 287/471, 110/168, 761/720). Gercek hucre
                             # yakalamalar arasinda TEKRAR eder, gurultu etmez.
































                             # suzgeci Nyquist'e kadar duz DEGIL; pencerenin son
                             # ~%10'unda sinyal bastirilir. 120 MHz'lik bir
                             # kapsami 122.88 MHz pencereye "sigdirmak" alt blogu
                             # etege oturtur ve SSB'yi kaybettirir.













_WCAL = None                 # kablolu kalibrasyon sonucu (taps). None -> yok.




















































































































_GEOM_CLI = {}          # komut satirindan gelen geometri; DOSYAYI EZER






# ===================================================================
#  GPU HIZLANDIRMA — cupy varsa GPU, yoksa ayni numpy yolu
# ===================================================================

def gpu_mod():
    """cupy modulu (kullanilabilirse), yoksa None. Bir kez denenir."""
    global _CP, _GPU_TRIED
    if _GPU_TRIED:
        return _CP
    _GPU_TRIED = True
    if not GPU_ENABLE:
        return None
    try:
        import cupy as cp
        cp.zeros(1)                      # surucu gercekten calisiyor mu
        _CP = cp
    except Exception:
        _CP = None
    return _CP

def gpu_bilgi():
    """Tek satirlik durum metni (baslangicta yazilir)."""
    cp = gpu_mod()
    if cp is None:
        return ("GPU: kapali (GPU_ENABLE=False)" if not GPU_ENABLE
                else "GPU: yok -> numpy")
    try:
        d = cp.cuda.runtime.getDeviceProperties(0)
        ad = d["name"].decode() if isinstance(d["name"], bytes) else str(d["name"])
        free, tot = cp.cuda.runtime.memGetInfo()
        return f"GPU: {ad}  ({tot/2**30:.1f} GB, {free/2**30:.1f} GB bos)"
    except Exception:
        return "GPU: cupy var"

def gpu_fft(x, n=None, axis=-1):
    """FFT — buyuk dizide GPU, kucukte numpy (aktarim masrafi kazanci yer)."""
    cp = gpu_mod()
    if cp is None or x.size < GPU_MIN_SIZE:
        return np.fft.fft(x, n, axis=axis)
    g = cp.asarray(x)
    return cp.asnumpy(cp.fft.fft(g, n, axis=axis))

def gpu_ifft(x, n=None, axis=-1):
    cp = gpu_mod()
    if cp is None or x.size < GPU_MIN_SIZE:
        return np.fft.ifft(x, n, axis=axis)
    g = cp.asarray(x)
    return cp.asnumpy(cp.fft.ifft(g, n, axis=axis))

def gpu_filtre(x, w, n_out):
    """ifft(fft(x, nf) * w)[:n_out] — tek GPU gidis-donusunde.

    band_limit_sig/bandpass_sig'in tamami budur; ara diziyi CPU'ya
    tasimadan yapinca 100 ms'lik yakalamada 1093 ms -> ~50 ms'ye iner."""
    cp = gpu_mod()
    nf = len(w)
    if cp is None or x.size < GPU_MIN_SIZE:
        return np.fft.ifft(np.fft.fft(x, nf) * w)[:n_out]
    g = cp.asarray(x)
    W = cp.asarray(w)
    y = cp.fft.ifft(cp.fft.fft(g, nf) * W)[:n_out]
    return cp.asnumpy(y)

def gpu_bosalt():
    """GPU bellek havuzunu bosalt (uzun kosularda parcalanmayi onler)."""
    cp = gpu_mod()
    if cp is not None:
        try:
            cp.get_default_memory_pool().free_all_blocks()
        except Exception:
            pass



# ===================================================================
#  YARDIMCILAR — vektor, dizi geometrisi, izgara
# ===================================================================

# ═══════════════════════════════════════════════════════════════════
#  3d) GEOMETRI YARDIMCILARI
# ═══════════════════════════════════════════════════════════════════
def _unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    if n < 1e-12:
        raise ValueError("sifir uzunluklu yon vektoru")
    return v / n

def array_lambda():
    return C_AIR / CENTER_FREQ

def array_axis():
    """Eleman dizilim yonu (birim): ARRAY_N2'ye DIK ve YATAY (z=0).

    u = normalize( z_hat x n2 ).  n2 yatay oldugundan u da yatay ve n2'ye dik."""
    n2 = _unit(ARRAY_N2)
    u = np.cross(np.array([0.0, 0.0, 1.0]), n2)
    if np.linalg.norm(u) < 1e-9:
        # n2 dikeye yakinsa (olmamali, z=0 isteniyor) x eksenine dus
        u = np.array([1.0, 0.0, 0.0])
    return ARRAY_ORDER_SIGN * _unit(u)

def element_positions():
    """(N_RX, 3) — dizi elemanlarinin konumu. Orta nokta ARRAY_POS.

    Eleman k, ortadan (k - (N-1)/2)*d kadar u yonunde kayar."""
    u = array_axis()
    k = np.arange(N_RX) - (N_RX - 1) / 2.0
    return ARRAY_POS[None, :] + (k[:, None] * ARRAY_D_M) * u[None, :]

def check_spacing():
    """d < lambda/2 kosulu (aci belirsizligi olmamasi icin)."""
    half = array_lambda() / 2.0
    if ARRAY_D_M >= half + 1e-9:
        print(f"[UYARI] ARRAY_D_M={ARRAY_D_M*100:.2f} cm >= lambda/2="
              f"{half*100:.2f} cm. Aci belirsizligi (grating) olusabilir.")
    return half

def tx_pattern_gain(P):
    """TX huzme agirligi. P: (..., 3) noktalar. Doner: (...) [0..1].

    Baz istasyonu n1 etrafinda -3 dB tam genisligi TX_BW3_DEG olan Gaussian
    bir huzme ile yayilir. theta = (p-TX) ile n1 arasindaki aci.
    g = exp(-4 ln2 * (theta / TX_BW3)^2) -> theta = TX_BW3/2'de tam -3 dB."""
    if not USE_TX_PATTERN:
        return np.ones(P.shape[:-1])
    n1 = _unit(TX_N1)
    d = P - TX_POS[None, :] if P.ndim == 2 else P - TX_POS
    r = np.linalg.norm(d, axis=-1)
    cos_th = np.clip((d @ n1) / (r + 1e-12), -1.0, 1.0)
    th = np.degrees(np.arccos(cos_th))
    k = 4.0 * np.log(2.0)
    return np.exp(-k * (th / TX_BW3_DEG) ** 2)

def grid_axes(quiet=True):
    """Backprojection izgara eksenleri (x, y) metre. z=0 sabit.

    DIKKAT: eksen basina hucre sayisi GRID_MAX_CELLS ile sinirlidir. Istenen
    adim bu siniri asarsa GERCEK adim KABALASIR — sessizce olmasin diye ilk
    cagrida uyari basilir (olculdu: 110x130 m alanda 0.10 m isteyince 0.24 m
    aliniyor)."""
    global _GRID_WARNED
    if GRID_BOUNDS is not None:
        xmin, xmax, ymin, ymax = GRID_BOUNDS
    else:
        xs = [TX_POS[0], ARRAY_POS[0]]
        ys = [TX_POS[1], ARRAY_POS[1]]
        el = element_positions()
        xs += list(el[:, 0]); ys += list(el[:, 1])
        xmin, xmax = min(xs) - GRID_MARGIN_M, max(xs) + GRID_MARGIN_M
        ymin, ymax = min(ys) - GRID_MARGIN_M, max(ys) + GRID_MARGIN_M
    nx_w = int(round((xmax - xmin) / GRID_RES_M)) + 1
    ny_w = int(round((ymax - ymin) / GRID_RES_M)) + 1
    nx, ny = min(GRID_MAX_CELLS, nx_w), min(GRID_MAX_CELLS, ny_w)
    X = np.linspace(xmin, xmax, nx)
    Y = np.linspace(ymin, ymax, ny)
    if (nx < nx_w or ny < ny_w) and not _GRID_WARNED and not quiet:
        _GRID_WARNED = True
        dx = (X[1] - X[0]) if nx > 1 else 0.0
        dy = (Y[1] - Y[0]) if ny > 1 else 0.0
        print(f"  [UYARI] izgara {GRID_MAX_CELLS} hucre/eksen sinirina takildi:")
        print(f"          istenen adim {GRID_RES_M:.2f} m -> GERCEK adim "
              f"{dx:.2f} x {dy:.2f} m")
        print(f"          Daha ince istiyorsan ALANI kucult: "
              f"--grid XMIN XMAX YMIN YMAX")
    return X, Y

def bistatic_geometry(points):
    """points: (M, 3). Doner her eleman k icin bistatik menzil ve dogrudan yol.

    R_bi[k, m] = |p_m - TX| + |p_m - RX_k|
    D[k]       = |RX_k - TX|              (dogrudan yol; noktadan bagimsiz)
    excess[k,m]= R_bi - D0  (D0 = |ARRAY_POS - TX|, ortak referans)"""
    el = element_positions()                       # (N_RX, 3)
    r_tx = np.linalg.norm(points[None, :, :] - TX_POS[None, None, :], axis=-1)  # (1,M)->(N,M) yayilir
    r_rx = np.linalg.norm(points[None, :, :] - el[:, None, :], axis=-1)         # (N_RX, M)
    R_bi = r_tx + r_rx                             # (N_RX, M)
    D = np.linalg.norm(el - TX_POS[None, :], axis=-1)   # (N_RX,)
    D0 = float(np.linalg.norm(ARRAY_POS - TX_POS))
    return R_bi, D, D0



# ===================================================================
#  NR IZGARASI — sembol/slot zamanlamasi ve Gold dizisi
# ===================================================================

def cp_len(sym_in_slot, slot_in_frame):
    l_sf = (slot_in_frame % SLOTS_PER_SF) * NSYM_PER_SLOT + sym_in_slot
    return CP_LONG if l_sf in LONG_CP_SYMS_IN_SF else CP_NORM

def symbol_offsets(slot_in_frame):
    """Slot icindeki 14 sembolun (cp_basi, veri_basi, cp_uzunlugu) listesi."""
    out, n = [], 0
    for sy in range(NSYM_PER_SLOT):
        cp = cp_len(sy, slot_in_frame)
        out.append((n, n + cp, cp))
        n += cp + N_FFT
    return out

def _lfsr_bits(state, taps, n):
    """Fibonacci LFSR'i tamsayi uzerinde surer (numpy indekslemesinden ~5x hizli).

    state: 31 bitlik baslangic (bit0 = x[0]). taps: geri besleme bit konumlari."""
    out = bytearray(n)
    s = state & 0x7FFFFFFF
    for i in range(n):
        out[i] = s & 1
        fb = 0
        for t in taps:
            fb ^= s >> t
        s = (s >> 1) | ((fb & 1) << 30)
    return np.frombuffer(bytes(out), np.uint8)

def gold_sequence(c_init, length):
    """TS 38.211 5.2.1 — c(n) = x1(n+Nc) + x2(n+Nc), Nc = 1600."""
    global _GOLD_X1
    Nc, n_tot = 1600, length + 1600
    if _GOLD_X1 is None or _GOLD_X1.size < n_tot:
        _GOLD_X1 = _lfsr_bits(1, (3, 0), max(n_tot, 1 << 15))
    x2 = _lfsr_bits(c_init, (3, 2, 1, 0), n_tot)
    return _GOLD_X1[Nc:Nc + length] ^ x2[Nc:Nc + length]

def gold_qpsk(c_init, n_sym):
    """TS 38.211 5.2.1 diziden QPSK: r(m) = [(1-2c(2m)) + j(1-2c(2m+1))]/sqrt(2).

    Butun DMRS'ler (PBCH 7.4.1.4.1, PDCCH 7.4.1.3.1, PDSCH 7.4.1.1.1) boyle
    uretilir; aralarindaki tek fark c_init'tir."""
    b = gold_sequence(c_init, 2 * n_sym).astype(np.float64)
    return ((1.0 - 2.0 * b[0::2]) + 1j * (1.0 - 2.0 * b[1::2])) / np.sqrt(2.0)



# ===================================================================
#  DONANIM — X410 kurulumu, PPS, yakalama
# ===================================================================

# ═══════════════════════════════════════════════════════════════════
#  6) DONANIM — X410 4 KANAL RFNoC + GPSDO  (eski dosyayla birebir)
# ═══════════════════════════════════════════════════════════════════
def wait_for_pps_edge(tk, timeout=2.0):
    import time
    last = tk.get_time_last_pps().get_real_secs()
    dl = time.monotonic() + timeout
    while tk.get_time_last_pps().get_real_secs() == last:
        if time.monotonic() > dl:
            raise RuntimeError("PPS edge timeout — GPSDO anteni bagli/kilitli mi?")
        time.sleep(0.02)

def next_trigger(tk, offset_s):
    now = tk.get_time_now().get_real_secs()
    nxt = np.floor(now) + 1.0
    while (nxt + offset_s) - now < MIN_LEAD_S:
        nxt += 1.0
    return nxt + offset_s

def setup_x410(win_s=None, advance_s=None, pps_offset=None):
    """RFNoC: Radio -> DDC(decim) -> Replay(DRAM) -> rx_streamer, 4 kanal.

    Oturum zaten aciksa YENIDEN KURMAZ, mevcudunu dondurur (bkz. _SESSION)."""
    import time
    global _SESSION
    if _SESSION is not None:
        want = (win_s, advance_s, pps_offset)
        got = (_SESSION["req_win_s"], _SESSION["req_adv_s"], _SESSION["req_pps"])
        def _ne(a, b):
            if a is None or b is None:
                return False
            return abs(float(a) - float(b)) > 1e-9
        if any(_ne(a, b) for a, b in zip(want, got)) and _CHAIN:
            # --auto zincirinde bu BEKLENEN durumdur: oturum PPS+0'da acildi,
            # sonraki asamalar baska bir pps_offset ister ve bu, occasion
            # yerlesimindeki kayma ile (off0) cozulur. Uyari degil, bilgi.
            print(f"  [BILGI] oturum PPS+{got[2]*1e3:.2f} ms'de acik; istenen "
                  f"PPS+{(want[2] or 0)*1e3:.2f} ms fark, occasion kaymasiyla "
                  f"karsilaniyor.")
        elif any(_ne(a, b) for a, b in zip(want, got)):
            print("\n  [UYARI] mevcut alici oturumu FARKLI parametrelerle acilmisti:")
            print(f"          istenen pencere/advance/pps = {want}")
            print(f"          acik olan                    = {got}")
            print("          Oturum YENIDEN KURULMAZ (LO fazlari korunsun diye).")
            print("          Dogru sira: kalibrasyon asamasi oturumu, olcumun")
            print("          ihtiyac duydugu parametrelerle acar.")
        return _SESSION
    try:
        graph = uhd.rfnoc.RfnocGraph(ADDR)
    except Exception as e:
        print(f"[HATA] X410 baglantisi: {e}")
        print("       ADDR icindeki IP QSFP arayuzune ait mi? 'uhd_find_devices' calistir.")
        sys.exit(1)

    radio_ids  = graph.find_blocks("Radio")
    ddc_ids    = graph.find_blocks("DDC")
    replay_ids = graph.find_blocks("Replay")
    if not (radio_ids and ddc_ids and replay_ids):
        print("[HATA] Radio + DDC + Replay bloklari bulunamadi.")
        print(f"       Bulunanlar: {graph.find_blocks('')}")
        sys.exit(1)

    n_radio_need = max(r for r, _ in RX_CHANS) + 1
    if len(radio_ids) < n_radio_need or len(ddc_ids) < n_radio_need:
        print(f"[HATA] RX_CHANS {n_radio_need} Radio+DDC blogu istiyor; "
              f"bulunan Radio={len(radio_ids)} DDC={len(ddc_ids)}.")
        sys.exit(1)

    radios = [uhd.rfnoc.RadioControl(graph.get_block(radio_ids[r]))
              for r in range(n_radio_need)]
    ddcs   = [uhd.rfnoc.DdcBlockControl(graph.get_block(ddc_ids[r]))
              for r in range(n_radio_need)]
    replay = uhd.rfnoc.ReplayBlockControl(graph.get_block(replay_ids[0]))
    radio  = radios[0]

    if replay.get_num_input_ports() < N_RX:
        print(f"[HATA] Replay {replay.get_num_input_ports()} portlu, "
              f"{N_RX} kanal icin yetersiz.")
        sys.exit(1)

    print(f"\nRFNoC bloklari:")
    for r in range(n_radio_need):
        print(f"  Radio  : {radio_ids[r]}   DDC: {ddc_ids[r]}")
    print(f"  Replay : {replay_ids[0]}   DRAM {replay.get_mem_size()/1e9:.2f} GB, "
          f"{replay.get_num_input_ports()} port")
    print(f"  Dizi   : {N_RX} kanal  " +
          "  ".join(f"k{k}={radio_ids[r]}:ch{c}"
                    for k, (r, c) in enumerate(RX_CHANS)))

    mb = graph.get_mb_controller(0)
    tk = mb.get_timekeeper(0)

    # --- GPSDO: kilidi bekle, zaman tabanini GPS saniyesine otur ---
    print("\nGPSDO:")
    GPS_LOCK_TIMEOUT_S = 600
    dl = time.monotonic() + GPS_LOCK_TIMEOUT_S
    waiting = False
    while True:
        try:
            if mb.get_sensor("gps_locked").to_bool():
                print("  gps_locked : OK")
                break
        except Exception as e:
            print(f"  [UYARI] gps_locked sensoru okunamadi ({e})")
            break
        if time.monotonic() > dl:
            raise RuntimeError("GPS kilidi zaman asimi")
        if not waiting:
            print(f"  kilit bekleniyor (en fazla {GPS_LOCK_TIMEOUT_S/60:.0f} dk)...")
            waiting = True
        time.sleep(2.0)
    try:
        wait_for_pps_edge(tk)
        gps_t = mb.get_sensor("gps_time").to_int()
        tk.set_time_next_pps(uhd.types.TimeSpec(float(gps_t + 1)))
        time.sleep(1.1)
        print(f"  zaman tabani GPS'e ayarlandi -> {tk.get_time_now().get_real_secs():.6f} s")
    except Exception as e:
        print(f"  [UYARI] gps_time yok ({e}); PPS'e goreli sifirlaniyor.")
        wait_for_pps_edge(tk)
        tk.set_time_next_pps(uhd.types.TimeSpec(0.0))
        time.sleep(1.1)

    # --- RF: 4 kanalin hepsi ayni frekans/kazanc/anten ---
    for k, (r, c) in enumerate(RX_CHANS):
        radios[r].set_rx_frequency(CENTER_FREQ, c)
        radios[r].set_rx_gain(RX_GAIN, c)
        radios[r].set_rx_antenna(RX_ANTENNA, c)
    radio_rate = radio.get_rate()
    print(f"\nRF:")
    print(f"  radio rate : {radio_rate/1e6:.3f} Msps (MCR)")
    for k, (r, c) in enumerate(RX_CHANS):
        fe = radios[r].get_rx_frequency(c) - CENTER_FREQ
        print(f"  kanal {k}    : {radios[r].get_rx_frequency(c)/1e6:.6f} MHz "
              f"(LO hatasi {fe:+.3f} Hz)  {radios[r].get_rx_gain(c):.1f} dB / "
              f"{radios[r].get_rx_antenna(c)}")

    # --- LO paylasimi: kanallar arasi faz uyumu icin ---
    lo_shared = True
    try:
        src_r, src_c = RX_CHANS[0]
        for lo in radios[src_r].get_rx_lo_names(src_c):
            radios[src_r].set_rx_lo_source("internal", lo, src_c)
            radios[src_r].set_rx_lo_export_enabled(True, lo, src_c)
        for k, (r, c) in enumerate(RX_CHANS[1:], start=1):
            for lo in radios[r].get_rx_lo_names(c):
                radios[r].set_rx_lo_source("external", lo, c)
    except Exception as e:
        lo_shared = False
        print(f"  [UYARI] LO paylasimi kurulamadi ({e})")
        print(f"          Kanallar bagimsiz LO -> her acilista --calib tekrarla.")
    if lo_shared:
        print(f"  LO        : kanal 0 export, digerleri external (paylasimli)")

    # --- Pencere boyutu ---
    burst_n = N_SLOT                 # en kisa anlamli pencere: bir slot (0.5 ms)
    if advance_s is None:
        advance_s = ADVANCE_MS * 1e-3
    if pps_offset is None:
        pps_offset = PPS_OFFSET_S
    if win_s is None:
        win_s = ADVANCE_MS * 1e-3 + burst_n / FS + MARGIN_MS * 1e-3
    N_win = int(win_s * FS)
    word = replay.get_word_size()
    nb = N_win * 4
    nb += (word - nb % word) % word
    N_act = nb // 4
    mem_off = [k * nb for k in range(N_RX)]
    if N_RX * nb > replay.get_mem_size():
        print(f"[HATA] DRAM yetersiz: {N_RX} x {nb/1e6:.1f} MB > "
              f"{replay.get_mem_size()/1e9:.2f} GB"); sys.exit(1)

    # --- RFNoC baglantilari ---
    st = uhd.usrp.StreamArgs("fc32", "sc16")
    rx_streamer = graph.create_rx_streamer(N_RX, st)
    for k, (r, c) in enumerate(RX_CHANS):
        graph.connect(ddc_ids[r], c, replay_ids[0], k)
        graph.connect(replay_ids[0], k, rx_streamer, k)
    graph.commit()

    for k, (r, c) in enumerate(RX_CHANS):
        ddcs[r].set_input_rate(radio_rate, c)
        ddcs[r].set_output_rate(FS, c)
        got = ddcs[r].get_output_rate(c)
        if abs(got - FS) > 1.0:
            print(f"\n[HATA] kanal {k}: Fs={FS/1e6:.3f} MHz elde edilemedi "
                  f"({got/1e6:.3f}). ADDR icinde master_clock_rate=245.76e6 var mi?")
            sys.exit(1)
    print(f"\nDDC: {radio_rate/1e6:.3f} -> {FS/1e6:.3f} Msps "
          f"(decim {radio_rate/FS:.0f}), {N_RX} kanalin hepsi")

    for k in range(N_RX):
        replay.set_record_type("sc16", k)
        replay.set_play_type("sc16", k)

    n_adv = int(advance_s * FS)
    print(f"\nYakalama:")
    print(f"  Fs={FS/1e6:.2f} MHz  N_FFT={N_FFT}  pencere {N_act/FS*1e3:.1f} ms "
          f"({nb/1e6:.1f} MB/kanal, toplam {N_RX*nb/1e6:.1f} MB)")
    print(f"  RX acilir : PPS {(pps_offset - advance_s)*1e3:+.3f} ms")
    el = element_positions()
    print(f"  dizi      : {N_RX} eleman, d={ARRAY_D_M*100:.2f} cm "
          f"(lambda/2={array_lambda()/2*100:.2f} cm)")

    _SESSION = dict(graph=graph, radios=radios, radio=radio, ddcs=ddcs,
                    replay=replay, rx_streamer=rx_streamer, tk=tk,
                    N_act=N_act, nb=nb, mem_off=mem_off, n_adv=n_adv,
                    burst_n=burst_n, adv_s=advance_s, pps_off=pps_offset,
                    req_win_s=win_s, req_adv_s=advance_s, req_pps=pps_offset)
    return _SESSION

def retune(ctx, f_hz, quiet=False):
    """Acik oturumu baska bir merkez frekansa al (CENTER_FREQ global'i dahil).

    DIKKAT: ZBX'te LO ihrac edilemedigi icin her tune KANALLAR ARASI FAZI
    RASGELE degistirir. Bu yuzden olcum/kalibrasyon oturumunda ASLA
    kullanilmaz — sadece --cells gibi tek kanalla calisan teshis modlari icin.
    Frekans DOGRULUGU etkilenmez (GPSDO'ya kilitli), bozulan sey fazdir."""
    for r, c in RX_CHANS:
        ctx["radios"][r].set_rx_frequency(f_hz, c)
    globals()["CENTER_FREQ"] = f_hz
    r0, c0 = RX_CHANS[0]
    got = ctx["radios"][r0].get_rx_frequency(c0)
    if not quiet:
        print(f"  LO -> {got/1e6:.6f} MHz  (istenen {f_hz/1e6:.3f} MHz, "
              f"hata {got-f_hz:+.3f} Hz)")
    return got

def acquire(ctx):
    """PPS hizali tek yakalama, N_RX kanal. Doner: (samples|None, t_trig).

    samples sekli (N_RX, N_act). Tum kanallar AYNI time_spec ile tetiklenir."""
    import time
    radios, replay = ctx["radios"], ctx["replay"]
    streamer, tk = ctx["rx_streamer"], ctx["tk"]
    N_act, nb, mem_off = ctx["N_act"], ctx["nb"], ctx["mem_off"]

    dl = time.monotonic() + 0.5
    while any(replay.get_record_fullness(k) > 0 for k in range(N_RX)) \
            and time.monotonic() < dl:
        for k in range(N_RX):
            replay.record_restart(k)
        time.sleep(0.01)
    for k in range(N_RX):
        replay.record(mem_off[k], nb, k)

    t_trig = next_trigger(tk, ctx["pps_off"])
    t_open = t_trig - ctx["adv_s"]

    for k, (r, c) in enumerate(RX_CHANS):
        cmd = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
        cmd.num_samps  = N_act * DECIM
        cmd.stream_now = False
        cmd.time_spec  = uhd.types.TimeSpec(t_open)
        radios[r].issue_stream_cmd(cmd, c)

    now = tk.get_time_now().get_real_secs()
    deadline = time.monotonic() + (t_open + N_act / FS - now) + 3.0
    while any(replay.get_record_fullness(k) < nb for k in range(N_RX)):
        if time.monotonic() > deadline:
            return None, t_trig
        time.sleep(0.001)

    for k in range(N_RX):
        replay.config_play(mem_off[k], nb, k)
    p = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
    p.num_samps, p.stream_now = N_act, True
    for k in range(N_RX):
        replay.issue_stream_cmd(p, k)

    buf = np.zeros((N_RX, N_act), np.complex64)
    md  = uhd.types.RXMetadata()
    tmp = np.zeros((N_RX, 65536), np.complex64)
    tot, to = 0, 3.0
    while tot < N_act:
        n = streamer.recv(tmp, md, timeout=to)
        to = 1.0
        if n == 0 or md.error_code == uhd.types.RXMetadataErrorCode.timeout:
            break
        take = min(n, N_act - tot)
        buf[:, tot:tot + take] = tmp[:, :take]
        tot += take
    return (buf, t_trig) if tot >= N_act else (None, t_trig)

def adc_health(buf, sat=0.985):
    """ADC doyma TESHISI. Ciplak maksimum YETMEZ, ondan bu fonksiyon var.

    "tepe 0 dBFS" tek basina hicbir sey soylemez: 4.9 milyon ornekte TEK bir
    doymus ornek maksimumu sonsuza kadar 0 dBFS'e civiler ve kazanci ne kadar
    dusurursen dusur oyle kalir. Ayirt edici soru KAC ornegin ve NEREDE
    doydugudur:

      * cok az (<1e-5) ve BASTA toplanmis -> yakalama basi gecici olayi
        (DDC/Replay oturmasi, LO kaymasi). Gercek kirpma DEGIL, gormezden gel.
      * yaygin, orani kazancla DUSUYOR                -> normal kirpma,
        --gain dusur ve gecer.
      * yaygin, orani kazancla DUSMUYOR ve ORTALAMA da dusmuyor
        -> RF ON UC doymus (LNA/mikser, kazanc kademesinden ONCE).
           Dijital kazanc bunu KURTARMAZ; disaridan ZAYIFLATICI gerekir.
           Yakin bir makro hucrede tipik durumdur.

    Doner sozluk: frac (kanal basina doyma orani), n_sat, first/last indeks,
    head_frac (doymus orneklerin ilk %1'lik dilimde kalan orani), pk (ciplak
    maksimum), pk_rob (ilk %1 atilarak olculen tepe)."""
    n = buf.shape[1]
    head = max(1, n // 100)                       # ilk %1 = yakalama basi
    sat_m = (np.abs(buf.real) >= sat) | (np.abs(buf.imag) >= sat)
    n_sat = sat_m.sum(axis=1)
    idx = [np.flatnonzero(sat_m[k]) for k in range(buf.shape[0])]
    first = np.array([int(i[0]) if i.size else -1 for i in idx])
    last = np.array([int(i[-1]) if i.size else -1 for i in idx])
    head_n = np.array([int((i < head).sum()) for i in idx])
    pk = np.array([float(max(np.abs(buf[k].real).max(),
                             np.abs(buf[k].imag).max()))
                   for k in range(buf.shape[0])])
    pk_rob = np.array([float(max(np.abs(buf[k, head:].real).max(),
                                 np.abs(buf[k, head:].imag).max()))
                       for k in range(buf.shape[0])])
    return dict(frac=n_sat / float(n), n_sat=n_sat, first=first, last=last,
                head_frac=head_n / np.maximum(n_sat, 1), pk=pk, pk_rob=pk_rob,
                head=head, n=n)

def adc_report(h, avg_db, rx_gain):
    """adc_health ciktisini yorumla ve bas. Doner (gercek_kirpma, oneri_metni)."""
    worst = float(h["frac"].max())
    print(f"\n  ADC DOYMA TESHISI (ciplak tepe TEK basina yaniltir):")
    print(f"  {'kanal':>6} {'doymus':>9} {'oran':>11} {'ilk %1de':>9} "
          f"{'tepe':>8} {'tepe(bassiz)':>13}")
    for k in range(len(h["frac"])):
        print(f"  {k:>6} {h['n_sat'][k]:>9d} {h['frac'][k]:>10.2e} "
              f"{h['head_frac'][k]*100:>8.0f}% "
              f"{20*np.log10(h['pk'][k]+1e-30):>+7.1f} "
              f"{20*np.log10(h['pk_rob'][k]+1e-30):>+12.1f} dBFS")
    if worst == 0.0:
        print("  -> doymus ornek YOK.")
        return False, ""
    head_dom = float(np.nanmean(np.where(h["n_sat"] > 0, h["head_frac"], np.nan)))
    if worst < 1e-5 and head_dom > 0.5:
        print(f"  -> doyma cok seyrek ({worst:.1e}) ve cogu yakalama BASINDA "
              f"(ilk {h['head']} ornek).")
        print(f"     Bu bir GECICI OLAYDIR (DDC/Replay oturmasi), gercek kirpma")
        print(f"     degil. 'tepe(bassiz)' sutunu gercek seviyeyi verir.")
        return False, ""
    if worst < 1e-5:
        print(f"  -> doyma cok seyrek ({worst:.1e}) ama basa toplanmamis. "
              f"Tek tuk asiri tepe; OFDM'de normaldir.")
        return False, ""
    print(f"  -> YAYGIN doyma (en kotu kanal %{worst*100:.3f}). GERCEK KIRPMA.")
    print(f"     Kazanci dusur; ORTALAMA guc ({avg_db:+.1f} dBFS) da dusuyorsa")
    print(f"     dijital kirpmadir ve gecer. Kazanci dusurdugun halde ORTALAMA")
    print(f"     DEGISMIYORSA RF on uc doymustur (kazanc kademesinden ONCE) ->")
    print(f"     dijital kazanc kurtarmaz, DISARIDAN ZAYIFLATICI gerekir.")
    return True, f"--gain {max(0.0, rx_gain - 6):.0f} ile tekrar dene"



# ===================================================================
#  ANAHTAR — ogrenme, yukleme, determinizm
# ===================================================================

# ═══════════════════════════════════════════════════════════════════
#  7) REFERANS / ANAHTAR + KORELASYON YARDIMCILARI
# ═══════════════════════════════════════════════════════════════════
def _segments(mask, min_len):
    m = np.asarray(mask, bool)
    if not m.any():
        return []
    d = np.diff(m.astype(np.int8))
    starts = list(np.flatnonzero(d == 1) + 1)
    ends = list(np.flatnonzero(d == -1) + 1)
    if m[0]:
        starts.insert(0, 0)
    if m[-1]:
        ends.append(len(m))
    return [(int(s), int(e)) for s, e in zip(starts, ends) if e - s >= min_len]

def dominant_period_ms(offsets_s, win_s, cands=SSB_PERIODS_MS, tol_us=30.0):
    """Ofset listesinden BASKIN tekrar periyodunu bul.

    ARDISIK FARKLAR ISE YARAMAZ: cok huzmeli (beam-swept) bir SSB burst set'inde
    tek periyot icinde onlarca parca vardir ve ardisik farklar o parcalarin
    ic araliklarini olcer (tipik hata: "periyot 0.02 ms"). Dogru olcut, her aday
    periyot icin "kac ofsetin tam +P otede bir esi var" saymaktir.

    Doner (P_ms | None, eslesme_sayisi, toplam)."""
    o = np.sort(np.asarray(offsets_s, float))
    if o.size < 2:
        return None, 0, int(o.size)
    tol = tol_us * 1e-6
    best, bn = None, 0
    for P in cands:
        p = P * 1e-3
        if p > win_s - tol:          # pencereye sigmayan periyot GORULEMEZ
            continue
        n = int(np.sum([np.min(np.abs(o - (x + p))) < tol for x in o
                        if x + p <= o[-1] + tol]))
        if n > bn:
            best, bn = P, n
    return best, bn, int(o.size)

def merge_segments(segs, max_gap):
    """Aralarindaki bosluk max_gap'ten kucuk olan araliklari birlestir.

    Bir SSB 4 sembolduk (~142 us) ama PBCH VERI bitleri SFN ile degistigi icin
    ortasindaki bazi ornekler tutarlilik esigini gecemez ve aralik parcalanir.
    Birlestirince anahtar SSB'nin TAMAMINI kapsar -> daha cok koherent enerji.
    Bosluktaki ornekler ortalamada ~0 oldugu icin korelasyona gurultu de tasimaz."""
    if not segs:
        return []
    out = [list(segs[0])]
    for a, b in segs[1:]:
        if a - out[-1][1] <= max_gap:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(int(a), int(b)) for a, b in out]

def load_key(path):
    """Ogrenilmis anahtari yukle. Doner: (referans, PPS'ten baslangic [s], meta)."""
    if not os.path.isabs(path):
        cand = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        path = cand if os.path.exists(cand) else path
    if not os.path.exists(path):
        print(f"[HATA] anahtar dosyasi yok: {path}")
        print("       Once eski dosyanin --learn'i ya da bu dosyanin --learn'i ile ogren.")
        sys.exit(1)
    d = np.load(path)
    if abs(float(d["fs"]) - FS) > 1.0:
        print(f"[HATA] anahtar Fs={float(d['fs'])/1e6:.3f} MHz, simdiki {FS/1e6:.3f} MHz.")
        sys.exit(1)
    if abs(float(d["center_freq"]) - CENTER_FREQ) > 1.0:
        print(f"[UYARI] anahtar {float(d['center_freq'])/1e6:.2f} MHz'te ogrenildi, "
              f"simdi {CENTER_FREQ/1e6:.2f} MHz.")
    # TEKRAR PERIYODU: --learn bunu OLCUP dosyaya yazdi. Elle --step
    # verilmediyse OLCULENI kullan.
    # NEDEN KRITIK: varsayilan 10 ms (NR frame) ama ticari hucrede SSB 20 ms'de
    # tekrar eder. Yanlis step occasion'larin YARISINI BOS YERE dusurur; LOO
    # sablonu sinyalli ve sinyalsiz occasion'lari karistirir, hicbir sey iptal
    # olmaz ve waterfall duz gurultu cikar — sahada tam olarak bu gorulduu.
    if KEY_STEP_MS is None:
        _p = (float(d["key_period_ms"]) if "key_period_ms" in d.files else 0.0)
        if _p > 0:
            globals()["KEY_STEP_MS"] = _p
            globals()["KEY_STEP_SRC"] = "--learn OLCTU, dosyadan alindi"
        else:
            print(f"\n  [UYARI] bu anahtar dosyasi TEKRAR PERIYODUNU tasimiyor "
                  f"(eski surumle ogrenilmis).")
            print(f"          Varsayilan {SLOTS_PER_FRAME*SLOT_DUR_S*1e3:.0f} ms "
                  f"(NR frame) kullanilacak — ticari hucrede bu genelde YANLIS")
            print(f"          ve MTI'yi TAMAMEN bozar (olculdu: 10 ms'de LOS "
                  f"bastirma -1.5 dB, 20 ms'de -322 dB).")
            print(f"          Cozum: --learn ile yeniden ogren, ya da --step 20 ver.")
    key, mask = d["key"], d["mask"]
    segs = _segments(mask, LEARN_MIN_SEG)
    if not segs:
        print("[HATA] anahtar dosyasinda tutarli aralik yok."); sys.exit(1)
    # Butun secimler KANAL ICI guce gore (bkz. band_limit_sig): dosya ham
    # saklanir ki --fullband ile yeniden yorumlanabilsin.
    key = band_limit_sig(key)
    e = [float(np.sum(np.abs(key[a:b]) ** 2)) for a, b in segs]
    a, b = segs[int(np.argmax(e))]
    # Cok huzmeli burst set'te tutarli bolge ms'lerce surebilir -> en guclu
    # LEARN_KEY_MAX_US'luk alt pencereye kirp (bkz. LEARN_KEY_MAX_US notu).
    nmax = int(LEARN_KEY_MAX_US * 1e-6 * FS)
    if b - a > nmax:
        pw = np.abs(key[a:b]) ** 2
        cs = np.concatenate([[0.0], np.cumsum(pw)])
        off = int(np.argmax(cs[nmax:] - cs[:-nmax]))
        print(f"\n  [BILGI] tutarli bolge {(b-a)/FS*1e6:.0f} us. En guclu "
              f"{LEARN_KEY_MAX_US:.0f} us'luk alt penceresi anahtar")
        print(f"          yapiliyor (+{off/FS*1e6:.1f} us kaydirma). Uzatmak "
              f"enerji ekler ama BANDI (cozunurlugu) degistirmez; --keymax.")
        a, b = a + off, a + off + nmax
    print(f"\nAnahtar: {os.path.basename(path)}  ->  PPS +{a/FS*1e3:.4f} ms, "
          f"{b-a} ornek ({(b-a)/FS*1e6:.1f} us), {int(d['n_cap'])} frame ortalamasi")
    if "pci" in d.files and int(d["pci"]) >= 0:
        print(f"  hucre    : PCI {int(d['pci'])} "
              f"(N_ID_1={int(d['n_id1'])}, N_ID_2={int(d['n_id2'])}), "
              f"SSB {float(d['f_ssb'])/1e6:.3f} MHz"
              + (f", tekrar {float(d['ssb_period_ms']):.1f} ms"
                 if float(d["ssb_period_ms"]) > 0 else ""))
    # ANAHTARIN KENDI BANDI — menzil cozunurlugunu belirleyen sey budur.
    # Sabit "SSB = 7.2 MHz" VARSAYMA: ticari hucrede tutarli icerik CORESET0/
    # PDCCH/SIB1'i de kapsayabilir ve cok daha genis cikar (olculdu: 33 MHz).
    # Anahtar KANAL ICINE kisitlanir. Kisitlamazsak komsu tasiyicinin (kanal
    # disi) enerjisi hem korelasyona girer hem de b_rms'i sisirir: sahada
    # olculdu -> ham 94.2 MHz (1.59 m) ilan ederken gercek icerik 17.3 MHz
    # (8.06 m) idi, cunku kanal DISI ortalama guc kanal icinden 5.9 dB fazlaydi.
    ref = key[a:b]                       # key yukarida zaten kanala kisitlandi
    nf  = 1 << int(np.ceil(np.log2(max(2 * (b - a), 1024))))
    S   = np.abs(np.fft.fft(ref, nf)) ** 2
    fb  = np.fft.fftfreq(nf, 1.0 / FS)
    tot = float(np.sum(S)) + 1e-30
    f0  = float(np.sum(fb * S) / tot)
    b_rms = float(np.sqrt(np.sum((fb - f0) ** 2 * S) / tot)) * 2 * np.sqrt(3)
    occ_b = S > 0.05 * S.max()
    span = float(fb[occ_b].max() - fb[occ_b].min()) if occ_b.any() else 0.0
    print(f"  anahtar bandi : {(CENTER_FREQ+f0)/1e6:.2f} MHz merkez, "
          f"{span/1e6:.1f} MHz kapsam (etkin {b_rms/1e6:.1f} MHz)"
          + ("" if BAND_LIMIT_ON else "   [--fullband: KANAL DISI DAHIL]"))
    print(f"  -> MENZIL COZUNURLUGU ~{C_AIR/(2*max(b_rms,1e3)):.1f} m")
    if "wb_f_lo" in d.files and float(d["wb_f_hi"]) > float(d["wb_f_lo"]):
        bw = float(d["wb_f_hi"]) - float(d["wb_f_lo"])
        print(f"  (tasiyicinin tamami {bw/1e6:.1f} MHz -> --ref los ile "
              f"{C_AIR/(2*bw):.2f} m mumkun, ama sadece hareketli hedef)")
    return ref.astype(np.complex64), a / FS, d

def learn_key(n_cap=LEARN_N_DEF, win_ms=LEARN_WIN_MS, out_path=None,
              gamma_min=LEARN_GAMMA_MIN, overwrite=False):
    """N frame boyunca degismeyen anlari bul, IQ ortalamasini anahtar yap.

    (Eski 4rx dosyasindaki --learn ile ayni cikti; konum kodu icin referans.)

    Pencere TAM PPS kenarinda acilir (advance = pps_offset), yani bulunan
    araligin ofseti dogrudan PPS'e goredir; baz istasyonunun frame ofsetini
    ONCEDEN BILMEYE GEREK YOKTUR.

    TICARI SEBEKE NOTU: deterministik olan sey SSB'dir (PSS/SSS/PBCH-DMRS).
    PBCH VERI bitleri SFN ile degistigi icin o ornekler tutarsiz cikar ve maske
    disinda kalir — beklenen davranis. gamma_min'i dusurmek (0.2-0.3) zayif
    hucrede yardim eder; anahtarin KENDISI zaten N yakalama boyunca koherent
    ortalandigi icin temizdir, esik sadece maske icindir."""
    # UZERINE YAZMA KORUMASI — donanimdan ve 2 dakikalik yakalamadan ONCE.
    # Ogrenilmis bir anahtar SAHA VERISIDIR: o anin hucresini, bandini ve
    # kanalini tasir, masa basinda yeniden uretilemez. Ustune yazmak sadece
    # dosyayi degil, iki olcumu KARSILASTIRMA imkanini da yok eder (--keydiff).
    if out_path is None:
        out_path = LEARN_FILE
    if not os.path.isabs(out_path):
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), out_path)
    if os.path.exists(out_path) and not overwrite:
        print(f"[HATA] anahtar dosyasi ZATEN VAR: {out_path}")
        print(f"       Uzerine yazilmadi. Iki secenek:")
        print(f"         --learn-out YENI.npz   yeni anahtari AYRI dosyaya yaz,")
        print(f"                                sonra karsilastir:")
        print(f"                                  --keydiff {os.path.basename(out_path)} YENI.npz")
        print(f"         --force-key            eskisini bilerek ez")
        sys.exit(1)
    if not _HAVE_UHD:
        print("[HATA] uhd modulu yok."); sys.exit(1)
    print("=" * 70)
    print(f" OGRENME — {n_cap} x {win_ms:.1f} ms (saniyede 1, ~{n_cap/60:.1f} dk)")
    print("=" * 70)
    ctx = setup_x410(win_s=win_ms * 1e-3, advance_s=PPS_OFFSET_S)
    N = ctx["N_act"]
    S = np.zeros(N, np.complex128)
    P = np.zeros(N, np.float64)
    used = 0
    # WB icin: isgal edilen bandi olc (anahtar dosyasina yazilir) ve ilk temiz
    # yakalamayi hucre kimligi (PSS/SSS) icin sakla.
    nf_wb = min(WB_NFFT, 1 << int(np.floor(np.log2(max(N, 2)))))
    Pf_wb = np.zeros(nf_wb)
    first_buf = None
    print(f"\n  {'#':>4}  {'faz':>8}  {'guc[dBFS]':>10}  {'tutarli %':>9}")
    for i in range(n_cap):
        buf, t_trig = acquire(ctx)
        if buf is None:
            print(f"  {i+1:>4}  yakalama EKSIK"); continue
        b = buf[0]
        if first_buf is None:
            first_buf = b.copy()
        nb_av = b.size // nf_wb
        if nb_av >= 1:
            blk = b[:nb_av * nf_wb].reshape(nb_av, nf_wb)
            sel = np.linspace(0, nb_av - 1, min(4, nb_av)).astype(int)
            Pf_wb += (np.abs(np.fft.fft(blk[sel], axis=1)) ** 2).mean(0)
        coef = 1.0 + 0.0j if used == 0 else complex(np.vdot(S, b))
        b = b * np.exp(-1j * np.angle(coef))
        S += b; P += np.abs(b).astype(np.float64) ** 2; used += 1
        g = float(np.sum(np.abs(S) ** 2) / (used * np.sum(P) + 1e-30))
        print(f"  {i+1:>4}  {np.degrees(np.angle(coef)):>8.1f}  "
              f"{10*np.log10((np.abs(b)**2).mean()+1e-30):>10.1f}  {100*g:>8.1f}%")
    if used < 2:
        print("\n[HATA] yeterli yakalama yok."); sys.exit(1)

    # --- ISGAL EDILEN BANT (WB modun cozunurlugunu bu belirler) ---
    Pf_wb /= used
    edges, _ = _wb_band_edges(Pf_wb)
    df_wb = FS / nf_wb
    if edges is None:
        f_lo_wb = f_hi_wb = 0.0
        print("\n  [UYARI] isgal edilen bant olculemedi (tasiyici zayif?).")
    else:
        f_lo_wb = (edges[0] - nf_wb // 2) * df_wb
        f_hi_wb = (edges[1] - 1 - nf_wb // 2) * df_wb
        bw_wb = f_hi_wb - f_lo_wb
        print(f"\n  ISGAL EDILEN BANT: {(CENTER_FREQ+f_lo_wb)/1e6:.3f} .. "
              f"{(CENTER_FREQ+f_hi_wb)/1e6:.3f} MHz  ({bw_wb/1e6:.2f} MHz)")
        print(f"  -> WB menzil cozunurlugu c/(2B) = {C_AIR/(2*bw_wb):.2f} m  "
              f"(dar bant anahtar/SSB ile ~{C_AIR/(2*7.2e6):.0f} m olurdu)")

    # --- HUCRE KIMLIGI (PSS/SSS -> PCI) ---
    cell = None
    if first_buf is not None:
        band = (f_lo_wb, f_hi_wb) if edges is not None else None
        cell = detect_cell(first_buf, win_ms=min(win_ms, CELL_WIN_MS), band=band)
        if cell is None:
            print("  [UYARI] hucre kimligi cozulemedi; anahtar yine de kaydedilir.")
    key = (S / used).astype(np.complex64)
    gamma = (np.abs(S) ** 2) / (used * P + 1e-30)
    if LEARN_SMOOTH > 1:
        gamma = np.convolve(gamma, np.ones(LEARN_SMOOTH)/LEARN_SMOOTH, mode="same")
    mask = gamma > gamma_min
    segs = _segments(mask, LEARN_MIN_SEG)
    if not segs:
        print(f"\n[HATA] tutarli an bulunamadi (esik gamma={gamma_min:.2f}).")
        print(f"       gamma: azami {gamma.max():.3f}, medyan {np.median(gamma):.3f} "
              f"(gurultu tabani ~1/N={1.0/used:.3f})")
        if gamma.max() > 1.5 / used:
            print(f"       -> Sinyal VAR ama zayif. Tekrar dene: --gamma "
                  f"{max(0.15, 0.6*gamma.max()):.2f}  (ya da kazanci/anteni artir)")
        else:
            print("       -> Deterministik tekrar YOK. Kontrol et: CENTER_FREQ dogru mu "
                  "(--psd ile bak), GPSDO kilitli mi, anten baz istasyonunu goruyor mu.")
        sys.exit(1)

    # Bir SSB'nin parcalanmis araliklarini birlestir (bkz. merge_segments).
    segs_raw = segs
    segs = merge_segments(segs, int(LEARN_MERGE_US * 1e-6 * FS))
    # Siralama KANAL ICI enerjiye gore. Ham enerjiyle siralarsak komsu
    # tasiyicinin gucu yarisa girer ve "en guclu kume" yanlis secilebilir.
    key_bl = band_limit_sig(key)
    e_all = [float(np.sum(np.abs(key_bl[s:e]) ** 2)) for s, e in segs]
    e_ref = max(e_all) + 1e-30

    print(f"\n  Tutarli araliklar (esik gamma>{gamma_min:.2f}): "
          f"{len(segs_raw)} ham parca -> {len(segs)} kume "
          f"(<{LEARN_MERGE_US:.0f} us bosluklar birlestirildi)")
    print(f"  {'#':>3}  {'PPS ofset[ms]':>13}  {'sure[us]':>9}  {'guc[dB]':>8}  {'gamma':>6}")
    order = np.argsort(e_all)[::-1]
    show_n = min(len(segs), 12)
    for i in sorted(order[:show_n]):
        (a_, b_), ew = segs[i], e_all[i]
        print(f"  {i:>3}  {a_/FS*1e3:>13.4f}  {(b_-a_)/FS*1e6:>9.1f}  "
              f"{10*np.log10(ew/e_ref+1e-30):>+8.1f}  {gamma[a_:b_].mean():>6.3f}")
    if len(segs) > show_n:
        print(f"  ... ({len(segs)-show_n} kume daha, en zayiflari gizlendi)")

    # TEKRAR PERIYODU — ardisik farklar DEGIL, baskin periyot (bkz. fonksiyon)
    offs = [a_ / FS for a_, _ in segs]
    per_ms, nmatch, ntot = dominant_period_ms(offs, N / FS)
    if per_ms:
        print(f"\n  TEKRAR PERIYODU: {per_ms:.1f} ms  "
              f"({nmatch}/{ntot} kumenin tam +{per_ms:.0f} ms otede esi var)")
        print(f"  -> locate/range/calib komutlarina  --step {per_ms:.0f}  EKLE")
        if per_ms >= win_ms * 0.9:
            print(f"     [UYARI] periyot pencereye ({win_ms:.0f} ms) ancak siginiyor; "
                  f"--learn-win'i buyutup dogrula")
    else:
        print(f"\n  [UYARI] {win_ms:.0f} ms pencerede NR periyotlarindan "
              f"({'/'.join(f'{p:.0f}' for p in SSB_PERIODS_MS)} ms) hicbiri "
              f"dogrulanamadi.")
        print(f"          --learn-win 60 ile tekrar dene; bulunamazsa --step 20 "
              f"(en yaygin SSB periyodu) ile devam et.")

    j = int(np.argmax(e_all))
    a, b = segs[j]
    print(f"\n  En guclu kume (anahtar bu): PPS +{a/FS*1e3:.4f} ms, "
          f"{(b-a)/FS*1e6:.1f} us  ({b-a} ornek)")
    # Anahtar occasion diliminden (N_SLOT) kisa OLMALI; yoksa korelasyon
    # penceresi (nlag) kapanir ve _occasion_layout hata verir.
    if b - a > 0.6 * N_SLOT:
        print(f"  [UYARI] anahtar slotun ({N_SLOT/FS*1e6:.0f} us) %60'ini asiyor; "
              f"menzil penceresi daraliyor.")
        print(f"          Cok huzmeli SSB kumeleri birlesmis olabilir -> "
              f"LEARN_MERGE_US'i ({LEARN_MERGE_US:.0f}) kucult.")
    np.savez(out_path, key=key, gamma=gamma.astype(np.float32), mask=mask,
             fs=FS, center_freq=CENTER_FREQ, rx_gain=RX_GAIN,
             win_ms=win_ms, n_cap=used, t0=0.0,
             # WB icin: isgal edilen bant (cozunurlugu bu belirler)
             wb_psd=Pf_wb.astype(np.float32), wb_nfft=nf_wb,
             wb_f_lo=f_lo_wb, wb_f_hi=f_hi_wb,
             # hucre kimligi (yoksa -1)
             pci=(-1 if not cell or cell["pci"] is None else cell["pci"]),
             n_id1=(-1 if not cell or cell["n_id1"] is None else cell["n_id1"]),
             n_id2=(-1 if not cell else cell["n_id2"]),
             f_ssb=(0.0 if not cell else cell["f_ssb"]),
             t_ssb=(0.0 if not cell else cell["t0"]),
             ssb_period_ms=(0.0 if not cell or not cell["period_ms"]
                            else cell["period_ms"]),
             # ANAHTARIN kendi olculen tekrar periyodu (kumelerden). --step'in
             # dogru degeri budur; --auto bunu kendiliginden uygular.
             key_period_ms=(0.0 if not per_ms else float(per_ms)))
    print(f"\n  Kaydedildi: {out_path}")
    if cell and cell["pci"] is not None:
        print(f"  Hucre     : PCI {cell['pci']}"
              + (f",  SSB tekrari {cell['period_ms']:.1f} ms"
                 if cell["period_ms"] else ""))
    # HANGI FREKANSLAR SABIT — tahmin degil, olcum.
    try:
        key_determinism(np.load(out_path))
    except Exception as _e:
        print(f"  [UYARI] determinizm profili cikarilamadi ({_e})")
    if os.path.basename(out_path) != LEARN_FILE:
        print(f"\n  ONCEKIYLE KARSILASTIR (donanim gerekmez):")
        print(f"    python3 {os.path.basename(__file__)} --keydiff "
              f"{LEARN_FILE} {os.path.basename(out_path)}")
        print(f"  Olcumde bu anahtari kullanmak icin: --key "
              f"{os.path.basename(out_path)}")
    print(f"\n  SONRAKI ADIM — kalibrasyon + olcum, TEK KOSUDA:")
    print(f"    python3 {os.path.basename(__file__)}")
    print(f"  (anahtar artik diskte; o kosu splitter kalibrasyonuyla baslar ve")
    print(f"   ayni oturumda olcume gecer.)")
    print("=" * 70)
    return out_path

# ═══════════════════════════════════════════════════════════════════
#  11c) --learn (v4) — JENERIK: HUCREYI TANI, SONRA ANAHTARI KUR
# ═══════════════════════════════════════════════════════════════════
# NEDEN YENIDEN YAZILDI (1): v3'un --learn'i ALINAN sinyali ortalar. Ortalama
# rastgele icerigi sondurur ama KANALI sondurmez — cikan anahtar s(t) degil,
# s(t) (*) h(t)'dir. Ogrenme gununun cok yolu anahtarin ICINE gomulur.
#
# OLCULDU (signal_key.npz, 2026-08-14, 3530 MHz) — anahtarin otokorelasyonu
# (s*s) (*) (h*h) icinde gomulu kanal:
#    -8.7 dB @  24.40 m      -17.7 dB @  78.07 m
#   -14.0 dB @  43.91 m      -19.4 dB @  60.99 m   ... 270 m'ye kadar 16 tepe
#   RMS gecikme yayilimi 62 ns, ana yol disi enerji %17.7
#   Isgal edilen bant KESINTISIZ -> spektral delik artefakti DEGIL, gercek cok yol.
# Korelasyon conj(R) ile yapildigindan tepeler t_hedef - t_i'de cikar: her
# HAREKETLI hedef kendi ONUNDE -9/-14 dB'lik kopyalar birakir ve o kopyalar da
# hareketli oldugu icin LOO MTI onlari TEMIZLEMEZ.
#
# NEDEN YENIDEN YAZILDI (2) — JENERIKLIK: ilk surum hucre kimligine (PCI)
# bagliydi; pilotlari (SSS, PBCH-DMRS) ondan uretiyordu. SAHADA OLCULDU ki PCI
# GUVENILMEZ: detect_cell ayni veriden her kosuda baska sayi veriyor
# (471/39/945/72/378...), SSS tepe/medyan 3.0-3.8 ile esigin dibinde, ve
# PBCH DMRS ne 918'i ne 837'yi dogruluyor (tepe/medyan 1.30-1.44, kabul >1.8).
# signal_key.npz'deki "PCI 918" bile kendi verisinden yeniden URETILEMIYOR.
# Bu yuzden yeni tasarim hucre KIMLIGINE HIC BAKMAZ.
#
# Neye bakar: dalga formunun KENDI olculebilir ozelliklerine.
#   1) numeroloji mu  -> CP korelasyonundan (15/30/60/120 kHz denenir)
#   2) isgal edilen bant + merkez  -> spektrumdan
#   3) deterministik bolgenin yeri + TEKRAR PERIYODU -> yakalamalar arasi
#      tutarliliktan (v3'un gamma mantigi)
#   4) kanal H(f) -> QPSK'nin x^4 = -1 ozelliginden (KOR, pilot gerekmez)
#   5) sembol basina faz -> OLCULUR (LO tasiyici merkezinde olmak ZORUNDA degil)
# Hicbiri PCI, PSS, SSS ya da PBCH bilmeyi gerektirmez.
#
#   ORTALAMA kanali kaldirmaz.  DILIMLEME kaldirir.

RECON_GAMMA_MIN  = 0.55     # RE "sabit" sayilmasi icin yakalamalar arasi tutarlilik
RECON_EVM_MAX    = 0.40     # dilimlemeden ONCE azami EVM (|x_hat - dilim|)
RECON_CP_SEARCH  = 96       # kafes ortak kaymasi arama yaricapi [ornek]
RECON_TAU_MAX_M  = 400.0    # kanal kestiriminde tutulan azami gecikme [m]
# Altasiyici "dolu" sayilmasi icin tepeden esik [dB]. Bu kapinin isi BOS
# altasiyiciyi elemektir; bos olan gercekten SIFIRDIR (-inf dB). Dar tutmak
# (10 dB) derin SONUMLEMEDEKI gercek altasiyicilari da keser: sentetik testte
# 620'nin 23'u boyle dusup referansta spektral DELIK aciyordu (corr 0.9824).
# 15 dB uzerinde hepsi geri geliyor (1.0000), 10 kat gurultude bile.
RECON_OCC_DB     = 20.0
RECON_MIN_SC     = 64       # bu kadar altasiyici dolmazsa yeniden kurgu iptal
# YUMUSAK MOD: sembolleri takimyildiza KUANTALAMA, sadece kanali sok ve genligi
# birime cek. Pilotsuz sinyalde ayrik karar mutlak faz referansi ister ve o
# yoksa tekrarlanabilirligi bozar (bkz. _recon_slice). Varsayilan ACIK.
RECON_SOFT       = True
RECON_KEEP_AMP   = True     # yumusak modda olculen genligi koru (SNR agirligi)
RECON_KEY_US     = 900.0    # kurgulanacak pencere [us] (sembol sayisina cevrilir)
RECON_SURVEY_N   = 12       # TANIMA asamasi yakalama sayisi
RECON_MU_TRY     = (0, 1, 2, 3)     # denenecek numerolojiler (15/30/60/120 kHz)
RECON_BPSK_R     = 0.55     # |<V^2>| / <|V|^2> bunun ustundeyse altasiyici BPSK
RECON_PHI_MIN_RE = 24       # sembol basi faz olcumu icin asgari RE sayisi


def nr_numerology(mu, fs=None):
    """mu -> (SCS, N_FFT, CP, uzun CP, uzun CP periyodu). TS 38.211 5.3.1.

    Dosyanin geri kalani mu=1'e (30 kHz) gomulu; bu fonksiyon SADECE yeni
    ogrenme yolu icin numerolojiyi RUNTIME'da tasir. Boylece baska bir bantta
    (n1/n3/n8'de SCS tipik 15 kHz) ogrenme calisir, global sabitler bozulmaz.

      SCS   = 15 kHz * 2^mu
      N_FFT = fs / SCS
      CP    = 144 * 64 * 2^-mu * kappa,   kappa = fs / (480000*4096)
      uzun CP ek olarak 16*64*kappa (her yarim alt cerceve basi)
      uzun CP'ler l_sf = 0 ve 7*2^mu'da -> ARALIK 7*2^mu sembol
    """
    fs = FS if fs is None else float(fs)
    scs = 15e3 * (1 << mu)
    n_fft = fs / scs
    if abs(n_fft - round(n_fft)) > 1e-6:
        return None                      # fs bu numerolojiye tam bolunmuyor
    n_fft = int(round(n_fft))
    kappa = fs / (480000.0 * 4096.0)
    cp = int(round(144 * 64 * 2.0 ** (-mu) * kappa))
    cpl = int(round((144 * 64 * 2.0 ** (-mu) + 16 * 64) * kappa))
    if n_fft < 128 or cp < 8:
        return None
    return dict(mu=mu, scs=scs, n_fft=n_fft, cp=cp, cp_long=cpl,
                per_long=7 * (1 << mu),          # uzun CP'ler arasi sembol
                sym=n_fft + cp, fs=fs,
                slot_us=1e6 / (1000.0 * (1 << mu)))


def _cp_profile(x, nu):
    """Normalize CP korelasyon profili r(u); u = sembolun VERI baslangici.

        r(u) = |sum_{i<CP} x[u-CP+i] conj(x[u-CP+i+N_FFT])| / sqrt(E1*E2)
    Normalizasyon SART: ham |toplam| farkli uzunluktaki pencereleri ve farkli
    numerolojileri kiyaslanamaz kilar (buyuk N_FFT sirf daha cok ornek
    topladigi icin kazanir)."""
    n = x.size
    nf, cp = nu["n_fft"], nu["cp"]
    M = n - nf
    if M <= cp + 8:
        return None, None
    prod = (x[:M] * np.conj(x[nf:nf + M])).astype(np.complex128)
    e = (np.abs(x).astype(np.float64) ** 2)
    csp = np.concatenate([[0j], np.cumsum(prod)])
    cse = np.concatenate([[0.0], np.cumsum(e)])
    return csp, cse


def _cp_score(csp, cse, u, nu, n_lim):
    """Verilen VERI baslangiclarinda normalize CP korelasyonu (vektorel)."""
    nf, cp = nu["n_fft"], nu["cp"]
    u = np.asarray(u, np.int64)
    ok = (u - cp >= 0) & (u + nf <= n_lim) & (u <= csp.size - 2)
    out = np.zeros(u.shape, float)
    if not ok.any():
        return out
    uu = u[ok]
    num = np.abs(csp[uu] - csp[uu - cp])
    d1 = cse[uu] - cse[uu - cp]
    d2 = cse[uu + nf] - cse[uu - cp + nf]
    out[ok] = num / (np.sqrt(d1 * d2) + 1e-30)
    return out


def detect_numerology(x, mus=RECON_MU_TRY, n_sym=40, quiet=False):
    """KOR NUMEROLOJI TESPITI — hangi SCS ile yayin yapiliyor?

    Her mu icin OFDM kafesi kurulup butun sembollerin normalize CP korelasyonu
    ortalanir. Dogru numerolojide CP gercekten sembolun kuyrugunun kopyasidir
    ve oran 1'e yaklasir; yanlis numerolojide pencere sembol sinirlarini kesip
    ilintisiz veriye bakar ve oran gurultu seviyesinde kalir.

    Hucre kimligine (PCI/PSS) GEREK YOKTUR — sadece OFDM'in kendi yapisina bakar.

    Doner: (nu, rapor_listesi) ya da (None, rapor_listesi)."""
    x = np.asarray(x).ravel()
    rep = []
    best = None
    for mu in mus:
        nu = nr_numerology(mu)
        if nu is None:
            continue
        csp, cse = _cp_profile(x, nu)
        if csp is None:
            continue
        sym = nu["sym"]
        n_use = min(n_sym, max(2, (x.size - nu["n_fft"]) // sym - 1))
        if n_use < 2:
            continue
        # kafesin baslangic fazini tara, butun sembolleri TOPLA
        ph = np.arange(0, sym, max(1, sym // 512))
        base = nu["cp"] + ph[:, None] + sym * np.arange(n_use)[None, :]
        sc = _cp_score(csp, cse, base.ravel(), nu, x.size).reshape(base.shape)
        m = sc.mean(1)
        j = int(np.argmax(m))
        rec = dict(mu=mu, scs=nu["scs"], n_fft=nu["n_fft"], cp=nu["cp"],
                   score=float(m[j]), phase=int(ph[j]), nu=nu)
        rep.append(rec)
        if best is None or rec["score"] > best["score"]:
            best = rec
    if not quiet:
        print("\n  NUMEROLOJI TESPITI (kor — hucre kimligi kullanilmaz)")
        print(f"    {'SCS':>9} {'N_FFT':>7} {'CP':>6} {'CP korelasyonu':>16}")
        for r in sorted(rep, key=lambda z: -z["score"]):
            mark = "  <- SECILDI" if best and r["mu"] == best["mu"] else ""
            print(f"    {r['scs']/1e3:>7.0f}k {r['n_fft']:>7d} {r['cp']:>6d} "
                  f"{r['score']:>16.3f}{mark}")
    if best is None:
        return None, rep
    others = [r["score"] for r in rep if r["mu"] != best["mu"]]
    marj = best["score"] - (max(others) if others else 0.0)
    if not quiet:
        print(f"    secilen SCS {best['scs']/1e3:.0f} kHz, ikinciye fark {marj:+.3f}")
        if best["score"] < 0.30:
            print("    [UYARI] CP korelasyonu zayif — sinyal cok zayif ya da OFDM degil")
        elif marj < 0.05:
            print("    [UYARI] numerolojiler arasi fark kucuk; secim GUVENILMEZ")
    # KARARSIZ SECIMLE DEVAM ETME: yanlis mu ile butun zincir sessizce coker
    # (sahada olculdu: 120 kHz secilince 101x1024 izgarada sadece 22 sabit RE).
    if best["score"] < 0.25 or marj < 0.04:
        if not quiet:
            print("    [HATA] numeroloji secimi kararsiz — devam edilmiyor.")
        return None, rep
    return best["nu"], rep


def _recon_lattice(x, u0, n_before, n_after, nu, search=RECON_CP_SEARCH):
    """PSS'e DEGIL, verilen capaya oturan RIJIT OFDM sembol kafesi.

    RIJIT olmasi sart: sembol araligi donanimla sabittir. Her sembolu bagimsiz
    ince ayarlamak CAZIP ama YANLIS — cok yol CP korelasyon tepesini genisletir
    ve tepe sembolden sembole oynar (sentetik testte olculdu: -2..+5 ornek).
    d ornek kayma izgaraya 2*pi*d*k/N_FFT LINEER FAZ RAMPASI bindirir; 570
    altasiyicilik bantta d=5 icin 4.4 radyan. O zaman H "sembolden bagimsiz"
    olmaktan cikar ve hem 4. kuvvet kestirimi hem dilimleme coker.

    Bu yuzden SADECE IKI serbestlik derecesi aranir:
        d : kafesin ortak kaymasi
        p : uzun CP'nin faz konumu (uzun CP'ler 7*2^mu sembolde bir)
    ve butun sembollerin normalize CP korelasyonu TOPLANARAK en iyi (d,p) secilir.
    Kalan ortak kayma zararsizdir — H'nin icine giren sabit bir gecikmedir.

    Doner: (u[], cp[])."""
    nf, cp0, cpl = nu["n_fft"], nu["cp"], nu["cp_long"]
    per_long, dlong = nu["per_long"], nu["cp_long"] - nu["cp"]
    n_tot = n_before + n_after + 1
    csp, cse = _cp_profile(x, nu)
    if csp is None:
        return (np.full(n_tot, int(u0), np.int64),
                np.full(n_tot, cp0, np.int64))
    ks = np.arange(-n_before, n_after + 1)

    def _offsets(p):
        """Capaya goreli sembol baslangiclari (ortak kayma haric)."""
        pos = {0: 0}
        cur = 0
        for kk in range(1, n_after + 1):
            cur += nf + (cpl if (kk % per_long) == (p % per_long) else cp0)
            pos[kk] = cur
        cur = 0
        for kk in range(-1, -n_before - 1, -1):
            cur -= nf + (cpl if ((kk + 1) % per_long) == (p % per_long) else cp0)
            pos[kk] = cur
        return np.array([pos[int(v)] for v in ks], np.int64)

    ds = np.arange(-search, search + 1)
    best = (-1.0, 0, 0, None)
    for p in range(per_long):
        o = _offsets(p)
        U = int(u0) + ds[:, None] + o[None, :]
        sc = _cp_score(csp, cse, U.ravel(), nu, x.size).reshape(U.shape).sum(1)
        a = int(np.argmax(sc))
        if sc[a] > best[0]:
            best = (float(sc[a]), int(ds[a]), p, o)
    _, dbest, pbest, o = best
    uu = (int(u0) + dbest + o).astype(np.int64)
    cp = np.full(uu.size, cp0, np.int64)
    cp[1:] = np.where((uu[1:] - (uu[:-1] + nf)) > (cp0 + dlong // 2), cpl, cp0)
    _recon_lattice.last = dict(d=dbest, p=pbest, score=best[0] / max(uu.size, 1))
    return uu, cp

_recon_lattice.last = dict(d=0, p=0, score=0.0)


def _recon_demod(x, us, rot, nu):
    """Sembol kafesinden (n_sym, N_FFT) izgara; fftshift sirali (bin0 = -FS/2)."""
    nf = nu["n_fft"]
    G = np.empty((len(us), nf), np.complex64)
    for i, u in enumerate(us):
        G[i] = np.fft.fftshift(np.fft.fft(x[u:u + nf] * rot[u:u + nf]))
    return G


def _recon_align(G, Gref, w):
    """Yakalamayi referans yakalamaya oturt (ortak faz + kazanc).

    PSS GEREKMEZ. Deterministik RE'ler yakalamalar arasi KOHERENT toplandigi
    icin ic carpimi onlar domine eder; rastgele icerik ortalamada soner. Bu,
    v3'un zaman domeninde yaptigi hizalamanin (vdot(S,b)) izgara halidir.

    Doner (G_hizali, alpha) ya da (None, None)."""
    a = complex(np.vdot(Gref[w], G[w]))
    den = float(np.vdot(Gref[w], Gref[w]).real) + 1e-30
    al = a / den
    if not np.isfinite(al) or abs(al) < 1e-12:
        return None, None
    return G / al, al


def _unwrap_gapped(idx, val, lo, hi):
    """Bosluklu bir indis kumesinde faz sarimini ac.

    unwrap ARDISIK ornek varsayar; bosluk varsa yanlis atlar. Bu yuzden once
    tam izgaraya en-yakin-komsu ile doldurulur, sarim orada acilir, sonra
    yalnizca GERCEK indisler geri okunur."""
    full = np.arange(lo, hi + 1)
    j = np.searchsorted(idx, full)
    j = np.clip(j, 0, len(idx) - 1)
    jm = np.clip(j - 1, 0, len(idx) - 1)
    pick = np.where(np.abs(idx[j] - full) <= np.abs(idx[jm] - full), j, jm)
    ph = np.unwrap(val[pick])
    return ph[idx - lo]


def _recon_chan_blind(Vbar, cons, nu, tau_max_m=RECON_TAU_MAX_M,
                      occ_db=RECON_OCC_DB, bpsk_r=RECON_BPSK_R, band=None):
    """KOR kanal kestirimi — pilot, PCI, PSS/SSS GEREKMEZ.

    DAYANDIGI TEK SEY MODULASYONUN KENDISI:
      QPSK'de x^4 = -1 SABITTIR. Dolayisiyla altasiyici basina
          A_k = <V_k,l^4>_l = -H_k^4 * <phi_l^4>_l
      Buradaki <phi_l^4> SEMBOL BASINA fazdan gelir ama k'dan BAGIMSIZDIR,
      yani sadece GLOBAL bir sabit uretir; H'nin bant boyunca SEKLINI bozmaz.
      Global faz uyumlu filtrede zararsizdir (korelasyon genligi degismez).
      -> H_k, 4 kat belirsizlikle olculur; belirsizlik angle(A_k)'nin
         altasiyici ekseninde SARIMI ACILARAK cozulur.
      Sarim acmanin gecerlilik siniri 4*|dphi| < pi, yani
         tau < 1/(8*SCS).  30 kHz'de 4.17 us = 1250 m; olculen yayilim 270 m.

    BPSK ELEME: PSS/SSS BPSK'dir ve BPSK'de x^4 = +1 (QPSK'de -1). Ayni
    ortalamaya karisirlarsa kestirimi 90 derece kaydirirlar. Ayrim kolay:
    BPSK'de x^2 = +1 hep sabit oldugundan |<V^2>| / <|V|^2> ~ 1; QPSK'de
    x^2 = +-j karisik geldiginden ~0. Bu altasiyicilar H kestiriminden
    CIKARILIR (dilimlemede kendi ekseniyle geri kazanilirlar).

    DUZLESTIRME: H, CIR tabaninda EN KUCUK KARELER ile tau_max'a sinirlanir
    (kapi degil LS — bant sinirli H'nin IFFT'si kapi ile bozulur).

    Doner (H, ks, bpsk_mask, rapor) ya da (None, None, None, mesaj)."""
    n_sym, nsc = Vbar.shape
    ncons = cons.sum(0)
    pw = np.zeros(nsc)
    w = np.where(cons, np.abs(Vbar) ** 2, 0.0).sum(0)
    occ0 = ncons >= 2
    # TASIYICI DISINI ELE. Guc esigi tek basina YETMEZ: bant disinda da
    # yakalamalar arasi tutarli gorunen bilesenler var (LO sizmasi, DC, alias)
    # ve bunlar kestirime girince H bozulur. SAHADA OLCULDU: bant kisiti
    # olmadan ks 122.88 MHz'e yayildi, CIR LS artigi %57, EVM 0.29 ve olculen
    # cok yol profili anlamsiz cikti (8 tap, hepsi -0.0 dB, 11..342 m).
    if band is not None:
        f = (np.arange(nsc) - nsc // 2) * nu["scs"]
        occ0 &= (f >= band[0]) & (f <= band[1])
    if occ0.sum() < RECON_MIN_SC:
        return None, None, None, f"dolu altasiyici {int(occ0.sum())} < {RECON_MIN_SC}"
    pw[occ0] = w[occ0] / ncons[occ0]
    thr = pw[occ0].max() * 10 ** (-occ_db / 10.0)
    occ = occ0 & (pw > thr)
    if occ.sum() < RECON_MIN_SC:
        return None, None, None, f"esik sonrasi altasiyici {int(occ.sum())} < {RECON_MIN_SC}"

    # --- BPSK altasiyicilarini isaretle ---
    V2 = np.where(cons, Vbar ** 2, 0.0).sum(0)
    P2 = np.where(cons, np.abs(Vbar) ** 2, 0.0).sum(0)
    r2 = np.zeros(nsc)
    ok2 = occ & (ncons >= 6)
    r2[ok2] = np.abs(V2[ok2]) / (P2[ok2] + 1e-30)
    # ESIK ORNEK SAYISINA GORE OLCEKLENIR: QPSK'de <x^2> sifira ancak
    # 1/sqrt(n) hizinda yakinsar. n=6 icin bu 0.41'dir, yani sabit 0.55'lik
    # esik kisa pencerede QPSK'yi BPSK sanir (olculdu: mu=0, 12 sembol ->
    # 600 altasiyicinin 140'i yanlis isaretlendi ve YANLIS eksende dilimlendi).
    # 3/sqrt(n) ~ %0.3 yanlis alarm birakir; supheliyi QPSK sayariz.
    thr2 = np.maximum(bpsk_r, 3.0 / np.sqrt(np.maximum(ncons, 1)))
    bpsk = ok2 & (r2 > thr2)

    ks_all = np.where(occ & ~bpsk)[0]
    if ks_all.size < RECON_MIN_SC:
        return None, None, None, (f"QPSK altasiyicisi {ks_all.size} < "
                                  f"{RECON_MIN_SC} (BPSK elendi: {int(bpsk.sum())})")

    # --- 4. kuvvet ---
    V4 = np.where(cons, Vbar ** 4, 0.0)
    nA = cons.sum(0)
    A = np.where(nA > 0, V4.sum(0) / np.maximum(nA, 1), 0.0)
    good = ks_all[np.abs(A[ks_all]) > 0]
    if good.size < RECON_MIN_SC:
        return None, None, None, "4. kuvvet kestirimi bos"
    lo, hi = int(good.min()), int(good.max())
    ph4 = _unwrap_gapped(good, np.angle(-A[good]), lo, hi)
    phb = ph4 / 4.0
    amp = np.sqrt(np.sqrt(np.abs(A[good])))
    Hk = amp * np.exp(1j * phb)

    # --- CIR tabaninda LS duzlestirme ---
    ntap = int(np.ceil(tau_max_m / C_AIR * nu["fs"]))
    ntap = int(np.clip(ntap, 8, max(8, good.size // 3)))
    t = np.arange(-(ntap // 4), ntap)
    E = np.exp(-2j * np.pi * np.outer(good - nsc // 2, t) / nsc)
    c, *_ = np.linalg.lstsq(E, Hk, rcond=None)
    Hs = E @ c
    res = float(np.linalg.norm(Hk - Hs) / (np.linalg.norm(Hk) + 1e-30))

    # BPSK altasiyicilarini da CIR modelinden DOLDUR (olcmedik, kestiriyoruz)
    kb = np.where(bpsk)[0]
    H = np.zeros(nsc, np.complex128)
    H[good] = Hs
    if kb.size:
        Eb = np.exp(-2j * np.pi * np.outer(kb - nsc // 2, t) / nsc)
        H[kb] = Eb @ c
    ks = np.sort(np.concatenate([good, kb])) if kb.size else good
    rep = dict(n_sc=int(good.size), n_bpsk=int(kb.size), ntap=int(t.size),
               resid=res,
               bw_mhz=float((ks.max() - ks.min() + 1) * nu["scs"] / 1e6))
    return H, ks, bpsk, rep


def _recon_chan_dd(Vbar, Gc, phi, ks, nu, tau_max_m=RECON_TAU_MAX_M):
    """KARAR-YONLENDIRMELI kanal kestirimi — dilimlenen semboller PILOT sayilir.

    NEDEN GEREKLI: kor 4. kuvvet kestirimi V^4 aldigi icin faz gurultusunu 4
    KATINA cikarir. Sahada olculdu: medyan EVM 0.28, CIR LS artigi %30, iki
    bagimsiz ogrenmenin korelasyonu 0.68. Oysa ayni sahada HAM dalga formunun
    20 ms tekrar korelasyonu 0.998 olculdu (occasion_period_test.py, 180 ms'ye
    kadar butun occasion'larda) — yani sinyal bol ve temiz, kayip TAMAMEN
    kestirimde.

    Bir kere dilimledikten sonra x BILINIR. O zaman H dogrusal bir problemdir:
        V[l,k] = H_k * phi_l * x[l,k]  ->  H_k = <V, phi*x> / <|x|^2>
    Bu, 4. kuvvete gore cok daha dusuk varyanslidir (kuvvet alma yok). Sonuc
    yine CIR tabaninda LS ile duzlestirilir.

    Doner (H, artik) — Gc'de dilimlenmis RE'si olmayan altasiyicilar CIR
    modelinden doldurulur."""
    n_sym, nsc = Vbar.shape
    X = Gc * phi[:, None]                      # bilinen (dilimlenmis) sembol
    w = np.abs(X) ** 2
    num = (Vbar * np.conj(X)).sum(0)
    den = w.sum(0)
    good = np.where((den > 0) & np.isin(np.arange(nsc), ks))[0]
    if good.size < RECON_MIN_SC:
        return None, 1.0
    Hk = num[good] / den[good]
    ntap = int(np.clip(int(np.ceil(tau_max_m / C_AIR * nu["fs"])), 8,
                       max(8, good.size // 3)))
    t = np.arange(-(ntap // 4), ntap)
    E = np.exp(-2j * np.pi * np.outer(good - nsc // 2, t) / nsc)
    # AGIRLIKLI LS: cok pilotu olan altasiyici daha guvenilir
    wk = np.sqrt(den[good])
    c, *_ = np.linalg.lstsq(E * wk[:, None], Hk * wk, rcond=None)
    Hs = E @ c
    res = float(np.linalg.norm((Hk - Hs) * wk) / (np.linalg.norm(Hk * wk) + 1e-30))
    H = np.zeros(nsc, np.complex128)
    Eall = np.exp(-2j * np.pi * np.outer(np.asarray(ks) - nsc // 2, t) / nsc)
    H[ks] = Eall @ c
    return H, res


def _recon_sym_phase(Xh, cons, ks):
    """SEMBOL BASINA ortak faz phi_l — OLCULUR, varsayilmaz.

    NEDEN VAR: NR vericisi sembol basina exp(j 2pi f_c t_l) faz telafisi
    uygular. LO tam tasiyici merkezindeyse bu alicida BIREBIR sadelesir ve
    phi_l sabit kalir. Merkezde DEGILSE (bizim durumda olculdu: bant ortasi
    3529.88, LO 3530.00 -> 120 kHz) sadelesmez ve sembolden sembole rampa olur:
    120 kHz x 35.7 us = sembol basina ~102 derece. Bu rampa duzeltilmezse
    dilimleme coker.

    Olcum yine x^4 = -1'den: phi_l^4 = -<(V/H)^4>_k.  Sarim l ekseninde acilir.
    SENTEZDE GERI UYGULANIR — cunku bu faz ILETILEN sinyalin (ve ayni LO ile
    yapilacak olcumun) parcasidir, alicinin uydurmasi degil.

    Doner (phi[n_sym], guvenilir_mi)."""
    n_sym = Xh.shape[0]
    phi = np.ones(n_sym, np.complex128)
    a4 = np.zeros(n_sym, np.complex128)
    nre = np.zeros(n_sym, int)
    for l in range(n_sym):
        sel = cons[l, ks]
        n = int(sel.sum())
        nre[l] = n
        if n >= RECON_PHI_MIN_RE:
            a4[l] = np.mean(Xh[l, ks][sel] ** 4)
    ok = nre >= RECON_PHI_MIN_RE
    if ok.sum() < 2:
        return phi, False
    idx = np.where(ok)[0]
    ph = _unwrap_gapped(idx, np.angle(-a4[idx]), int(idx.min()), int(idx.max())) / 4.0
    # olculemeyen semboller icin komsudan tasi
    full = np.interp(np.arange(n_sym), idx, ph)
    phi = np.exp(1j * full)
    return phi, True


def _recon_slice(Vbar, cons, H, ks, bpsk, phi, evm_max=RECON_EVM_MAX):
    """Kanali ve sembol fazini sok, takimyildiza dilimle, TEMIZ izgarayi kur.

    Dilimleme kritik adimdir: ORTALAMA kanali kaldirmaz, DILIMLEME kaldirir.
    x_hat = Vbar/(H*phi) bir takimyildiz noktasinin yakinina duser; en yakin
    noktaya yuvarlaninca elde kalan sey ILETILEN sembolun ta kendisidir.
    Kanal, gurultu ve equalizer artigi bu adimda tamamen duser.

    BIRIM GENLIK: butun kabul edilen RE'ler |x|=1 yazilir -> referans spektrumu
    DUZ olur. Bu, renkli girisimde beyazlatilmis uyumlu filtreye karsilik gelir
    ve menzil yan lobunu TX guc dagilimindan bagimsiz kilar.

    BPSK altasiyicilari kendi EKSENIYLE dilimlenir: eksen, o altasiyicilarin
    kendi <x^2>'sinden olculur (global 90 derece dal belirsizligi BPSK'yi
    hayali eksene dusurebilir; olcup duzeltiyoruz)."""
    n_sym, nsc = Vbar.shape
    Gc = np.zeros((n_sym, nsc), np.complex128)
    Hs = np.zeros(nsc, np.complex128)
    Hs[ks] = H[ks]
    ok = np.zeros(nsc, bool)
    ok[ks] = np.abs(H[ks]) > 0
    Xh = np.zeros_like(Vbar)
    Xh[:, ok] = Vbar[:, ok] / Hs[ok][None, :]
    Xh = Xh / phi[:, None]

    sel = cons & ok[None, :]
    if not sel.any():
        return Gc, Xh, dict(n_re=0, n_qpsk=0, n_bpsk=0, evm=float("nan"), n_cand=0)
    med = float(np.median(np.abs(Xh[sel]))) + 1e-30
    Xn = Xh / med

    kb = np.zeros(nsc, bool)
    kb[ks] = bpsk[ks] if bpsk is not None else False
    qmask = sel & ~kb[None, :]
    bmask = sel & kb[None, :]

    # --- YUMUSAK MOD: KUANTALAMA YOK ---
    # NEDEN: dilimleme, sembolu 4 QPSK noktasindan birine YUVARLAR. Bu ayrik
    # karar bir MUTLAK FAZ REFERANSI ister; pilotsuz sinyalde her sembolun
    # 90 derecelik dali serbest kalir ve iki kosu farkli dala kilitlenir.
    # SAHADA OLCULDU: kume ortusmesi 0.97 olmasina ragmen ortak RE'lerdeki
    # deger uyumu %73 ile %0 arasinda oynuyor -> tekrarlanabilirlik 0.84'te
    # takiliyor.
    # Oysa KUANTALAMAYA GEREK YOK: v4'un amaci kanali sokmek ve bunun icin
    # V/(H*phi) yeterli. Dilimleme sadece gurultu temizligi icindi, ama ham
    # dalga formunun 20 ms tekrar korelasyonu 0.998 olculdu — temizlenecek
    # gurultu zaten yok denecek kadar az.
    # Bu modda faz OLDUGU GIBI korunur, sadece genlik birime cekilir (duz
    # spektrum = beyazlatilmis uyumlu filtre). Ayrik karar yok -> dal
    # belirsizligi yok -> tekrarlanabilirlik yalnizca gurultuyle sinirli.
    if RECON_SOFT:
        amp_ok = np.abs(Xn) > 0.35
        keep = sel & amp_ok
        # GENLIGI KORU (birime cekme): birime cekmek zayif RE'leri de tam
        # agirliga cikarir, oysa fazi en gurultulu olanlar onlardir. Olculen
        # genlik dogal bir SNR agirligidir ve ayrica ILETILEN spektrumun
        # kendisidir — uyumlu filtrenin dogru tanimi budur.
        Xs = Xn if RECON_KEEP_AMP else Xn / (np.abs(Xn) + 1e-30)
        Gc[keep] = Xs[keep]
        Xs = Xs / (np.abs(Xs) + 1e-30)
        act = Gc != 0
        # kalite olcutu: kuantalanmis noktaya UZAKLIK (bilgi amacli, kapi degil)
        qq = (np.sign(Xs.real) + 1j * np.sign(Xs.imag)) / np.sqrt(2.0)
        ev = float(np.median(np.abs(Xs[keep] - qq[keep]))) if keep.any() else float("nan")
        return Gc, Xh, dict(n_re=int(act.sum()), n_qpsk=int(keep.sum()),
                            n_bpsk=0, evm=ev, n_cand=int(sel.sum()))

    # --- QPSK: DILIM ve KAPI FAZ UZERINDEN ---
    # NEDEN: referansi birim genlikle yaziyoruz (duz spektrum = beyazlatilmis
    # uyumlu filtre), ama EVM'i |Xn - q| ile olcmek YANLISTI. NR'de kanallar
    # arasi GUC OFSETLERI var; genligi 3 olan KUSURSUZ bir RE'nin toplam
    # mesafesi 2.5 cikiyor ve 0.40'lik kapida eleniyordu.
    # SAHADA OLCULDU (evm_source_test.py, 11063 RE):
    #     EVM toplam  medyan 0.635   ort 1.080   %90 2.490
    #     EVM faz     medyan 0.082   ort 0.137   %90 0.345
    #     faz hatasi 45 dereceyi asan RE orani: %0.0  (YANLIS DILIM YOK)
    #     |Xn| histogrami cok modlu: ~0 (bos), ~0.9, ~1.3, ~2.8
    # Yani faz zaten dogru; kapi adaylarin yarisindan fazlasini sirf GENLIGI
    # 1 degil diye atiyordu -> referans spektrumunda delik, yuksek yan lob,
    # dusuk tekrarlanabilirlik. Olcut faz olunca hepsi geri geliyor.
    amp_ok = np.abs(Xn) > 0.35                 # BOS RE'ler (iletim yok) elensin
    Xu = Xn / (np.abs(Xn) + 1e-30)             # faza indirge
    q = (np.sign(Xu.real) + 1j * np.sign(Xu.imag)) / np.sqrt(2.0)
    q = np.where(np.abs(q) < 1e-9, (1 + 1j) / np.sqrt(2.0), q)
    evm = np.abs(Xu - q)                       # FAZ EVM'i (genlikten bagimsiz)
    keepq = qmask & amp_ok & (evm <= evm_max)
    Gc[keepq] = q[keepq]

    # --- BPSK: ekseni OLC, o eksende dilimle ---
    n_b = 0
    if bmask.any():
        z0 = Xn[bmask]
        z = z0 / (np.abs(z0) + 1e-30)          # BPSK'de de olcut FAZ
        th = 0.5 * np.angle(np.mean(z ** 2) + 1e-30)
        r = (z * np.exp(-1j * th)).real
        b = np.sign(r)
        b[b == 0] = 1.0
        val = b * np.exp(1j * th)
        e_b = np.abs(z - val)
        keepb = np.zeros_like(bmask)
        sub = (np.abs(z0) > 0.35) & (e_b <= evm_max)
        idxb = np.where(bmask)
        keepb[idxb[0][sub], idxb[1][sub]] = True
        Gc[keepb] = val[sub]
        n_b = int(sub.sum())

    n_q = int(keepq.sum())
    act = Gc != 0
    ev = float(np.median(evm[keepq])) if n_q else float("nan")
    return Gc, Xh, dict(n_re=int(act.sum()), n_qpsk=n_q, n_bpsk=n_b,
                        evm=ev, n_cand=int(sel.sum()))


def _recon_synth(Gc, us, cps, n_out, nu, phi=None):
    """Temiz izgaradan ZAMAN domeni referansi (IFFT + CP), tam uzunlukta diz.

    phi verilirse SEMBOL BASINA FAZ GERI UYGULANIR — o faz iletilen sinyalin
    (ve ayni LO ile yapilacak olcumun) parcasidir.

    Cikti PPS'e goreli tam pencere uzunlugundadir; boylece load_key'in bekledigi
    'key + mask' bicimi degismeden calisir ve t_ref dogrudan PPS ofsetidir."""
    nf = nu["n_fft"]
    out = np.zeros(n_out, np.complex128)
    msk = np.zeros(n_out, bool)
    for i, (u, cp) in enumerate(zip(us, cps)):
        g = Gc[i] if phi is None else Gc[i] * phi[i]
        x = np.fft.ifft(np.fft.ifftshift(g)) * nf
        sym = np.concatenate([x[-cp:], x])
        a, b = int(u - cp), int(u + nf)
        if a < 0 or b > n_out:
            continue
        out[a:b] = sym
        msk[a:b] = True
    return out, msk


def _recon_selfcheck(ref, tag="YENIDEN KURGU"):
    """Yeniden kurulan referansin KENDI otokorelasyonundaki cok yolu olc.

    v3 anahtarinda bu -8.7 dB idi (24.40 m'de gomulu yansitici). Temiz bir
    referansta ana lobun disinda TB carpimi tabaninin ustunde tepe OLMAMALIDIR."""
    n = ref.size
    if n < 1024:
        return None
    nf = 1 << int(np.ceil(np.log2(2 * n)))
    R = np.fft.fft(ref, nf)
    P = np.abs(R) ** 2
    tot = float(P.sum()) + 1e-30
    f0 = float((np.fft.fftfreq(nf, 1.0 / FS) * P).sum() / tot)
    fb = np.fft.fftfreq(nf, 1.0 / FS)
    b_rms = float(np.sqrt(((fb - f0) ** 2 * P).sum() / tot)) * 2 * np.sqrt(3)
    A = np.abs(np.fft.ifft(P))
    A /= A[0] + 1e-30
    main = max(2, int(np.ceil(FS / max(b_rms, 1e3))))
    win = min(nf // 2, int(400.0 / C_AIR * FS))
    if win <= main + 2:
        return None
    side = A[main + 1:win]
    j = int(np.argmax(side))
    tb = ref.size / FS * max(b_rms, 1e3)
    print(f"\n  {tag} — OTOKORELASYON DENETIMI")
    print(f"    etkin bant   : {b_rms/1e6:.2f} MHz  -> menzil cozunurlugu "
          f"{C_AIR/(2*max(b_rms,1e3)):.2f} m")
    print(f"    TB carpimi   : {tb:.0f}  -> beklenen yan lob tabani "
          f"{-10*np.log10(max(tb,1.0)):.1f} dB")
    print(f"    en buyuk yan : {20*np.log10(side[j]+1e-30):+.1f} dB @ "
          f"{(main+1+j)/FS*C_AIR:.2f} m")
    print(f"    (v3 anahtarinda bu -8.7 dB @ 24.40 m idi — gomulu cok yol)")
    return dict(b_rms=b_rms, side_db=20 * np.log10(side[j] + 1e-30),
                side_m=(main + 1 + j) / FS * C_AIR)



# ═══════════════════════════════════════════════════════════════════
#  11d) SSB TARAMASI — hucreyi ZAMAN DOMENINDE bul (telefon gibi)
# ═══════════════════════════════════════════════════════════════════
# NEDEN AYRI BIR TARAYICI: v4'un ilk surumlerinde hucre kimligi FREKANS
# domeninde, kendi kurdugumuz sembol kafesine oturarak araniyordu. Kafes
# VERIDEN (CP korelasyonundan) geliyordu; SSB baska zamanlamadaysa ya da
# kafes birkac ornek kaydiysa FFT penceresi sembol sinirini kesiyor ve PSS
# yok oluyordu. SAHADA OLCULDU: 40 ms'in tamami, 11.4M hipotez tarandi ve
# PSS tepe/medyani 1.16-1.23'te kaldi — yani hicbir sey bulunamadi.
#
# BU TARAYICI KAFESE HIC BAKMAZ. Gercek alicilarin ilk kilitlenmede yaptigini
# yapar: PSS'in ZAMAN DOMENI dalga formunu uretip kaydirmali korelasyon arar
# ve SSB periyoduna katlayarak biriktirir. Sembol sinirini BILMEYE gerek
# yoktur — korelasyon zaten onu bulur.
#
# DAR BANT: bantta cok guclu bir yayici olabilir (sahada 25 dB kazancta ADC'yi
# kirpiyordu). Her GSCN adayina DIJITAL inip desimasyonla daraltmak bant disi
# gucu isleme sokmaz ve PSS'in ~21 dB korelasyon kazancini tam kullanir.
#
# HASSASIYET (sentetik kontrol): -20 dB SNR'da bile oran ~350 ile DOGRU bulur.
# Eski frekans-domeni arama -10 dB'de cokuyordu -> 30+ dB fark.
#
# SAHADA DOGRULANDI (2026-08-19): GSCN 340 / 3489.60 MHz, PSS 0.9994,
# SSS N_ID_1=56 -> PCI 168, PBCH i_SSB=1 (0.996). Telefonun ServiceMode
# ciktisiyla (PCI 168, SSB Index 1, ARFCN 632640 -> 3489.6 MHz) UCU DE BIREBIR.

SSB_DEC       = 16          # tarama desimasyonu (122.88 -> 7.68 MHz)
SSB_BAND      = (3460e6, 3580e6)   # taranacak bant (n78 Turkiye)
SSB_SCAN_CAP  = 3           # tarama yakalama sayisi
SSB_ID_CAP    = 8           # kimlik cozumu yakalama sayisi
SSB_MIN_RATIO = 5.0e4       # aday sayilmak icin asgari tepe/medyan
SSB_HALF_SC   = 15e3        # PSS merkezi SS_REF'in bu kadar ALTINDA
                            # (SSB 240 altasiyici, merkez 119.5; PSS 56..182
                            #  -> merkezi 119 -> yarim altasiyici asagida)


def gscn_candidates(lo=None, hi=None):
    """TS 38.104 5.4.3.1 — 3-24.25 GHz senkron rasteri.

    SS_REF = 3000 MHz + N * 1.44 MHz,  GSCN = 7499 + N
    SSB, tasiyicinin altasiyici izgarasina degil BU rastere oturur."""
    lo = SSB_BAND[0] if lo is None else lo
    hi = SSB_BAND[1] if hi is None else hi
    n0 = int(np.ceil((lo - 3000e6) / 1.44e6))
    n1 = int(np.floor((hi - 3000e6) / 1.44e6))
    return [(n, 3000e6 + n * 1.44e6) for n in range(n0, n1 + 1)]


def pss_time(n_id2, fs_eff, cfo=0.0):
    """PSS'in ZAMAN DOMENI hali (CP'siz), DC'ye ortalanmis."""
    nfft = int(round(fs_eff / SCS_HZ))
    X = np.zeros(nfft, complex)
    X[(np.arange(PSS_NSC) - PSS_NSC // 2) % nfft] = pss_seq(n_id2)
    t = np.fft.ifft(X) * nfft
    if cfo:
        t = t * np.exp(2j * np.pi * cfo * np.arange(nfft) / fs_eff)
    return t.astype(np.complex64)


def _ssb_downmix(x, f_target, f_lo, dec):
    """f_target'i DC'ye getir ve dec kati desim (frekans domeninde, tam)."""
    n = x.size
    nb = n // dec
    X = np.fft.fft(x.astype(np.complex64))
    k0 = int(round((f_target - f_lo) / (FS / n)))
    Xr = np.roll(X, -k0)
    Z = np.concatenate([Xr[:nb // 2], Xr[-(nb - nb // 2):]])
    return (np.fft.ifft(Z) * (nb / n)).astype(np.complex64), FS / dec


def _pss_corr(xd, fs_eff, n_id2, cfo, per_s=0.020):
    """Zaman domeni PSS korelasyonu + periyoda katlama. Doner (profil, nfft)."""
    t = pss_time(n_id2, fs_eff, cfo)
    n = xd.size
    nf = 1 << int(np.ceil(np.log2(n)))
    c = np.fft.ifft(np.fft.fft(xd, nf) * np.conj(np.fft.fft(t, nf)))[:n - t.size]
    p = (np.abs(c) ** 2).astype(np.float64)
    per = int(round(per_s * fs_eff))
    nrep = p.size // per
    if nrep >= 2:
        p = p[:nrep * per].reshape(nrep, per).sum(0)
    return p, t.size


def ssb_scan(ctx, band=None, n_cap=SSB_SCAN_CAP, cfos=None, quiet=False):
    """Bandi tara, SSB adaylarini bul. Doner sirali liste.

    Tek LO yerlesimi butun bandi kapsar (122.88 MHz pencere); GSCN'lere
    DIJITAL inilir, retune YOKTUR (hizli ve faz tutarli)."""
    if cfos is None:
        cfos = np.arange(-12.5e3, 12.6e3, 2.5e3)
    gl = gscn_candidates(*(band or SSB_BAND))
    caps = []
    for _ in range(n_cap):
        b, _t = acquire(ctx)
        if b is not None:
            caps.append(b[0].copy())
    if not caps:
        return []
    if not quiet:
        pk = max(float(np.abs(c).max()) for c in caps)
        print(f"  {len(caps)} yakalama, tepe {20*np.log10(pk+1e-30):+.1f} dBFS"
              + ("   [KIRPMA]" if pk > 0.85 else ""))
        print(f"  {len(gl)} GSCN adayi {gl[0][1]/1e6:.2f} .. {gl[-1][1]/1e6:.2f} MHz")
    rows = []
    for n_g, f_ss in gl:
        best = (-1.0, -1, 0.0, 0)
        for c in caps:
            xd, fse = _ssb_downmix(c, f_ss - SSB_HALF_SC, CENTER_FREQ, SSB_DEC)
            for i2 in range(3):
                for cf in cfos:
                    p, _ = _pss_corr(xd, fse, i2, cf)
                    j = int(np.argmax(p))
                    r = float(p[j]) / (float(np.median(p)) + 1e-30)
                    if r > best[0]:
                        best = (r, i2, float(cf), j)
        rows.append(dict(gscn=n_g, f_ss=f_ss, ratio=best[0], n_id2=best[1],
                         cfo=best[2], pos=best[3]))
    rows.sort(key=lambda z: -z["ratio"])
    if not quiet:
        med = float(np.median([r["ratio"] for r in rows])) + 1e-30
        print(f"\n  {'GSCN':>6} {'SS_REF[MHz]':>12} {'oran':>12} {'N_ID_2':>7} "
              f"{'tepe/medyan':>12}")
        for r in rows[:6]:
            print(f"  {r['gscn']:>6d} {r['f_ss']/1e6:>12.2f} {r['ratio']:>12.0f} "
                  f"{r['n_id2']:>7d} {r['ratio']/med:>12.1f}")
        print(f"  tarama medyani {med:.0f}")
    return rows


def ssb_identify(ctx, f_ss, n_cap=SSB_ID_CAP, quiet=False):
    """Bulunan SSB'de hucre kimligini coz: PCI ve i_SSB.

    SSS ve PBCH DMRS STANDARDA GORE denenir; ikisi de tutmazsa None doner.
    Doner dict(pci, n_id1, n_id2, i_ssb, cfo, pos, metrikler...)."""
    caps = []
    for _ in range(n_cap):
        b, _t = acquire(ctx)
        if b is not None:
            caps.append(b[0].copy())
    if len(caps) < 2:
        return None
    fse = FS / SSB_DEC
    nfft = int(round(fse / SCS_HZ))
    cp = int(round(nfft * CP_NORM / N_FFT))
    per = int(round(0.020 * fse))
    xs = [_ssb_downmix(c, f_ss - SSB_HALF_SC, CENTER_FREQ, SSB_DEC)[0]
          for c in caps]

    best = (-1.0, 0, 0.0, 0)
    for i2 in range(3):
        for cf in np.arange(-20e3, 20.1e3, 1.0e3):
            acc = None
            for xd in xs:
                p, _ = _pss_corr(xd, fse, i2, cf)
                acc = p if acc is None else acc + p
            j = int(np.argmax(acc))
            r = float(acc[j]) / (float(np.median(acc)) + 1e-30)
            if r > best[0]:
                best = (r, i2, float(cf), j)
    ratio, n_id2, cfo, j_pss = best
    xs = [x * np.exp(-2j * np.pi * cfo * np.arange(x.size) / fse) for x in xs]

    def grid(k):
        """SSB'nin k. sembolunun 240 altasiyicisi, butun tekrarlardan."""
        out = []
        for xd in xs:
            u = j_pss + k * (nfft + cp)
            while u + nfft <= xd.size:
                Y = np.fft.fftshift(np.fft.fft(xd[u:u + nfft]))
                c0 = nfft // 2
                if c0 - 119 >= 0 and c0 + 121 <= nfft:
                    out.append(Y[c0 - 119:c0 + 121])
                u += per
        if not out:
            return None
        A = np.array(out)
        ref = A[0]
        S = np.zeros_like(ref)
        for a in A:
            S = S + a * np.exp(-1j * np.angle(np.vdot(ref, a) + 1e-30))
        return S / len(A)

    V = {k: grid(k) for k in range(4)}
    if V[0] is None or V[2] is None:
        return None
    mp = [_dmrs_metric(V[0][PSS_SC0:PSS_SC0 + PSS_NSC],
                       pss_seq(i).astype(np.complex128)) for i in range(3)]
    n_id2 = int(np.argmax(mp))
    ms = np.array([_dmrs_metric(V[2][PSS_SC0:PSS_SC0 + PSS_NSC],
                                sss_seq(i, n_id2).astype(np.complex128))
                   for i in range(336)])
    n_id1 = int(np.argmax(ms))
    pci = 3 * n_id1 + n_id2
    srt = np.sort(ms)[::-1]
    md = []
    for iss in range(L_MAX_FR1):
        r = pbch_dmrs_seq(pci, iss)
        tot, nn = 0.0, 0
        for s_, sc_, sl_ in pbch_dmrs_re(pci):
            if V[s_] is None:
                continue
            tot += _dmrs_metric(V[s_][np.asarray(sc_)], r[sl_]); nn += 1
        md.append(tot / max(nn, 1))
    md = np.array(md)
    i_ssb = int(np.argmax(md))
    dsrt = np.sort(md)[::-1]
    out = dict(pci=pci, n_id1=n_id1, n_id2=n_id2, i_ssb=i_ssb, cfo=cfo,
               pos=j_pss, f_ss=f_ss, pss_ratio=ratio,
               m_pss=float(mp[n_id2]), m_sss=float(ms[n_id1]),
               m_dmrs=float(md[i_ssb]),
               r_sss=float(srt[0] / (srt[1] + 1e-30)),
               r_dmrs=float(dsrt[0] / (dsrt[1] + 1e-30)),
               fs_eff=fse, nfft_eff=nfft, cp_eff=cp)
    if not quiet:
        print(f"\n  HUCRE KIMLIGI (SSB {f_ss/1e6:.2f} MHz)")
        print(f"    PSS  N_ID_2={n_id2}   uyum {mp[n_id2]:.4f}  "
              f"(digerleri {', '.join(f'{v:.3f}' for i, v in enumerate(mp) if i != n_id2)})")
        print(f"    SSS  N_ID_1={n_id1}   uyum {ms[n_id1]:.4f}  "
              f"2.ye {out['r_sss']:.2f}x")
        print(f"    -> PCI = 3*{n_id1} + {n_id2} = {pci}")
        print(f"    PBCH i_SSB={i_ssb}   uyum {md[i_ssb]:.4f}  "
              f"2.ye {out['r_dmrs']:.2f}x")
        print(f"    kesirli kayma {cfo/1e3:+.2f} kHz, "
              f"PSS periyot ici {j_pss/fse*1e6:.1f} us")
        ok = (mp[n_id2] > 0.6 and ms[n_id1] > 0.6 and md[i_ssb] > 0.6)
        print(f"    [{'OK — kimlik KESIN' if ok else 'ZAYIF — kimlik guvenilmez'}]")
    return out


def ssb_find(band=None, n_scan=SSB_SCAN_CAP, n_id=SSB_ID_CAP, f_lo=None):
    """Tam akis: bandi tara -> en iyi adayi coz. Oturumu kendi acar."""
    lo, hi = band or SSB_BAND
    if f_lo is None:
        f_lo = 0.5 * (lo + hi)
    print("=" * 70)
    print(f" SSB TARAMASI — {lo/1e6:.0f} .. {hi/1e6:.0f} MHz")
    print("=" * 70)
    # TARAMA LO'su GECICIDIR: bandin ortasina alinir ki tek yerlesim butun
    # bandi kapsasin. Ama CENTER_FREQ olcumun de kullandigi global degerdir
    # ve tarama bitince GERI KONMALIDIR — yoksa sonrasinda uretilen anahtar
    # tarama LO'suna gore kurulur ve olcum LO'suyla uyusmaz.
    # SAHADA GORULDU: --learn --synth anahtari 3520 MHz'e gore kuruldu, olcum
    # 3489.6'da yapildi -> 30.4 MHz kayma -> korelasyon tepe/medyan 3.4
    # (ogrenilmis anahtarda 138.8), MTI 0 dB, anahtar tamamen ise yaramaz.
    _f_meas = CENTER_FREQ
    globals()["CENTER_FREQ"] = f_lo
    try:
        ctx = setup_x410(win_s=40.0e-3, advance_s=PPS_OFFSET_S)
        rows = ssb_scan(ctx, (lo, hi), n_scan)
    finally:
        pass
    if not rows or rows[0]["ratio"] < SSB_MIN_RATIO:
        print("\n[HATA] bantta SSB bulunamadi.")
        globals()["CENTER_FREQ"] = _f_meas
        return None
    cand = rows[0]
    print(f"\n  EN IYI: GSCN {cand['gscn']}, SS_REF {cand['f_ss']/1e6:.2f} MHz")
    cell = ssb_identify(ctx, cand["f_ss"], n_id)
    globals()["CENTER_FREQ"] = _f_meas          # OLCUM LO'suna geri don
    if cell is None:
        print("\n[HATA] hucre kimligi cozulemedi.")
        return None
    cell["gscn"] = cand["gscn"]
    cell["f_lo_scan"] = f_lo
    cell["f_lo_meas"] = _f_meas
    cell["others"] = [dict(gscn=r["gscn"], f_ss=r["f_ss"], ratio=r["ratio"])
                      for r in rows[1:4]]
    print(f"\n  Bantta gorulen diger adaylar:")
    for o in cell["others"]:
        print(f"    GSCN {o['gscn']:>4d}  {o['f_ss']/1e6:>8.2f} MHz  "
              f"oran {o['ratio']:>10.0f}")
    print("=" * 70)
    return cell




# ═══════════════════════════════════════════════════════════════════
#  11e) --learn --synth — ANAHTARI OLCME, PCI'DAN URET
# ═══════════════════════════════════════════════════════════════════
# Hucre kimligi (PCI, i_SSB) cozuldukten sonra SSB'nin PSS/SSS/PBCH-DMRS
# RE'leri PCI'nin DETERMINISTIK FONKSIYONUDUR — olculmesine gerek yoktur.
# Anahtari olcmek yerine URETMEK su sorunlarin HEPSINI bir anda bitirir:
#   * kanal                 : hic girmez (olculen bir sey yok)
#   * dal belirsizligi      : yok (dilimleme yok)
#   * gurultu               : yok
#   * tekrarlanabilirlik    : TANIM GEREGI 1.0 (ayni PCI -> ayni bitler)
#
# Dosyanin eski kurali "referans URETILMEZ, OGRENILIR" idi ve o kural
# DOGRUYDU: hucre kimligi bilinmeden uretilemez. Artik biliniyor
# (--ssbscan, sahada PCI 168 / i_SSB 1, metrikler 0.999).
#
# BEDELI: bant SSB'nin 240 altasiyicisi = 7.2 MHz -> menzil cozunurlugu
# ~20.8 m. Ogrenilmis anahtar 17-20 MHz ile ~8.6 m veriyordu. Yani
# tekrarlanabilirlik ile cozunurluk arasinda acik bir takas var; ikisi de
# uretilebildigi icin secim kullanicinin.
#
# PBCH VERI RE'leri BOS birakilir: SFN ile degisirler, deterministik
# degildirler (v3'un gamma maskesi de onlari zaten eliyordu).

def _synth_ssb_grid(pci, i_ssb):
    """SSB'nin 4 sembolu x 240 altasiyici — SADECE TAM BILINEN RE'ler.

    PSS  : sembol 0, altasiyici 56..182   (m-dizisi, N_ID_2'den)
    SSS  : sembol 2, altasiyici 56..182   (m-dizisi, PCI'den)
    DMRS : sembol 1,2,3, TS 38.211 Tablo 7.4.3.1-1 konumlari (Gold, PCI+i_SSB)
    PBCH VERI: BOS (SFN ile degisir)."""
    n_id1, n_id2 = pci // 3, pci % 3
    G = np.zeros((SSB_SYMS, SSB_NSC), np.complex128)
    G[0, PSS_SC0:PSS_SC0 + PSS_NSC] = pss_seq(n_id2)
    G[2, PSS_SC0:PSS_SC0 + PSS_NSC] = sss_seq(n_id1, n_id2)
    r = pbch_dmrs_seq(pci, i_ssb)
    for sym, sc, sl in pbch_dmrs_re(pci):
        G[sym, np.asarray(sc)] = r[sl]
    return G


def synth_key_from_cell(cell, out_path=None, overwrite=False, n_rep=1):
    """Cozulmus hucreden ANAHTARI URET (olcum yok).

    cell: ssb_find()/ssb_identify() ciktisi.
    Cikti bicimi load_key ile AYNIDIR; olcum zinciri degismez."""
    pci, i_ssb = cell["pci"], cell["i_ssb"]
    f_ss = cell["f_ss"]
    if out_path is None:
        out_path = LEARN_FILE
    if not os.path.isabs(out_path):
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), out_path)
    if os.path.exists(out_path) and not overwrite:
        print(f"[HATA] anahtar dosyasi ZATEN VAR: {out_path}")
        print(f"       --learn-out YENI.npz  ya da  --force-key")
        sys.exit(1)

    print("=" * 70)
    print(" ANAHTAR URETIMI — PCI'dan (olcum YOK)")
    print("=" * 70)
    print(f"  PCI {pci} (N_ID_1={pci//3}, N_ID_2={pci%3}), i_SSB {i_ssb}")
    print(f"  SSB {f_ss/1e6:.3f} MHz,  LO {CENTER_FREQ/1e6:.3f} MHz "
          f"(SSB LO'ya gore {(f_ss-CENTER_FREQ)/1e6:+.2f} MHz)")
    if abs(f_ss - CENTER_FREQ) > 0.45 * CARRIER_BW_HZ:
        print(f"  [UYARI] SSB, bant sinirinin ({CARRIER_BW_HZ/2e6:.0f} MHz) "
              f"disina yakin. Olcumu --freq {f_ss/1e6:.1f} ile yap.")

    G = _synth_ssb_grid(pci, i_ssb)
    n_re = int(np.count_nonzero(G))
    print(f"  TAM BILINEN RE: {n_re}  "
          f"(PSS {PSS_NSC} + SSS {PSS_NSC} + PBCH-DMRS {PBCH_DMRS_N})")

    # --- SSB'yi tam ornekleme hizinda sentezle ---
    # SSB altasiyicisi m, SS_REF'e gore (m - 119.5)*SCS frekansindadir.
    # Yarim altasiyici tamsayi bin'e oturmadigi icin once (m-119) bin'ine
    # konur, sonra zaman domeninde -SCS/2 kadar kaydirilir.
    df_ss = f_ss - CENTER_FREQ
    k_ss = int(round(df_ss / SCS_HZ))
    if abs(k_ss) > N_FFT // 2 - 130:
        print(f"[HATA] SSB ({f_ss/1e6:.2f} MHz) pencerenin disinda; "
              f"--freq {f_ss/1e6:.1f} ile tekrar dene.")
        sys.exit(1)
    sym_len = N_FFT + CP_NORM
    out_len = SSB_SYMS * sym_len
    x = np.zeros(out_len, np.complex128)
    for i in range(SSB_SYMS):
        X = np.zeros(N_FFT, np.complex128)
        b0 = N_FFT // 2 + k_ss - 119
        X[b0:b0 + SSB_NSC] = G[i]
        s = np.fft.ifft(np.fft.ifftshift(X)) * N_FFT
        x[i * sym_len:(i + 1) * sym_len] = np.concatenate([s[-CP_NORM:], s])
    # yarim altasiyici kaymasi
    x = x * np.exp(-2j * np.pi * (SCS_HZ / 2.0) * np.arange(out_len) / FS)

    # --- zaman ekseni: PSS'in PPS'e goreli konumu ---
    per_s = 0.020
    pos_full = int(round(cell["pos"] * (FS / cell["fs_eff"])))
    t_ref = pos_full % int(round(per_s * FS))
    N = int(round(LEARN_WIN_MS * 1e-3 * FS))
    if t_ref + out_len > N:
        t_ref = t_ref % int(round(per_s * FS))
    key = np.zeros(N, np.complex128)
    mask = np.zeros(N, bool)
    a0 = int(t_ref)
    a1 = min(N, a0 + out_len)
    key[a0:a1] = x[:a1 - a0]
    mask[a0:a1] = True
    key = key / (np.sqrt(np.mean(np.abs(key[a0:a1]) ** 2)) + 1e-30) * 0.05
    print(f"  sentez: PPS +{a0/FS*1e3:.4f} ms, {(a1-a0)/FS*1e6:.1f} us "
          f"({a1-a0} ornek, {SSB_SYMS} sembol)")

    _recon_selfcheck(band_limit_sig(key[a0:a1].astype(np.complex64)),
                     tag="URETILEN ANAHTAR")

    gam = np.zeros(N, np.float32)
    gam[a0:a1] = 1.0
    np.savez(out_path, key=key.astype(np.complex64), gamma=gam, mask=mask,
             fs=FS, center_freq=CENTER_FREQ, rx_gain=RX_GAIN,
             win_ms=LEARN_WIN_MS, n_cap=0, t0=0.0,
             wb_psd=np.zeros(1024, np.float32), wb_nfft=1024,
             wb_f_lo=-SSB_NSC * SCS_HZ / 2, wb_f_hi=SSB_NSC * SCS_HZ / 2,
             pci=pci, n_id1=pci // 3, n_id2=pci % 3,
             f_ssb=f_ss, t_ssb=a0 / FS,
             ssb_period_ms=20.0, key_period_ms=20.0,
             recon=3, recon_synth=1, recon_i_ssb=i_ssb,
             recon_n_re=n_re, recon_gscn=cell.get("gscn", -1),
             recon_df_hz=cell.get("cfo", 0.0),
             recon_m_pss=cell.get("m_pss", 0.0),
             recon_m_sss=cell.get("m_sss", 0.0),
             recon_m_dmrs=cell.get("m_dmrs", 0.0))
    print(f"\n  Kaydedildi: {out_path}   [recon=3, URETILMIS]")
    print(f"  Bu anahtar PCI'nin fonksiyonudur: ayni PCI -> BIT DUZEYINDE ayni")
    print(f"  dosya. Tekrarlanabilirlik TANIM GEREGI 1.0.")
    print("=" * 70)
    return out_path


def _recon_cir_report(H, ks, nu, tag="KANAL"):
    """Kestirilen H(f)'ten KANALI olc ve tap tap raporla.

    Bu, yeniden kurgunun bedava yan urunudur: H zaten kestiriliyor, CIR onun
    ters donusumu. v3'te bu bilgi anahtarin ICINE gomuluyordu; burada AYRI
    olarak olculuyor ve anahtardan CIKARILIYOR.

    Bant sinirli oldugu icin cozunurluk c/B'dir; taplar bundan yakinsa birlesir.
    Kenar sinc etegini kirmak icin Tukey pencere uygulanir."""
    if H is None or ks is None or ks.size < 8:
        return None
    lo, hi = int(ks.min()), int(ks.max())
    n = hi - lo + 1
    Hb = np.zeros(n, np.complex128)
    Hb[ks - lo] = H[ks]
    a = 0.25
    w = np.ones(n)
    m = max(1, int(a * n / 2))
    w[:m] = 0.5 * (1 - np.cos(np.pi * np.arange(m) / m))
    w[-m:] = w[:m][::-1]
    npad = 1 << int(np.ceil(np.log2(max(8 * n, 4096))))
    cir = np.fft.ifft(np.concatenate([Hb * w, np.zeros(npad - n)]))
    cir = np.abs(cir) / (np.abs(cir).max() + 1e-30)
    df = nu["scs"]
    dt = 1.0 / (npad * df)
    res_m = C_AIR / (n * df)
    lim = min(npad // 2, int(600.0 / C_AIR / dt))
    prof = cir[:lim]
    main = max(1, int(res_m / (C_AIR * dt)))
    pk = []
    for i in range(1, lim - 1):
        if prof[i] >= prof[i - 1] and prof[i] > prof[i + 1] and prof[i] > 10 ** (-35 / 20.0):
            pk.append((20 * np.log10(prof[i] + 1e-30), i * dt * C_AIR))
    pk.sort(key=lambda z: -z[0])
    tot = float(np.sum(prof ** 2)) + 1e-30
    d0 = float(np.sum(prof[:main + 1] ** 2))
    rr = np.arange(lim) * dt * C_AIR
    p2 = prof ** 2
    mean_m = float((rr * p2).sum() / tot)
    rms_m = float(np.sqrt((p2 * (rr - mean_m) ** 2).sum() / tot))
    print(f"\n  {tag} — OLCULEN COK YOL (H(f)'ten, anahtardan AYRI)")
    print(f"    bant {n*df/1e6:.2f} MHz -> gecikme cozunurlugu {res_m:.1f} m")
    print(f"    {'gecikme[m]':>12} {'seviye[dB]':>11}")
    for db, rm in pk[:8]:
        print(f"    {rm:>12.2f} {db:>+11.1f}")
    print(f"    RMS gecikme yayilimi : {rms_m:.1f} m ({rms_m/C_AIR*1e9:.0f} ns)")
    print(f"    ana yol disi enerji  : %{100*(1-d0/tot):.1f}")
    print(f"    (v3 anahtarinda bu cok yol ANAHTARIN ICINE gomuluyordu;")
    print(f"     v4'te olculup DISARIDA birakiliyor)")
    return dict(peaks=pk[:8], rms_m=rms_m, res_m=res_m,
                off_main=float(1 - d0 / tot))


def recon_survey(ctx, n_cap=RECON_SURVEY_N, win_ms=LEARN_WIN_MS, quiet=False):
    """TANIMA ASAMASI — hucre KIMLIGI degil, dalga formunun OLCULEBILIR ozellikleri.

    Olculenler:
      1) isgal edilen bant ve merkez   (spektrumdan)
      2) numeroloji mu / SCS           (CP korelasyonundan, KOR)
      3) deterministik bolgenin yeri   (yakalamalar arasi tutarliliktan)
      4) TEKRAR PERIYODU               (bolgelerin PPS ofseti dagilimindan)
    Hicbiri PCI/PSS/SSS/PBCH bilmeyi gerektirmez.

    Doner dict ya da None."""
    N = ctx["N_act"]
    S = np.zeros(N, np.complex128)
    P = np.zeros(N, np.float64)
    nf_wb = min(WB_NFFT, 1 << int(np.floor(np.log2(max(N, 2)))))
    Pf = np.zeros(nf_wb)
    first = None
    used = 0
    if not quiet:
        print("=" * 70)
        print(f" ASAMA 1/2 — TANIMA ({n_cap} yakalama)")
        print("=" * 70)
    for i in range(n_cap):
        buf, _t = acquire(ctx)
        if buf is None:
            continue
        b = buf[0]
        if first is None:
            first = b.copy()
        nb = b.size // nf_wb
        if nb >= 1:
            blk = b[:nb * nf_wb].reshape(nb, nf_wb)
            sel = np.linspace(0, nb - 1, min(4, nb)).astype(int)
            Pf += (np.abs(np.fft.fft(blk[sel], axis=1)) ** 2).mean(0)
        coef = 1.0 + 0j if used == 0 else complex(np.vdot(S, b))
        b2 = b * np.exp(-1j * np.angle(coef))
        S += b2
        P += np.abs(b2).astype(np.float64) ** 2
        used += 1
        if not quiet:
            g = float(np.sum(np.abs(S) ** 2) / (used * np.sum(P) + 1e-30))
            print(f"\r    yakalama {used}/{n_cap}  tutarlilik %{100*g:.1f}",
                  end="", flush=True)
    if not quiet:
        print()
    if used < 3 or first is None:
        print("\n[HATA] TANIMA icin yeterli yakalama yok.")
        return None

    # --- 1) bant / merkez ---
    Pf /= used
    edges, _ = _wb_band_edges(Pf)
    df_wb = FS / nf_wb
    if edges is None:
        f_lo = f_hi = 0.0
        if not quiet:
            print("  [UYARI] isgal edilen bant olculemedi.")
    else:
        f_lo = (edges[0] - nf_wb // 2) * df_wb
        f_hi = (edges[1] - 1 - nf_wb // 2) * df_wb
    ctr = 0.5 * (f_lo + f_hi)
    if not quiet:
        print(f"\n  ISGAL EDILEN BANT: {(CENTER_FREQ+f_lo)/1e6:.3f} .. "
              f"{(CENTER_FREQ+f_hi)/1e6:.3f} MHz  ({(f_hi-f_lo)/1e6:.2f} MHz)")
        print(f"    bant ortasi   : {(CENTER_FREQ+ctr)/1e6:.3f} MHz")
        print(f"    LO kaymasi    : {ctr/1e6:+.3f} MHz", end="")
        if abs(ctr) > 0.5e6:
            print("   [BILGI] LO merkezde degil -> sembol basina faz OLCULECEK")
        else:
            print()

    # --- 2) deterministik bolge + periyot (numerolojiden BAGIMSIZ) ---
    gam = (np.abs(S) ** 2) / (used * P + 1e-30)
    if LEARN_SMOOTH > 1:
        gam = np.convolve(gam, np.ones(LEARN_SMOOTH) / LEARN_SMOOTH, mode="same")
    key_bl = band_limit_sig((S / used).astype(np.complex64))
    best = None
    for gmin in (RECON_GAMMA_MIN, 0.45, 0.35, 0.25, 0.15):
        segs = _segments(gam > gmin, LEARN_MIN_SEG)
        if not segs:
            continue
        segs = merge_segments(segs, int(LEARN_MERGE_US * 1e-6 * FS))
        e = [float(np.sum(np.abs(key_bl[a:b]) ** 2)) for a, b in segs]
        j = int(np.argmax(e))
        offs = [a / FS for a, _ in segs]
        per_ms, nok, ntot = dominant_period_ms(offs, N / FS)
        best = dict(gmin=gmin, segs=segs, j=j, per_ms=per_ms, nok=nok,
                    ntot=ntot, gam=gam)
        if per_ms:
            break
    if best is None:
        print(f"\n[HATA] deterministik bolge bulunamadi (gamma azami {gam.max():.3f}).")
        print("       Sinyal cok zayif ya da tekrar eden icerik yok.")
        return None
    a0, b0 = best["segs"][best["j"]]
    if not quiet:
        print(f"\n  DETERMINISTIK BOLGE (gamma>{best['gmin']:.2f}): "
              f"{len(best['segs'])} kume")
        print(f"    en guclu      : PPS +{a0/FS*1e3:.4f} ms, "
              f"{(b0-a0)/FS*1e6:.1f} us")
        if best["per_ms"]:
            print(f"    TEKRAR PERIYODU: {best['per_ms']:.1f} ms  "
                  f"({best['nok']}/{best['ntot']} kume dogruladi)")
        else:
            print(f"    [UYARI] tekrar periyodu dogrulanamadi -> 20 ms varsayilacak")

    # --- 3) numeroloji: DETERMINISTIK BOLGEDE ve KOHERENT ORTALAMADA ---
    # NEDEN BURADA: ilk surum mu'yu rastgele bir yakalamanin TAMAMINDA olcuyordu.
    # TDD'de pencerenin buyuk kismi UL/bos oldugu icin skor gurultude kaliyor ve
    # secim yakalamadan yakalamaya degisiyordu. SAHADA OLCULDU: ayni hucrede
    # arka arkaya iki kosu, biri 30 kHz (0.373 vs 0.155, net), digeri 120 kHz
    # (0.130 vs 0.108) secti ve ikincisinde zincir tamamen coktu.
    # Dogrusu: once DL'in gercekten oldugu bolgeyi bul, mu'yu ORADA ve
    # yakalamalarin KOHERENT ORTALAMASINDA olc (~10*log10(N) dB daha temiz).
    avg = (S / used).astype(np.complex64)
    seg_a, seg_b = int(a0), int(min(b0, a0 + int(4e-3 * FS)))
    nu, _rep = detect_numerology(avg[seg_a:seg_b], quiet=quiet)
    if nu is None:
        print("\n[HATA] numeroloji tespit edilemedi (OFDM yapisi bulunamadi).")
        return None

    # --- kafes capasi: bolge baslangicini sembol sinirina otur ---
    csp, cse = _cp_profile(avg, nu)
    sym = nu["sym"]
    cand = np.arange(max(nu["cp"], a0 - sym), min(avg.size - nu["n_fft"], a0 + sym))
    u0 = int(a0)
    if csp is not None and cand.size:
        sc = _cp_score(csp, cse, cand, nu, avg.size)
        u0 = int(cand[int(np.argmax(sc))])
    n_sym = max(4, int(round(RECON_KEY_US * 1e-6 * FS / sym)))

    # --- KESIRLI FREKANS KAYMASI (KOR, Van de Beek) ---
    # Baz istasyonunun altasiyici izgarasi bizim FFT izgaramizla ORTUSMEK
    # ZORUNDA DEGILDIR (SSB kendi senkron rasterinde, biz CENTER_FREQ+k*SCS'te).
    # Duzeltilmezse kesirli kayma ICI uretir ve DILIMLEME COKER.
    # SAHADA OLCULDU: duzeltmesiz medyan EVM 0.29, CIR LS artigi %54, olculen
    # cok yol profili anlamsiz (RMS 441 ns; gercegi ~62 ns).
    # Olcum BEDAVA: CP korelasyonunun FAZI zaten elimizde —
    #     arg(sum_l (csp[u_l] - csp[u_l-CP])) = -2*pi*df*N_FFT/FS
    # Belirsiz olmayan aralik +-FS/(2*N_FFT) = +-SCS/2 (30 kHz'de +-15 kHz),
    # olculen kaymalar (+-10 kHz) bunun ICINDE.
    df_hat = 0.0
    if csp is not None:
        us_s, cps_s = _recon_lattice(avg, u0, 2, n_sym - 3, nu)
        z = 0j
        for uu in us_s:
            if uu - nu["cp"] >= 0 and uu + nu["n_fft"] <= avg.size:
                z += csp[uu] - csp[uu - nu["cp"]]
        if abs(z) > 0:
            df_hat = float(-np.angle(z) * FS / (2 * np.pi * nu["n_fft"]))
    if not quiet:
        print(f"    izgara kaymasi: {df_hat/1e3:+.3f} kHz "
              f"({100*abs(df_hat)/nu['scs']:.1f}% altasiyici) — duzeltilecek")
    if not quiet:
        print(f"    kafes capasi  : PPS +{u0/FS*1e3:.4f} ms "
              f"({u0-a0:+d} ornek sembol sinirina cekildi)")
        print(f"    pencere       : {n_sym} sembol "
              f"({n_sym*sym/FS*1e6:.0f} us)")
    return dict(nu=nu, u0=u0, n_sym=n_sym, seg=(a0, b0), df_hat=df_hat,
                per_ms=(best["per_ms"] or 20.0), per_ok=bool(best["per_ms"]),
                f_lo=f_lo, f_hi=f_hi, ctr=ctr, Pf=Pf, nf_wb=nf_wb,
                gamma_used=best["gmin"], N=N)


def learn_key_recon(n_cap=LEARN_N_DEF, win_ms=LEARN_WIN_MS, out_path=None,
                    overwrite=False, gamma_min=RECON_GAMMA_MIN,
                    evm_max=RECON_EVM_MAX, n_survey=RECON_SURVEY_N,
                    key_us=RECON_KEY_US):
    """v4 --learn: TANI, sonra KUR. Hucre kimligine (PCI) BAGLI DEGILDIR.

    v3'ten farki tek cumleyle: v3 ALINAN sinyali ortalar (s (*) h), v4
    ILETILEN sinyali geri kurar (s). Cikti dosya bicimi AYNIDIR — load_key,
    _build_refs, locate_live, range_diag, keydiff hicbir degisiklik gormez."""
    if out_path is None:
        out_path = LEARN_FILE
    if not os.path.isabs(out_path):
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), out_path)
    # UZERINE YAZMA KORUMASI — anahtar SAHA VERISIDIR, masa basinda uretilemez.
    if os.path.exists(out_path) and not overwrite:
        print(f"[HATA] anahtar dosyasi ZATEN VAR: {out_path}")
        print(f"       Uzerine yazilmadi. Iki secenek:")
        print(f"         --learn-out YENI.npz   yeni anahtari AYRI dosyaya yaz,")
        print(f"                                sonra karsilastir:")
        print(f"                                  --keydiff {os.path.basename(out_path)} YENI.npz")
        print(f"         --force-key            eskisini bilerek ez")
        sys.exit(1)
    if not _HAVE_UHD:
        print("[HATA] uhd modulu yok."); sys.exit(1)

    globals()["RECON_KEY_US"] = float(key_us)
    print("=" * 70)
    print(" OGRENME v4 — TANI, SONRA KUR (kanalsiz referans)")
    print("=" * 70)
    print(f"  Hucre KIMLIGI (PCI/PSS/SSS/PBCH) KULLANILMAZ — sahada guvenilmez")
    print(f"  oldugu olculdu. Onun yerine dalga formunun kendi olculebilir")
    print(f"  ozellikleri kullanilir: numeroloji, bant, tekrar periyodu, QPSK.")
    print(f"  ORTALAMA kanali kaldirmaz; DILIMLEME kaldirir.")

    ctx = setup_x410(win_s=win_ms * 1e-3, advance_s=PPS_OFFSET_S)
    sv = recon_survey(ctx, n_survey, win_ms)
    if sv is None:
        sys.exit(1)
    nu, N = sv["nu"], sv["N"]
    n_sym = sv["n_sym"]
    n_before, n_after = 2, n_sym - 3
    j0 = n_before

    print("\n" + "=" * 70)
    print(f" ASAMA 2/2 — OGRENME ({n_cap} yakalama, ~{n_cap/60:.1f} dk)")
    print("=" * 70)

    # TANIMA'da olculen kesirli kaymayi duzelt (yoksa ICI dilimlemeyi coker)
    rot = np.exp(-2j * np.pi * sv["df_hat"] * np.arange(N) / FS).astype(np.complex64)
    nf = nu["n_fft"]
    S = np.zeros((n_sym, nf), np.complex128)
    P = np.zeros((n_sym, nf), np.float64)
    Gref = None
    wsel = None
    us0 = cps0 = None
    used = 0
    print(f"\n  {'#':>4}  {'kafes d':>8} {'CP kor.':>8}  {'faz':>8}  {'tutarli %':>9}")
    for i in range(n_cap):
        buf, _t = acquire(ctx)
        if buf is None:
            print(f"  {i+1:>4}  yakalama EKSIK")
            continue
        x = buf[0]
        us, cps = _recon_lattice(x, sv["u0"], n_before, n_after, nu)
        if us[0] - cps[0] < 0 or us[-1] + nf > x.size:
            print(f"  {i+1:>4}  kafes pencereye sigmadi")
            continue
        lat = dict(_recon_lattice.last)
        G = _recon_demod(x, us, rot, nu).astype(np.complex128)
        if Gref is None:
            Gref = G.copy()
            us0, cps0 = us, cps
            pw = np.abs(G) ** 2
            wsel = pw > (np.median(pw) * 4.0)      # guclu RE'ler: hizalama capasi
            if wsel.sum() < 64:
                wsel = pw > np.median(pw)
            al = 1.0 + 0j
        else:
            G, al = _recon_align(G, Gref, wsel)
            if G is None:
                print(f"  {i+1:>4}  hizalama basarisiz")
                continue
        S += G
        P += np.abs(G) ** 2
        used += 1
        g = float(np.sum(np.abs(S) ** 2) / (used * np.sum(P) + 1e-30))
        print(f"  {i+1:>4}  {lat['d']:>+8d} {lat['score']:>8.3f}  "
              f"{np.degrees(np.angle(al)):>+8.1f}  {100*g:>8.1f}%")

    # YAKALAMA SAYISI TUTARLILIK TESTININ COZUNURLUGUDUR: rastgele icerik de
    # N kucukken tesaduffen "sabit" gorunur. Sentetik testte olculdu: 4
    # yakalamada 1168 RE yanlislikla sabit sayildi, 8'de 17, 24'te 0.
    if used < 8:
        print(f"\n[HATA] yeterli yakalama yok ({used}); en az 8 gerekir.")
        sys.exit(1)
    if used < 16:
        print(f"\n  [UYARI] sadece {used} yakalama: tutarlilik testi zayif.")

    Vbar = S / used
    gam = (np.abs(S) ** 2) / (used * P + 1e-30)
    cons = gam > gamma_min
    print(f"\n  {used} yakalama islendi.")
    print(f"  SABIT RE ({n_sym}x{nf} izgarada, gamma>{gamma_min:.2f}): "
          f"{int(cons.sum())}  (%{100*cons.mean():.2f})")

    H, ks, bpsk, rep = _recon_chan_blind(Vbar, cons, nu,
                                         band=(sv["f_lo"], sv["f_hi"]))
    if H is None:
        print(f"\n[HATA] kor kanal kestirimi basarisiz: {rep}")
        sys.exit(1)
    print(f"\n  KOR KANAL KESTIRIMI (pilot/PCI YOK)")
    print(f"    QPSK altasiyici : {rep['n_sc']}  ({rep['bw_mhz']:.2f} MHz)")
    print(f"    BPSK elenen     : {rep['n_bpsk']} (PSS/SSS gibi; x^4=+1 oldugu icin)")
    print(f"    CIR LS          : {rep['ntap']} tap, artik %{100*rep['resid']:.1f}")

    Hs = np.zeros(nf, np.complex128)
    Hs[ks] = H[ks]
    okm = np.zeros(nf, bool)
    okm[ks] = np.abs(H[ks]) > 0
    Xh0 = np.zeros_like(Vbar)
    Xh0[:, okm] = Vbar[:, okm] / Hs[okm][None, :]
    phi, phi_ok = _recon_sym_phase(Xh0, cons, ks[okm[ks]] if ks.size else ks)
    dph = np.degrees(np.angle(phi[1:] * np.conj(phi[:-1])))
    print(f"    sembol basi faz : "
          + (f"olculdu, adim medyani {np.median(dph):+.1f} derece" if phi_ok
             else "olculemedi -> sabit varsayildi"))

    Gc, Xh, srep = _recon_slice(Vbar, cons, H, ks, bpsk, phi, evm_max)

    # --- KARAR-YONLENDIRMELI ITERASYON ---
    # Kor kestirim sadece BASLANGIC noktasidir. Bir kere dilimledikten sonra
    # x bilinir ve H dogrusal LS ile cok daha temiz cikar; yeni H ile yeniden
    # dilimlenir. Tipik olarak 2-3 turda yakinsar.
    print(f"\n  KARAR-YONLENDIRMELI ITERASYON")
    print(f"    {'tur':>4} {'H artik':>9} {'RE':>7} {'medyan EVM':>11}")
    print(f"    {'kor':>4} {rep['resid']:>8.3f} {srep['n_re']:>7d} "
          f"{srep['evm']:>11.3f}")
    for it in range(3):
        Hd, rd = _recon_chan_dd(Vbar, Gc, phi, ks, nu)
        if Hd is None:
            break
        Hs2 = np.zeros(nf, np.complex128); Hs2[ks] = Hd[ks]
        ok2 = np.zeros(nf, bool); ok2[ks] = np.abs(Hd[ks]) > 0
        X2 = np.zeros_like(Vbar)
        X2[:, ok2] = Vbar[:, ok2] / Hs2[ok2][None, :]
        phi2, _ = _recon_sym_phase(X2, cons, ks)
        Gc2, Xh2, sr2 = _recon_slice(Vbar, cons, Hd, ks, bpsk, phi2, evm_max)
        print(f"    {it+1:>4} {rd:>8.3f} {sr2['n_re']:>7d} {sr2['evm']:>11.3f}")
        if sr2["n_re"] < 200:
            print("    [UYARI] iterasyon RE sayisini dusurdu, onceki tur korunuyor")
            break
        H, phi, Gc, srep, rep = Hd, phi2, Gc2, sr2, dict(rep, resid=rd)
        if abs(rd - rep.get("_prev", 1.0)) < 0.002:
            break
        rep["_prev"] = rd

    print(f"\n  DILIMLEME")
    print(f"    aday RE         : {srep['n_cand']}")
    print(f"    QPSK dilimlenen : {srep['n_qpsk']}  (medyan EVM {srep['evm']:.3f})")
    print(f"    BPSK dilimlenen : {srep['n_bpsk']}  (kendi ekseninde)")
    print(f"    TOPLAM aktif RE : {srep['n_re']}")
    if srep["n_re"] < 200:
        print("\n[HATA] yeniden kurgulanan RE sayisi cok dusuk.")
        sys.exit(1)

    _recon_cir_report(H, ks, nu)

    key, mask = _recon_synth(Gc, us0, cps0, N, nu, phi)
    if not mask.any():
        print("\n[HATA] sentez penceresi yerlestirilemedi."); sys.exit(1)
    a0 = int(np.argmax(mask))
    a1 = int(N - np.argmax(mask[::-1]))
    key = key / (np.sqrt(np.mean(np.abs(key[a0:a1]) ** 2)) + 1e-30) * 0.05
    print(f"\n  SENTEZ: PPS +{a0/FS*1e3:.4f} ms, {(a1-a0)/FS*1e6:.1f} us "
          f"({a1-a0} ornek)")
    _recon_selfcheck(band_limit_sig(key[a0:a1].astype(np.complex64)))

    gam_t = np.zeros(N, np.float32)
    gam_t[a0:a1] = 1.0
    np.savez(out_path, key=key.astype(np.complex64), gamma=gam_t, mask=mask,
             fs=FS, center_freq=CENTER_FREQ, rx_gain=RX_GAIN,
             win_ms=win_ms, n_cap=used, t0=0.0,
             wb_psd=sv["Pf"].astype(np.float32), wb_nfft=sv["nf_wb"],
             wb_f_lo=sv["f_lo"], wb_f_hi=sv["f_hi"],
             pci=-1, n_id1=-1, n_id2=-1,           # KIMLIK KULLANILMADI
             f_ssb=0.0, t_ssb=0.0,
             ssb_period_ms=sv["per_ms"], key_period_ms=sv["per_ms"],
             # --- v4 yeniden kurgu ustverisi ---
             recon=2, recon_mu=nu["mu"], recon_scs=nu["scs"],
             recon_nfft=nu["n_fft"], recon_nsym=n_sym,
             recon_n_re=srep["n_re"], recon_n_qpsk=srep["n_qpsk"],
             recon_n_bpsk=srep["n_bpsk"], recon_evm=srep["evm"],
             recon_bw_mhz=rep["bw_mhz"], recon_n_sc=rep["n_sc"],
             recon_resid=rep["resid"], recon_lo_off=sv["ctr"],
             recon_df_hz=sv["df_hat"],
             recon_phi=phi.astype(np.complex64))
    print(f"\n  Kaydedildi: {out_path}   [recon=2, KANALSIZ, kimliksiz]")
    if not sv["per_ok"]:
        print(f"  [UYARI] tekrar periyodu dogrulanamadi, 20 ms yazildi. "
              f"Kontrol: --keycheck {os.path.basename(out_path)}")
    try:
        key_determinism(np.load(out_path))
    except Exception as _e:
        print(f"  [UYARI] determinizm profili cikarilamadi ({_e})")
    if os.path.basename(out_path) != LEARN_FILE:
        print(f"\n  ESKISIYLE KARSILASTIR (donanim gerekmez):")
        print(f"    python3 {os.path.basename(__file__)} --keydiff "
              f"{LEARN_FILE} {os.path.basename(out_path)}")
    print("=" * 70)
    return out_path


def key_determinism(d, quiet=False):
    """Anahtarin HANGI FREKANSLARININ sabit oldugunu olc.

    Iki spektrum karsilastirilir:
      KOHERENT   |ortalama(x_n)|^2  — anahtarin kendisi. Tekrar ETMEYEN icerik
                                      ortalamada sifira gider.
      INKOHERENT ortalama(|X_n|^2)  — tasiyicinin ham gucu, trafik dahil.
    Oran = determinizm. Yuksek -> o bolge her periyot AYNI geliyor.
    Dusuk -> orada guc var ama her periyot BASKA (PDSCH kullanici trafigi).

    Sahada olculdu: 3480-3500 +2..+5 dB (SSB/CORESET0/SIB1), 3500-3580
    -31..-49 dB. Yani 98 MHz'lik tasiyicinin sadece ~20 MHz'i deterministik.
    Doner: (deterministik bant [Hz], dilim listesi)."""
    FS_k = float(d["fs"])
    CF_k = float(d["center_freq"])
    key, mask = d["key"], d["mask"]
    segs = _segments(mask, LEARN_MIN_SEG)
    if not segs or "wb_psd" not in d.files:
        return 0.0, []
    kbl = band_limit_sig(key)
    e = [float(np.sum(np.abs(kbl[a:b]) ** 2)) for a, b in segs]
    a, b = segs[int(np.argmax(e))]
    nmax = int(LEARN_KEY_MAX_US * 1e-6 * FS_k)
    if b - a > nmax:
        pw = np.abs(kbl[a:b]) ** 2
        cs = np.concatenate([[0.0], np.cumsum(pw)])
        a = a + int(np.argmax(cs[nmax:] - cs[:-nmax]))
        b = a + nmax
    ref = kbl[a:b]
    NF = 1 << int(np.ceil(np.log2(max(len(ref), 1024))))
    Sc = np.abs(np.fft.fftshift(np.fft.fft(ref, NF))) ** 2
    fc = (np.arange(NF) - NF // 2) * (FS_k / NF)
    NW = int(d["wb_nfft"])
    Pw = np.fft.fftshift(np.asarray(d["wb_psd"], float))
    fw = (np.arange(NW) - NW // 2) * (FS_k / NW)
    Sci = np.interp(fw, fc, Sc)
    inb = (fw >= band_limit_hz()[0]) & (fw <= band_limit_hz()[1])
    if inb.sum() < 16:
        return 0.0, []
    Sci = Sci / (np.mean(Sci[inb]) + 1e-30)
    Pw = Pw / (np.mean(Pw[inb]) + 1e-30)

    step = 5e6
    rows, det_bw = [], 0.0
    lo0, hi0 = band_limit_hz()
    f = lo0
    while f < hi0 - 1.0:
        s = inb & (fw >= f) & (fw < f + step)
        if s.sum() >= 8:
            pc = 10 * np.log10(np.mean(Pw[s]) + 1e-30)
            kc = 10 * np.log10(np.mean(Sci[s]) + 1e-30)
            rows.append((f, kc - pc, pc, kc))
            if kc - pc > DET_MIN_DB:
                det_bw += min(step, hi0 - f)
        f += step
    if not quiet and rows:
        print(f"\n  ANAHTARIN DETERMINIZM PROFILI  "
              f"(hangi frekanslar HER PERIYOT AYNI geliyor)")
        print(f"  {'MHz':>17} {'tasiyici':>9} {'koherent':>9} {'DETERMINIZM':>12}")
        for f, dd, pc, kc in rows:
            bar = "#" * max(0, min(28, int((dd + 30) / 2)))
            tag = "  SABIT" if dd > DET_MIN_DB else ""
            print(f"  {(CF_k+f)/1e6:8.0f}..{(CF_k+f+step)/1e6:<7.0f} "
                  f"{pc:>9.1f} {kc:>9.1f} {dd:>+12.1f}  {bar}{tag}")
        print(f"\n  SABIT (deterministik) bant : {det_bw/1e6:.0f} MHz  -> "
              f"menzil cozunurlugu ~{C_AIR/(2*max(det_bw,1e3)):.1f} m")
        print(f"  Tasiyicinin tamami         : "
              f"{(hi0-lo0)/1e6:.0f} MHz, ama gerisi PDSCH trafigi — her periyot")
        print(f"  degisir, koherent ortalamada yok olur. Referansa KATILMAZ.")
    return det_bw, rows


# ===================================================================
#  ANAHTAR KARSILASTIRMA — --keydiff (donanim gerekmez)
# ===================================================================

def _kd_get(d, name, default=None):
    """Anahtar dosyasindan alan oku (eski surumde alan olmayabilir)."""
    if name not in d.files:
        return default
    v = np.asarray(d[name])
    return v.item() if v.ndim == 0 else v


def _kd_row(label, va, vb, fmt="{}", unit="", tol=None):
    """Iki degeri yan yana bas; farkliysa isaretle. Doner: ayni mi."""
    sa = "-" if va is None else fmt.format(va)
    sb = "-" if vb is None else fmt.format(vb)
    if va is None or vb is None:
        same = (va is None and vb is None)
    elif tol is not None:
        same = abs(float(va) - float(vb)) <= tol
    else:
        same = (va == vb)
    print(f"  {label:<24} {sa:>17} {sb:>17}  {unit:<7}"
          + ("" if same else "<-- FARKLI"))
    return same


def key_ref_seg(d, fs=None):
    """Anahtar dosyasindan korelasyon REFERANSINI cikar — SESSIZ.

    load_key ile AYNI kural (oyle olmali: karsilastirdigimiz sey, olcumde
    gercekten kullanilan dalga formu olmali): maskeden cikan kumelerden kanal
    ICI enerjice en guclusu, LEARN_KEY_MAX_US'e kirpilmis.
    Doner (ref, a, b) — a/b PPS'e gore ornek indisleri."""
    fs = float(_kd_get(d, "fs", FS)) if fs is None else fs
    segs = _segments(np.asarray(d["mask"]), LEARN_MIN_SEG)
    if not segs:
        return None, 0, 0
    kbl = band_limit_sig(np.asarray(d["key"]))
    e = [float(np.sum(np.abs(kbl[a:b]) ** 2)) for a, b in segs]
    a, b = segs[int(np.argmax(e))]
    nmax = int(LEARN_KEY_MAX_US * 1e-6 * fs)
    if b - a > nmax:
        pw = np.abs(kbl[a:b]) ** 2
        cs = np.concatenate([[0.0], np.cumsum(pw)])
        a = a + int(np.argmax(cs[nmax:] - cs[:-nmax]))
        b = a + nmax
    return np.asarray(kbl[a:b], np.complex128), int(a), int(b)


def _kd_slices(f_abs, lo, hi, step=KEYDIFF_SLICE_MHZ * 1e6):
    """[lo,hi] bandini step'lik dilimlere bol; her dilim icin bool maske uret."""
    out = []
    f = lo
    while f < hi - 1.0:
        s = (f_abs >= f) & (f_abs < min(f + step, hi))
        if s.sum() >= 8:
            out.append((f, min(f + step, hi), s))
        f += step
    return out


def _kd_psd_compare(da, db, cfa, cfb, fsa):
    """Iki anahtarin GENIS BANT (inkoherent) guc profilini mutlak frekansta
    karsilastir. Anahtar dalga formundan BAGIMSIZDIR: PCI degisse, hatta hucre
    degisse bile calisir — "ayni bandi mi dinliyoruz, tasiyici ayni yerde mi"
    sorusunu bu bolum cevaplar."""
    Pa, Pb = _kd_get(da, "wb_psd"), _kd_get(db, "wb_psd")
    NA, NB = _kd_get(da, "wb_nfft"), _kd_get(db, "wb_nfft")
    if Pa is None or Pb is None or not NA or not NB:
        print("  (wb_psd alani yok — eski surum anahtar, atlaniyor)")
        return
    fa = cfa + (np.arange(NA) - NA // 2) * (fsa / NA)
    fb = cfb + (np.arange(NB) - NB // 2) * (fsa / NB)
    Sa = np.fft.fftshift(np.asarray(Pa, float))
    Sb = np.fft.fftshift(np.asarray(Pb, float))
    lo = max(fa[0], fb[0])
    hi = min(fa[-1], fb[-1])
    if hi - lo < 1e6:
        print(f"  [HATA] iki yakalamanin bantlari ORTUSMUYOR "
              f"({fa[0]/1e6:.0f}..{fa[-1]/1e6:.0f} ve "
              f"{fb[0]/1e6:.0f}..{fb[-1]/1e6:.0f} MHz).")
        print(f"         Merkez frekans degismis: bu iki anahtar ayni sinyalin "
              f"iki olcumu DEGIL.")
        return
    fg = np.arange(lo, hi, 100e3)
    Ga = np.interp(fg, fa, Sa)
    Gb = np.interp(fg, fb, Sb)
    # Ortak bandin ORTALAMASINA normalize: mutlak seviye RX kazancina ve
    # yakalama sayisina bagli, ilgilendigimiz sey SEKIL farki.
    Ga = Ga / (np.mean(Ga) + 1e-30)
    Gb = Gb / (np.mean(Gb) + 1e-30)
    print(f"  Ortak bant: {lo/1e6:.2f} .. {hi/1e6:.2f} MHz "
          f"(sekil farki; her ikisi de kendi ortalamasina normalize)")
    print(f"  {'MHz':>17} {'A[dB]':>8} {'B[dB]':>8} {'B-A':>8}")
    worst = 0.0
    for f0, f1, s in _kd_slices(fg, lo, hi):
        da_ = 10 * np.log10(np.mean(Ga[s]) + 1e-30)
        db_ = 10 * np.log10(np.mean(Gb[s]) + 1e-30)
        dd = db_ - da_
        worst = max(worst, abs(dd))
        bar = "#" * max(0, min(24, int(abs(dd) * 4)))
        print(f"  {f0/1e6:8.0f}..{f1/1e6:<7.0f} {da_:>8.1f} {db_:>8.1f} "
              f"{dd:>+8.1f}  {bar}")
    print(f"\n  En buyuk dilim farki: {worst:.1f} dB", end="")
    if worst < 2.0:
        print("  -> tasiyici profili AYNI (ayni hucre/ayni yuk dagilimi).")
    elif worst < 6.0:
        print("  -> profil benzer; fark trafik yuku olabilir.")
    else:
        print("  -> profil DEGISMIS. Farkli hucre, farkli tune ya da")
        print("     baz istasyonunun bant kullanimi degismis olabilir.")


def _kd_peaks(h, fs, min_sep=1, n_max=KEYDIFF_CIR_PEAKS,
              floor_db=KEYDIFF_CIR_FLOOR_DB):
    """|h| icindeki yerel tepeleri (yollari) bul. Doner [(gecikme_s, dB), ...].

    min_sep: iki tepe arasinda aranan asgari ayrim [ornek]. BUNSUZ OLMAZ —
    bant sinirli bir CIR'in tepesi bir sinc'tir ve sinc'in yan loblari yerel
    maksimumdur. Ayrim vermezsek tek yollu (degismemis) bir kanalda bile
    ilk yan lob "ikinci yol" diye raporlanir. Dogru esik cozunurluk hucresi
    (1/B): ondan yakin iki tepe zaten AYIRT EDILEMEZ."""
    m = np.abs(h)
    n = len(m)
    pk = float(m.max()) + 1e-30
    idx = [i for i in range(n)
           if m[i] >= m[(i-1) % n] and m[i] > m[(i+1) % n]
           and 20 * np.log10(m[i] / pk) > floor_db]
    idx.sort(key=lambda i: -m[i])
    sep = max(1, int(round(min_sep)))
    keep = []
    for i in idx:
        if all(min(abs(i - j), n - abs(i - j)) >= sep for j in keep):
            keep.append(i)
        if len(keep) >= n_max:
            break
    out = []
    for i in keep:
        # dairesel eksende negatif gecikme n'nin ust yarisindadir
        k = i - n if i > n // 2 else i
        out.append((k / fs, 20 * np.log10(m[i] / pk)))
    return sorted(out, key=lambda t: -t[1])


def keydiff(path_a, path_b):
    """IKI ANAHTARI KARSILASTIR — donanim GEREKMEZ, sadece iki .npz.

    NEDEN: bir anahtar iki sey tasir — baz istasyonunun YAYDIGI dalga formu ve
    onun bize gelirken gectigi KANAL (cok yolluluk + alici zinciri). Ayni hucre
    ayni frekanstan iki kez ogrenilirse yayilan kisim AYNIDIR; geriye kalan
    fark KANALIN kendisidir. Bu mod once "gercekten ayni sinyal mi" sorusunu
    cevaplar (RF ayari, hucre kimligi, bant), sonra kalan farki kanal olarak
    olcer (gecikme, frekansa gore kazanc/faz, CIR).

    ONEMLI — MUTLAK FAZ ANLAMSIZDIR: learn_key her kosuda anahtari O KOSUNUN
    ilk yakalamasina gore hizalar (S'nin fazi), yani anahtarin toplam fazi
    kosudan kosuya rastgeledir. Bu yuzden asagida faz FARKI hep bulk gecikme
    cikarildiktan SONRA, frekansa gore DEGISIMI olarak yorumlanir; tek bir
    sabit faz farki bir sey ifade etmez. (Ayni sebeple X410'da kanallar arasi
    faz her restart'ta sifirlanir — bkz. wcal.)"""
    import time
    for p in (path_a, path_b):
        if not os.path.exists(p):
            print(f"[HATA] anahtar dosyasi yok: {p}"); sys.exit(1)
    da, db = np.load(path_a), np.load(path_b)
    na, nb = os.path.basename(path_a), os.path.basename(path_b)
    print("=" * 78)
    print(f" ANAHTAR KARSILASTIRMASI")
    print("=" * 78)
    print(f"  A = {path_a}")
    print(f"  B = {path_b}")

    # ---- 1) KAYIT BILGISI -------------------------------------------------
    print(f"\n  1) KAYIT")
    print(f"  {'':24} {na[:17]:>17} {nb[:17]:>17}")
    ta = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(path_a)))
    tb = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(path_b)))
    _kd_row("ogrenilme zamani", ta, tb)
    _kd_row("yakalama sayisi", _kd_get(da, "n_cap"), _kd_get(db, "n_cap"), "{:d}")
    _kd_row("pencere", _kd_get(da, "win_ms"), _kd_get(db, "win_ms"), "{:.1f}", "ms")

    # ---- 2) RF AYARI ------------------------------------------------------
    # Kullanicinin sordugu ilk sey bu: arada merkez frekansi/kazanci
    # degistirdiysek iki anahtar ayni seyin iki olcumu DEGILDIR.
    print(f"\n  2) RF AYARI  (bunlar tutmuyorsa geri kalan her sey suphelidir)")
    fsa, fsb = float(_kd_get(da, "fs", 0)), float(_kd_get(db, "fs", 0))
    cfa, cfb = float(_kd_get(da, "center_freq", 0)), float(_kd_get(db, "center_freq", 0))
    ok_fs = _kd_row("ornekleme (Fs)", fsa / 1e6, fsb / 1e6, "{:.3f}", "MHz", tol=1.0)
    ok_cf = _kd_row("MERKEZ FREKANS", cfa / 1e6, cfb / 1e6, "{:.3f}", "MHz", tol=1e-3)
    ok_g = _kd_row("RX kazanci", _kd_get(da, "rx_gain"), _kd_get(db, "rx_gain"),
                   "{:.0f}", "dB")
    if not ok_cf:
        print(f"\n     [DIKKAT] merkez frekans {abs(cfb-cfa)/1e6:+.3f} MHz farkli.")
        print(f"     Dalga formu karsilastirmasi B'yi A'nin taban bandina TASIYARAK")
        print(f"     yapilir; gecerli olmasi icin iki bandin ORTUSMESI sarttir.")
    if not ok_g:
        print(f"\n     [BILGI] RX kazanci farkli -> genlik farki BEKLENIR, kanal")
        print(f"     degismis demek DEGILDIR. Asagidaki kazanc farkini bu kadar")
        print(f"     ({float(_kd_get(db,'rx_gain',0))-float(_kd_get(da,'rx_gain',0)):+.0f} dB) kaydirarak oku.")
    if not ok_fs:
        print(f"\n  [HATA] iki anahtarin ornekleme hizi farkli — karsilastirilamaz.")
        sys.exit(1)
    if abs(fsa - FS) > 1.0:
        print(f"\n  [UYARI] anahtarlarin Fs'i ({fsa/1e6:.3f}) simdiki koddan "
              f"({FS/1e6:.3f}) farkli; bant kisitlama simdiki ayarla yapiliyor.")

    # ---- 3) HUCRE KIMLIGI -------------------------------------------------
    print(f"\n  3) HUCRE KIMLIGI  (PSS/SSS'ten cozuldu)")
    pa, pb = _kd_get(da, "pci", -1), _kd_get(db, "pci", -1)
    ok_pci = _kd_row("PCI", pa, pb, "{:d}")
    _kd_row("N_ID_1", _kd_get(da, "n_id1", -1), _kd_get(db, "n_id1", -1), "{:d}")
    _kd_row("N_ID_2", _kd_get(da, "n_id2", -1), _kd_get(db, "n_id2", -1), "{:d}")
    _kd_row("SSB frekansi", float(_kd_get(da, "f_ssb", 0)) / 1e6,
            float(_kd_get(db, "f_ssb", 0)) / 1e6, "{:.3f}", "MHz", tol=1e-3)
    _kd_row("SSB tekrari", _kd_get(da, "ssb_period_ms", 0.0),
            _kd_get(db, "ssb_period_ms", 0.0), "{:.1f}", "ms", tol=0.01)
    ok_step = _kd_row("ANAHTAR PERIYODU", _kd_get(da, "key_period_ms", 0.0),
                      _kd_get(db, "key_period_ms", 0.0), "{:.1f}", "ms", tol=0.01)
    if not ok_pci and int(pa) >= 0 and int(pb) >= 0:
        print(f"\n     [DIKKAT] PCI farkli ({int(pa)} -> {int(pb)}): BASKA BIR")
        print(f"     HUCRE ogrenilmis. Aradaki fark kanal degil, bastan baska")
        print(f"     bir vericidir. Ayni anteni/frekansi dinledigine emin ol.")
    if not ok_step:
        print(f"\n     [DIKKAT] tekrar periyodu farkli -> --step degeri de degisir.")

    # ---- 4) ISGAL EDILEN BANT (MUTLAK) ------------------------------------
    print(f"\n  4) ISGAL EDILEN BANT  (mutlak frekans — menzil cozunurlugu bundan)")
    la = cfa + float(_kd_get(da, "wb_f_lo", 0.0))
    ha = cfa + float(_kd_get(da, "wb_f_hi", 0.0))
    lb = cfb + float(_kd_get(db, "wb_f_lo", 0.0))
    hb = cfb + float(_kd_get(db, "wb_f_hi", 0.0))
    _kd_row("bant alt kenari", la / 1e6, lb / 1e6, "{:.2f}", "MHz", tol=0.5)
    _kd_row("bant ust kenari", ha / 1e6, hb / 1e6, "{:.2f}", "MHz", tol=0.5)
    _kd_row("genislik", (ha - la) / 1e6, (hb - lb) / 1e6, "{:.2f}", "MHz", tol=0.5)

    # ---- 5) TASIYICI GUC PROFILI ------------------------------------------
    print(f"\n  5) TASIYICI GUC PROFILI  (inkoherent — anahtardan bagimsiz)")
    _kd_psd_compare(da, db, cfa, cfb, fsa)

    # ---- 6) ANAHTAR KUMESI (ZAMANLAMA) ------------------------------------
    print(f"\n  6) ANAHTAR KUMESI  (PPS'e gore)")
    ra, aa, ba_ = key_ref_seg(da, fsa)
    rb, ab, bb_ = key_ref_seg(db, fsa)
    if ra is None or rb is None:
        print("  [HATA] anahtarlardan birinde tutarli aralik yok."); sys.exit(1)
    ga, gb = np.asarray(da["gamma"]), np.asarray(db["gamma"])
    ma, mb = np.asarray(da["mask"]), np.asarray(db["mask"])
    _kd_row("kume basi (PPS+)", aa / fsa * 1e3, ab / fsa * 1e3, "{:.4f}", "ms",
            tol=1e-4)
    _kd_row("kume uzunlugu", (ba_ - aa) / fsa * 1e6, (bb_ - ab) / fsa * 1e6,
            "{:.1f}", "us", tol=0.5)
    _kd_row("tutarli kume sayisi", len(_segments(ma, LEARN_MIN_SEG)),
            len(_segments(mb, LEARN_MIN_SEG)), "{:d}")
    _kd_row("maskeli ornek orani", 100.0 * ma.mean(), 100.0 * mb.mean(),
            "{:.2f}", "%", tol=0.05)
    _kd_row("gamma (kume ici ort.)", float(ga[aa:ba_].mean()),
            float(gb[ab:bb_].mean()), "{:.3f}", "", tol=0.005)
    d_off_us = (ab - aa) / fsa * 1e6
    if abs(ab - aa) > 0:
        print(f"\n     Kume ofsetleri {d_off_us:+.1f} us farkli. Bu, baz "
              f"istasyonunun cerceve")
        print(f"     zamanlamasinin GPS PPS'e gore kaymasidir (sebeke bize "
              f"senkron degil);")
        print(f"     asagidaki ince gecikme bunun uzerine eklenir.")

    # ---- 7) DALGA FORMU: AYNI SINYAL MI? ----------------------------------
    print(f"\n  7) DALGA FORMU KARSILASTIRMASI")
    # B'yi A'nin taban bandina tasi. Faz rampasinin zaman orijini PPS olmali,
    # yoksa merkez frekans farkinda sabit bir faz hatasi kalir (genlige zarar
    # vermez ama CIR fazini kaydirir).
    if abs(cfb - cfa) > 1e-3:
        n_abs = ab + np.arange(len(rb), dtype=np.float64)
        rb = rb * np.exp(2j * np.pi * (cfb - cfa) * n_abs / fsa)
        print(f"  B, A'nin taban bandina tasindi ({(cfb-cfa)/1e6:+.3f} MHz).")
    L = max(len(ra), len(rb))
    nfft = 1 << int(np.ceil(np.log2(max(2 * L, KEYDIFF_NFFT_MIN))))
    Xa = np.fft.fft(ra, nfft)
    Xb = np.fft.fft(rb, nfft)
    # c[m] = SUM_p rb[p+m] * conj(ra[p])  ->  tepe m0'da ise B, kendi cercevesi
    # icinde A'ya gore m0 ornek GECIKMISTIR.
    c = np.fft.ifft(Xb * np.conj(Xa))
    i0 = int(np.argmax(np.abs(c)))
    nrm = (np.linalg.norm(ra) * np.linalg.norm(rb)) + 1e-30
    rho = float(np.abs(c[i0]) / nrm)
    # yarim ornek cozunurluk: tepe cevresinde parabol
    im1, ip1 = (i0 - 1) % nfft, (i0 + 1) % nfft
    y0, y1, y2 = (abs(c[im1]), abs(c[i0]), abs(c[ip1]))
    den = (y0 - 2 * y1 + y2)
    frac = 0.5 * (y0 - y2) / den if abs(den) > 1e-30 else 0.0
    m0 = (i0 - nfft if i0 > nfft // 2 else i0) + float(np.clip(frac, -1, 1))
    tot_smp = (ab - aa) + m0
    print(f"  Koherens |rho|        : {rho:.4f}   "
          f"({20*np.log10(max(rho,1e-9)):+.1f} dB)")
    print(f"  Ince gecikme (kume ici): {m0:+.2f} ornek = {m0/fsa*1e9:+.1f} ns")
    print(f"  TOPLAM gecikme (PPS'e) : {tot_smp:+.1f} ornek = "
          f"{tot_smp/fsa*1e6:+.3f} us = {tot_smp/fsa*C_AIR:+.1f} m yol farki")
    e_a = float(np.sum(np.abs(ra) ** 2))
    e_b = float(np.sum(np.abs(rb) ** 2))
    print(f"  Genlik farki (B/A)     : {10*np.log10(e_b/(e_a+1e-30)):+.2f} dB"
          + ("" if ok_g else "   (RX kazanci da farkli!)"))
    if rho >= KEYDIFF_RHO_SAME:
        print(f"  -> AYNI dalga formu. Kalan fark KANAL + gurultudur.")
    elif rho >= KEYDIFF_RHO_WEAK:
        print(f"  -> KISMEN ayni. Ortak bir cekirdek var ama icerigin bir kismi")
        print(f"     degismis (ornegin PBCH veri bitleri SFN ile degisir) ya da")
        print(f"     anahtarlardan biri gurultulu (n_cap dusuk / gamma dusuk).")
    else:
        print(f"  -> ILISKISIZ. Bunlar ayni sinyalin iki olcumu degil.")
        print(f"     Once 2) ve 3) bolumlerine bak: frekans/hucre tutuyor mu?")

    # ---- 8) FREKANSA GORE KANAL -------------------------------------------
    # Bulk gecikmeyi CIKAR: kalan faz artik "frekansa gore ne kadar degisiyor"
    # sorusunun cevabidir. Bu, kalibrasyondaki per-frekans equalizer mantiginin
    # ta kendisidir — tek bir katsayi bu tabloyu ozetleyemez.
    print(f"\n  8) FREKANSA GORE KANAL  (bulk gecikme cikarildi)")
    kk = np.arange(nfft)
    Xb_al = Xb * np.exp(2j * np.pi * kk * m0 / nfft)
    f_bb = np.fft.fftfreq(nfft, 1.0 / fsa)
    f_abs = cfa + f_bb
    Pa_ = np.abs(Xa) ** 2
    lo_bl, hi_bl = band_limit_hz()
    inb = (f_bb >= lo_bl) & (f_bb <= hi_bl)
    if inb.sum() < 16:
        inb = np.ones(nfft, bool)
    thr = Pa_[inb].max() * (10 ** (KEYDIFF_BIN_FLOOR_DB / 10.0))
    sel = inb & (Pa_ > thr)
    if sel.sum() < 16:
        print("  [UYARI] anahtarin bandi cok dar/zayif, frekans profili atlaniyor.")
    else:
        f_sel = f_abs[sel]
        b_lo, b_hi = float(f_sel.min()), float(f_sel.max())
        print(f"  Anahtarin gercek bandi: {b_lo/1e6:.2f} .. {b_hi/1e6:.2f} MHz "
              f"({(b_hi-b_lo)/1e6:.2f} MHz, {KEYDIFF_BIN_FLOOR_DB:.0f} dB esigi)")
        print(f"  {'MHz':>17} {'koherens':>9} {'kazanc':>8} {'faz':>8}")
        Hc = Xb_al * np.conj(Xa)
        Pb_ = np.abs(Xb) ** 2
        phs = []
        for f0, f1, s in _kd_slices(f_abs, b_lo, b_hi):
            s = s & sel
            if s.sum() < 8:
                continue
            num = np.abs(np.sum(Hc[s]))
            den2 = np.sqrt(np.sum(Pa_[s]) * np.sum(Pb_[s])) + 1e-30
            coh = float(num / den2)
            gdb = 10 * np.log10((np.sum(Pb_[s]) / (np.sum(Pa_[s]) + 1e-30)) + 1e-30)
            ph = np.degrees(np.angle(np.sum(Hc[s])))
            phs.append(ph)
            bar = "#" * max(0, min(20, int(coh * 20)))
            print(f"  {f0/1e6:8.2f}..{f1/1e6:<7.2f} {coh:>9.3f} {gdb:>+8.2f} "
                  f"{ph:>+8.1f}  {bar}")
        if len(phs) >= 2:
            pu = np.degrees(np.unwrap(np.radians(np.asarray(phs))))
            print(f"\n  Faz yayilimi (dilimler arasi): {pu.max()-pu.min():.1f} derece")
            if pu.max() - pu.min() > 20.0:
                print(f"  -> Bant boyunca faz DUZ DEGIL: tek bir kompleks katsayi "
                      f"bu farki")
                print(f"     temsil edemez; per-frekans equalizer sart (zaten oyle "
                      f"yapiliyor).")

        # ---- 9) DIFERANSIYEL CIR ------------------------------------------
        # h = IFFT(Xb/Xa). A'yi "verici", B'yi "alici" gibi dusun: ciktinin
        # tepeleri, iki olcum ARASINDA degisen yollari verir.
        print(f"\n  9) DIFERANSIYEL KANAL YANITI (CIR)  —  B'nin A'ya gore yollari")
        lam = 0.05 * float(np.mean(Pa_[sel]))
        B_key = max(b_hi - b_lo, 1e3)
        # BANT PENCERESI (Hann): bantla kesilmis bir CIR'in tepesi sinc'tir ve
        # ilk yan lobu -13 dB'dedir — pencere olmadan bu yan lob "ikinci yol"
        # diye okunur. Hann yan lobu -31 dB'ye indirir; bedeli ana lobun 2 kat
        # genislemesi, yani cozunurlugun yarisidir (asagida oyle raporlanir).
        w = np.zeros(nfft)
        u = (f_abs[sel] - b_lo) / max(b_hi - b_lo, 1.0)
        w[sel] = 0.5 - 0.5 * np.cos(2 * np.pi * np.clip(u, 0.0, 1.0))
        H = np.zeros(nfft, complex)
        H[sel] = Hc[sel] / (Pa_[sel] + lam) * w[sel]
        h = np.fft.ifft(H)
        res_s = 2.0 / B_key                      # Hann -> ana lob 2/B
        print(f"  Cozunurluk (Hann pencereli) = {res_s*1e9:.1f} ns = "
              f"{res_s*C_AIR:.1f} m   (anahtarin bandi {B_key/1e6:.2f} MHz)")
        pks = _kd_peaks(h, fsa, min_sep=res_s * fsa)
        if not pks:
            print("  (tepe bulunamadi)")
        else:
            print(f"  {'gecikme[ns]':>12} {'yol[m]':>9} {'seviye[dB]':>11}")
            for t_s, lv in pks:
                print(f"  {t_s*1e9:>12.1f} {t_s*C_AIR:>9.2f} {lv:>+11.1f}")
            if len(pks) > 1:
                spread = max(abs(p[0]) for p in pks[1:]) * C_AIR
                print(f"\n  Ana yolun disinda {len(pks)-1} tepe var "
                      f"(en uzagi {spread:.1f} m).")
                print(f"  Bunlar iki olcum ARASINDA DEGISEN yollardir: ortamda "
                      f"kalici bir")
                print(f"  sacici gelmis/gitmis ya da hareket etmis demektir. "
                      f"Sabit sahnede")
                print(f"  tek tepe beklenir.")
            else:
                print(f"\n  Tek tepe: iki olcum arasinda kanal SEKIL olarak "
                      f"degismemis;")
                print(f"  fark sadece toplu gecikme/genliktir (saat kaymasi + "
                      f"seviye).")

    # ---- 10) DETERMINIZM PROFILI ------------------------------------------
    print(f"\n  10) DETERMINIZM PROFILI  (hangi frekanslar HER PERIYOT AYNI)")
    _, rows_a = key_determinism(da, quiet=True)
    _, rows_b = key_determinism(db, quiet=True)
    if rows_a and rows_b:
        print(f"  {'MHz':>17} {'A[dB]':>8} {'B[dB]':>8} {'B-A':>8}")
        map_b = {round((cfb + r[0]) / 1e6, 1): r for r in rows_b}
        for r in rows_a:
            fabs = (cfa + r[0]) / 1e6
            rb_ = map_b.get(round(fabs, 1))
            sb_ = f"{rb_[1]:>+8.1f}" if rb_ else f"{'-':>8}"
            dd = f"{rb_[1]-r[1]:>+8.1f}" if rb_ else f"{'-':>8}"
            tag = ""
            if rb_:
                if r[1] > DET_MIN_DB and rb_[1] > DET_MIN_DB:
                    tag = "  ikisinde de SABIT"
                elif r[1] > DET_MIN_DB:
                    tag = "  A'da sabit, B'de DEGIL"
                elif rb_[1] > DET_MIN_DB:
                    tag = "  B'de sabit, A'da DEGIL"
            print(f"  {fabs:8.0f}..{fabs+KEYDIFF_SLICE_MHZ:<7.0f} {r[1]:>+8.1f} "
                  f"{sb_} {dd}{tag}")
    else:
        print("  (profil cikarilamadi)")

    # ---- 11) HUKUM --------------------------------------------------------
    print(f"\n" + "=" * 78)
    print(f" HUKUM")
    print("=" * 78)
    same_rf = ok_fs and ok_cf
    if not same_rf:
        print("  * RF AYARI DEGISMIS. Iki anahtar ayni olcum kosulundan gelmiyor;")
        print("    once bunu duzelt, sonra karsilastir.")
    if int(pa) >= 0 and int(pb) >= 0 and not ok_pci:
        print("  * BASKA HUCRE (PCI farkli). Fark kanal degil, baska bir verici.")
    if rho >= KEYDIFF_RHO_SAME and same_rf and ok_pci:
        print(f"  * AYNI hucre, AYNI frekans, AYNI dalga formu (rho={rho:.3f}).")
        print(f"    Iki anahtar birbirinin yerine kullanilabilir. Aradaki fark")
        print(f"    ({tot_smp/fsa*C_AIR:+.1f} m gecikme, "
              f"{10*np.log10(e_b/(e_a+1e-30)):+.1f} dB seviye) KANALIN kendisidir;")
        print(f"    8) ve 9) bolumleri bu farkin frekansa ve gecikmeye dagilimini")
        print(f"    verir. OLCUMLERDE HANGISINI KULLANMALI: n_cap'i buyuk ve")
        print(f"    gamma'si yuksek olan (yukarida 6. bolum) daha temizdir.")
    elif rho < KEYDIFF_RHO_WEAK:
        print(f"  * Dalga formlari ILISKISIZ (rho={rho:.3f}). Ayni sinyalin iki")
        print(f"    olcumu degiller — eskisini yenisiyle DEGISTIR, karistirma.")
    else:
        print(f"  * Kismi benzerlik (rho={rho:.3f}). Karar icin 5) ve 10)")
        print(f"    bolumlerine bak: bant profili ve deterministik bant tutuyorsa")
        print(f"    fark gurultudur; tutmuyorsa sebeke tarafinda bir sey degismis.")
    print("=" * 78)
    return rho


def build_test_burst(n_rb=N_RB_CELL - 1, n_sym=12, seed=7):
    """SELF-TEST icin genis bant OFDM darbesi — SAHADA KULLANILMAZ.

    Tam yuklu bir PDSCH'in kaba taklidi: butun RB'ler Gold diziden QPSK ile
    doldurulur. Amaci goruntuleme zincirini (korelasyon, equalizer, MTI,
    backprojection) 98 MHz bantla sinamak; SSB'nin 7.2 MHz'i buna yetmez."""
    n_sc = n_rb * NSC_PER_RB
    k0 = N_FFT // 2 - n_sc // 2
    offs = symbol_offsets(0)[:n_sym]
    out = np.zeros(offs[-1][1] + N_FFT, complex)
    for i, (cp0, u0, cp) in enumerate(offs):
        d = gold_qpsk((seed * 131 + i * 7919) % (1 << 31), n_sc)
        X = np.zeros(N_FFT, complex)
        X[k0:k0 + n_sc] = d
        x = np.fft.ifft(np.fft.ifftshift(X)) * N_FFT
        sym = np.concatenate([x[-cp:], x])
        if PHASE_COMP:
            sym = sym * np.exp(-1j * 2 * np.pi * CENTER_FREQ * (u0 / FS))
        out[cp0:cp0 + cp + N_FFT] = sym
    return out.astype(np.complex64)



# ===================================================================
#  KORELASYON — occasion yerlesimi, uyumlu filtre, equalizer
# ===================================================================

def _build_refs(key_path):
    """Referans dalga formu + occasion adimi. Doner (refs, step_s, t_ref).

    TICARI HUCREDE ANAHTAR ZORUNLUDUR: sentetik bir sablon (PRS gibi) yoktur,
    cunku sebeke oyle bir sinyal yayinlamaz. Referans --learn ile ogrenilir."""
    if not key_path:
        print("[HATA] --key ZORUNLU: ticari hucrede deterministik referans "
              "ogrenilir, uretilmez.")
        print("       Once:  python3 %s --learn --step 20"
              % os.path.basename(__file__))
        sys.exit(1)
    ref0, t_ref, _ = load_key(key_path)
    step_s = (KEY_STEP_MS * 1e-3) if KEY_STEP_MS else SLOTS_PER_FRAME * SLOT_DUR_S
    print(f"  anahtar tekrar periyodu: {step_s*1e3:.3f} ms"
          + (f"  ({KEY_STEP_SRC})" if KEY_STEP_MS else "  (varsayilan: NR frame)"))
    return [ref0.astype(np.complex64)], step_s, t_ref

def _occasion_layout(N, refs, step_s, off0=0):
    """Occasion baslangiclari + sinif indisleri. Doner (occ, cls, n_cls, L_seg, nlag).

    off0: ilk occasion'in yakalama ICINDEKI ornek konumu. Normalde 0'dir cunku
    pencere anahtarin t_ref'inde acilir. Ama TEK OTURUM zincirinde (kablolu
    kalibrasyon -> ogrenme -> olcum) pencere PPS+0'da acilmistir ve bir daha
    ACILAMAZ (acilirsa kanallar arasi faz, yani kalibrasyon gider). O yuzden
    kayma yazilimda verilir."""
    n_cls = len(refs)
    L_ref = len(refs[0])
    # Occasion dilimi normalde bir NR slotu (0.5 ms). Referans buna gore uzunsa
    # dilimi buyut (occasion'lar cakismasin diye adimin %90'ini asmadan) —
    # boylece uzun anahtar sert hata yerine calisir, sadece menzil penceresi
    # (nlag) kisalir.
    L_seg = N_SLOT
    if L_ref > 0.6 * L_seg:
        L_seg = int(min(0.9 * step_s * FS, max(N_SLOT, 2 * L_ref)))
        print(f"  [BILGI] referans uzun ({L_ref/FS*1e6:.0f} us) -> occasion dilimi "
              f"{L_seg/FS*1e6:.0f} us'a buyutuldu")
    off0 = max(0, int(off0))
    occ = [off0 + int(round(k * step_s * FS))
           for k in range(int(LOC_WIN_MS * 1e-3 / step_s) + 2)]
    occ = [o for o in occ if o + L_seg <= N]
    if not occ:
        print(f"[HATA] pencereye ({N/FS*1e3:.1f} ms) tek occasion sigmadi "
              f"(kayma {off0/FS*1e3:.1f} ms, dilim {L_seg/FS*1e3:.2f} ms).")
        print(f"       --win ile pencereyi buyut.")
        sys.exit(1)
    n_occ = (len(occ) // n_cls) * n_cls
    occ = occ[:n_occ]
    cls = [k % n_cls for k in range(len(occ))]
    nlag = L_seg - L_ref + 1
    if nlag < 2:
        print(f"[HATA] referans ({L_ref} ornek) occasion diliminden ({L_seg}) uzun.")
        print(f"       --keymax ile anahtari kisalt (su an "
              f"{LEARN_KEY_MAX_US:.0f} us).")
        sys.exit(1)
    return occ, cls, n_cls, L_seg, nlag

@functools.lru_cache(maxsize=8)
def _ref_spec(key, nfft):
    """Referansin conj(FFT)'i — her occasion'da yeniden hesaplanmasin.

    key: ref dizisinin bytes'i (lru_cache hashlenebilir olmasini istiyor).
    Occasion basina 1 FFT tasarrufu; 5 occasion x 2 sinif = kucuk ama bedava."""
    ref = np.frombuffer(key, dtype=np.complex64)
    return np.conj(gpu_fft(ref, nfft))


def _corr_batch(segs, ref, nfft, nlag, eq_inv=None):
    """BIRDEN COK occasion'i TEK yiginda korele et.

    segs: (M, N_RX, L_seg). Doner (M, N_RX, nlag).
    M ayri (4, nfft) FFT yerine tek (M*4, nfft) FFT: cagri masrafi ve GPU
    gidis-donusu M kat azalir. Sonuc birebir ayni (FFT satir bagimsizdir)."""
    M, nr, _ = segs.shape
    S = gpu_fft(segs.reshape(M * nr, -1), nfft, axis=1).reshape(M, nr, nfft)
    if eq_inv is not None:
        S = S * eq_inv[None, :, :]
    R = _ref_spec(np.ascontiguousarray(ref, np.complex64).tobytes(), nfft)
    C = gpu_ifft(S * R[None, None, :], axis=2)[:, :, :nlag]
    # DIKKAT — complex64'e KIRPMA YOK. Cagiran taraf LOO artigini
    #   Cres = C_j - (Csum - C_j)/(M-1)
    # olarak hesapliyor; artik KUCUK, terimler BUYUK. complex64'te bu
    # felaketli sadelesme demek (olculdu: buyuk/kucuk orani 1e5 iken
    # goreli hata 1e8'e ciktigi sentetik ornek). v1 cikarmayi ZAMAN
    # alaninda complex128 ile yapiyordu; ayni hassasiyeti korumak icin
    # burada da complex128 dondurulur, kirpma en sonda yapilir.
    return C.astype(np.complex128)


def _corr_all(segs_k, ref, nfft, nlag, eq_inv=None):
    """segs_k: (N_RX, L_seg) kompleks — ILK EKSEN KANAL. ref korelasyonu.

    eq_inv: (N_RX, nfft) frekans basina equalizer TERSI. Verilirse kanal
    spektrumlari korelasyondan ONCE esitlenir; boylece dort zincirin genlik/faz
    farki her bin icin ayri ayri giderilmis olur (tek katsayi degil).

    Doner: (N_RX, nlag) kompleks korelasyon (uyumlu filtre)."""
    S = gpu_fft(segs_k, nfft, axis=1)
    if eq_inv is not None:
        if S.shape[0] != eq_inv.shape[0] or S.shape[1] != eq_inv.shape[1]:
            raise ValueError(f"eq_inv sekli {eq_inv.shape} spektrum {S.shape} "
                             f"ile uyusmuyor")
        S = S * eq_inv
    R = np.conj(gpu_fft(ref, nfft))
    return gpu_ifft(S * R[None, :], axis=1)[:, :nlag].astype(np.complex64)

def eq_from_taps(taps, nfft):
    """Kisa FIR equalizer taplarini HERHANGI bir FFT izgarasinda degerlendir.

    Equalizer'i tap olarak saklamanin sebebi: LOS'tan tam bantta (WB blogu,
    nfft=131072) kestiriliyor ama korelasyon BASKA bir izgarada (occasion
    nfft'i) yapiliyor. Frekans dizisini yeniden orneklemek yerine taplari
    dogrudan hedef izgarada degerlendirmek TAM dogru sonucu verir.

    taps: (N_RX, 2*ng+1) — wb_los_eq ciktisi (merkez indis ng, gecikme -ng..+ng).
    Doner (EQ, inv); S_k * inv_k = esitlenmis spektrum."""
    taps = np.asarray(taps)
    ng = (taps.shape[1] - 1) // 2
    t  = np.arange(-ng, ng + 1)
    E  = np.exp(-2j * np.pi * np.outer(np.arange(nfft, dtype=np.float64), t) / nfft)
    EQ = (E @ taps.T).T.astype(np.complex64)
    a   = np.abs(EQ)
    med = np.median(a, axis=1)[:, None] + 1e-30
    eps = (EQ_REG * med).astype(np.float32)
    inv = (np.conj(EQ) / (a ** 2 + eps ** 2)).astype(np.complex64)
    return EQ, inv

def seg_coherence(segs):
    """Occasion'lar birbirine benziyor mu? 1 = ayni, 1/K = tamamen ilintisiz.

    (4rx_1tx_kdyf_80mhz_v1.py'den port.) Cikarmanin calisabilmesinin ON
    KOSULU budur: ortalama, tek bir occasion'i ancak occasion'lar benzerse
    temsil eder. Once hepsi ilkinin fazina hizalanir, yoksa kucuk bir frekans
    kaymasi bile olcutu yaniltir."""
    A = np.stack(segs).astype(np.complex128)
    for i in range(1, len(A)):
        A[i] *= np.exp(-1j * np.angle(complex(np.vdot(A[0], A[i]))))
    num = float(np.sum(np.abs(A.mean(axis=0)) ** 2))
    den = float(np.sum(np.mean(np.abs(A) ** 2, axis=0)))
    return num / (den + 1e-30)

def _dbias(coh, M_coh, M_tpl):
    """Genlik katsayisinin yanlilik duzeltmesi (eski dosyadan port).

    Sablon T'nin KENDI gurultusu paydaya girer:
        a_olculen = <T,s>/<T,T> = a_gercek / (1 + r/M)
    r = gurultu/sinyal, M = ortalanan occasion sayisi. Segment SNR'i birkac dB
    oldugunda a belirgin kuculur, cikarma eksik kalir ve bastirma tavan yapar.
    r uyum olcutunden cikar: gamma = (1 + r/M_coh)/(1 + r)."""
    if 1.0 / M_coh + 1e-3 < coh < 1.0:
        r = (1.0 - coh) / (coh - 1.0 / M_coh)
        return min(1.0 + r / max(M_tpl, 1), 4.0)
    return 1.0

def align_to_template(seg, T, L_est, tt, dbias=1.0):
    """Bir occasion'i sablona oturt: ARTIK FREKANS KAYMASI + kompleks kazanc.

    (4rx_1tx_kdyf_80mhz_v1.py:_radar_step'ten port — arka plan cikarmanin
    calismasi bu hizalamaya bagli.)

    1) df: baz istasyonunun tasiyicisi bizim GPSDO'muza KILITLI DEGILDIR. Makro
       hucre ~±0.05 ppm -> 3.51 GHz'de ~176 Hz. 800 us'lik bir segmentte bu
       ~50 derecelik bir FAZ RAMPASI demektir. Sabit faz duzeltmesi rampayi
       gideremez ve cikarma coker (428 us'de 11 derecelik rampa bile artigi
       -25 dB'de tutar). df, sablonla ic carpimi iki yariya bolup faz farkindan
       kestirilir ve rampa geri alinir.
    2/3) a = <T,s>/<T,T>: sabit faz ve genligi TEK en-kucuk-kareler izdusumuyle
       birlikte alir; s sablonun olcegine cekilir. dbias sablon gurultusunun
       yarattigi kuculmeyi telafi eder.

    KRITIK: df ve a SADECE kanal 0'dan kestirilip DORT kanala AYNEN uygulanir.
    Kanal basina ayri normalize edilirse kanallar arasi faz farki — yani ACI
    bilgisinin tamami — silinir.

    Doner (hizalanmis seg, df, a)."""
    t0 = T[0]
    h = max(1, L_est // 2)
    z1 = complex(np.vdot(t0[:h], seg[0, :h]))
    z2 = complex(np.vdot(t0[h:L_est], seg[0, h:L_est]))
    df = float(np.angle(z2 * np.conj(z1)) / (2 * np.pi * (h / FS)))
    seg = seg * np.exp(-2j * np.pi * df * tt)[None, :]
    a = complex(np.vdot(t0[:L_est], seg[0, :L_est])
                / (np.vdot(t0[:L_est], t0[:L_est]) + 1e-30)) * dbias
    if abs(a) > 1e-9:
        seg = seg / a
    return seg, df, a

def _subsample_peak(y):
    """|y| tepesinin alt-ornek konumu (parabolik interpolasyon). Doner float lag."""
    j = int(np.argmax(np.abs(y)))
    if j <= 0 or j >= len(y) - 1:
        return float(j)
    a, b, c = (abs(y[j - 1]), abs(y[j]), abs(y[j + 1]))
    den = (a - 2 * b + c)
    return float(j) + (0.5 * (a - c) / den if abs(den) > 1e-30 else 0.0)

def delay_shift(x, d):
    """x'i d ornek (kesirli olabilir) GECIKTIR. Frekans domeninde faz rampasi."""
    if abs(d) < 1e-6:
        return x
    x = np.atleast_2d(x)
    n = x.shape[-1]
    f = np.fft.fftfreq(n)
    return np.fft.ifft(np.fft.fft(x, axis=-1) *
                       np.exp(-2j * np.pi * f * d)[None, :], axis=-1)

def measure_channel_delays(buf, occ, cls, L_seg, bg_t, win=64):
    """Canli verinin sablona gore gecikmesini KANAL BASINA olc.

    NEDEN KANAL BASINA: k0,k1 Radio#0/DDC#0'da, k2,k3 Radio#1/DDC#1'de. IKI AYRI
    DDC blogu, iki bagimsiz desimasyon fazi. Her program calistirmasinda faz
    yeniden oturur ve iki radyo AYNI kaymayi almaz. Sahada goruldu: kanal 0'dan
    olculen kaymayi dorde birden uygulayinca k0/k1 duzeldi, k2/k3 duzelmedi —
    tam olarak radyo ayrimi.

    Olcum ZAMAN domeninde (ham segment x sablon capraz korelasyonu). Korelasyon
    profilinden olcmek YANLIS: profil yalniz negatif-olmayan lag'leri tasir ve
    LOS lag ~8'de oldugu icin sol etek kirpilir.

    Doner: d (N_RX,) — canli, sablona GORE gecikme [ornek, kesirli]."""
    buf = np.atleast_2d(buf)
    T = np.asarray(bg_t[cls[0]])
    m = 1 << int(np.ceil(np.log2(2 * L_seg)))
    c0 = m // 2
    mx = int(min(win, c0 - 2))
    d = np.zeros(N_RX)
    for k in range(N_RX):
        a0 = buf[k, occ[0]:occ[0] + L_seg].astype(np.complex128)
        t0 = T[k].astype(np.complex128)
        x = np.fft.fftshift(np.fft.ifft(np.fft.fft(a0, m) *
                                        np.conj(np.fft.fft(t0, m))))
        dk = _subsample_peak(x[c0 - mx:c0 + mx + 1]) - mx
        d[k] = 0.0 if abs(dk) > mx - 1 else dk
    return d

def _direct_ref(seg0, ref, nfft, nlag, bin_fix=None):
    """Occasion'in DOGRUDAN YOL (LOS) faz referansini bul.

    Kanal 0'i referansla korele et ve o binin KOMPLEKS degerini dondur. Fazi,
    bu occasion'in ortak faz referansidir. Occasion'i bu faza gore dondurmek:
      * kanallar arasi faz farkini (aci bilgisi) BOZMAZ (dort kanala ayni donme)
      * occasion'dan occasion'a CFO/faz jitterini giderir -> koherent ortalama
        ve arka plan cikarma temiz calisir.

    bin_fix verilirse tepe ARANMAZ, DOGRUDAN o bin okunur. v4'te varsayilan
    yol budur; v3 ile ayrilan TEK olcum davranisi da budur.

    SABIT BIN NEDEN SART: her occasion icin BAGIMSIZ argmax almak, occasion'lar
    ayni bine oturdugu surece dogru calisir. Ama HEDEF SAHNEDEYKEN tepe
    occasion'dan occasion'a baska bine kayabiliyor; o zaman her occasion BASKA
    bir referansa bolunur ve leave-one-out cikarmasi anlamini yitirir.

    SAHADA OLCULDU (v4_tek.npz, 60 bos + 120 hedefli tur; ayni kayit uzerinde
    offline A/B, tek degisken normalizasyon):
        occ'lar arasi tepe farki = 0 olan turlerde bastirma : -34.7 dB (110 tur)
        occ'lar arasi tepe farki > 0 olan turlerde          :  -6.0 dB ( 70 tur)
        tepe farki>0 orani: bos fazda %22, HEDEFLI fazda %48
    Yani hedefin kendisi, kendisini gizleyen mekanizmayi tetikliyordu.

        yontem                       bastirma  saglam tur   marj  gorulme
        her occasion kendi argmax'i    -27.6        45%    +2.29     76%
        tur basina tek bin             -31.8        60%    +4.10     85%
        hepsi n_dir bininde           -151.5       100%    +4.42     88%
    n_dir disaridan (8 yakalamanin medyani) geldigi icin hedeften etkilenmez;
    turun kendi tepesini kullanmak yetmiyor."""
    C = np.fft.ifft(np.fft.fft(seg0, nfft) * np.conj(np.fft.fft(ref, nfft)))[:nlag]
    j = int(bin_fix) if bin_fix is not None else int(np.argmax(np.abs(C)))
    j = max(0, min(nlag - 1, j))
    return complex(C[j])

def _alpha_direct(Craw_c, Cbg_c, n_dir, nlag):
    """Arka plani o anki dogrudan yol seviyesine oturtan kompleks olcek alpha.

    KORELASYON domeninde, SADECE dogrudan yol bini (n_dir +- DIR_WIN) uzerinde
    en-kucuk-kareler: alpha_k = <Cbg, Craw> / <Cbg, Cbg>. Hedef farkli bir
    gecikme bininde oldugu icin alpha'yi kaydirMAZ -> arka plan cikarma zayif
    hedefi silmeden dogrudan yolu temiz gotursun. Doner: (N_RX,) kompleks."""
    lo, hi = max(0, n_dir - DIR_WIN), min(nlag, n_dir + DIR_WIN + 1)
    num = np.sum(np.conj(Cbg_c[:, lo:hi]) * Craw_c[:, lo:hi], axis=1)
    den = np.sum(np.abs(Cbg_c[:, lo:hi]) ** 2, axis=1) + 1e-30
    return num / den



# ===================================================================
#  MTI VE GORUNTULEME — arka plan cikarma, backprojection
# ===================================================================

# ═══════════════════════════════════════════════════════════════════
#  7c) KALIBRASYON + IMAGING PLANI (geometri -> lag indeksi + faz agirligi)
# ═══════════════════════════════════════════════════════════════════
def imaging_plan(nlag, n_dir, fs=None):
    """z=0 izgarasi icin her (kanal, nokta) lag indeksi ve backprojection agirligi.

    fs: lag ekseninin ornekleme hizi. WB modda menzil profili ust-orneklendigi
    icin FS degil wb["fs_eff"] = FS*ups verilir; None -> FS.

    Doner sozluk:
      X, Y      : izgara eksenleri
      P         : (M,3) izgara noktalari (z=0)
      lag_idx   : (N_RX, M) int  — C_k profilinde okunacak ornek
      valid     : (N_RX, M) bool — lag profil icinde mi
      phase     : (N_RX, M) kompleks — exp(+j 2pi fc R_bi/c) (tasiyici faz telafisi)
      wgt       : (M,) reel — TX huzme + yol kaybi telafi agirligi
      Rbi       : (N_RX, M) bistatik menzil
    lag_k(p) = n_dir + round((R_bi_k(p) - D0)/c * fs)."""
    fs = FS if fs is None else float(fs)
    X, Y = grid_axes()
    XX, YY = np.meshgrid(X, Y, indexing="xy")           # (ny, nx)
    P = np.column_stack([XX.ravel(), YY.ravel(),
                         np.zeros(XX.size)])             # (M,3)
    R_bi, D, D0 = bistatic_geometry(P)                  # (N_RX,M),(N_RX,),scalar
    excess = R_bi - D0
    lag = np.rint(n_dir + excess / C_AIR * fs).astype(np.int64)   # (N_RX,M)
    valid = (lag >= 0) & (lag < nlag)
    lag_idx = np.clip(lag, 0, nlag - 1)
    phase = np.exp(1j * 2 * np.pi * CENTER_FREQ * (R_bi / C_AIR)).astype(np.complex64)

    # TX huzmesi: YUMUSAK MASKE (huzme icinde 1, disinda 0'a iner) -> tepe
    # konumunu kaydirmadan huzme disi hayaletleri kirar.
    txg = tx_pattern_gain(P).astype(np.float64)         # (M,)
    wgt = np.clip(txg / TX_MASK_FLOOR, 0.0, 1.0) if USE_TX_PATTERN \
        else np.ones(P.shape[0])
    if PATHLOSS_COMP > 0:
        r_tx = np.linalg.norm(P - TX_POS[None, :], axis=1)
        r_rx = np.linalg.norm(P - ARRAY_POS[None, :], axis=1)
        pl = (r_tx * r_rx) ** (2.0 * PATHLOSS_COMP)     # ~ (R^2) telafi
        pl = pl / (np.median(pl) + 1e-30)
        pl = np.clip(pl, 0.0, PATHLOSS_MAX)             # kose patlamasini sinirla
        wgt = wgt * pl
    return dict(X=X, Y=Y, P=P, lag_idx=lag_idx, valid=valid,
                phase=phase, wgt=wgt, Rbi=R_bi, D=D, D0=D0,
                shape=(len(Y), len(X)))

def backproject(Cbar, plan, cal):
    """Cbar: (N_RX, nlag) kompleks (occasion-ortalama korelasyon).

    I(p) = | sum_k [C_k[lag_k(p)] / cal_k] * exp(+j 2pi fc R_bi_k(p)/c) | * wgt(p)
    Doner: (ny, nx) reel goruntu."""
    N_RX_ = Cbar.shape[0]
    M = plan["lag_idx"].shape[1]
    acc = np.zeros(M, np.complex128)
    for k in range(N_RX_):
        vals = Cbar[k][plan["lag_idx"][k]]              # (M,) gather
        vals = np.where(plan["valid"][k], vals, 0.0)
        acc += (vals / cal[k]) * plan["phase"][k]
    img = np.abs(acc) * plan["wgt"]
    return img.reshape(plan["shape"])

def capture_corr(buf, refs, occ, cls, n_cls, L_seg, nlag, bg=None, n_dir=0,
                 return_raw=False, eq_inv=None, bg_t=None, dly=None):
    """Bir yakalamayi occasion'lara bol, BOS SAHA sablonuna hizala, cikar, korele et.

    buf : (N_RX, N)
    bg_t: (n_cls, N_RX, L_seg) BOS SAHA sablonu, ZAMAN domeninde. ASIL YOL budur.
    bg  : (n_cls, N_RX, nlag) ayni sablonun korelasyon (CIR) hali — bg_t yoksa
          eski, yalniz-olcekli cikarma yolu (zayif) icin kullanilir.

    NEDEN ZAMAN DOMENI: cikarmanin kalitesini belirleyen sey occasion'in sablona
    ne kadar iyi OTURDUGUDUR. Oturtma uc bilesenlidir (artik frekans kaymasi,
    faz, genlik) ve bunlardan FREKANS KAYMASI zaman domeninde bir faz rampasidir
    — korelasyon domeninde tek bir kompleks olcekle DUZELTILEMEZ. Baz istasyonu
    bizim GPSDO'muza kilitli olmadigi icin bu rampa her zaman vardir (bkz.
    align_to_template). Duzeltilmezse dogrudan yol iptal olmaz ve menzil
    profilinde kendi yan lob yapisi olarak kalir.

    Artiklar occasion'lar arasinda KOHERENT toplanir: her occasion sablonun
    olcegine cekildigi icin DURGUN hedefin yankisi hepsinde ayni komplekse
    oturur ve koherent buyur (hareketli hedef kismen soner — o --mti isi).

    Doner: Cbar (N_RX, nlag). return_raw=True ise (Cbar, Craw, alpha)."""
    buf = np.atleast_2d(buf)
    nfft = 1 << int(np.ceil(np.log2(L_seg + len(refs[0]) - 1)))
    tt = np.arange(L_seg) / FS

    Cbar = np.zeros((N_RX, nlag), np.complex128)
    Craw = np.zeros((N_RX, nlag), np.complex128)
    per_cls_count = np.zeros(n_cls, int)
    acc_raw = [np.zeros((N_RX, L_seg), np.complex128) for _ in range(n_cls)]
    acc_res = [np.zeros((N_RX, L_seg), np.complex128) for _ in range(n_cls)]
    dfs, alphas = [], []

    if bg_t is not None:
        # Genlik yanliligi duzeltmesi icin sinif ici uyum (eski dosyadaki gibi)
        L_est = len(refs[0])
        M_coh = max(2, len(occ) // max(n_cls, 1))
        coh_cls = []
        for c in range(n_cls):
            ss = [buf[0, o:o + L_est] for o, cc in zip(occ, cls) if cc == c]
            coh_cls.append(seg_coherence(ss) if len(ss) >= 2 else 1.0)
        db = [_dbias(g, M_coh, M_coh) for g in coh_cls]

        for o, c in zip(occ, cls):
            seg = buf[:, o:o + L_seg].astype(np.complex128)
            if dly is not None and np.any(np.abs(dly) > 1e-3):
                # Canliyi KALIBRASYON koordinatina geri cek (kanal basina).
                # Sablonu kaydirmak yerine canliyi kaydirmak sart: saklanan
                # equalizer ve n_dir kalibrasyon koordinatinda tanimli.
                for k in range(N_RX):
                    if abs(dly[k]) > 1e-3:
                        seg[k] = delay_shift(seg[k][None, :], -dly[k])[0]
            seg, df, al = align_to_template(seg, np.asarray(bg_t[c]), L_est,
                                            tt, db[c])
            dfs.append(df); alphas.append(al)
            acc_raw[c] += seg
            acc_res[c] += seg - np.asarray(bg_t[c])     # ZAMAN domeninde cikar
            per_cls_count[c] += 1
    else:
        # Sablon yok (ya da yalniz CIR): eski faz-hizalamali yol
        for o, c in zip(occ, cls):
            seg = buf[:, o:o + L_seg].astype(np.complex128)
            ref0 = _direct_ref(seg[0], refs[c], nfft, nlag)
            seg = seg * np.exp(-1j * np.angle(ref0))
            acc_raw[c] += seg
            per_cls_count[c] += 1

    alpha = np.ones(N_RX, np.complex128)
    for c in range(n_cls):
        if per_cls_count[c] == 0:
            continue
        Craw_c = _corr_all(acc_raw[c] / per_cls_count[c], refs[c], nfft, nlag,
                           eq_inv)
        Craw += Craw_c
        if bg_t is not None:
            Cbar += _corr_all(acc_res[c] / per_cls_count[c], refs[c], nfft,
                              nlag, eq_inv)
        elif bg is not None:
            Cbg_c = np.asarray(bg[c])
            alpha = _alpha_direct(Craw_c, Cbg_c, n_dir, nlag)
            Cbar += Craw_c - alpha[:, None] * Cbg_c
        else:
            Cbar += Craw_c
    nrm = max(1, np.count_nonzero(per_cls_count))
    Cbar = (Cbar / nrm).astype(np.complex64)
    if dfs:
        capture_corr.last_df = float(np.mean(dfs))
        capture_corr.last_amp = float(np.mean(np.abs(alphas)))
    if return_raw:
        return Cbar, (Craw / nrm).astype(np.complex64), alpha
    return Cbar

capture_corr.last_df = 0.0

capture_corr.last_amp = 1.0

def capture_running_tpl(buf, refs, occ, cls, n_cls, L_seg, nlag, hist,
                        eq_inv=None):
    """KAYAN PENCERE SABLONU — 4rx_1tx_kdyf_80mhz_v1.py:_radar_step portu.

    Sablon, AYNI AKISTAN gelen son `hist.maxlen` occasion'in ortalamasidir ve
    her occasion'da tazelenir. Saklanan bir arka plan dosyasi YOKTUR.

    NEDEN SAGLAM: --calib ile --range ayri program calistirmalari oldugu icin
    aralarinda (a) DDC desimasyon fazi KANAL/RADYO basina degisir, (b) LO'lar
    yeniden kilitlenir, (c) CFO surukleniyor olabilir. Kayan pencerede bunlarin
    HICBIRI yok — sablon her zaman guncel ve ayni kosudan.

    BEDELI: durgun hedef de sablona girer ve iptal olur; yalnizca HAREKETLI
    hedef gorunur. Durgun hedef icin saklanan bos saha sablonu (--cal) sart,
    orada da kanal basina gecikme telafisi gerekir.

    Doner (Pmti, Praw) — (N_RX, nlag) reel guc."""
    buf = np.atleast_2d(buf)
    L_est = len(refs[0])
    tt = np.arange(L_seg) / FS
    nfft = 1 << int(np.ceil(np.log2(L_seg + L_est - 1)))
    Pmti = np.zeros((N_RX, nlag))
    Praw = np.zeros((N_RX, nlag))
    n_out = 0
    M_coh = max(2, len(occ) // max(n_cls, 1))
    coh = [seg_coherence([buf[0, o:o + L_est] for o, cc in zip(occ, cls)
                          if cc == c][:8]) if len(occ) >= 2 else 1.0
           for c in range(n_cls)]
    for o, c in zip(occ, cls):
        seg = buf[:, o:o + L_seg].astype(np.complex128)
        if len(hist[c]):
            T = np.mean(hist[c], axis=0)
            seg, _, _ = align_to_template(seg, T, L_est, tt,
                                          _dbias(coh[c], M_coh, hist[c].maxlen))
        else:
            seg = seg * np.exp(-1j * np.angle(complex(seg[0, :L_est].sum())))
        Praw += np.abs(_corr_all(seg, refs[c], nfft, nlag, eq_inv)) ** 2
        if len(hist[c]) == hist[c].maxlen:
            resid = seg - np.mean(hist[c], axis=0)
            Pmti += np.abs(_corr_all(resid, refs[c], nfft, nlag, eq_inv)) ** 2
            n_out += 1
        hist[c].append(seg)
    if n_out == 0:
        return None, Praw / max(1, len(occ))
    return Pmti / n_out, Praw / max(1, len(occ))

def capture_loo(buf, refs, occ, cls, n_cls, L_seg, nlag, eq_inv=None,
                n_dir=None):
    """CAPTURE-ICI LEAVE-ONE-OUT MTI (eski gpu_v4 --tpl loo ile ayni mantik).

    Bir yakalamadaki 80-100 ms icindeki occasion'lar dalga formu sinifina
    ayrilir. Her occasion, kendi DOGRUDAN YOL (LOS) tepesine BOLUNEREK normalize
    edilir (faz+genlik). Boylece:
      * LOS ve tum SABIT yansiticilar occasion'dan occasion'a AYNI olur
        (reflektor-LOS faz farki 2*pi*fc*(tau_R-tau_LOS), CFO'dan bagimsiz sabit),
      * HAREKETLI hedef occasion'lar arasi Doppler ile fazi doner -> FARKLI olur.
    Her occasion icin sablon = AYNI siniftaki DIGER occasion'larin ortalamasi
    (leave-one-out). Artik = occasion - sablon: sabit her sey iptal, hareketli
    kalir. Artiklarin korelasyon GUCU (koherent olmayan) kanal basina toplanir.

    Doner: (Pmti, Praw) — her biri (N_RX, nlag) REEL guc. Praw = MTI'siz (LOS
    dahil), 0 dB referansi icin."""
    buf = np.atleast_2d(buf)
    nfft = 1 << int(np.ceil(np.log2(L_seg + len(refs[0]) - 1)))
    Pmti = np.zeros((N_RX, nlag))
    Praw = np.zeros((N_RX, nlag))
    for c in range(n_cls):
        idx = [i for i, cc in enumerate(cls) if cc == c]
        M = len(idx)
        if M < 2:
            for i in idx:
                seg = buf[:, occ[i]:occ[i] + L_seg].astype(np.complex128)
                Praw += np.abs(_corr_all(seg, refs[c], nfft, nlag, eq_inv)) ** 2
            continue
        # LOS'a bolerek normalize (dort kanala AYNI bolen -> kanallar arasi faz korunur)
        normed = []
        for i in idx:
            seg = buf[:, occ[i]:occ[i] + L_seg].astype(np.complex128)
            ref0 = _direct_ref(seg[0], refs[c], nfft, nlag, bin_fix=n_dir)
            if abs(ref0) < 1e-12:
                ref0 = 1.0 + 0j
            normed.append(seg / ref0)
        # Korelasyon DOGRUSAL: LOO artiginin korelasyonu, ham korelasyonlardan
        # cikar. Occasion basina 2 yerine 1 korelasyon -> FFT sayisi YARIYA.
        corrs = list(_corr_batch(np.stack(normed), refs[c], nfft, nlag, eq_inv))
        Csum = np.sum(corrs, axis=0)
        for j in range(M):
            Craw = corrs[j]                       # complex128
            Praw += np.abs(Craw) ** 2
            Cres = Craw - (Csum - Craw) / (M - 1)  # cikarma complex128'te
            Pmti += np.abs(Cres) ** 2
    return Pmti, Praw

def los_self_cal(Craw_los, n_dir):
    """LOS (dogrudan yol) ile SELF-KALIBRASYON — hedef koymaya gerek yok.

    Dogrudan yol baz istasyonundan gelir; yonu geometriden BILINIR. Kanal k'daki
    LOS'un beklenen fazi -2*pi*fc*D_k/c (D_k=|RX_k-TX|). Olculen LOS bu fazi ve
    kanal kazancini tasir:  m_k = g_k * exp(-j2pi fc D_k/c). Geometriyi cikarinca
    saf kanal kazanci kalir:  cal_k = m_k * exp(+j2pi fc D_k/c),  cal_0=1.
    Craw_los: (N_RX, nlag) LOS'u iceren korelasyon (occasion ortalamasi). LOS
    bagimsiz LO'lu kanallar arasi fazi HER YAKALAMADA yeniden referanslar."""
    el = element_positions()
    Dk = np.linalg.norm(el - TX_POS[None, :], axis=1)       # |RX_k - TX|
    vk = Craw_los[:, n_dir]                                 # kanal basina LOS
    cal = vk * np.exp(1j * 2 * np.pi * CENTER_FREQ * (Dk / C_AIR))
    cal = cal / (cal[0] + 1e-30)
    return cal.astype(np.complex64)

def _ndir_robust(ctx, refs, occ, cls, n_cls, L_seg, nlag, eq_inv=None,
                 n_cap=8, quiet=False):
    """LOS binini SAGLAM belirle: N yakalamanin ham profilini TOPLA, alt-ornek
    tepeyi bul, yuvarla.

    NEDEN: n_dir menzil sifir noktasidir; 1 bin hata BUTUN menzilleri 2.44 m
    kaydirir. Tek yakalamanin argmax'i (ya da argmax'larin medyani) bunu
    guvenilir vermiyor — SAHADA OLCULDU: v4_tek.npz'de n_dir=0 secildi ama
    ham tepenin gercek yeri 0.98 bin idi, yani TAM BIR BIN (2.40 m) hata.
    Ayni hedef ikinci kayitta 11.59 m, birincide 9.27 m cikti; farkin
    neredeyse tamami bu hatadandi.

    Biriktirilmis profilde tepe cok daha kararlidir ve alt-ornek parabolik
    kestirim yuvarlamayi dogru tarafa dusurur.

    Doner (n_dir, alt_ornek_tepe, kullanilan_yakalama)."""
    acc = None
    used = 0
    for _ in range(n_cap * 2):
        b0, _t = acquire(ctx)
        if b0 is None:
            continue
        _, Pr = capture_loo(b0, refs, occ, cls, n_cls, L_seg, nlag, eq_inv)
        acc = Pr[0].astype(np.float64) if acc is None else acc + Pr[0]
        used += 1
        if used >= n_cap:
            break
    if acc is None:
        return 0, 0.0, 0
    k = int(np.argmax(acc))
    if 0 < k < len(acc) - 1:
        y0, y1, y2 = acc[k - 1], acc[k], acc[k + 1]
        d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-30)
        d = float(np.clip(d, -0.5, 0.5))
    else:
        d = 0.0
    pk = k + d
    n_dir = int(round(pk))
    if not quiet:
        print(f"  n_dir = {n_dir}  ({used} yakalama toplami, alt-ornek tepe "
              f"{pk:.2f} bin; yuvarlama {pk-n_dir:+.2f} bin = "
              f"{(pk-n_dir)*C_AIR/FS:+.2f} m)")
    return n_dir, pk, used


def capture_track(buf, refs, occ, cls, n_cls, L_seg, nlag, plan, n_dir, eq_inv=None):
    """CAPTURE-ICI LOO MTI + LOS SELF-KALIBRASYON + backprojection.

    1) occasion'lar LOS'a bolunerek normalize (kanallar arasi faz korunur),
    2) LOS'tan self-cal (cal_k = g_k/g_0), her yakalamada yeniden,
    3) LOO MTI artigi kanal basina korele edilir; HER occasion'in artigi
       backprojection ile z=0 duzlemine yansitilir ve KOHERENT OLMAYAN toplanir
       (occasion'lar arasi Doppler fazi bilinmedigi icin). Sabit her sey MTI'de
       gitti; geriye hareketli hedef kalir.
    Doner: (img (ny,nx) reel, cal (N_RX,) kompleks) ya da (None, None)."""
    buf = np.atleast_2d(buf)
    nfft = 1 << int(np.ceil(np.log2(L_seg + len(refs[0]) - 1)))
    normed_by_cls = []
    Craw_sum = np.zeros((N_RX, nlag), np.complex128)
    n_tot = 0
    for c in range(n_cls):
        idx = [i for i, cc in enumerate(cls) if cc == c]
        normed = []
        for i in idx:
            seg = buf[:, occ[i]:occ[i] + L_seg].astype(np.complex128)
            ref0 = _direct_ref(seg[0], refs[c], nfft, nlag, bin_fix=n_dir)
            if abs(ref0) < 1e-12:
                ref0 = 1.0 + 0j
            normed.append(seg / ref0)
            n_tot += 1
        if not normed:
            continue
        corrs = list(_corr_batch(np.stack(normed), refs[c], nfft, nlag, eq_inv))
        Craw_sum += np.sum(corrs, axis=0)
        normed_by_cls.append((c, normed, corrs))
    if n_tot == 0:
        return None, None
    # KABLOLU KALIBRASYON VARSA ACI ONDAN GELIR — LOS'TAN DEGIL.
    # los_self_cal, kanallar arasi fazi DOGRUDAN YOLDAN cikarir ve varsayilan
    # geometriye (D_k = |RX_k - TX|) dayanir. Kablolu kalibrasyon zaten
    # eq_inv icinde uygulanmisken bunu da uygulamak:
    #   (a) cift duzeltme yapar,
    #   (b) geometri/dizi-yonu hatasini dogrudan aciya enjekte eder,
    #   (c) "LOS'tan 4 kanal arasi kalibrasyon yapma" kuralini cigner.
    # Bu yuzden _WCAL varken cal = 1 birakilir.
    if _WCAL is not None:
        cal = np.ones(N_RX, np.complex64)
    else:
        cal = los_self_cal(Craw_sum, n_dir)                 # LOS self-cal
    img = np.zeros(plan["shape"])
    for c, normed, corrs in normed_by_cls:
        M = len(normed)
        if M < 2:
            continue
        # KORELASYON DOGRUSALDIR: corr(a - b) = corr(a) - corr(b).
        # LOO artigi  resid_j = x_j - (S - x_j)/(M-1)  oldugundan
        #   corr(resid_j) = C_j - (Csum - C_j)/(M-1)
        # C_j'ler zaten yukarida hesaplandi -> occasion basina IKINCI bir
        # korelasyona gerek yok. Sonuc AYNI, FFT sayisi YARIYA iner.
        Csum = np.sum(corrs, axis=0)
        for j in range(M):
            # cikarma complex128'te, sonra v1 ile ayni sekilde complex64
            Cres = (corrs[j] - (Csum - corrs[j]) / (M - 1)).astype(np.complex64)
            img += backproject(Cres, plan, cal)            # occasion'lar koherent-olmayan
    return img, cal

def _measure_background(ctx, refs, occ, cls, n_cls, L_seg, seconds, label,
                        wb=None):
    """BOS SAHA olcumu — SADECE BIRIKTIRIR, korelasyonu cagirana birakir.

    `seconds` saniye boyunca occasion dilimleri LOS fazina hizalanip KANAL
    BAZINDA koherent ortalanir. Ortalama ZAMAN domeninde yapilir (dogru yeri
    orasi), korelasyon sonda tek sefer yapilir — cunku uygulanacak equalizer
    ancak dongu bittiginde biliniyor.

    wb verilirse ayrica LOS'un TAM BANT transfer fonksiyonu (num/den)
    biriktirilir; frekans basina equalizer bundan cikar.

    Doner: (bg_t (n_cls listesi, her biri (N_RX,L_seg)), num, den)."""
    nlag = L_seg - len(refs[0]) + 1
    nfft = 1 << int(np.ceil(np.log2(L_seg + len(refs[0]) - 1)))
    acc = [np.zeros((N_RX, L_seg), np.complex128) for _ in range(n_cls)]
    cnt = np.zeros(n_cls, int)
    num = np.zeros((N_RX, wb["nfft"]), np.complex128) if wb else None
    den = np.zeros(wb["nfft"], np.float64) if wb else None
    # SABLONUN KENDISI de hizalanarak kurulmali. Sadece faza gore toplamak
    # (eski hali) sablonu 30 s boyunca LEKELER: baz istasyonunun tasiyicisi
    # GPSDO'muza kilitli olmadigi icin her occasion'da farkli bir faz RAMPASI
    # vardir ve rampali sinyalleri koherent toplamak kenarlari soldurur.
    # Ilk occasion capa, sonrakiler kosan ortalamaya (df, a) ile oturtulur.
    L_est = len(refs[0])
    tt = np.arange(L_seg) / FS
    tpl = [None] * n_cls
    dfs, cohs = [], []
    print(f"\n  {label}: {seconds} s olcum...")
    print(f"  {'#':>4}  {'guc[dBFS]':>10}  {'df[Hz]':>9}  {'uyum':>6}  {'durum':>8}")
    for i in range(int(seconds)):
        buf, _ = acquire(ctx)
        if buf is None:
            print(f"  {i+1:>4}  {'--':>10}  yakalama EKSIK")
            continue
        pw = 10 * np.log10((np.abs(buf[0]) ** 2).mean() + 1e-30)
        cap_df = []
        for o, c in zip(occ, cls):
            seg = buf[:, o:o + L_seg].astype(np.complex128)
            if tpl[c] is None:
                # ilk occasion: capa. Sadece ortak fazi sifirla.
                seg = seg * np.exp(-1j * np.angle(complex(seg[0, :L_est].sum())))
                tpl[c] = seg.copy()
            else:
                seg, df, _ = align_to_template(seg, tpl[c], L_est, tt)
                cap_df.append(df)
            acc[c] += seg
            cnt[c] += 1
            tpl[c] = acc[c] / cnt[c]              # kosan ortalama = yeni capa
        if wb:
            n2, d2 = wb_accum_los(buf, wb)
            num += n2; den += d2
        g = seg_coherence([buf[0, o:o + L_est] for o, c in zip(occ, cls)
                           if c == 0][:8])
        cohs.append(g)
        dfs += cap_df
        print(f"  {i+1:>4}  {pw:>10.1f}  {np.mean(cap_df) if cap_df else 0:>9.1f}  "
              f"{g:>6.3f}  {'OK':>8}")
    if cnt.min() == 0:
        print("[HATA] bazi occasion siniflarinda hic veri yok."); sys.exit(1)
    _measure_background.last_coh = float(np.mean(cohs)) if cohs else 1.0
    if dfs:
        print(f"\n  artik frekans kaymasi: ort {np.mean(dfs):+.1f} Hz, "
              f"sapma {np.std(dfs):.1f} Hz  "
              f"({np.mean(dfs)/CENTER_FREQ*1e9:+.2f} ppb)")
        ramp = abs(np.mean(dfs)) * (L_est / FS) * 360.0
        print(f"  -> {L_est/FS*1e6:.0f} us'lik segmentte {ramp:.1f} derecelik faz "
              f"rampasi; duzeltilmeseydi cikarma bunu iptal EDEMEZDI.")
    return [acc[c] / cnt[c] for c in range(n_cls)], num, den

_measure_background.last_coh = 1.0



# ===================================================================
#  BANT SINIRI — kanal ici isleme
# ===================================================================

def band_limit_hz():
    """Islenecek bandin (f_lo, f_hi) sinirlari [Hz, CENTER_FREQ'e goreli]."""
    return -CARRIER_BW_HZ / 2.0, CARRIER_BW_HZ / 2.0

def band_limit_mask(nfft, shifted=True):
    """Kanal ICINDEKI binler icin bool maske. BAND_LIMIT_ON kapaliysa hepsi True.

    shifted=True -> fftshift sirasinda (bin 0 = -FS/2)."""
    if not BAND_LIMIT_ON:
        return np.ones(nfft, bool)
    lo, hi = band_limit_hz()
    if shifted:
        f = (np.arange(nfft) - nfft // 2) * (FS / nfft)
    else:
        f = np.fft.fftfreq(nfft, 1.0 / FS)
    return (f >= lo) & (f <= hi)

def band_limit_weight(nfft, shifted=False):
    """Kanal ici 1, disi 0, kenarlarda yukseltilmis-kosinus gecis. Agirlik olarak
    kullanilir (band_limit_mask'in yumusak surumu)."""
    if not BAND_LIMIT_ON:
        return np.ones(nfft)
    lo, hi = band_limit_hz()
    f = ((np.arange(nfft) - nfft // 2) * (FS / nfft) if shifted
         else np.fft.fftfreq(nfft, 1.0 / FS))
    tw = max(BAND_LIMIT_TW_HZ, 4.0 * FS / nfft)
    r = (np.clip((f - (lo - tw / 2)) / tw, 0.0, 1.0)
         * np.clip(((hi + tw / 2) - f) / tw, 0.0, 1.0))
    return 0.5 - 0.5 * np.cos(np.pi * r)

def band_limit_sig(x):
    """Zaman dizisini kanalin icine kisitla (BAND_LIMIT_ON kapaliysa aynen doner).

    KORELASYONDA REFERANSI KISITLAMAK YETER: C = IFFT(X * conj(R)) ve R kanal
    disinda sifirsa carpim da orada sifirdir — alinan veriyi ayrica suzmeye
    gerek yok. Boylece komsu tasiyici ne korelasyona ne de anahtarin ilan
    edilen bandina (= cozunurluk) girer.
    """
    if not BAND_LIMIT_ON:
        return x
    n = len(x)
    if n < 16:
        return x
    # Uzun dizide 2x dolgu bellege sigmaz; suzgecin darbe yaniti ~1/tw (~2 us)
    # oldugundan dairesel tasma sadece ilk birkac us'yi etkiler -> ihmal.
    nf = n if n > (1 << 19) else 1 << int(np.ceil(np.log2(max(2 * n, 1024))))
    y = gpu_filtre(x, band_limit_weight(nf), n)
    return y.astype(np.complex64)

def bandpass_sig(x, f_lo, f_hi, tw=None):
    """x'i [f_lo, f_hi] bandina kisitla (frekanslar CENTER_FREQ'e goreli)."""
    tw = BAND_LIMIT_TW_HZ if tw is None else tw
    n = len(x)
    nf = n if n > (1 << 19) else 1 << int(np.ceil(np.log2(max(2 * n, 1024))))
    f = np.fft.fftfreq(nf, 1.0 / FS)
    tww = max(tw, 4.0 * FS / nf)
    r = (np.clip((f - (f_lo - tww / 2)) / tww, 0.0, 1.0)
         * np.clip(((f_hi + tww / 2) - f) / tww, 0.0, 1.0))
    w = 0.5 - 0.5 * np.cos(np.pi * r)
    return gpu_filtre(x, w, n).astype(np.complex64)



# ===================================================================
#  GENIS BANT (WB) — LOS referansi ve frekans basina equalizer
# ===================================================================

def _wb_band_edges(Pf_nat):
    """Ortalama guc spektrumundan isgal edilen bandi bul.

    Pf_nat: (nfft,) DOGAL FFT sirasinda guc. Doner: ((a, b), floor_db) —
    a,b KAYDIRILMIS (fftshift) dizideki [a, b) sinirlari, ya da (None, floor).

    Gurultu tabani icin MEDYAN DEGIL %10'luk dilim kullanilir: 122.88 MHz
    pencerede 100 MHz'lik bir NR tasiyicisi binlerin cogunu doldurur ve medyan
    tasiyicinin ICINE duser (psd_probe ile ayni gerekce)."""
    nfft = Pf_nat.size
    Ps   = np.fft.fftshift(Pf_nat)
    dc   = nfft // 2
    ndc  = max(2, int(round(0.2e6 / (FS / nfft))))       # LO sizintisi/DC ofset
    keep = np.ones(nfft, bool); keep[dc - ndc:dc + ndc + 1] = False
    keep_ch = keep & band_limit_mask(nfft)      # sadece KANAL ICI
    if keep_ch.sum() < 8:
        return None, 0.0
    # DIKKAT — iki AYRI maske, bilerek:
    #   * normalizasyon ve ISGAL SECIMI  -> keep_ch (kanal ici)
    #   * GURULTU TABANI                 -> keep (TUM pencere)
    # Taban da kanal icinden alinsaydi, kanal bastan sona dolu oldugu icin
    # %10'luk dilim SINYALIN ICINE duserdi ve "taban + 6 dB" esigi yalnizca
    # en guclu birkac bini gecirirdi (olculdu: 100 MHz yerine 3 MHz).
    # Sessiz bin aramak icin pencerenin tamamina bakmak SART.
    Pdb  = 10 * np.log10(Ps / (Ps[keep_ch].max() + 1e-30) + 1e-30)
    floor = float(np.percentile(Pdb[keep], 10))
    occ = keep_ch & (Pdb > floor + WB_OCC_DB)
    if occ.sum() < 8:
        return None, floor
    # Isgal maskesindeki kucuk delikleri (koruma araligi, DC cukuru, sonmus RB)
    # kapat, sonra EN GENIS surekli blogu al -> tek tasiyici. Genisletme kadar
    # geri daralt ki kenarlar kaymasin.
    gap = max(1, int(round(WB_GAP_MHZ * 1e6 / (FS / nfft))))
    occ_d = np.convolve(occ.astype(np.float32),
                        np.ones(2 * gap + 1, np.float32), "same") > 0
    # SADECE bant siniriyla kesistir — keep_ch ile DEGIL: keep_ch DC deligini
    # de tasir ve onu geri acmak bandi ikiye boler (olculdu: 100 MHz yerine
    # 48 MHz, yani DC'nin solundaki yari). Dilatasyonun isi zaten o deligi
    # kapatmakti.
    occ_d &= band_limit_mask(nfft)
    runs = _segments(occ_d, 1)
    if not runs:
        return None, floor
    a, b = max(runs, key=lambda t: t[1] - t[0])
    a = min(a + gap, b - 1); b = max(b - gap, a + 1)
    return (int(a), int(b)), floor

def _wb_weight(nfft, a, b):
    """Bant icinde 1, kenarlarda Tukey inisi olan reel agirlik (DOGAL sira).

    Kenar inisi olmazsa keskin bant kesimi korelasyonda sinc yan lobu (-13 dB)
    birakir ve guclu LOS'un yan lobu zayif hedefi orter."""
    w_s = np.zeros(nfft, np.float32)
    n   = b - a
    nt  = max(1, int(round(WB_TAPER * n)))
    win = np.ones(n, np.float32)
    ramp = (0.5 * (1 - np.cos(np.pi * (np.arange(nt) + 0.5) / nt))).astype(np.float32)
    win[:nt] = ramp
    win[n - nt:] = ramp[::-1]
    w_s[a:b] = win
    return np.fft.ifftshift(w_s)

def wb_blocks(N, nblk, nfft, start=0):
    """Yakalama penceresini nfft uzunlugunda bloklara bol, esit araliklarla yay."""
    n_max = max(0, (N - start) // nfft)
    if n_max < 1:
        return []
    n = int(min(nblk, n_max))
    step = max(1, n_max // n)
    return [start + i * step * nfft for i in range(n)]

def wb_setup(bufs, nfft=None, nblk=None, quiet=False):
    """WB islem plani: isgal edilen bant, agirlik W(f), lag penceresi.

    nfft/nblk None ise MODUL SABITLERI okunur (varsayilan deger olarak
    baglanmaz — yoksa --blk/--nblk override'lari etkisiz kalirdi).
    bufs: bir ya da birkac yakalama ((N_RX,N) ya da (N,)). Doner sozluk:
      nfft, nblk, mask (bool, dogal sira), w (reel agirlik), f_abs (mutlak frek.)
      lag_take (IFFT ciktisindan alinacak indisler), n_neg/n_pos/nlag,
      f_lo/f_hi/bw (MHz/Hz), res_m (menzil cozunurlugu)."""
    nfft = WB_NFFT if nfft is None else int(nfft)
    nblk = WB_NBLK if nblk is None else int(nblk)
    Pf, nb = np.zeros(nfft), 0
    for buf in bufs:
        x = np.atleast_2d(buf)[0]
        nblk_av = x.size // nfft
        if nblk_av < 1:
            continue
        take = x[:nblk_av * nfft].reshape(nblk_av, nfft)
        sel = np.linspace(0, nblk_av - 1, min(8, nblk_av)).astype(int)
        Pf += (np.abs(np.fft.fft(take[sel], axis=1)) ** 2).mean(0)
        nb += 1
    if nb == 0:
        print(f"[HATA] WB blogu icin yakalama kisa (< {nfft} ornek)."); sys.exit(1)
    Pf /= nb

    df = FS / nfft
    if WB_BW_MHZ is not None:                 # --bw ile ELLE zorlanan bant
        half = int(round(WB_BW_MHZ * 1e6 / 2 / df))
        # Elle verilen bant bile kanali ASAMAZ: komsu tasiyici hicbir yoldan
        # equalizer'a girmemeli.
        half = min(half, int(round(CARRIER_BW_HZ / 2 / df))) \
            if BAND_LIMIT_ON else half
        a, b = nfft // 2 - half, nfft // 2 + half
        floor_db, forced = float("nan"), True
    else:
        edges, floor_db = _wb_band_edges(Pf)
        forced = False
        if edges is None:
            print("\n[HATA] bantta tasiyici bulunamadi (isgal esigi tutmadi).")
            print("       --psd ile frekansi/kazanci dogrula, ya da --bw ile "
                  "bandi elle ver.")
            sys.exit(1)
        a, b = edges
    a = max(0, a); b = min(nfft, b)
    w    = _wb_weight(nfft, a, b)
    # Tukey etegi ve gap-genisletme kanal disina birkac bin tasabilir; agirligi
    # orada kesin olarak sifirla. Islenen HICBIR bin kanal disinda kalmasin.
    w *= np.fft.ifftshift(band_limit_mask(nfft)).astype(w.dtype)
    mask = w > 0
    fb   = np.fft.fftfreq(nfft, 1.0 / FS)                  # dogal sira, +-FS/2
    f_lo = (a - nfft // 2) * df
    f_hi = (b - 1 - nfft // 2) * df
    bw   = f_hi - f_lo

    n_pos = int(np.ceil(WB_RMAX_M / C_AIR * FS))
    n_neg = int(np.ceil(WB_NEG_M / C_AIR * FS))
    if n_neg + n_pos + 1 > nfft // 2:
        print("[HATA] WB_RMAX_M/WB_NEG_M blok icin cok buyuk."); sys.exit(1)
    lag_take = np.concatenate([np.arange(nfft - n_neg, nfft),
                               np.arange(0, n_pos + 1)]).astype(np.int64)
    res_m = C_AIR / (2.0 * max(bw, 1.0))

    # LAG UST-ORNEKLEME. Ornek araligi c/FS = 2.44 m iken tam bantta cozunurluk
    # c/(2B) = 1.50 m: menzil profili KENDI cozunurlugunun altinda orneklenmis
    # olur ve tepeyi en yakin ornege yuvarlamak ~1 m sistematik konum hatasi
    # birakir. Cikarilan lag penceresi sinc (FFT) ile ups katina yogunlastirilir
    # -> hem gather hem tepe okuma alt-ornek dogrulukta olur.
    ups = int(max(1, np.ceil(4.0 * bw / FS)))
    nlag_raw = n_neg + n_pos + 1

    wb = dict(nfft=nfft, nblk=nblk, mask=mask, w=w, edge=(a, b),
              f_abs=(CENTER_FREQ + fb), df=df,
              lag_take=lag_take, n_neg=n_neg, n_pos=n_pos,
              ups=ups, fs_eff=FS * ups, nlag_raw=nlag_raw,
              nlag=nlag_raw * ups, n_dir0=n_neg * ups,
              f_lo=f_lo, f_hi=f_hi, bw=bw, res_m=res_m, floor_db=floor_db)
    if not quiet:
        print(f"\n  WB bant   : {(CENTER_FREQ+f_lo)/1e6:.3f} .. "
              f"{(CENTER_FREQ+f_hi)/1e6:.3f} MHz  ({bw/1e6:.2f} MHz genis)"
              + ("   [--bw ile ZORLANDI]" if forced else
                 f"   [olculdu, taban {floor_db:+.1f} dB]"))
        # Beklenen isgal: RB'den turetilen OCC_BW_HZ (100 MHz kanal -> 273 RB
        # -> 98.28 MHz; kalan 2x845 kHz guard band'dir ve BOSTUR).
        # Olculen bunun cok altindaysa ya frekans/pencere kaymistir ya da DDC
        # kenari yiyordur; cok ustundeyse komsu tasiyici da maskeye girmistir.
        if OCC_BW_HZ:
            exp_bw = OCC_BW_HZ
            print(f"  beklenen  : {exp_bw/1e6:.2f} MHz isgal "
                  f"({CARRIER_BW_HZ/1e6:.0f} MHz kanal - 2 x "
                  f"{GUARD_BAND_HZ/1e3:.0f} kHz guard)  -> "
                  f"olculen/beklenen = {bw/exp_bw:.2f}")
            if not forced and not (0.8 < bw / exp_bw < 1.25):
                print(f"  [UYARI] olculen bant beklenenden cok farkli. Kontrol: "
                      f"CENTER_FREQ={CENTER_FREQ/1e6:.1f} MHz dogru mu (--psd), "
                      f"kazanc kirpiyor mu, pencere DL'e mi denk geliyor.")
        if BAND_LIMIT_ON:
            _bl, _bh = band_limit_hz()
            print(f"  bant siniri: {(CENTER_FREQ+_bl)/1e6:.1f} .. "
                  f"{(CENTER_FREQ+_bh)/1e6:.1f} MHz — disi ISLENMEDI "
                  f"(komsu hucre/alias). Kapatmak: --fullband")
        print(f"  cozunurluk: c/(2B) = {res_m:.2f} m   "
              f"(dar bant SSB ~7.2 MHz olsaydi {C_AIR/(2*7.2e6):.1f} m)")
        print(f"  blok      : {nfft} ornek ({nfft/FS*1e3:.3f} ms) x {nblk}, "
              f"bin {df/1e3:.3f} kHz")
        print(f"  lag       : -{WB_NEG_M:.0f} .. +{WB_RMAX_M:.0f} m "
              f"({wb['nlag']} ornek, ust-ornekleme x{ups} -> adim "
              f"{C_AIR/wb['fs_eff']:.2f} m), LOS indeksi n_dir={wb['n_dir0']}")
    return wb

def _lag_interp(C, ups):
    """Lag ekseninde sinc (FFT) ust-ornekleme. C: (..., nlag)."""
    if ups <= 1:
        return C.astype(np.complex64)
    n = C.shape[-1]
    F = np.fft.fft(C, axis=-1)
    h = (n + 1) // 2
    Fp = np.zeros(C.shape[:-1] + (n * ups,), np.complex128)
    Fp[..., :h] = F[..., :h]
    Fp[..., n * ups - (n - h):] = F[..., h:]
    return (np.fft.ifft(Fp, axis=-1) * ups).astype(np.complex64)

def wb_core_mask(wb, drop=0.05):
    """Bant kenarindaki `drop` oranini disarida birakan maske (DOGAL FFT sirasi).

    DIKKAT: wb["mask"] dogal sirada oldugu icin bant indis 0'in ETRAFINA sarilir;
    kenari kirpmak icin once kaydirilmis siraya gecmek ZORUNLU (dogrudan
    flatnonzero ile ilk/son binleri atmak bandin ORTASINI kirpar)."""
    a, b = wb["edge"]
    d = int(round(drop * (b - a)))
    ms = np.zeros(wb["nfft"], bool)
    ms[a + d:max(a + d + 1, b - d)] = True
    return np.fft.ifftshift(ms)

def _wb_whiten(Rf, wb):
    """Referans spektrumunu duzleyen agirlik (uyumsuz filtre).

    OFDM tasiyicisinin |S_ref(f)| dalgalanmasi korelasyon tepesini yayar;
    1/|S_ref| ile bolunce bant icinde duz genlik kalir -> tepe ideal sinc.
    EQ_REG payi, sonmus binlerde gurultunun patlamasini engeller."""
    mag = np.abs(Rf).astype(np.float32)
    lvl = float(np.sqrt(np.mean(mag[wb["mask"]] ** 2))) + 1e-30
    if WB_WHITEN <= 0:
        return wb["w"]
    wht = (lvl / (mag + EQ_REG * lvl)) ** WB_WHITEN
    return (wb["w"] * wht).astype(np.float32)

def wb_accum_los(buf, wb):
    """Sadece LOS transfer fonksiyonu birikimi — korelasyon YAPMAZ.

    Frekans basina equalizer, referans SSB anahtari olsa bile TAM BANTTAN
    kestirilir: LOS 100 MHz'i tasidigi icin kestirim orada cok daha iyi
    kosullanir. Sonra taplar korelasyon izgarasinda degerlendirilip SSB'nin
    GERCEKTE durdugu frekansta uygulanir (bkz. eq_from_taps).

    Doner (num (N_RX,nfft), den (nfft,))."""
    buf  = np.atleast_2d(buf)
    nfft = wb["nfft"]
    starts = wb_blocks(buf.shape[1], wb["nblk"], nfft)
    num = np.zeros((N_RX, nfft), np.complex128)
    den = np.zeros(nfft, np.float64)
    if not starts:
        return num, den
    pw = np.array([float(np.mean(np.abs(buf[0, o:o + nfft]) ** 2)) for o in starts])
    keep = pw > pw.max() * 10 ** (-WB_BLK_DYN_DB / 10.0)
    for o, g in zip(starts, keep):
        if not g:
            continue
        Sr = _FFT(np.ascontiguousarray(buf[:, o:o + nfft]).astype(_FFT_C), axis=1)
        num += Sr * np.conj(Sr[0])[None, :]
        den += np.abs(Sr[0]) ** 2
    return num, den

def wb_corr(buf, wb, eq=None, ref_mode=None, self_eq=True):
    """Yakalamayi WB bloklarina bol; her blok icin kanal MENZIL PROFILI (CIR).

    Her blokta:  S_k(f) = FFT(kanal k)  ->  equalizer ile esitlenir
                 Ref(f) = referans (kanal 0 ya da TX'e huzme)
                 C_k    = IFFT{ S_k conj(Ref) W(f) }  ->  lag penceresi

    self_eq=True: ileri FFT'ler bellekte tutulur, equalizer AYNI yakalamadan
    LOS ile kestirilip hemen uygulanir (ek FFT maliyeti yok). Bellek yetmezse
    ya da self_eq=False ise disaridan verilen `eq` (bir onceki yakalamaninki)
    kullanilir — equalizer sicaklikla yavas suruklendigi icin bu da gecerlidir.

    Doner sozluk:
      C   : (n_blk, N_RX, nlag) kompleks CIR
      num : (N_RX, nfft) kompleks  Sum_b S_k^ham conj(S_0^ham)   (equalizer icin)
      den : (nfft,) reel           Sum_b |S_0^ham|^2
      eq  : kullanilan equalizer (None olabilir)
      blk : kullanilan blok baslangiclari (TDD'de zayif olanlar atilmistir)"""
    buf  = np.atleast_2d(buf)
    nfft = wb["nfft"]
    ref_mode = WB_REF if ref_mode is None else ref_mode
    starts = wb_blocks(buf.shape[1], wb["nblk"], nfft)
    empty = dict(C=np.zeros((0, N_RX, wb["nlag"]), np.complex64),
                 num=np.zeros((N_RX, nfft), np.complex128),
                 den=np.zeros(nfft), eq=eq, blk=[])
    if not starts:
        return empty
    # TDD: DL olmayan (UL/bosluk) bloklari at — referans zayifsa korelasyon
    # gurultuden ibaret olur ve LOO sablonunu bozar.
    pw = np.array([float(np.mean(np.abs(buf[0, o:o + nfft]) ** 2)) for o in starts])
    keep = pw > pw.max() * 10 ** (-WB_BLK_DYN_DB / 10.0)
    starts = [o for o, g in zip(starts, keep) if g]
    if not starts:
        return empty

    nb  = len(starts)
    num = np.zeros((N_RX, nfft), np.complex128)
    den = np.zeros(nfft, np.float64)
    cache = (self_eq and
             nb * N_RX * nfft * 8 <= WB_MAXMEM_MB * (1 << 20))
    Sall = np.zeros((nb, N_RX, nfft), np.complex64) if cache else None

    for i, o in enumerate(starts):
        Sr = _FFT(np.ascontiguousarray(buf[:, o:o + nfft]).astype(_FFT_C), axis=1)
        # equalizer'in KENDISI ham (esitlenmemis) spektrumdan kestirilir
        num += Sr * np.conj(Sr[0])[None, :]
        den += np.abs(Sr[0]) ** 2
        if cache:
            Sall[i] = Sr

    eq_use = wb_los_eq(num, den, wb) if cache else eq
    C = np.zeros((nb, N_RX, wb["nlag"]), np.complex64)
    for i, o in enumerate(starts):
        Sr = Sall[i] if cache else \
            _FFT(np.ascontiguousarray(buf[:, o:o + nfft]).astype(_FFT_C), axis=1)
        C[i] = _wb_one_block(Sr, wb, eq_use, ref_mode)
    del Sall
    return dict(C=C, num=num, den=den, eq=eq_use, blk=starts)

def _wb_one_block(Sr, wb, eq, ref_mode):
    """Tek blogun spektrumundan esitleme + beyazlatma ile CIR. Doner (N_RX,nlag)."""
    S = Sr if (eq is None or not EQ_ON) else (Sr * eq["inv"])
    Rf = _wb_beam_ref(S, wb) if ref_mode == "beam" else S[0]
    G = S * (np.conj(Rf) * _wb_whiten(Rf, wb))[None, :]
    c = _IFFT(G.astype(_FFT_C), axis=1)[:, wb["lag_take"]]
    return _lag_interp(c, wb["ups"])

def _wb_beam_ref(S, wb):
    """TX yonune huzme: esitlenmis kanallari geometrik faza gore koherent topla.

    Referans kanal 0 yerine huzme kullanmak LOS SNR'ini ~6 dB artirir ve
    LOS DISI yankilarin referansi kirletmesini bir miktar bastirir. Equalizer
    HENUZ yoksa (ilk yakalama) kanallar esitlenmemis olur; o durumda huzme
    kazanci dusuk kalir ama bozmaz."""
    el = element_positions()
    Dk = np.linalg.norm(el - TX_POS[None, :], axis=1)
    ph = np.exp(2j * np.pi * np.outer(Dk - Dk[0], wb["f_abs"]) / C_AIR)
    return (S * ph.astype(np.complex64)).sum(0) / N_RX

def wb_los_eq(num, den, wb):
    """LOS'tan FREKANS BASINA kanal equalizer'i (tek katsayi DEGIL).

    H_k(f) = <S_k conj(S_0)>/<|S_0|^2>  kanal k'nin kanal 0'a gore transfer
    fonksiyonu; icinde hem donanim uyumsuzlugu g_k/g_0 hem LOS'un geometrik
    gecikmesi exp(-j2pi f_abs (D_k-D_0)/c) hem de CEVRE YANKILARI var.
      1) geometrik faz ANALITIK olarak cikarilir (f_abs ile, yani genis bantta
         dogru; boylece kalan sey saf donanimdir ve KISA bir darbe yanitidir),
      2) kalan, +-ng gecikme tapasindan olusan KISA FIR'a agirlikli en-kucuk-
         kareler ile oturtulur.

    Neden kapi (gating) degil de LS? Bant sinirli H'nin IFFT'sini +-ng ile
    kesmek sinc kuyruklarini atar ve bant kenarinda Gibbs dalgalanmasi birakir
    (olculdu: birkac dB). LS ayni tap sayisiyla bant ICINDE en iyi uyumu verir,
    kenarda patlamaz. Agirlik = Tukey x referans gucu (den): kestirimin gercek
    guvenilirligi. ng, hem EQ_GATE_M'in hem de bant genisliginin (ana lob
    FS/B ornek) dayattigi degerdir; cevre yankisi ng disinda kaldigi icin
    equalizer'a KARISMAZ.

    Doner sozluk: EQ (N_RX,nfft), inv (MMSE tersi; S_k * inv_k = esitlenmis),
    gate (ornek), rms_db / rms_deg (bant ici sapma ozeti)."""
    nfft, m = wb["nfft"], wb["mask"]
    ng = max(int(np.ceil(2.0 * FS / max(wb["bw"], 1.0))),
             int(round(EQ_GATE_M / C_AIR * FS)), 1)
    idx = np.flatnonzero(m)
    el  = element_positions()
    Dk  = np.linalg.norm(el - TX_POS[None, :], axis=1)
    geo = np.exp(2j * np.pi * np.outer(Dk - Dk[0], wb["f_abs"][idx]) / C_AIR)
    Hb  = (num[:, idx] / (den[idx][None, :] + 1e-30)) * geo      # (N_RX, nb)

    wf = wb["w"][idx].astype(np.float64) * den[idx]
    wf /= (wf.max() + 1e-30)
    # DFT matrisleri sadece maskeye+ng'ye bagli; her yakalamada yeniden uretmek
    # yerine wb icinde onbelleklenir (canli modda saniyede bir cagriliyor).
    cache = wb.get("_ls")
    if cache is None or cache[0] != ng:
        t = np.arange(-ng, ng + 1)
        E = np.exp(-2j * np.pi * np.outer(idx.astype(np.float64), t) / nfft)
        Eall = np.exp(-2j * np.pi *
                      np.outer(np.arange(nfft, dtype=np.float64), t) / nfft)
        wb["_ls"] = cache = (ng, t, E, Eall)
    _, t, E, Eall = cache
    G  = E.conj().T @ (wf[:, None] * E)                          # (nt, nt)
    G += (1e-8 * np.trace(G).real / len(t)) * np.eye(len(t))     # kosullandirma
    B  = E.conj().T @ (wf[None, :] * Hb).T                       # (nt, N_RX)
    Cc = np.linalg.solve(G, B)                                   # FIR taplari
    EQ = (Eall @ Cc).T.astype(np.complex64)                      # (N_RX, nfft)

    a   = np.abs(EQ)
    med = np.median(a[:, m], axis=1)[:, None] + 1e-30
    eps = (EQ_REG * med).astype(np.float32)
    inv = (np.conj(EQ) / (a ** 2 + eps ** 2)) * m[None, :]

    # Ozet: equalizer bant boyunca NE KADAR degisiyor? Buyukse tek katsayili
    # kalibrasyon yetersiz demektir (bu dosyanin varlik sebebi).
    amp = 20 * np.log10(a[:, m] / med + 1e-30)
    phs = np.degrees(np.angle(EQ[:, m] * np.conj(np.median(EQ[:, m], axis=1))[:, None]))
    return dict(EQ=EQ, inv=inv.astype(np.complex64), gate=ng, taps=Cc.T,
                med=med[:, 0], rms_db=amp.std(axis=1),
                rms_deg=((phs + 180) % 360 - 180).std(axis=1))

def wb_ndir(res, wb):
    """LOS lag indeksi (ust-ornekli eksende). ref=ch0 iken teorik olarak n_dir0."""
    if res["C"].shape[0] == 0:
        return wb["n_dir0"]
    p = (np.abs(res["C"][:, 0, :]) ** 2).sum(0)
    return int(np.argmax(p))

def wb_los_phase_err(res, n_dir):
    """Equalizer sonrasi LOS fazi geometriyle uyusuyor mu? [derece, kanal basina]

    Sifira yakin olmali. Buyukse: dizi geometrisi (ARRAY_D_M / ARRAY_ORDER_SIGN /
    n2) ya da kablo sirasi yanlistir — backprojection da o kadar kayar."""
    if res["C"].shape[0] == 0:
        return np.zeros(N_RX)
    v = res["C"][:, :, n_dir].mean(0)                        # (N_RX,)
    el = element_positions()
    Dk = np.linalg.norm(el - TX_POS[None, :], axis=1)
    exp_ = np.exp(-2j * np.pi * CENTER_FREQ * (Dk - Dk[0]) / C_AIR)
    r = v * np.conj(v[0]) * np.conj(exp_)
    return np.degrees(np.angle(r))

def _wb_norm_loo(C, n_dir):
    """Her blogu kendi LOS tapasina (kompleks) bolup leave-one-out artik uret.

    Bolen DORT KANALA DA AYNI (kanal 0'in LOS'u) -> kanallar arasi faz, yani
    ACI bilgisi KORUNUR; sadece bloktan bloga CFO/genlik jitteri gider.
    Doner (Cn, resid) — ikisi de (n_blk, N_RX, nlag)."""
    los = C[:, 0:1, n_dir:n_dir + 1]
    los = np.where(np.abs(los) < 1e-20, np.complex64(1.0), los)
    Cn = (C / los).astype(np.complex64)
    nb = Cn.shape[0]
    if nb < 2:
        return Cn, np.zeros_like(Cn)
    S = Cn.sum(0, keepdims=True)
    return Cn, (Cn - (S - Cn) / (nb - 1)).astype(np.complex64)

def wb_range(res, n_dir):
    """CIR domeninde LOO MTI -> (Pmti, Praw), her biri (N_RX, nlag) reel guc."""
    C = res["C"]
    if C.shape[0] == 0:
        return None, None
    Cn, resid = _wb_norm_loo(C, n_dir)
    return (np.abs(resid) ** 2).sum(0), (np.abs(Cn) ** 2).sum(0)

def wb_track(res, plan, n_dir):
    """CIR domeninde LOO MTI + backprojection (bloklar koherent-olmayan toplanir).

    Equalizer frekans domeninde ZATEN uygulandigi icin backprojection'a birim
    kalibrasyon verilir; kanallar arasi kalan tek fark GEOMETRIKTIR."""
    C = res["C"]
    if C.shape[0] < 2:
        return None, None
    Cn, resid = _wb_norm_loo(C, n_dir)
    one = np.ones(N_RX, np.complex64)
    img = np.zeros(plan["shape"])
    for b in range(resid.shape[0]):
        img += backproject(resid[b], plan, one)
    return img, Cn.mean(0)

def wb_bring_up(ctx, n_cap=2):
    """WB acilisi: bandi olc, LOS equalizer'ini kur, n_dir'i bul.

    Doner (wb, eq, n_dir, res) — res son yakalamanin WB sonucu."""
    bufs = []
    for _ in range(4 * n_cap):
        b, _ = acquire(ctx)
        if b is not None:
            bufs.append(b)
        if len(bufs) >= n_cap:
            break
    if not bufs:
        print("[HATA] WB acilisi icin yakalama alinamadi."); sys.exit(1)
    wb  = wb_setup(bufs)
    res = wb_corr(bufs[-1], wb, eq=None, self_eq=True)
    if res["C"].shape[0] == 0:
        print("[HATA] WB blogu olusmadi (pencere kisa ya da sinyal yok)."); sys.exit(1)
    eq    = res["eq"]
    n_dir = wb_ndir(res, wb)
    print(f"  blok      : {len(res['blk'])}/{wb['nblk']} kullanildi "
          f"(digerleri TDD'de UL/bosluk)")
    print(f"  n_dir     : {n_dir} (beklenen {wb['n_dir0']}; LOS ortak gecikmesi "
          f"referansla iptal olur)")
    print(f"  equalizer : kapi +-{eq['gate']} ornek "
          f"({eq['gate']/FS*C_AIR:.1f} m),  bant ici sapma "
          + "  ".join(f"k{k}:{eq['rms_db'][k]:.2f}dB/{eq['rms_deg'][k]:.1f}der"
                      for k in range(N_RX)))
    ph = wb_los_phase_err(res, n_dir)
    print(f"  LOS faz hatasi (equalizer sonrasi, geometriye gore) [der]: "
          + "  ".join(f"{p:+.1f}" for p in ph))
    if np.max(np.abs(ph[1:])) > 25.0:
        print("  [UYARI] LOS fazi geometriyle uyusmuyor: ARRAY_D_M / ARRAY_ORDER_SIGN /")
        print("          ARRAY_N2 ya da kablo sirasi (RX_CHANS) yanlis olabilir.")
    return wb, eq, n_dir, res



# ===================================================================
#  NR STANDARDI — PSS/SSS, PBCH/PDCCH/PDSCH DMRS, CORESET#0
# ===================================================================

def _lfsr7(init, taps, n=PSS_NSC):
    """7 bitlik m-dizisi. init: x(0..6). taps: geri besleme (x(i+t) toplami)."""
    x = np.zeros(n + 7, np.uint8)
    x[:7] = init
    for i in range(n):
        s = 0
        for t in taps:
            s ^= int(x[i + t])
        x[i + 7] = s
    return x[:n]

def pss_seq(n_id2):
    """d_PSS(n) = 1-2x[(n+43*N_ID_2) mod 127],  x(i+7)=x(i+4)+x(i)."""
    x = _lfsr7([0, 1, 1, 0, 1, 1, 1], [4, 0])
    n = np.arange(PSS_NSC)
    return (1.0 - 2.0 * x[(n + 43 * n_id2) % PSS_NSC]).astype(np.float32)

def sss_seq(n_id1, n_id2):
    """d_SSS(n) = [1-2x0((n+m0)%127)] * [1-2x1((n+m1)%127)]."""
    x0 = _lfsr7([1, 0, 0, 0, 0, 0, 0], [4, 0])
    x1 = _lfsr7([1, 0, 0, 0, 0, 0, 0], [1, 0])
    m0 = 15 * (n_id1 // 112) + 5 * n_id2
    m1 = n_id1 % 112
    n = np.arange(PSS_NSC)
    return ((1.0 - 2.0 * x0[(n + m0) % PSS_NSC]) *
            (1.0 - 2.0 * x1[(n + m1) % PSS_NSC])).astype(np.float32)

def _symbol_starts(x, n_search):
    """CP korelasyonuyla OFDM sembol sinirlarini bul (0..n_search ornek icinde).

    r(n) = |sum_{i<CP} x[n+i] conj(x[n+i+N_FFT])| — CP, sembolun son N_FFT'inci
    orneginin kopyasi oldugu icin sembol basinda tepe yapar. Doner: indis listesi
    (her tepe bir sembolun CP baslangici)."""
    n_search = int(min(n_search, x.size - N_FFT - CP_NORM - 1))
    if n_search < 4 * (N_FFT + CP_NORM):
        return np.zeros(0, np.int64)
    y = (x[:n_search + CP_NORM] *
         np.conj(x[N_FFT:N_FFT + n_search + CP_NORM])).astype(np.complex64)
    cs = np.concatenate([[0], np.cumsum(y)])
    r = np.abs(cs[CP_NORM:CP_NORM + n_search] - cs[:n_search])
    # Sembol periyodu boyunca yerel azami -> sembol sinirlari
    per = N_FFT + CP_NORM
    npk = n_search // per
    if npk < 2:
        return np.zeros(0, np.int64)
    blk = r[:npk * per].reshape(npk, per)
    idx = blk.argmax(1) + np.arange(npk) * per
    amp = blk.max(1)
    return idx[amp > 0.35 * amp.max()].astype(np.int64)

def detect_cell(buf, win_ms=CELL_WIN_MS, quiet=False, band=None):
    """PSS/SSS ile hucre kimligi. buf: (N_RX,N) ya da (N,) tek yakalama.

    Doner sozluk (bulunamazsa None):
      pci, n_id1, n_id2, t0 (PSS sembolunun PPS'ten ofseti [s]),
      f_ssb (SSB merkez frekansi [Hz]), snr_db, hits (tum PSS tepeleri [s]),
      period_ms (ardisik PSS'ler arasi fark, bulunabildiyse)."""
    x = np.atleast_2d(buf)[0].astype(np.complex64)
    n_search = int(min(x.size, win_ms * 1e-3 * FS))
    starts = _symbol_starts(x, n_search)
    if starts.size == 0:
        if not quiet:
            print("  [HATA] OFDM sembol siniri bulunamadi (CP korelasyonu zayif).")
        return None

    L = 1 << int(np.ceil(np.log2(N_FFT + PSS_NSC)))
    D = np.stack([pss_seq(i) for i in range(3)]).astype(np.complex64)
    Df = np.conj(np.fft.fft(D, L, axis=1))

    # SSB bant ICINDE olmali -> arama araligini isgal edilen banda kisitla
    b_lo, b_hi = 0, N_FFT - PSS_NSC
    if band is not None:
        b_lo = max(0, int(N_FFT // 2 + band[0] / SCS_HZ) - PSS_NSC)
        b_hi = min(N_FFT - PSS_NSC, int(N_FFT // 2 + band[1] / SCS_HZ))
        if b_hi <= b_lo:
            b_lo, b_hi = 0, N_FFT - PSS_NSC

    # CP korelasyonu tepesi UZUN CP'li sembollerde 64 ornek erken cikabilir
    # (plato). FFT penceresi 64 ornek kaysa 127 altasiyici boyunca ~12 rad faz
    # egimi olur ve PSS korelasyonu coker; bu yuzden iki CP uzunlugu da denenir.
    best = None
    hits = []
    for s in starts:
        for du in (CP_NORM, CP_LONG):
            u = s + du
            if u + N_FFT > x.size:
                continue
            Y = np.fft.fftshift(np.fft.fft(x[u:u + N_FFT]))
            nrm = np.sqrt(float(np.mean(np.abs(Y[b_lo:b_hi + PSS_NSC]) ** 2))) + 1e-30
            cc = np.abs(np.fft.ifft(np.fft.fft(Y / nrm, L) * Df, axis=1))
            cc = cc[:, b_lo:b_hi]
            j = np.unravel_index(int(np.argmax(cc)), cc.shape)
            # Tepe / arka plan: PSS gercekse oran >> 1 (rastgele veride ~sqrt(127))
            rec = (float(cc[j] / (np.median(cc) + 1e-30)), int(s), int(u),
                   int(j[0]), int(j[1] + b_lo))
            hits.append(rec)
            if best is None or rec[0] > best[0]:
                best = rec
    if best is None:
        return None
    snr, s, u_p, n_id2, b0 = best
    if snr < 6.0:
        if not quiet:
            print(f"  [UYARI] PSS tepesi zayif (tepe/medyan {snr:.1f}) — "
                  f"hucre kimligi GUVENILMEZ.")

    # --- IZGARA HIZALAMA (SSS icin ZORUNLU) ---
    # SSB, tasiyicinin altasiyici izgarasina OTURMAK ZORUNDA DEGILDIR: kendi
    # senkron rasterindedir (FR1: N*1200 + M*50 kHz), bizim FFT izgaramiz ise
    # CENTER_FREQ + k*30 kHz. Aradaki fark 30 kHz'in KESIRI kadar olabilir.
    # PSS bunu yutar (127 uzunlukta dizi, birkac dB kayipla yine bulunur) ama
    # SSS IKI sembolun koherent carpimina dayandigi icin coker: kesirli kayma
    # komsu altasiyicilardan sizinti (ICI) uretir ve o sizinti PSS ile SSS
    # sembolunde FARKLI veriden gelir. Bu yuzden once kesirli frekans + bin
    # ince aramasi yapilir.
    n_t = np.arange(N_FFT)
    d_pss = pss_seq(n_id2)
    best_ref = (-1.0, 0.0, b0)
    for df in np.arange(-SCS_HZ / 2, SCS_HZ / 2 + 1.0, SCS_HZ / 24):
        rot = np.exp(-2j * np.pi * df * n_t / FS)
        Y = np.fft.fftshift(np.fft.fft(x[u_p:u_p + N_FFT] * rot))
        for bb in range(max(0, b0 - 2), min(N_FFT - PSS_NSC, b0 + 3)):
            m = abs(complex(np.dot(d_pss, Y[bb:bb + PSS_NSC])))
            if m > best_ref[0]:
                best_ref = (m, float(df), int(bb))
    _, df_hat, b0 = best_ref
    rot = np.exp(-2j * np.pi * df_hat * n_t / FS)

    # SSS: SSB'nin 2. sembolu (PSS 0. sembol), AYNI altasiyici penceresi.
    # PSS'ten kanal kestirimi cikarilip 336 N_ID_1 adayi denenir.
    Yp = np.fft.fftshift(np.fft.fft(x[u_p:u_p + N_FFT] * rot))[b0:b0 + PSS_NSC]
    He = Yp * d_pss                               # PSS +-1 -> kanal kestirimi
    Sm = np.stack([sss_seq(i, n_id2) for i in range(336)])
    n_id1, sss_snr = None, 0.0
    dcp = CP_LONG - CP_NORM
    for du2 in (0, dcp, -dcp):                    # araya uzun CP girmis olabilir
        u2 = u_p + 2 * (N_FFT + CP_NORM) + du2
        if u2 < 0 or u2 + N_FFT > x.size:
            continue
        Ys = np.fft.fftshift(np.fft.fft(x[u2:u2 + N_FFT] * rot))
        Z = Ys[b0:b0 + PSS_NSC] * np.conj(He)     # kanal esitlenmis SSS
        met = np.abs(Sm @ Z)
        j = int(np.argmax(met))
        r = float(met[j] / (np.median(met) + 1e-30))
        if r > sss_snr:
            sss_snr, n_id1 = r, j
    if sss_snr < 3.0:
        n_id1 = None

    # SSB merkezi: PSS altasiyicisi 56'da baslar, SSB merkezi = altasiyici 120
    f_ssb = (CENTER_FREQ + (b0 - PSS_SC0 + SSB_NSC / 2 - N_FFT / 2) * SCS_HZ
             + df_hat)
    # Ayni N_ID_2 ile guclu diger tepeler -> SSB tekrar periyodu
    same = sorted(set(h[1] for h in hits
                      if h[0] > max(6.0, 0.5 * snr) and h[3] == n_id2))
    # Ardisik farklar DEGIL: cok huzmeli burst set'te onlarca PSS tepesi vardir
    # ve ardisik farklar huzmeler arasi araligi olcer, periyodu degil.
    per_ms, n_ok, n_tot = dominant_period_ms([t / FS for t in same],
                                             n_search / FS)

    out = dict(pci=(3 * n_id1 + n_id2) if n_id1 is not None else None,
               n_id1=n_id1, n_id2=n_id2, t0=s / FS, b0=b0, f_ssb=f_ssb,
               df_hat=df_hat, u_p=u_p,   # u_p: PSS sembolunun VERI baslangici

               snr_db=20 * np.log10(snr), sss_snr_db=20 * np.log10(sss_snr + 1e-30),
               hits=[h[1] / FS for h in hits if h[0] > 6.0], period_ms=per_ms)
    if not quiet:
        print(f"\n  HUCRE KIMLIGI")
        print(f"    N_ID_2 (PSS)  : {n_id2}      tepe/medyan {snr:.1f} "
              f"({out['snr_db']:+.1f} dB)")
        if n_id1 is not None:
            print(f"    N_ID_1 (SSS)  : {n_id1}    tepe/medyan {sss_snr:.1f}")
            print(f"    PCI           : {out['pci']}   (= 3*{n_id1} + {n_id2})")
        else:
            print(f"    N_ID_1 (SSS)  : okunamadi (en iyi tepe/medyan "
                  f"{sss_snr:.1f}, esik 3.0)")
        print(f"    izgara kaymasi: {df_hat/1e3:+.2f} kHz  (SSB senkron "
              f"rasterinde, tasiyici izgarasinda DEGIL)")
        print(f"    SSB merkezi   : {f_ssb/1e6:.3f} MHz  "
              f"(CENTER_FREQ {CENTER_FREQ/1e6:.3f} + {(f_ssb-CENTER_FREQ)/1e6:+.3f})")
        print(f"    SSB zamani    : PPS +{out['t0']*1e3:.4f} ms"
              + (f",  tekrar {per_ms:.0f} ms ({n_ok}/{n_tot} tepe)" if per_ms else
                 ",  tekrar periyodu okunamadi (pencereyi buyut)"))
        print(f"    PSS tepesi    : {len(same)} adet "
              f"(cok huzmeli SSB burst set ise normaldir)")
    return out

# ---------------------------------------------------------------- PBCH DMRS
def pbch_dmrs_seq(pci, i_ssb):
    """TS 38.211 7.4.1.4.1 — PBCH DMRS dizisi (144 QPSK).

    c_init = 2^11 (i_SSB+1) (floor(N_ID/4)+1) + 2^6 (i_SSB+1) + (N_ID mod 4)
    i_SSB, L_max=8 icin SSB indisinin 3 dusuk bitidir -> huzme kimligi."""
    c = ((1 << 11) * (i_ssb + 1) * ((pci >> 2) + 1)
         + (1 << 6) * (i_ssb + 1) + (pci & 3)) % (1 << 31)
    return gold_qpsk(c, PBCH_DMRS_N)

def pbch_dmrs_re(pci):
    """TS 38.211 Tablo 7.4.3.1-1 — PBCH DMRS'in SSB icindeki RE'leri.

    v = N_ID mod 4 kadar kaydirilir; dizi indisi once k sonra l artacak
    sekilde ilerler. Doner: [(sembol, altasiyicilar, dizi_dilimi), ...]"""
    v = pci % 4
    s1 = 4 * np.arange(60) + v
    s2 = np.concatenate([4 * np.arange(0, 12) + v, 4 * np.arange(48, 60) + v])
    s3 = 4 * np.arange(60) + v
    return [(1, s1, slice(0, 60)), (2, s2, slice(60, 84)), (3, s3, slice(84, 144))]

def _dmrs_metric(vals, ref, chunk=12):
    """Kanal duzlugune duyarsiz korelasyon: chunk icinde KOHERENT topla,
    chunk'lar arasinda GENLIK topla. Tam uyum -> 1.0, rastgele -> ~1/sqrt(chunk).

    Neden: 8.6 MHz'lik CORESET boyunca kanalin fazi doner; tek bir koherent
    toplam bunu yutar ve gercek DMRS bile kaybolur."""
    n = (len(vals) // chunk) * chunk
    if n == 0:
        return 0.0
    v = vals[:n] / (np.sqrt(np.mean(np.abs(vals[:n]) ** 2)) + 1e-30)
    z = (v * np.conj(ref[:n])).reshape(-1, chunk).sum(1)
    return float(np.sum(np.abs(z)) / n)

def _dmrs_metric_mat(V, R, chunk=12):
    """_dmrs_metric'in toplu hali. V:(nv,n) alinan, R:(nr,n) referans -> (nr,nv).

    Tarama 500 binden fazla kombinasyon deniyor; tek tek cagirmak numpy cagri
    masrafinda boguluyordu (olculdu: >2 dk). Vektorlestirilmis hali saniyeler."""
    n = (V.shape[1] // chunk) * chunk
    if n == 0:
        return np.zeros((R.shape[0], V.shape[0]))
    Vn = V[:, :n]
    Vn = Vn / (np.sqrt(np.mean(np.abs(Vn) ** 2, axis=1, keepdims=True)) + 1e-30)
    z = Vn[None, :, :] * np.conj(R[:, None, :n])
    z = z.reshape(R.shape[0], V.shape[0], n // chunk, chunk).sum(-1)
    return np.abs(z).sum(-1) / n

def ssb_pbch_check(x, cell, quiet=False):
    """SSB'yi STANDARDA GORE dogrula: PBCH DMRS korelasyonu -> i_SSB.

    Doner dict(i_ssb, metric, ratio, dcp) ya da None."""
    if cell is None or cell.get("pci") is None:
        return None
    pci, b_ssb = cell["pci"], cell["b0"] - PSS_SC0
    if b_ssb < 0 or b_ssb + SSB_NSC > N_FFT:
        return None
    rot = np.exp(-2j * np.pi * cell["df_hat"] * np.arange(N_FFT) / FS)
    refs = np.stack([pbch_dmrs_seq(pci, i) for i in range(L_MAX_FR1)])
    plan = pbch_dmrs_re(pci)
    best = None
    # SSB'nin ortasina uzun CP girmis olabilir -> iki hizalama denenir
    for dcp in (0, CP_LONG - CP_NORM):
        met = np.zeros(L_MAX_FR1)
        ok = True
        for sym, sc, sl in plan:
            u = cell["u_p"] + sym * (N_FFT + CP_NORM) + (dcp if sym >= 2 else 0)
            if u < 0 or u + N_FFT > x.size:
                ok = False
                break
            Y = np.fft.fftshift(np.fft.fft(x[u:u + N_FFT] * rot))
            v = Y[b_ssb:b_ssb + SSB_NSC][sc]
            for i in range(L_MAX_FR1):
                met[i] += _dmrs_metric(v, refs[i][sl])
        if not ok:
            continue
        met /= len(plan)
        j = int(np.argmax(met))
        rec = dict(i_ssb=j, metric=float(met[j]),
                   ratio=float(met[j] / (np.median(met) + 1e-30)), dcp=dcp)
        if best is None or rec["metric"] > best["metric"]:
            best = rec
    if best is not None and not quiet:
        print(f"    PBCH DMRS     : i_SSB={best['i_ssb']}  uyum {best['metric']:.3f} "
              f"(tepe/medyan {best['ratio']:.1f})"
              + ("   [OK] hucre STANDARDA GORE dogrulandi" if best["ratio"] > 1.8
                 else "   [ZAYIF] dogrulanamadi"))
    return best

def build_ssb(pci, i_ssb, n_fft=None):
    """STANDARDA GORE tek SSB (4 OFDM sembolu) uret — SADECE DOGRULAMA ICIN.

    Sahada referans URETILMEZ, --learn ile OGRENILIR. Bu fonksiyon PSS/SSS/PBCH
    DMRS zincirinin dogru yazildigini ispatlamak icindir: uretilen sinyali
    detect_cell + ssb_pbch_check'e verip PCI ve i_SSB'yi geri okuyabiliyorsak
    korelasyon tarafi da dogrudur."""
    n_fft = N_FFT if n_fft is None else n_fft
    n_id1, n_id2 = pci // 3, pci % 3
    G = np.zeros((SSB_SYMS, SSB_NSC), complex)
    G[0, PSS_SC0:PSS_SC0 + PSS_NSC] = pss_seq(n_id2)
    G[2, PSS_SC0:PSS_SC0 + PSS_NSC] = sss_seq(n_id1, n_id2)
    r = pbch_dmrs_seq(pci, i_ssb)
    for sym, sc, sl in pbch_dmrs_re(pci):
        G[sym, sc] = r[sl]
    # PBCH veri RE'leri: bilinmez -> rasgele QPSK (korelasyona girmez)
    rng = np.random.default_rng(1000 * pci + i_ssb)
    for sym in (1, 2, 3):
        free = np.where(G[sym] == 0)[0]
        if sym == 2:                      # SSS'in yani + korunan bosluklar
            free = free[(free < PSS_SC0 - 8) | (free >= PSS_SC0 + PSS_NSC + 8)]
        G[sym, free] = ((1 - 2 * rng.integers(0, 2, free.size))
                        + 1j * (1 - 2 * rng.integers(0, 2, free.size))) / np.sqrt(2)

    k0 = n_fft // 2 - SSB_NSC // 2
    out = np.zeros(SSB_SYMS * (n_fft + CP_NORM), complex)
    for i in range(SSB_SYMS):
        X = np.zeros(n_fft, complex)
        X[k0:k0 + SSB_NSC] = G[i]
        x = np.fft.ifft(np.fft.ifftshift(X)) * n_fft
        out[i * (n_fft + CP_NORM):(i + 1) * (n_fft + CP_NORM)] = \
            np.concatenate([x[-CP_NORM:], x])
    return out.astype(np.complex64)

# ------------------------------------------------- CORESET#0 / SIB1 DMRS
@functools.lru_cache(maxsize=4096)
def pdcch_dmrs_seq(pci, n_slot, l, n_rb):
    """TS 38.211 7.4.1.3.1 — PDCCH DMRS. CORESET#0'da N_ID = PCI.

    c_init = (2^17 (14 n_s + l + 1)(2 N_ID + 1) + 2 N_ID) mod 2^31
    RB basina 3 DMRS (k = 12n + 4m + 1). CORESET#0 icin referans nokta
    CORESET'in KENDI en dusuk RB'sidir (7.4.1.3.2) — mutlak CRB gerekmez."""
    c = (((1 << 17) * (NSYM_PER_SLOT * n_slot + l + 1) * (2 * pci + 1)
          + 2 * pci) % (1 << 31))
    return gold_qpsk(c, 3 * n_rb)

def pdsch_dmrs_seq(pci, n_slot, l, n_sym, n_scid=0):
    """TS 38.211 7.4.1.1.1 — PDSCH DMRS (SIB1: N_ID = PCI, n_SCID = 0).

    c_init = (2^17 (14 n_s + l + 1)(2 N_ID + 1) + 2 N_ID + n_SCID) mod 2^31
    Tip 1 haritalama: RB basina 6 DMRS (k = 4n + 2k' + delta)."""
    c = (((1 << 17) * (NSYM_PER_SLOT * n_slot + l + 1) * (2 * pci + 1)
          + 2 * pci + n_scid) % (1 << 31))
    return gold_qpsk(c, n_sym)

def coreset0_scan(x, cell, n_slot_hint=None, quiet=False):
    """CORESET#0'i STANDARDA GORE ara: Tablo 13-4 satirlari x PDCCH DMRS.

    SSB'nin bulundugu slotun +-2 slotu taranir; her aday sembol icin tablonun
    ongordugu frekans konumunda PDCCH DMRS korelasyonu hesaplanir. k_SSB
    (SSB'nin RB izgarasina gore altasiyici kaymasi) bilinmedigi icin frekans
    konumu +-12 altasiyici gevsetilir.

    Doner: en iyi eslesme dict'i ya da None."""
    if cell is None or cell.get("pci") is None:
        return None
    pci = cell["pci"]
    b_ssb = cell["b0"] - PSS_SC0                  # SSB'nin en dusuk altasiyicisi
    rot = np.exp(-2j * np.pi * cell["df_hat"] * np.arange(N_FFT) / FS)
    # SSB sembolunun mutlak zamani -> slot/sembol indisi (GPS hizali cerceve
    # varsayimi). Yanlissa slot ofseti taramasi bunu telafi eder.
    slot0 = int((cell["u_p"] / FS) // SLOT_DUR_S)

    # Sembol yerleri UZUN CP'yi hesaba katmali: 64 orneklik kayma 48 RB boyunca
    # ~4.7 rad faz egimi demektir ve DMRS korelasyonunu tamamen coker.
    cand = []                                     # (u, l_in_slot, slot)
    for ds in range(-2, 3):
        s_idx = slot0 + ds
        if s_idx < 0:
            continue
        offs = symbol_offsets(s_idx % SLOTS_PER_FRAME)
        for l, (_, u0, _) in enumerate(offs):
            u = s_idx * N_SLOT + u0
            if 0 <= u and u + N_FFT <= x.size:
                cand.append((u, l, s_idx % SLOTS_PER_FRAME))
    if not cand:
        return None

    # Slot indisi belirsizligi: cerceve PPS'e kilitli olmayabilir -> 20 slot
    # ofsetinin hepsi denenir (c_init sadece 14 n_s + l uzerinden girer).
    slots = (list(range(SLOTS_PER_FRAME)) if n_slot_hint is None
             else [n_slot_hint])
    # Referanslari ONCEDEN uret: (slot, sembol) ciftinin tamami 20x14 = 280
    # kombinasyon, her biri bir Gold dizisi. Tarama icinde uretmek olcum
    # suresini dakikalara cikariyordu.
    ref = {nrb: {sl: np.stack([pdcch_dmrs_seq(pci, sl, ll, nrb)
                               for ll in range(NSYM_PER_SLOT)])
                 for sl in slots}
           for nrb in sorted({r[1] for r in CORESET0_TABLE_13_4})}
    dks = np.arange(-12, 13)
    best = None
    for u, l, ns in cand:
        Y = np.fft.fftshift(np.fft.fft(x[u:u + N_FFT] * rot))
        for mux, n_rb, n_symb, off in CORESET0_TABLE_13_4:
            base = b_ssb - off * NSC_PER_RB
            rel = (NSC_PER_RB * np.repeat(np.arange(n_rb), 3)
                   + 4 * np.tile(np.arange(3), n_rb) + 1)
            idx = base + dks[:, None] + rel[None, :]          # (ndk, 3*n_rb)
            keep = (idx[:, 0] >= 0) & (idx[:, -1] < N_FFT)
            if not keep.any():
                continue
            idx, dk_ok = idx[keep], dks[keep]
            V = Y[idx]                                         # (ndk, 3*n_rb)
            R = np.stack([ref[n_rb][sl][l] for sl in slots])    # (nslot, 3*n_rb)
            M = _dmrs_metric_mat(V, R)                         # (nslot, ndk)
            j = np.unravel_index(int(np.argmax(M)), M.shape)
            if best is None or M[j] > best["metric"]:
                k0 = int(base + dk_ok[j[1]])
                best = dict(metric=float(M[j]), n_rb=n_rb, n_symb=n_symb,
                            offset=off, mux=mux, l=l, n_slot=slots[j[0]],
                            k0=k0, u=u, slot_abs=u // N_SLOT,
                            f_lo=CENTER_FREQ + (k0 - N_FFT / 2) * SCS_HZ)
    if best is None:
        return None

    # --- CORESET'in SEMBOL ARALIGINI coz ---
    # argmax'in sectigi sembolu "ilk sembol" saymak YANLIS: 3 sembollik bir
    # CORESET'te ucu de ayni olcude korele olur ve argmax sonuncuyu secebilir.
    # O zaman SIB1 aramasi CORESET'in OTESINDEN baslar ve SIB1'i kacirir
    # (olculdu: 24 RB x 3 sembolde SIB1 sembol 3'te, arama 4'ten basliyordu).
    # Bu yuzden ayni k0'da butun slot taranip BITISIK kosu bulunur.
    s_abs, n_rb, k0 = best["slot_abs"], best["n_rb"], best["k0"]
    offs_g = symbol_offsets(s_abs % SLOTS_PER_FRAME)
    idxk = k0 + (NSC_PER_RB * np.repeat(np.arange(n_rb), 3)
                 + 4 * np.tile(np.arange(3), n_rb) + 1)
    mets = np.zeros(NSYM_PER_SLOT)
    for l in range(NSYM_PER_SLOT):
        u = s_abs * N_SLOT + offs_g[l][1]
        if u + N_FFT > x.size:
            continue
        Y = np.fft.fftshift(np.fft.fft(x[u:u + N_FFT] * rot))
        mets[l] = _dmrs_metric(Y[idxk], pdcch_dmrs_seq(pci, best["n_slot"], l, n_rb))
    on = mets > max(0.45, 0.6 * mets.max())
    l0 = l1 = int(np.argmax(mets))
    while l0 > 0 and on[l0 - 1]:
        l0 -= 1
    while l1 + 1 < NSYM_PER_SLOT and on[l1 + 1]:
        l1 += 1
    best["l"] = l0
    best["n_symb"] = int(min(3, l1 - l0 + 1))
    best["sym_metric"] = mets
    # Nominal "offset" dejenere: base = b_ssb - off*12 ve dk +-12 birbirini
    # yutar (off=2,dk=-12 ile off=1,dk=0 ayni k0'i verir). Gercek olan k0'dir.
    best["offset"] = (b_ssb - k0) / NSC_PER_RB
    best["in_table"] = any(r[1] == n_rb and r[2] == best["n_symb"]
                           and abs(r[3] - best["offset"]) < 0.5
                           for r in CORESET0_TABLE_13_4)
    if not quiet:
        good = best["metric"] > 0.45
        print(f"    CORESET#0     : {'BULUNDU' if good else 'bulunamadi'}  "
              f"uyum {best['metric']:.3f}"
              + (f"  -> {n_rb} RB x {best['n_symb']} sembol, offset "
                 f"{best['offset']:.2f} RB, slot {best['n_slot']} sembol "
                 f"{l0}, {best['f_lo']/1e6:.2f} MHz'den itibaren"
                 f"{'' if best['in_table'] else '  [Tablo 13-4 disi]'}"
                 if good else "  (SIB1 yayini goremedik)"))
    return best

def sib1_check(x, cell, cs0, quiet=False):
    """SIB1 PDSCH DMRS'i (TS 38.211 7.4.1.1.1) CORESET#0 bolgesinde ara.

    SIB1 ayni ilk BWP'de ve CORESET#0'i takip eden sembollerde tasinir; tam
    tahsis DCI'de oldugu icin frekansta CORESET#0 acikligi, zamanda sonraki
    birkac sembol taranir. Tip 1 DMRS: RB basina 6 RE (cift altasiyicilar)."""
    if cs0 is None or cell is None or cell.get("pci") is None:
        return None
    pci, n_rb, k0 = cell["pci"], cs0["n_rb"], cs0["k0"]
    rot = np.exp(-2j * np.pi * cell["df_hat"] * np.arange(N_FFT) / FS)
    n_re = 6 * n_rb
    s_abs = cs0["slot_abs"]
    offs = symbol_offsets(s_abs % SLOTS_PER_FRAME)   # uzun CP dahil
    best = None
    l_beg = cs0["l"] + cs0["n_symb"]                 # CORESET'in HEMEN ardindan
    if l_beg >= NSYM_PER_SLOT:
        if not quiet:
            print(f"    SIB1 PDSCH    : aranamadi — CORESET#0 slotun son "
                  f"sembolunde ({cs0['l']}), ardinda yer yok")
        return None
    for l in range(l_beg, min(NSYM_PER_SLOT, l_beg + 6)):
        u = s_abs * N_SLOT + offs[l][1]
        if u + N_FFT > x.size:
            continue
        Y = np.fft.fftshift(np.fft.fft(x[u:u + N_FFT] * rot))
        for dk in (0, 1):                       # delta = 0 ya da 1 (port/CDM)
            idx = k0 + dk + 2 * np.arange(n_re)
            if idx[-1] >= N_FFT:
                continue
            v = Y[idx]
            m = _dmrs_metric(v, pdsch_dmrs_seq(pci, cs0["n_slot"], l, n_re))
            if best is None or m > best["metric"]:
                best = dict(metric=float(m), l=l, delta=dk)
    if best is not None and not quiet:
        good = best["metric"] > 0.45
        print(f"    SIB1 PDSCH    : {'BULUNDU' if good else 'bulunamadi'}  "
              f"uyum {best['metric']:.3f}"
              + (f"  (sembol {best['l']}, delta {best['delta']})" if good else ""))
    return best

# ------------------------------------------------------- frekans sapmasi
def cfo_cp(x, max_ms=20.0):
    """CP korelasyonu fazindan frekans ofseti. Doner dict(df, sd, n, anchor).

    DIKKAT — bu MUTLAK bir osilator hatasi DEGILDIR: olculen sey, sinyalin
    altasiyici izgarasinin bizim FFT izgaramizdan sapmasidir ve icinde LO'yu
    nereye koydugumuzdan gelen SABIT bir terim vardir (ornek: LO'yu 3520'ye
    alip 3470'teki blogu bakarsak -50 MHz kayma 30 kHz'in tam kati olmadigi
    icin ~10 kHz'lik sahte bir "sapma" gorunur). Osilator karsilastirmasi
    IKI BLOGUN FARKI uzerinden yapilmalidir — bkz. cells_verdict.

    y(s) = sum_{i<CP} x[s+i] conj(x[s+i+N_FFT]); CP son N_FFT orneginin kopyasi
    oldugu icin sembol basinda tepe yapar ve fazi -2 pi df N_FFT/FS olur
    (Van de Beek). Belirsiz olmayan aralik +-FS/(2 N_FFT) = +-15 kHz.

    Sembol yerlerini GENLIGE gore aramayiz: kuvvetli bir SSB huzmesi varken
    esik butun normal sembolleri eler (olculdu: 560 sembolden 5'i kalir). Bunun
    yerine NR sembol izgarasi (uzun CP'ler dahil, 1 ms'de 28 sembol) DOGRUDAN
    kurulur ve sadece izgaranin BASLANGIC FAZI aranir — boylece butun semboller
    koherent toplanir ve uzun CP'nin yarattigi kayma da dogru modellenir."""
    n = int(min(x.size, max_ms * 1e-3 * FS))
    if n < 20 * (N_FFT + CP_LONG):
        return None
    m = n - N_FFT - CP_NORM
    if m < 4 * (N_FFT + CP_LONG):
        return None
    prod = (x[:m + CP_NORM] * np.conj(x[N_FFT:N_FFT + m + CP_NORM])).astype(np.complex128)
    cs = np.concatenate([[0j], np.cumsum(prod)])
    y = cs[CP_NORM:CP_NORM + m] - cs[:m]            # y[s], s = 0..m-1

    # Bir alt cercevenin (1 ms = 28 sembol) sembol baslangiclari
    off, t = [], 0
    for l in range(NSYM_PER_SLOT * SLOTS_PER_SF):
        off.append(t)
        t += (CP_LONG if l in LONG_CP_SYMS_IN_SF else CP_NORM) + N_FFT
    sf_len = t                                       # 122880 = 1 ms
    grid = (np.arange(m // sf_len + 1)[:, None] * sf_len
            + np.array(off)[None, :]).ravel()

    def _sum(a):
        idx = grid + a
        idx = idx[idx < m]
        return (y[idx].sum(), idx) if idx.size >= 8 else (0j, idx)

    per = N_FFT + CP_NORM
    a_best = max(range(0, per, 8), key=lambda a: abs(_sum(a)[0]))
    a_best = max(range(max(0, a_best - 8), a_best + 9),
                 key=lambda a: abs(_sum(a)[0]))
    z, idx = _sum(a_best)
    if idx.size < 8 or abs(z) <= 0:
        return None
    # a conj(b) = |s|^2 e^{-j w N_FFT} -> acinin isareti TERS, bastaki eksi bunu duzeltir
    df = -float(np.angle(z)) * FS / (2 * np.pi * N_FFT)
    # BELIRSIZLIK: sembol basina acisal sacilmadan HESAPLAMA. TDD'de sembollerin
    # buyuk kismi bos ve fazlari rasgele; bu, gercek dogruluk 1 Hz iken +-300 Hz
    # gibi anlamsiz bir sayi uretiyordu. Bunun yerine semboller gruplara
    # bolunup gruplarin KENDI ARALARINDAKI sacilmasi kullanilir.
    ng = 8
    dfs = []
    for g in np.array_split(idx, ng):
        zz = y[g].sum()
        if abs(zz) > 0:
            dfs.append(-np.angle(zz) * FS / (2 * np.pi * N_FFT))
    sd = (float(np.std(dfs)) / np.sqrt(len(dfs)) if len(dfs) > 1
          else abs(df)) * (2 * np.pi * N_FFT) / FS
    # KOHERANS: |toplam| / toplam|.|  — 1'e yakin = temiz OFDM, 0'a yakin =
    # olcum gurultuden ibaret. Karar bu sayiya bakmali.
    coh = float(abs(z) / (np.abs(y[idx]).sum() + 1e-30))
    # anchor = OFDM sembol izgarasinin PPS'e gore fazi [ornek]. Ayni RU'dan
    # cikan iki tasiyicida BIREBIR ayni olur; ayri siteden gelende yol farki
    # kadar kayar. SSB t0'indan daha saglam bir zaman kiyasi (huzme indisinden
    # etkilenmez).
    return dict(df=df, sd=sd * FS / (2 * np.pi * N_FFT), n=int(idx.size),
                anchor=int(a_best), coh=coh)



# ===================================================================
#  KABLOLU KALIBRASYON (splitter)
# ===================================================================

def _wcal_prompt(msg):
    """Kablo degisimi icin bekle. Program BURADA beklerken LO'lar sabit kalir —
    tek oturum ilkesinin dayandigi nokta budur."""
    print("\n" + "*" * 70)
    for line in msg.split("\n"):
        print(f" *  {line}")
    print("*" * 70)
    input(" Hazir olunca ENTER'a bas (iptal icin Ctrl+C)... ")

def wcal_accum(buf, nfft, acc=None):
    """Capraz/oto spektrumlari biriktir.
      num (N_RX,nfft) = sum S_k conj(S_0),  den = sum |S_0|^2,
      pwr (N_RX,nfft) = sum |S_k|^2  (koherans icin)"""
    buf = np.atleast_2d(buf)
    if acc is None:
        acc = dict(num=np.zeros((N_RX, nfft), np.complex128),
                   den=np.zeros(nfft, np.float64),
                   pwr=np.zeros((N_RX, nfft), np.float64), nblk=0)
    for i in range(buf.shape[1] // nfft):
        S = np.fft.fft(buf[:, i * nfft:(i + 1) * nfft].astype(np.complex128), axis=1)
        acc["num"] += S * np.conj(S[0])[None, :]
        acc["den"] += np.abs(S[0]) ** 2
        acc["pwr"] += np.abs(S) ** 2
        acc["nblk"] += 1
    return acc

def wcal_band(den, fs, nfft):
    """Chirp'in doldurdugu binler. Gurultu tabani icin medyan DEGIL %10 dilim
    (chirp binlerin cogunu doldurur, medyan sinyalin ICINE duser).

    Kalibrasyon SADECE olcumun kullandigi banda (3480-3580) cozulur. TX bilerek
    daha genis suepuerur (110 MHz) ki Tukey eteginin yumusadigi kenarlar kanalin
    DISINDA kalsin; o etek bolgesini kalibrasyona katmak, hic kullanilmayacak
    ve 29 dB daha zayif binlere kisa-FIR uydurmak demektir.
    Taban TUM pencereden, secim KANAL ICINDEN (bkz. _wb_band_edges ayni desen)."""
    Ps = np.fft.fftshift(den)
    dc = nfft // 2
    ndc = max(2, int(round(0.2e6 / (fs / nfft))))
    keep = np.ones(nfft, bool)
    keep[dc - ndc:dc + ndc + 1] = False
    inb = band_limit_mask(nfft)
    keep_ch = keep & inb
    if keep_ch.sum() < 16:
        keep_ch = keep
    Pdb = 10 * np.log10(Ps / (Ps[keep_ch].max() + 1e-30) + 1e-30)
    floor_db = float(np.percentile(Pdb[keep], 10))     # taban: TUM pencere
    occ = keep_ch & (Pdb > floor_db + WCAL_OCC_DB)     # secim: KANAL ICI
    if occ.sum() < 16:
        return None, 0.0, 0.0, floor_db
    idx = np.flatnonzero(occ)
    a, b = int(idx[0]), int(idx[-1] + 1)
    ms = np.zeros(nfft, bool)
    ms[a:b] = True
    ms &= inb                                          # kanal disina TASMASIN
    ms[dc - ndc:dc + ndc + 1] = False
    df = fs / nfft
    return np.fft.ifftshift(ms), (a - dc) * df, (b - 1 - dc) * df, floor_db

def wcal_solve(acc, fs, ng=WCAL_NG):
    """H_k(f) = <S_k conj(S_0)>/<|S_0|^2>. Splitter'da GEOMETRIK FAZ YOKTUR —
    dort kanala giren sinyal ayni oldugu icin H dogrudan g_k(f)/g_0(f)'tir.
    (wb_los_eq'in exp(-j2pi f (D_k-D_0)/c) terimi burada 1'dir; iste LOS'tan
    kalibrasyona gore temel fark budur: hicbir geometri varsayimi girmez.)

    Kapi yerine agirlikli LS: bant sinirli H'nin IFFT'sini kesmek bant kenarinda
    Gibbs birakir; LS ayni tap sayisiyla bant ICINDE en iyi uyumu verir."""
    num, den, pwr = acc["num"], acc["den"], acc["pwr"]
    nfft = den.size
    mask, f_lo, f_hi, floor_db = wcal_band(den, fs, nfft)
    if mask is None:
        return None
    idx = np.flatnonzero(mask)
    H = num[:, idx] / (den[idx][None, :] + 1e-30)
    coh = np.abs(num[:, idx]) ** 2 / (pwr[:, idx] * den[idx][None, :] + 1e-30)

    w = den[idx] / (den[idx].max() + 1e-30)
    t = np.arange(-ng, ng + 1)
    E = np.exp(-2j * np.pi * np.outer(idx.astype(np.float64), t) / nfft)
    G = E.conj().T @ (w[:, None] * E)
    G += (1e-8 * np.trace(G).real / len(t)) * np.eye(len(t))
    B = E.conj().T @ (w[None, :] * H).T
    taps = np.linalg.solve(G, B).T
    Eall = np.exp(-2j * np.pi *
                  np.outer(np.arange(nfft, dtype=np.float64), t) / nfft)
    EQ = (Eall @ taps.T).T.astype(np.complex64)

    fb = np.fft.fftfreq(nfft, 1.0 / fs)[idx]
    order = np.argsort(fb)
    amp_db = 20 * np.log10(np.abs(EQ[:, idx]) + 1e-30)
    gd_ns = np.zeros(N_RX)
    for k in range(N_RX):
        ph = np.unwrap(np.angle(EQ[k, idx][order]))
        p = np.polyfit(fb[order], ph, 1, w=np.sqrt(w[order]))
        gd_ns[k] = -p[0] / (2 * np.pi) * 1e9
    ph_deg = np.degrees(np.angle(np.sum(EQ[:, idx] * w[None, :], axis=1)))
    resid = H - EQ[:, idx]
    fit_db = 20 * np.log10(
        np.sqrt(np.average(np.abs(resid) ** 2, axis=1, weights=w)) /
        np.sqrt(np.average(np.abs(H) ** 2, axis=1, weights=w)) + 1e-30)
    # Koherans ozeti GUC AGIRLIKLI ortalamadir, en kucuk bin DEGIL: bant
    # kenarinda chirp'in gucu zaten dusuktur ve koherans orada her zaman duser.
    coh_w = np.sum(coh * w[None, :], axis=1) / (np.sum(w) + 1e-30)
    return dict(taps=taps, EQ=EQ, mask=mask, nfft=nfft, fs=fs, ng=ng,
                f_lo=f_lo, f_hi=f_hi, floor_db=floor_db, nblk=acc["nblk"],
                coh=coh_w, coh_lo=np.percentile(coh, 10, axis=1),
                amp_db=amp_db.mean(axis=1), amp_rip=amp_db.std(axis=1),
                gd_ns=gd_ns, ph_deg=ph_deg, fit_db=fit_db)

def wcal_levels(buf):
    """Kirpma/zayiflik kontrolu. Kirpma olcutu I ve Q'ya AYRI bakar: kirpma
    I/Q'da olur, |z| kirpikken sqrt(2)=+3 dB'e cikar ve kompleks genlige bakan
    bir esik onu kacirir. Doner bool."""
    pk = float(max(np.abs(buf.real).max(), np.abs(buf.imag).max()))
    av = 10 * np.log10((np.abs(buf) ** 2).mean() + 1e-30)
    per_ch = [float(max(np.abs(buf[k].real).max(), np.abs(buf[k].imag).max()))
              for k in range(buf.shape[0])]
    print(f"  seviye      : tepe {20*np.log10(pk+1e-30):+.1f} dBFS, "
          f"ort {av:+.1f} dBFS")
    print(f"  kanal tepe  : " +
          "  ".join(f"k{k}:{20*np.log10(p+1e-30):+.1f}" for k, p in enumerate(per_ch)))
    if pk > WCAL_PEAK_MAX:
        print("  [KRITIK] KIRPMA. TX kazancini dusur ya da zayiflatici ekle.")
        return False
    if pk < WCAL_PEAK_MIN:
        print("  [KRITIK] sinyal cok zayif. TX kazancini artir / zayiflatici azalt.")
        print("           TX gercekten yayinda mi (obur terminal)?")
        return False
    spread = 20 * np.log10((max(per_ch) + 1e-30) / (min(per_ch) + 1e-30))
    if spread > 6.0:
        print(f"  [UYARI] kanallar arasi seviye farki {spread:.1f} dB — "
              f"bir splitter portu/kablo zayif olabilir.")
    return True

def wcal_report(sol):
    """Sonucu bas ve kabul edilebilir mi karar ver. Doner bool."""
    print("\n" + "=" * 70)
    print(" KABLOLU KALIBRASYON — SONUC")
    print("=" * 70)
    print(f"  islenen blok : {sol['nblk']} x {sol['nfft']} ornek "
          f"({sol['nblk']*sol['nfft']/sol['fs']*1e3:.0f} ms)")
    print(f"  chirp bandi  : {(CENTER_FREQ+sol['f_lo'])/1e6:.3f} .. "
          f"{(CENTER_FREQ+sol['f_hi'])/1e6:.3f} MHz  "
          f"({(sol['f_hi']-sol['f_lo'])/1e6:.2f} MHz, taban {sol['floor_db']:+.1f} dB)")
    print(f"\n  {'kanal':>6} {'genlik[dB]':>11} {'dalga[dB]':>10} {'faz[der]':>9} "
          f"{'grup gec.[ns]':>14} {'koherans':>9} {'FIR artik':>11}")
    for k in range(N_RX):
        print(f"  {k:>6} {sol['amp_db'][k]:>+11.2f} {sol['amp_rip'][k]:>10.2f} "
              f"{sol['ph_deg'][k]:>+9.2f} {sol['gd_ns'][k]:>+14.3f} "
              f"{sol['coh'][k]:>9.4f} {sol['fit_db'][k]:>+8.1f} dB"
              + ("   <- referans" if k == 0 else ""))
    print(f"\n  'dalga' = genligin bant boyunca standart sapmasi. Sifirdan farkliysa")
    print(f"  TEK bir kompleks katsayi bu kanali duzeltemez.")

    ok = True
    worst = float(np.min(sol["coh"][1:])) if N_RX > 1 else 1.0
    if worst < WCAL_COH_MIN:
        ok = False
        print(f"\n  [KRITIK] en dusuk koherans {worst:.4f} (< {WCAL_COH_MIN}).")
        print(f"     Kabloda ~0.999 beklenir. Olasi sebepler:")
        print(f"       * ADC kirpiyor  * splitter portu/kablo takili degil")
        print(f"       * sinyal cok zayif  * TX yayinda degil")
    else:
        print(f"\n  Koherans iyi (en dusuk {worst:.4f}) — dort kanal da ayni "
              f"sinyali goruyor.")
    gd_span = float(np.ptp(sol["gd_ns"]))
    if gd_span > WCAL_NG / sol["fs"] * 1e9 * 0.7:
        ok = False
        print(f"  [KRITIK] grup gecikmesi yayilimi {gd_span:.1f} ns, FIR "
              f"penceresine ({WCAL_NG/sol['fs']*1e9:.1f} ns) sigmiyor.")
    return ok

def wcal_eq(nfft):
    """Kablolu kalibrasyonu istenen FFT izgarasinda equalizer sozlugune cevir.
    locate_live/range_diag'in bekledigi bicimde doner. _WCAL yoksa None."""
    if _WCAL is None:
        return None
    EQ, inv = eq_from_taps(_WCAL["taps"], nfft)
    return dict(EQ=EQ, inv=inv, gate=(_WCAL["taps"].shape[1] - 1) // 2,
                med=np.ones(N_RX), rms_db=np.zeros(N_RX), rms_deg=np.zeros(N_RX))



# ===================================================================
#  HAVADAN KALIBRASYON (horn) — chirp ayiklama ve dogrulama
# ===================================================================

def ocal_chirp_ref(fs=None):
    """TX'in bastigi chirp'i ALICI ornekleme hizinda yeniden uret.

    TX 245.76 MHz'te 24576 ornek uretiyor; alici 122.88 MHz'te ayni 100 us
    12288 ornege denk gelir. Tukey etegi ve egim birebir ayni tutulur, yoksa
    uyumlu filtre tepesi yayilir."""
    fs = FS if fs is None else float(fs)
    n_tx = int(round(OCAL_TX_RATE * OCAL_CHIRP_DUR))
    n_tx -= n_tx % 2                      # TX'teki kelime hizalamasi
    period = n_tx / OCAL_TX_RATE          # gercek periyot (TX'teki ile ayni)
    n = int(round(fs * period))
    slope = OCAL_CHIRP_BW / period
    t = np.arange(n) / fs - period / 2.0
    a = OCAL_CHIRP_ALPHA
    w = np.ones(n)
    m = int(a * n / 2)
    if m > 0:
        w[:m] = 0.5 * (1 - np.cos(np.pi * np.arange(m) / m))
        w[-m:] = w[:m][::-1]
    sig = np.exp(1j * np.pi * slope * t ** 2) * w
    # Alici bandi disini isleme sokmuyoruz -> referans da ayni bantta olmali
    sig = band_limit_sig(sig.astype(np.complex64))
    return sig.astype(np.complex64), n, period

def ocal_epoch(x, ref, n_per):
    """Uyumlu filtre ile chirp baslangicini bul + PRF tutarliligini dogrula.

    Doner (epoch, tepe/yan orani [dB], tutarlilik 0..1) ya da (None, ...)."""
    n_use = int(min(len(x), 40 * n_per))
    nf = 1 << int(np.ceil(np.log2(n_use + len(ref))))
    C = np.fft.ifft(np.fft.fft(x[:n_use], nf) * np.conj(np.fft.fft(ref, nf)))
    P = np.abs(C[:n_use]) ** 2
    # Periyoda katla: gercek chirp her periyotta AYNI gecikmede tepe yapar
    nrep = n_use // n_per
    if nrep < 4:
        return None, 0.0, 0.0
    F = P[:nrep * n_per].reshape(nrep, n_per).sum(0)
    ep = int(np.argmax(F))
    # tepe/yan: ana lobun disindaki en buyuk deger
    g = max(4, int(0.002 * n_per))
    m = np.ones(n_per, bool)
    m[max(0, ep - g):ep + g + 1] = False
    pk_db = 10 * np.log10(F[ep] / (np.median(F[m]) + 1e-30) + 1e-30)
    # Tutarlilik: her periyotta tepe AYNI yerde mi?
    idx = np.argmax(P[:nrep * n_per].reshape(nrep, n_per), axis=1)
    hit = float(np.mean(np.abs((idx - ep + n_per // 2) % n_per - n_per // 2) <= g))
    return ep, float(pk_db), hit

def ocal_fold(buf, epoch, n_per, ref=None, n_grp=OCAL_N_GRP, n_max=1024):
    """Chirp periyoduna katla — HER CHIRP AYRI HIZALANARAK.

    TX (N321) ve RX (X410) AYRI SAATLERDE calisiyor (TX'te clock_source yok,
    dahili TCXO). Sonuclari:
      * ornekleme farki: chirp periyodu alicida tam n_per ornek DEGIL. 2 ppm
        icin 1000 chirp'te 24.6 ornek kayma olur. 110 MHz chirp'te 1 ornek
        kayma bant kenarinda 2.8 rad faz egimi demek — ham katlama COKER.
      * tasiyici ofseti: 2 ppm -> 7.1 kHz, 100 us'de 254 derece. Chirp'ten
        chirp'e faz tutmaz.
    COZUM: her chirp icin KANAL 0'dan gecikme (alt-ornek) ve faz olculur,
    ayni duzeltme DORT KANALA DA uygulanir. Ortak terim gittigi icin katlama
    koherent olur; kanallar arasi fark — yani olcmek istedigimiz sey — aynen
    kalir cunku duzeltme hepsine ayni uygulanir."""
    buf = np.atleast_2d(buf)
    n_av = (buf.shape[1] - epoch) // n_per
    if n_av < n_grp * 2:
        return None, 0
    if n_av > n_max:                     # cok fazlasi gereksiz; hiz icin kirp
        n_av = n_max
    n_av -= n_av % n_grp
    per_grp = n_av // n_grp
    f = np.fft.fftfreq(n_per, 1.0 / FS)
    R = np.conj(np.fft.fft(ref, n_per)) if ref is not None else None
    out = np.zeros((N_RX, n_grp, n_per), np.complex128)
    # TOPLU ISLEME: chirp'ler tek tek degil, YIGIN halinde FFT'lenir. Ayni
    # islemler, ayni sonuc — ama 1024 kucuk FFT yerine birkac buyuk yigin.
    # (v1'de dongu vardi ve her FFT GPU esiginin altinda kaliyordu.)
    seg_all = buf[:, epoch:epoch + n_av * n_per].reshape(N_RX, n_av, n_per)
    cp = gpu_mod()
    # GPU'DA KALARAK isle: her adimda gidip gelmek aktarim masrafinda bogar
    # (olculdu: FFT 2.2 ms, aktarimla 22.6 ms). Veri zaten complex64 geliyor;
    # complex128'e cikarmak T1000'de FFT'yi 7 kat yavaslatiyordu.
    xp = cp if cp is not None else np
    Rg = xp.asarray(R) if R is not None else None
    fg = xp.asarray(f)
    for c0 in range(0, n_av, OCAL_CHUNK):
        c1 = min(c0 + OCAL_CHUNK, n_av)
        blk = xp.asarray(seg_all[:, c0:c1, :])
        X = xp.fft.fft(blk, n_per, axis=2)
        if Rg is not None:
            cc = xp.fft.ifft(X[0] * Rg[None, :], axis=1)
            ac = xp.abs(cc)
            i0 = xp.argmax(ac, axis=1)
            k = xp.arange(i0.size)
            y0 = ac[k, (i0 - 1) % n_per]
            y1 = ac[k, i0]
            y2 = ac[k, (i0 + 1) % n_per]
            den = y0 - 2 * y1 + y2
            frac = xp.where(xp.abs(den) > 1e-30, 0.5 * (y0 - y2) / den, 0.0)
            d = i0 + xp.clip(frac, -0.5, 0.5)
            d = xp.where(d > n_per / 2, d - n_per, d)
            ph = xp.angle(cc[k, i0])
            corr = (xp.exp(2j * xp.pi * xp.outer(d, fg) / FS)
                    * xp.exp(-1j * ph)[:, None])
            X = X * corr[None, :, :]
        # grup toplama: chirp j -> grup (c0+j) % n_grp. Yigin n_grp'nin kati
        # secilirse dilimleme ile maskesiz yapilir (maskeleme kopya uretiyordu).
        for g in range(n_grp):
            j0 = (g - c0) % n_grp
            if j0 < (c1 - c0):
                out[:, g, :] += (X[:, j0::n_grp, :].sum(axis=1) if cp is None
                                 else cp.asnumpy(X[:, j0::n_grp, :].sum(axis=1)))
    out /= per_grp
    return out.astype(np.complex64), per_grp

def ocal_accum_clean(buf, ref, n_per, acc=None, n_grp=OCAL_N_GRP):
    """Chirp'i ayikla ve TEMIZ veriden capraz spektrum biriktir.

    wcal_accum ile ayni sozlugu doldurur, ama ham yakalama yerine periyoda
    katlanmis (hucreden arindirilmis) veriyi kullanir."""
    x0 = np.atleast_2d(buf)[0]
    ep, pk_db, hit = ocal_epoch(x0, ref, n_per)
    if ep is None:
        return acc, None
    folded, per_grp = ocal_fold(buf, ep, n_per, ref=ref, n_grp=n_grp)
    if folded is None:
        return acc, None
    if acc is None:
        acc = dict(num=np.zeros((N_RX, n_per), np.complex128),
                   den=np.zeros(n_per, np.float64),
                   pwr=np.zeros((N_RX, n_per), np.float64), nblk=0)
    for g in range(folded.shape[1]):
        S = folded[:, g, :].astype(np.complex128)   # ocal_fold FREKANS doner
        acc["num"] += S * np.conj(S[0])[None, :]
        acc["den"] += np.abs(S[0]) ** 2
        acc["pwr"] += np.abs(S) ** 2
        acc["nblk"] += 1
    return acc, dict(epoch=ep, pk_db=pk_db, hit=hit, per_grp=per_grp)

def ocal_curvature_deg(R_m):
    """Horn R metrede iken kuresel cephenin uc elemanda yarattigi faz hatasi.

    Duzlem dalga varsayimi yaklasiktir: kenardaki eleman merkeze gore
    y^2/(2R) kadar fazla yol alir (y = aciklik/2). Bu hata DOGRUDAN
    kalibrasyona girer ve sonra butun acilari bozar."""
    y = (N_RX - 1) / 2.0 * ARRAY_D_M
    lam = C_AIR / CENTER_FREQ
    return float(np.degrees(2 * np.pi * (y * y / (2.0 * max(R_m, 1e-3))) / lam))

def phase_to_angle_deg(ph_deg):
    """Elemanlar arasi faz rampasindan gelis acisi [derece].

    Rampa en kucuk kareler ile uydurulur (tek bir cifte bakmak gurultulu).
    d sin(th) = (dphi/2pi) * lambda."""
    lam = C_AIR / CENTER_FREQ
    k = np.arange(N_RX, dtype=float)
    ph = np.unwrap(np.radians(np.asarray(ph_deg, float)))
    slope = float(np.polyfit(k, ph, 1)[0])            # rad / eleman
    sin_th = slope * lam / (2 * np.pi * ARRAY_D_M) * ARRAY_ORDER_SIGN
    if abs(sin_th) > 1.0:
        return float("nan"), sin_th
    return float(np.degrees(np.arcsin(sin_th))), sin_th

def ocal_vector(acc, fs):
    """Bir birikimden KALIBRE EDILMIS kanal vektoru (N_RX,) kompleks.

    wcal_solve bant ici genlik/faz verir; kalibrasyon (_WCAL) bolunerek
    donanim cikarilir. Geriye sadece GELIS ACISININ yarattigi faz kalir."""
    sol = wcal_solve(acc, fs)
    if sol is None:
        return None, None
    v = (10.0 ** (np.asarray(sol["amp_db"], float) / 20.0)
         * np.exp(1j * np.radians(np.asarray(sol["ph_deg"], float))))
    if _WCAL is not None:
        w = (10.0 ** (np.asarray(_WCAL["amp_db"], float) / 20.0)
             * np.exp(1j * np.radians(np.asarray(_WCAL["ph_deg"], float))))
        v = v / (w + 1e-30)
    return v.astype(np.complex128), sol

def beam_spectrum(v, angles_deg):
    """Klasik huzme olusturucu cikisi P(theta) — dizinin acisal tepkisi."""
    lam = C_AIR / CENTER_FREQ
    pos = np.arange(N_RX) * ARRAY_D_M * ARRAY_ORDER_SIGN
    A = np.exp(2j * np.pi * np.outer(np.sin(np.radians(angles_deg)), pos) / lam)
    return np.abs(A @ np.conj(v)) ** 2

def ocal_verify_live(ctx, n_per=1, amax=60.0):
    """CANLI ACI TAKIBI — horn'u saga sola oynat, tepe seninle gelsin.

    Sabit bir aciya koyup tek sayi okumaktan daha iyi bir sinamadir:
      * tepe horn ile AYNI YONDE hareket etmeli (ters ise ARRAY_ORDER_SIGN),
      * 0 dereceye getirdiginde tepe 0'da olmali (ofset varsa hiza hatasi),
      * hareket duzgun ve simetrik olmali (atlamalar = faz sarmasi/zayif SNR).
    Pencere kapatilinca olcume devam edilir."""
    import matplotlib.pyplot as plt
    ang = np.linspace(-amax, amax, 361)
    hist_t, hist_a = [], []

    plt.ion()
    fig, (axp, axt) = plt.subplots(2, 1, figsize=(9, 7.2),
                                   gridspec_kw=dict(height_ratios=[1.25, 1]))
    fig.suptitle("KALIBRASYON DOGRULAMA — horn'u saga sola oynat, tepe takip etsin",
                 fontweight="bold")
    ln, = axp.plot(ang, np.zeros_like(ang), lw=1.8, color="#1976D2")
    pk = axp.axvline(0, color="#D32F2F", ls="--", lw=1.5)
    axp.axvline(0, color="#888", ls=":", lw=1.0)
    axp.set_xlim(-amax, amax)
    axp.set_ylim((0.0, 1.05) if PLOT_LINEAR else (-30, 1))
    axp.set_xlabel("gelis acisi [derece]   (0 = dizi normali, saat yonu +)")
    axp.set_ylabel("huzme cikisi" + (" (lineer)" if PLOT_LINEAR else " [dB]"))
    axp.grid(alpha=0.3)
    tp = axp.set_title("", fontsize=10, loc="left")

    tr, = axt.plot([], [], "-o", ms=3, lw=1.2, color="#00897B")
    axt.axhline(0, color="#888", ls=":", lw=1.0)
    axt.set_ylim(-amax, amax); axt.set_xlabel("olcum #")
    axt.set_ylabel("olculen aci [derece]"); axt.grid(alpha=0.3)
    plt.tight_layout(); plt.show(block=False)

    print("\n" + "=" * 70)
    print(" CANLI ACI TAKIBI")
    print("=" * 70)
    print("  Horn'u yavasca saga sola oynat. Kirmizi cizgi (tepe) seninle")
    print("  ayni yonde gitmeli. Ters gidiyorsa ARRAY_ORDER_SIGN ters demektir.")
    print("  Horn'u 0 dereceye (dizi normaline) getirdiginde tepe 0'da olmali;")
    print("  degilse hiza ya da kalibrasyon ofseti var.")
    print("  Yakalama PPS tetikli: saniyede bir guncellenir.")
    print("  Bitirince PENCEREYI KAPAT — olcume devam edilir.\n")
    print(f"  {'#':>4} {'aci':>8} {'tepe/yan':>9} {'koherans':>9}")

    i = 0
    while plt.fignum_exists(fig.number):
        acc = None
        for _ in range(max(1, n_per)):
            b, _t = acquire(ctx)
            if b is not None:
                acc = wcal_accum(b, WCAL_NFFT, acc)
        if acc is None or acc["nblk"] < 2:
            continue
        v, sol = ocal_vector(acc, FS)
        if v is None:
            continue
        P = beam_spectrum(v, ang)
        Pdb = ((P / (P.max() + 1e-30)) if PLOT_LINEAR
               else 10 * np.log10(P / (P.max() + 1e-30) + 1e-30))
        j = int(np.argmax(P))
        a_hat = float(ang[j])
        # tepe / yan lob orani: ana lobun disindaki en buyuk deger
        lam = C_AIR / CENTER_FREQ
        bw = np.degrees(0.886 * lam / max((N_RX - 1) * ARRAY_D_M, 1e-6))
        out = np.abs(ang - a_hat) > bw
        _Pn = P / (P.max() + 1e-30)
        sl_db = (10 * np.log10(_Pn[out].max() + 1e-30) if out.any()
                 else float("nan"))
        i += 1
        hist_t.append(i); hist_a.append(a_hat)
        ln.set_ydata(Pdb); pk.set_xdata([a_hat, a_hat])
        tr.set_data(hist_t, hist_a)
        axt.set_xlim(max(0, i - 60), max(10, i + 1))
        tp.set_text(f"olculen aci {a_hat:+6.1f} der   |   tepe/yan {-sl_db:4.1f} dB"
                    f"   |   koherans {np.min(sol['coh']):.3f}"
                    f"   |   huzme genisligi {bw:.0f} der")
        fig.canvas.draw_idle(); plt.pause(0.01)
        print(f"  {i:>4} {a_hat:>+7.1f}d {-sl_db:>8.1f}dB {np.min(sol['coh']):>9.3f}")

    plt.ioff()
    if hist_a:
        h = np.array(hist_a)
        print(f"\n  {len(h)} olcum: aci araligi {h.min():+.1f} .. {h.max():+.1f} der")
        print(f"  -> tepe horn ile AYNI yonde hareket ettiyse ve 0'da 0 verdiyse")
        print(f"     kalibrasyon dogrudur.")
    return hist_a

def ocal_verify(ctx, expect_deg=0.0, n_cap=8, tag="DOGRULAMA"):
    """Kalibrasyonun DOGRU olup olmadigini bagimsiz olarak sina.

    Mevcut kalibrasyonu uygulayip gelen sinyalin GELIS ACISINI olcer ve
    beklenen aciyla karsilastirir. 0 derecede yapilirsa kalibrasyonun kendi
    icinde tutarli oldugunu gosterir (zayif sinama). GERCEK sinama horn'u
    BASKA bir aciya (orn. +20 der) koyup orada olcmektir — kalibrasyon o
    aciyi bilmez, dogru cikarsa gercekten calisiyor demektir."""
    print("\n" + "=" * 70)
    print(f" {tag} — beklenen gelis acisi {expect_deg:+.1f} derece")
    print("=" * 70)
    acc = None
    for k in range(n_cap):
        b, _ = acquire(ctx)
        if b is None:
            continue
        acc = wcal_accum(b, WCAL_NFFT, acc)
        print(f"\r    olcum {k+1}/{n_cap}", end="", flush=True)
    print()
    if acc is None or acc["nblk"] < 2:
        print("  [HATA] yeterli veri yok."); return None
    sol = wcal_solve(acc, FS)
    if sol is None:
        print("  [HATA] bantta sinyal yok. Horn yayinda mi?"); return None

    ph_raw = sol["ph_deg"]                       # HAM (kalibrasyonsuz) faz
    ang_raw, _ = phase_to_angle_deg(ph_raw)
    # Kalibrasyon uygulanmis faz: taplarin bant ortasindaki fazi cikarilir
    if _WCAL is not None:
        ph_cal = np.array(ph_raw) - np.array(_WCAL["ph_deg"])
        ph_cal = (ph_cal + 180.0) % 360.0 - 180.0
    else:
        ph_cal = np.array(ph_raw)
    ang_cal, _ = phase_to_angle_deg(ph_cal)

    print(f"  {'kanal':>6} {'ham faz':>10} {'kalibreli faz':>15}")
    for k in range(N_RX):
        print(f"  {k:>6} {ph_raw[k]:>9.1f}d {ph_cal[k]:>14.1f}d")
    print(f"\n  koherans      : en dusuk {np.min(sol['coh']):.4f}")
    print(f"  HAM aci       : {ang_raw:+7.1f} der   (kalibrasyon uygulanmadan)")
    print(f"  KALIBRELI aci : {ang_cal:+7.1f} der   <- olculen")
    print(f"  beklenen      : {expect_deg:+7.1f} der")
    err = ang_cal - expect_deg
    print(f"  HATA          : {err:+7.1f} der")
    # Esik: dizinin huzme genisliginin ~%10'u. 4 eleman x 4 cm -> ~36 der huzme.
    lam = C_AIR / CENTER_FREQ
    bw = np.degrees(0.886 * lam / max((N_RX - 1) * ARRAY_D_M, 1e-6))
    thr = max(3.0, 0.10 * bw)
    ok = abs(err) < thr and np.min(sol["coh"]) > WCAL_COH_MIN
    print(f"  esik          : +-{thr:.1f} der  (huzme genisliginin %10'u, "
          f"huzme {bw:.0f} der)")
    print(f"\n  [{'OK  ' if ok else 'HATA'}] kalibrasyon "
          f"{'DOGRULANDI' if ok else 'DOGRULANMADI'}")
    if not ok:
        if np.min(sol["coh"]) <= WCAL_COH_MIN:
            print("        koherans dusuk -> sinyal zayif ya da kanallardan biri kopuk")
        else:
            print("        Olasi sebepler:")
            print("          - horn tam o acida degil (aciyi olcup tekrar dene)")
            print("          - dizi normali yanlis girilmis (--rxdir)")
            print(f"          - ARRAY_ORDER_SIGN ters (su an "
                  f"{ARRAY_ORDER_SIGN:+d}); isaret hatasi aciyi AYNALAR")
            if abs(ang_cal + expect_deg) < thr and abs(expect_deg) > 1:
                print(f"          ^^ olculen aci beklenenin TAM TERSI: "
                      f"ARRAY_ORDER_SIGN'i cevir")
    return dict(ang_raw=ang_raw, ang_cal=ang_cal, err=err, ok=ok, sol=sol)

def wcal_run(seconds=WCAL_SECONDS, key_path=None, out_path=None, quiet=False,
             n_cap=None, prompt_after=True, ota=False, ota_range_m=None,
             verify_deg=None, force=False):
    """KABLOLU kalibrasyon. Alici oturumunu ACAR ve _WCAL'i doldurur.

    Oturum, PESINDEN gelecek olcumun ihtiyac duydugu parametrelerle acilir
    (pencere = LOC_WIN_MS, pps_offset = anahtarin t_ref'i). Boylece olcum
    asamasi setup_x410'u tekrar cagirdiginda AYNI oturum dondurulur ve
    kanallar arasi faz — yani kalibrasyonun kendisi — bozulmaz."""
    global _WCAL
    if not _HAVE_UHD:
        print("[HATA] uhd modulu yok."); sys.exit(1)
    if out_path is None:
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                WCAL_FILE)
    print("=" * 70)
    print(f" {'HAVADAN (HORN, 0 DER)' if ota else 'KABLOLU (SPLITTER)'} DIZI KALIBRASYONU — "
          f"{f'{n_cap} olcum' if n_cap is not None else f'{seconds} s'}, "
          f"{N_RX} kanal")
    print("=" * 70)
    print("  Aci kalibrasyonu SADECE buradan gelir; LOS'tan kanal kalibrasyonu")
    print("  YAPILMAZ. LOS yalnizca menzil sifir noktasi icin kullanilir.")

    # Oturumu olcumun parametreleriyle ac — sonradan yeniden tune YOK.
    t_ref = 0.0
    if key_path:
        _, t_ref, _ = load_key(key_path)
    ctx = setup_x410(win_s=LOC_WIN_MS * 1e-3, advance_s=0.0, pps_offset=t_ref)

    if ota:
        R = ota_range_m if ota_range_m else OCAL_MIN_RANGE_M
        cur = ocal_curvature_deg(R)
        _wcal_prompt(
            "HORN'U DIZININ TAM KARSISINA, 0 DERECEYE KOY.\n"
            "  0 derece = dizi normali dogrultusu (broadside).\n"
            "  Bu acida dalga cephesi dizi eksenine DIK gelir, dort elemana\n"
            "  yol farki SIFIRDIR; olculen faz farki saf DONANIMDIR.\n"
            "\n"
            f"  Mesafe >= {OCAL_MIN_RANGE_M:.0f} m olsun. Yakinsa kuresel cephe\n"
            f"  egriligi kalibrasyona karisir ({R:.1f} m'de {cur:.1f} derece).\n"
            "\n"
            "  Horn dizinin ORTASINI gormeli, yuksekligi dizi ile ayni olmali.\n"
            "\n"
            "BASKA BIR TERMINALDE chirp'i baslat:\n"
            "  python3 fmcw_tx_turkcell_calib.py")
    else:
        _wcal_prompt(
            "SPLITTER'I TAK:\n"
            "  N321 RF0 TX/RX -> ZAYIFLATICI (>=30 dB) -> 4 yollu splitter\n"
            "  splitter cikislari -> X410'un 4 RX girisi\n"
            "\n"
            "BASKA BIR TERMINALDE chirp'i baslat:\n"
            "  python3 fmcw_tx_turkcell_calib.py\n"
            "\n"
            "X410 tarafindaki kablolar YERINDE KALSIN — kalibrasyon onlarin\n"
            "farkini da soguruyor; anteni sonra ayni kablolara baglayacaksin.")

    print("\n  Seviye kontrolu...")
    buf = None
    for _ in range(6):
        b, _t = acquire(ctx)
        if b is not None:
            buf = b
            break
    if buf is None:
        print("\n[HATA] yakalama alinamadi."); sys.exit(1)
    if not wcal_levels(buf):
        if not force:
            print("\n[HATA] seviye uygun degil; kalibrasyon YAPILMADI.")
            print("       Yine de denemek icin: --force-cal")
            sys.exit(1)
        print("\n[UYARI] seviye uygun degil ama --force-cal verildi, devam.")

    # HAVADAN MODDA CHIRP AYIKLANIR: hucre ayni bantta ve hep acik oldugu icin
    # ham veriden kalibrasyon cikmaz (olculdu: koherans 0.69). Chirp'i biz
    # urettigimiz icin periyoduna katlayip koherent ortalayabiliriz.
    cref = cn = None
    if ota:
        cref, cn, cper = ocal_chirp_ref()
        print(f"\n  CHIRP AYIKLAMA acik: {cn} ornek ({cper*1e6:.1f} us), "
              f"{OCAL_CHIRP_BW/1e6:.0f} MHz supurme")
        print(f"    periyoda katlanip {OCAL_N_GRP} grupta koherent ortalanacak")

    if ota:
        n_want = n_cap if n_cap is not None else int(seconds)
        print(f"\n  Veri toplaniyor ({n_want} olcum)...")
        acc, k, info = None, 0, None
        while k < n_want:
            b, _t = acquire(ctx)
            if b is None:
                continue
            acc, inf = ocal_accum_clean(b, cref, cn, acc)
            k += 1
            if inf is not None:
                info = inf
                print(f"\r    olcum {k}/{n_want}, blok {acc['nblk']}, "
                      f"chirp tepe/yan {inf['pk_db']:.0f} dB, "
                      f"tutarlilik {100*inf['hit']:.0f}%", end="", flush=True)
            else:
                print(f"\r    olcum {k}/{n_want}  [chirp BULUNAMADI]",
                      end="", flush=True)
        print()
        if info is None:
            print("\n[HATA] chirp hicbir yakalamada bulunamadi.")
            print("       TX yayinda mi? Horn diziye bakiyor mu? Bant dogru mu?")
            sys.exit(1)
        print(f"    chirp konumu  : ornek {info['epoch']} "
              f"({info['epoch']/FS*1e6:.1f} us)")
        print(f"    tepe/yan lob  : {info['pk_db']:.1f} dB "
              f"(uyumlu filtre, TB carpimi "
              f"{OCAL_CHIRP_BW*OCAL_CHIRP_DUR:.0f})")
        print(f"    PRF tutarlilik: {100*info['hit']:.0f}% "
              f"(her periyotta ayni yerde mi)")
        print(f"    katlama kazanci: grup basina {info['per_grp']} chirp -> "
              f"{10*np.log10(info['per_grp']):.1f} dB")
        if info["hit"] < 0.8:
            print(f"    [UYARI] tutarlilik dusuk; TX/RX saat farki ya da zayif sinyal")
    # Sayiyla ya da sureyle topla. Yakalama PPS tetikli oldugu icin saniyede
    # bir tanedir; "20 olcum" ~20 saniye demektir.
    elif n_cap is not None:
        print(f"\n  Veri toplaniyor ({n_cap} olcum)...")
        acc, k = None, 0
        while k < n_cap:
            b, _t = acquire(ctx)
            if b is None:
                continue
            acc = wcal_accum(b, WCAL_NFFT, acc)
            k += 1
            print(f"\r    olcum {k}/{n_cap}, blok {acc['nblk']}", end="", flush=True)
        print()
    else:
        print(f"\n  Veri toplaniyor ({seconds} s)...")
        acc, k, t0 = None, 0, __import__("time").time()
        while __import__("time").time() - t0 < seconds:
            b, _t = acquire(ctx)
            if b is None:
                continue
            acc = wcal_accum(b, WCAL_NFFT, acc)
            k += 1
            print(f"\r    yakalama {k}, blok {acc['nblk']}", end="", flush=True)
        print()
    if acc is None or acc["nblk"] < 2:
        print("\n[HATA] yeterli blok toplanamadi "
              f"(pencere {LOC_WIN_MS:.0f} ms, blok {WCAL_NFFT} ornek)."); sys.exit(1)

    sol = wcal_solve(acc, FS)
    if sol is None:
        print("\n[HATA] bantta chirp bulunamadi. TX yayinda mi, kablo takili mi?")
        sys.exit(1)
    if not wcal_report(sol):
        if not force:
            print("\n[HATA] kalibrasyon KABUL EDILMEDI. Nedenleri giderip tekrar "
                  "calistir.")
            print("       Yine de devam etmek icin: --force-cal")
            sys.exit(1)
        # ZORLA GECIS — sessizce degil, ne kadar bozuk oldugunu SOYLEYEREK.
        # Koherans gamma ile chirp/girisim guc orani r ~ gamma^2/(1-gamma^2);
        # kalan girisim faza YANLILIK bindirir ve yanlilik ~1/sqrt(r) radyandir.
        g = float(np.min(sol["coh"]))
        r = g * g / max(1.0 - g * g, 1e-6)
        bias = np.degrees(1.0 / np.sqrt(max(r, 1e-6)))
        print("\n" + "!" * 70)
        print(" --force-cal: KALIBRASYON KABUL EDILMEDI AMA DEVAM EDILIYOR")
        print("!" * 70)
        print(f"  en dusuk koherans {g:.3f} -> chirp/girisim orani ~{10*np.log10(r):.1f} dB")
        print(f"  bu, kanallar arasi faza ~{bias:.0f} derece YANLILIK bindirebilir.")
        print(f"  Aci kestirimi bu kadar kayabilir; menzil daha az etkilenir.")
        print(f"  DOGRULAMA asamasi (--verify) bunun kullanilabilir olup")
        print(f"  olmadigini gosterir: tepe 0 derecede 0'da mi, supurmede")
        print(f"  duzgun mu takip ediyor — ona bak.")
        print("!" * 70)

    np.savez(out_path, fmt=1, taps=sol["taps"], mask=sol["mask"],
             nfft=sol["nfft"], fs=sol["fs"], ng=sol["ng"],
             f_lo=sol["f_lo"], f_hi=sol["f_hi"], nblk=sol["nblk"],
             coh=sol["coh"], amp_db=sol["amp_db"], gd_ns=sol["gd_ns"],
             ph_deg=sol["ph_deg"], center_freq=CENTER_FREQ, rx_gain=RX_GAIN,
             array_d=ARRAY_D_M, stamp=__import__("time").strftime("%Y-%m-%d %H:%M:%S"))
    print(f"\n  Kaydedildi: {out_path}")
    print(f"  NOT: dosyanin FAZ kismi SADECE BU OTURUM icin gecerlidir "
          f"(ZBX LO'lari her acilista rastgele).")
    print(f"       Genlik ve grup gecikmesi kalicidir.")

    if ota:
        # HAM faz rampasi -> horn gercekten 0 derecede miydi?
        ang, _ = phase_to_angle_deg(sol["ph_deg"])
        print(f"\n  HAM faz rampasi {ang:+.1f} dereceye karsilik geliyor.")
        print(f"  Horn 0 derecedeyse bunun tamami DONANIMDIR ve kalibrasyon")
        print(f"  onu soguruyor. Ama horn aslinda {ang:+.1f} derecedeyse")
        print(f"  kalibrasyon o aciyi 'donanim' sanip icine alir ve bundan")
        print(f"  sonraki BUTUN acilar {-ang:+.1f} derece kayar.")
        if abs(ang) > 25.0:
            print(f"  [UYARI] rampa buyuk. Horn hizasini bir daha kontrol et.")
    _WCAL = sol
    if verify_deg is not None:
        if verify_deg == "live":
            _wcal_prompt(
                "DOGRULAMA — CANLI ACI TAKIBI.\n"
                "  Horn'u elinde tut, chirp yayinda kalsin.\n"
                "\n"
                "  ENTER'dan sonra bir grafik acilacak. Horn'u yavasca saga\n"
                "  sola oynat; tepe SENINLE AYNI YONDE gitmeli.\n"
                "  0 dereceye (dizi normali) getirdiginde tepe 0'da olmali.\n"
                "\n"
                "  Bitirince PENCEREYI KAPAT — olcum kendiliginden devam eder.")
            ocal_verify_live(ctx)
        else:
            _wcal_prompt(
                f"DOGRULAMA: horn'u {verify_deg:+.0f} DERECEYE al.\n"
                "  (0 derece = dizi normali, saat yonu +)\n"
                "\n"
                "  Kalibrasyon bu aciyi BILMIYOR. Dogru olcerse gercekten\n"
                "  calisiyor demektir — 0 derecede olcmek kendi kendini\n"
                "  dogrulamak olurdu.\n"
                "\n"
                "Chirp yayinda kalsin.")
            ocal_verify(ctx, verify_deg)

    if prompt_after:
        if ota:
            # HAVADAN kalibrasyonda antenler ZATEN takili; sokulecek bir sey yok.
            _wcal_prompt(
                "HORN'U KALDIR / KAPAT.\n"
                "  Chirp'i durdur (obur terminalde Ctrl+C).\n"
                "  Anten baglantilarina DOKUNMA — kalibrasyon onlari da kapsiyor.\n"
                "\n"
                "ENTER'a basinca olcum AYNI OTURUMDA devam edecek —\n"
                "alici bir daha ACILMAYACAK, kalibrasyon boylece gecerli kalir.")
        else:
            _wcal_prompt(
                "SPLITTER'I CIKAR, ANTENLERI TAK.\n"
                "  X410 tarafindaki kablolar AYNI kalmali; sadece uzak uc degissin.\n"
                "\n"
                "Chirp'i durdur (obur terminalde Ctrl+C).\n"
                "\n"
                "ENTER'a basinca olcum AYNI OTURUMDA devam edecek —\n"
                "alici bir daha ACILMAYACAK, kalibrasyon boylece gecerli kalir.")
    return sol



# ===================================================================
#  GEOMETRI — GPS, dosya, arayuz
# ===================================================================

def _bearing_to_vec(deg):
    """Pusula acisi -> birim vektor. 0 der = +y ekseni, saat yonu POZITIF."""
    r = np.radians(float(deg))
    return np.array([np.sin(r), np.cos(r), 0.0])

def _vec_to_bearing(v):
    v = np.asarray(v, float)
    return float(np.degrees(np.arctan2(v[0], v[1])) % 360.0)

def parse_latlon(s):
    """Enlem/boylam metnini ondalik dereceye cevir. Kabul edilenler:
         40°47'24.99"N 29°27'28.18"E
         40 47 24.99 N   /   40d47m24.99sN
         40.790275, 29.457828      (ondalik)
    Doner (lat, lon) ya da None."""
    import re
    t = s.strip().replace("’", "'").replace("″", '"').replace("''", '"')
    t = t.replace("°", " ").replace("'", " ").replace('"', " ")
    t = re.sub(r"[dDmMsS](?=\s|$|[NSEWnsew])", " ", t)
    t = t.replace(",", " ")
    toks = re.findall(r"[-+]?\d+\.?\d*|[NSEWnsew]", t)
    if not toks:
        return None
    vals, hemi = [], []
    cur = []
    for tk in toks:
        if tk.upper() in "NSEW":
            hemi.append(tk.upper())
            vals.append(cur)
            cur = []
        else:
            cur.append(float(tk))
    if cur:
        vals.append(cur)

    def _dms(parts):
        d = parts[0] if len(parts) > 0 else 0.0
        m = parts[1] if len(parts) > 1 else 0.0
        sec = parts[2] if len(parts) > 2 else 0.0
        sign = -1.0 if d < 0 else 1.0
        return sign * (abs(d) + m / 60.0 + sec / 3600.0)

    # Yarim kure harfi YOKSA sayilari ikiye bolmek gerekir: 2 sayi -> ondalik
    # cift, 6 sayi -> iki DMS ucllusu, 4 sayi -> iki derece-dakika cifti.
    if not hemi:
        flat = [v for grp in vals for v in grp]
        if len(flat) % 2 or not flat:
            return None
        h = len(flat) // 2
        vals, hemi = [flat[:h], flat[h:]], []
    if len(vals) < 2 or not vals[0] or not vals[1]:
        return None
    lat, lon = _dms(vals[0]), _dms(vals[1])
    if len(hemi) >= 1 and hemi[0] in "SW":
        lat = -lat
    if len(hemi) >= 2 and hemi[1] in "SW":
        lon = -lon
    if len(hemi) >= 2 and hemi[0] in "EW":       # boylam once yazilmissa
        lat, lon = lon, lat
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return lat, lon

def latlon_to_xy(lat, lon, lat0, lon0):
    """WGS84 -> yerel duzlem [m]. Baslangic (lat0,lon0) = ALICI = (0,0).
    x = DOGU, y = KUZEY  (yani pusula acisi 0 der = +y ile tutarli).

    Kure yerine elipsoid yaricaplari kullanilir: 40 derece enlemde meridyen ve
    dik kesit yaricaplari %0.4 farklidir, 100 m'lik bir tabanda bu 0.4 m eder."""
    a = 6378137.0
    f = 1.0 / 298.257223563
    e2 = f * (2 - f)
    p0 = np.radians(lat0)
    s = np.sin(p0)
    M = a * (1 - e2) / (1 - e2 * s * s) ** 1.5          # meridyen yaricapi
    Nr = a / np.sqrt(1 - e2 * s * s)                    # dik kesit yaricapi
    y = np.radians(lat - lat0) * M
    x = np.radians(lon - lon0) * Nr * np.cos(p0)
    return float(x), float(y)

def _ask_latlon(prompt):
    """GPS koordinati sor; bos birakilirsa None doner."""
    while True:
        s = input(f"    {prompt}: ").strip()
        if not s:
            return None
        r = parse_latlon(s)
        if r:
            return r
        print("      okunamadi. Ornek: 40°47'24.99\"N 29°27'28.18\"E "
              "ya da 40.790275, 29.457828")

def _ask(prompt, default=None, cast=float):
    while True:
        s = input(f"    {prompt}"
                  + (f" [{default}]" if default is not None else "") + ": ").strip()
        if not s and default is not None:
            return default
        try:
            return cast(s)
        except ValueError:
            print("      sayi gir.")

def geom_save(path):
    import json
    g = dict(tx=list(map(float, TX_POS)), tx_bearing=_vec_to_bearing(TX_N1),
             tx_bw3=float(TX_BW3_DEG),
             array=list(map(float, ARRAY_POS)),
             array_bearing=_vec_to_bearing(ARRAY_N2),
             d_m=float(ARRAY_D_M),
             grid=(list(GRID_BOUNDS) if GRID_BOUNDS else None),
             res_m=float(GRID_RES_M))
    with open(path, "w") as f:
        json.dump(g, f, indent=2)
    return g

def geom_load(path):
    """Doner True (yuklendi) / False (dosya yok ya da bozuk)."""
    global TX_POS, TX_N1, TX_BW3_DEG, ARRAY_POS, ARRAY_N2, ARRAY_D_M
    global GRID_BOUNDS, GRID_RES_M
    import json
    try:
        with open(path) as f:
            g = json.load(f)
        TX_POS     = np.array(g["tx"], float)
        TX_N1      = _bearing_to_vec(g["tx_bearing"])
        TX_BW3_DEG = float(g.get("tx_bw3", TX_BW3_DEG))
        ARRAY_POS  = np.array(g["array"], float)
        ARRAY_N2   = _bearing_to_vec(g["array_bearing"])
        ARRAY_D_M  = float(g["d_m"])
        GRID_BOUNDS = tuple(g["grid"]) if g.get("grid") else None
        GRID_RES_M  = float(g.get("res_m", GRID_RES_M))
        return True
    except Exception:
        return False

def geom_report():
    el = element_positions()
    b = np.linalg.norm(ARRAY_POS - TX_POS)
    print(f"    baz istasyonu : ({TX_POS[0]:+.1f}, {TX_POS[1]:+.1f}, "
          f"{TX_POS[2]:.1f}) m   yon {_vec_to_bearing(TX_N1):.0f} der, "
          f"huzme {TX_BW3_DEG:.0f} der")
    print(f"    alici dizisi  : ({ARRAY_POS[0]:+.1f}, {ARRAY_POS[1]:+.1f}, "
          f"{ARRAY_POS[2]:.1f}) m   yon {_vec_to_bearing(ARRAY_N2):.0f} der, "
          f"d={ARRAY_D_M*100:.1f} cm")
    print(f"    TX-RX arasi   : {b:.1f} m  (bistatik taban)")
    print(f"    dizi eksenine gore TX yonu: "
          f"{_vec_to_bearing(TX_POS - ARRAY_POS):.0f} der")
    _X, _Y = grid_axes()
    _dx = (_X[1] - _X[0]) if len(_X) > 1 else 0.0
    _dy = (_Y[1] - _Y[0]) if len(_Y) > 1 else 0.0
    _src = ("elle (--grid)" if GRID_BOUNDS else
            f"otomatik (TX+RX kutusu + {GRID_MARGIN_M:.0f} m pay)")
    print(f"    harita        : x {_X[0]:.1f}..{_X[-1]:.1f}, "
          f"y {_Y[0]:.1f}..{_Y[-1]:.1f} m   [{_src}]")
    print(f"    izgara        : {len(_X)} x {len(_Y)} hucre, adim "
          f"{_dx:.2f} x {_dy:.2f} m"
          + (f"   (istenen {GRID_RES_M:.2f} m — {GRID_MAX_CELLS} hucre/eksen "
             f"sinirina takildi)" if abs(_dx - GRID_RES_M) > 1e-6 else ""))

def geom_ask(path):
    """Geometriyi SORARAK al ve dosyaya yaz."""
    global TX_POS, TX_N1, TX_BW3_DEG, ARRAY_POS, ARRAY_N2, ARRAY_D_M
    global GRID_BOUNDS, GRID_RES_M
    print("\n" + "=" * 70)
    print(" GEOMETRI — konum kestirimi bunsuz yapilamaz")
    print("=" * 70)
    print("  Aci = pusula: 0 der = KUZEY (+y), saat yonu pozitif (90 der = dogu).")
    print("  Konumu GPS ile ya da metre ile verebilirsin.")
    use_gps = not input("\n  GPS koordinati ile mi gireceksin? "
                        "[E=evet / h=hayir, metre gireceksen]: "
                        ).strip().lower().startswith("h")

    if use_gps:
        # ALICI baslangic noktasidir: (0,0). Baz istasyonu ona GORE hesaplanir.
        print("\n  ALICI DIZISI (X410) — bu nokta haritanin (0,0)'i olacak")
        rx_ll = None
        while rx_ll is None:
            rx_ll = _ask_latlon("enlem/boylam")
        rx_z = _ask("yukseklik z [m]", 1.5)
        print("\n  BAZ ISTASYONU (aydinlatici)")
        tx_ll = None
        while tx_ll is None:
            tx_ll = _ask_latlon("enlem/boylam")
        tx_z = _ask("yukseklik z [m]", 30.0)
        tx_x, tx_y = latlon_to_xy(tx_ll[0], tx_ll[1], rx_ll[0], rx_ll[1])
        rng = float(np.hypot(tx_x, tx_y))
        brg = _vec_to_bearing(np.array([tx_x, tx_y, 0.0]))
        print(f"      -> baz istasyonu aliciya gore: x={tx_x:+.1f} m (dogu), "
              f"y={tx_y:+.1f} m (kuzey)")
        print(f"         yatay mesafe {rng:.1f} m, yon {brg:.1f} derece")
        TX_POS    = np.array([tx_x, tx_y, tx_z], float)
        ARRAY_POS = np.array([0.0, 0.0, rx_z], float)
        tx_b = _ask("baz istasyonu anteni hangi yone bakiyor [derece]",
                    round((brg + 180.0) % 360.0, 1))
        tx_w = _ask("-3 dB huzme genisligi [derece]", 65.0)
    else:
        print("\n  BAZ ISTASYONU (aydinlatici)")
        tx_x = _ask("x [m] (dogu +)", 0.0)
        tx_y = _ask("y [m] (kuzey +)", 0.0)
        tx_z = _ask("yukseklik z [m]", 30.0)
        tx_b = _ask("anten hangi yone bakiyor [derece]", 0.0)
        tx_w = _ask("-3 dB huzme genisligi [derece]", 65.0)
        print("\n  ALICI DIZISI (X410, 4 eleman)")
        rx_x = _ask("x [m]", 20.0)
        rx_y = _ask("y [m]", 100.0)
        rx_z = _ask("yukseklik z [m]", 0.0)
        TX_POS    = np.array([tx_x, tx_y, tx_z], float)
        ARRAY_POS = np.array([rx_x, rx_y, rx_z], float)
    b_tx = _vec_to_bearing(TX_POS - ARRAY_POS)
    print(f"      (dizinin bulundugu yerden baz istasyonu {b_tx:.0f} derecede)")
    rx_b = _ask("dizi normali hangi yone bakiyor [derece]", round(b_tx, 1))
    d_cm = _ask("eleman araligi [cm]", 4.0)
    TX_N1      = _bearing_to_vec(tx_b)
    TX_BW3_DEG = tx_w
    ARRAY_N2   = _bearing_to_vec(rx_b)
    ARRAY_D_M  = d_cm / 100.0
    print("\n  HARITA")
    auto = input("    harita sinirlarini otomatik hesaplayayim mi? "
                 "[E=evet / h=hayir, elle gireceksen]: ").strip().lower()
    if auto.startswith("h"):
        GRID_BOUNDS = (_ask("x min [m]", -50.0), _ask("x max [m]", 50.0),
                       _ask("y min [m]", 0.0), _ask("y max [m]", 150.0))
    else:
        GRID_BOUNDS = None
    GRID_RES_M = _ask("izgara adimi [m]", 0.5)
    print()
    geom_report()
    lam = C_AIR / CENTER_FREQ
    if ARRAY_D_M > lam / 2 + 1e-9:
        print(f"\n    [UYARI] d={ARRAY_D_M*100:.1f} cm > lambda/2="
              f"{lam/2*100:.2f} cm -> aci belirsizligi (grating lobe) olur.")
    geom_save(path)
    print(f"\n  Kaydedildi: {path}  (bir dahaki sefere sorulmayacak; "
          f"degistirmek icin --geom-ask)")

def rxdir_ui(path=None):
    """RX'in BAKTIGI DOGRULTUYU canli ayarla (--rxdir).

    Dizinin normali, aci kestiriminin SIFIR REFERANSIDIR: olculen aci bu yonden
    sapma olarak cikar. Yanlis girilirse butun hedefler ayni miktarda doner,
    yani harita saglam gorunur ama YANLIS yerde olur. Pusulayla olcmek zor
    oldugu icin burada gorerek ayarlanir.

    Kaydirici cevrildikce: dizi ekseni, normal oku, +-45 der gorus konisi ve
    TX'in diziye gore acisi aninda guncellenir. 'Kaydet' geometri dosyasina
    yazar."""
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Slider, Button
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), GEOM_FILE)
    geom_load(path)                       # varsa dosyadakiyle basla

    tx = TX_POS[:2].astype(float)
    rx = ARRAY_POS[:2].astype(float)
    b_tx = _vec_to_bearing(TX_POS - ARRAY_POS)        # dizi -> TX yonu
    span = max(np.linalg.norm(tx - rx), 20.0)
    pad = 0.35 * span

    fig, ax = plt.subplots(figsize=(8.2, 8.6))
    plt.subplots_adjust(bottom=0.22)
    ax.set_aspect("equal")
    ax.set_xlim(min(tx[0], rx[0]) - pad, max(tx[0], rx[0]) + pad)
    ax.set_ylim(min(tx[1], rx[1]) - pad, max(tx[1], rx[1]) + pad)
    ax.grid(alpha=0.3)
    ax.set_xlabel("x  [m]   (dogu +)")
    ax.set_ylabel("y  [m]   (kuzey +)")

    ax.plot([rx[0], tx[0]], [rx[1], tx[1]], color="#888", ls="--", lw=1.0,
            zorder=1, label=f"dogrudan yol {np.linalg.norm(tx-rx):.1f} m")
    ax.plot(*tx, marker="^", ms=15, color="#D32F2F", zorder=5)
    ax.annotate(f"BAZ ISTASYONU\n{b_tx:.1f} der, {np.linalg.norm(tx-rx):.1f} m",
                tx, textcoords="offset points", xytext=(10, 10),
                fontsize=9, color="#D32F2F", fontweight="bold")
    ax.plot(*rx, marker="s", ms=11, color="#1976D2", zorder=5)
    ax.annotate("ALICI (0,0)", rx, textcoords="offset points", xytext=(10, -18),
                fontsize=9, color="#1976D2", fontweight="bold")
    # kuzey oku
    ax.annotate("K", xy=(0.06, 0.93), xytext=(0.06, 0.83),
                xycoords="axes fraction", textcoords="axes fraction",
                ha="center", fontsize=11, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="k", lw=1.6))

    L = 0.30 * span
    arrow, = ax.plot([], [], color="#00897B", lw=2.6, zorder=6)
    axis_ln, = ax.plot([], [], color="#F57C00", lw=3.0, zorder=6)
    elems, = ax.plot([], [], marker="o", ms=6, ls="none", color="#F57C00", zorder=7)
    cone = ax.fill([], [], color="#00897B", alpha=0.10, zorder=2)[0]
    lbl_k0 = ax.text(0, 0, " k0", fontsize=8, color="#E65100", zorder=8,
                     ha="left", va="center", fontweight="bold")
    lbl_k3 = ax.text(0, 0, f" k{N_RX-1}", fontsize=8, color="#E65100", zorder=8,
                     ha="left", va="center", fontweight="bold")
    txt = ax.set_title("", fontsize=9.5, loc="left")

    def redraw(bearing):
        n = _bearing_to_vec(bearing)
        # dizi EKSENI normale dik (ULA): elemanlar bu eksende dizili
        u = np.array([n[1], -n[0], 0.0]) * ARRAY_ORDER_SIGN
        tip = rx + n[:2] * L
        arrow.set_data([rx[0], tip[0]], [rx[1], tip[1]])
        # Dizi 12 cm; 100 m'lik haritada gorunmez. GERCEK oranini korumak yerine
        # gorulebilir bir uzunluga olcekle (sadece YON onemli, boy degil).
        sc = (0.10 * span) / max((N_RX - 1) * ARRAY_D_M, 1e-6)
        off = (np.arange(N_RX) - (N_RX - 1) / 2.0) * ARRAY_D_M * sc
        ep = rx[None, :] + u[None, :2] * off[:, None]
        axis_ln.set_data([ep[0, 0], ep[-1, 0]], [ep[0, 1], ep[-1, 1]])
        elems.set_data(ep[:, 0], ep[:, 1])
        th = np.radians(np.linspace(bearing - 45, bearing + 45, 40))
        pts = np.vstack([rx, np.column_stack([rx[0] + L * 1.15 * np.sin(th),
                                              rx[1] + L * 1.15 * np.cos(th)])])
        cone.set_xy(pts)
        rel = (b_tx - bearing + 180.0) % 360.0 - 180.0
        # SAG/SOL, dizinin KENDI cercevesinde tanimlidir: normale bakarken
        # saat yonu (+) SAG, ters yon (-) SOL. Haritada TX batida gorunse bile
        # dizi baska yone bakiyorsa dizinin SAGINDA kalabilir — kafa karistiran
        # nokta buydu, o yuzden ikisi de yaziliyor.
        yan = "SAG" if rel > 0 else "SOL"
        gorus = "on" if abs(rel) <= 90 else "ARKA"
        warn = "" if abs(rel) <= 60 else "  [!] gorus konisi disi"
        # eleman uclarini isaretle (k0 / k3 hangi tarafta)
        lbl_k0.set_position((ep[0, 0], ep[0, 1]))
        lbl_k3.set_position((ep[-1, 0], ep[-1, 1]))
        txt.set_text(
            f"dizi normali {bearing:6.1f} der   |   TX pusulada {b_tx:.1f} der\n"
            f"TX diziye gore {rel:+.1f} der  ->  dizinin {yan}INDA, {gorus} tarafta{warn}")
        fig.canvas.draw_idle()

    sl = Slider(plt.axes([0.12, 0.10, 0.70, 0.035]), "dizi yonu [der]",
                0.0, 359.9, valinit=_vec_to_bearing(ARRAY_N2), valstep=0.1)
    sl.on_changed(redraw)

    def _tx(_):
        sl.set_val(round(b_tx, 1))
    # DIKKAT: matplotlib widget'lari REFERANS TUTULMAZSA cop toplayici
    # tarafindan silinir ve tiklama sessizce calismaz. Bu yuzden b_txbtn /
    # b_save degiskenlerde tutuluyor (kaydirici zaten sl'de duruyordu, o
    # yuzden o calisiyor ama dugmeler calismiyordu).
    b_txbtn = Button(plt.axes([0.12, 0.035, 0.20, 0.05]), "TX'e cevir")
    b_txbtn.on_clicked(_tx)

    state = dict(saved=False)

    def _save(_):
        global ARRAY_N2
        ARRAY_N2 = _bearing_to_vec(sl.val)
        geom_save(path)
        state["saved"] = True
        print(f"\n  dizi yonu {sl.val:.1f} der olarak kaydedildi -> "
              f"{os.path.basename(path)}")
        redraw(sl.val)
    b_save = Button(plt.axes([0.35, 0.035, 0.20, 0.05]), "KAYDET")
    b_save.on_clicked(_save)

    fig._widgets = (sl, b_txbtn, b_save)     # cop toplayiciya karsi
    redraw(sl.val)
    print("=" * 70)
    print(" RX DOGRULTU AYARI")
    print("=" * 70)
    print("  Kaydiriciyi cevirip dizinin baktigi yonu ayarla, KAYDET'e bas.")
    print("  Turuncu cizgi = dizi ekseni (elemanlar), yesil ok = normal.")
    print("  Normal, aci kestiriminin SIFIRIDIR: yanlissa butun hedefler ayni")
    print("  miktarda doner — harita saglam gorunur ama yanlis yerde olur.")
    print(f"\n  TX diziden {b_tx:.1f} derecede. Dizini TX'e cevirdiysen")
    print(f"  'TX'e cevir' dugmesi yeterli.\n")
    plt.show()
    if not state["saved"]:
        print("  [BILGI] kaydedilmedi; geometri degismedi.")
    return path

def _reapply_geom_cli():
    """Dosya yuklendikten sonra komut satiri degerlerini geri koy."""
    global TX_POS, ARRAY_POS, TX_N1, ARRAY_N2, ARRAY_D_M, TX_BW3_DEG
    global GRID_BOUNDS, GRID_RES_M
    g = _GEOM_CLI
    if "tx" in g:    TX_POS     = np.array(g["tx"], float)
    if "array" in g: ARRAY_POS  = np.array(g["array"], float)
    if "n1" in g:    TX_N1      = np.array(g["n1"], float)
    if "n2" in g:    ARRAY_N2   = np.array(g["n2"], float)
    if "d" in g:     ARRAY_D_M  = float(g["d"])
    if "bw3" in g:   TX_BW3_DEG = float(g["bw3"])
    if "grid" in g:  GRID_BOUNDS = tuple(g["grid"])
    if "res" in g:   GRID_RES_M  = float(g["res"])

def geom_setup(path=None, ask=False):
    """Geometriyi hazirla. SORMAZ.

    Konumlar koda GOMULU (bkz. 3b). Sirasiyla: geometri.json varsa ondan,
    yoksa koddaki degerlerden. Her halde ne kullanildigi YAZILIR.
    Degistirmek icin:  --rxdir (dizi yonu, kaydiricili)  ya da  --geom-ask."""
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), GEOM_FILE)
    if ask:
        geom_ask(path)
        return path
    loaded = geom_load(path)
    src = os.path.basename(path) if loaded else "koda gomulu degerler"
    if loaded and _GEOM_CLI:
        # KOMUT SATIRI DOSYAYI EZER — tersi degil.
        _reapply_geom_cli()
        src += " + komut satiri (" + ", ".join(sorted(_GEOM_CLI)) + ")"
    print(f"\n  GEOMETRI  ({src})")
    geom_report()
    if not USE_TX_PATTERN:
        print(f"    TX huzme maskesi: KAPALI (sektor azimutu bilinmiyor)")
    print(f"    dizi yonunu degistir: --rxdir")
    return path

def _apply_geometry_overrides(a, remember=True):
    """Komut satiri geometri argumanlarini uygula.

    remember=True ise hangi alanlarin CLI'dan geldigi kaydedilir; geometri
    dosyasi yuklendikten SONRA tekrar uygulanir. Yoksa dosya CLI'yi eziyordu
    (sahada gorulduu: --grid verildi ama harita degismedi, cunku
    geometri.json icindeki "grid": null sonradan yukleniyordu)."""
    global TX_POS, ARRAY_POS, TX_N1, ARRAY_N2, ARRAY_D_M, TX_BW3_DEG
    global GRID_BOUNDS, GRID_RES_M, _GEOM_CLI
    if remember:
        _GEOM_CLI = {k: v for k, v in
                     dict(tx=a.tx, array=a.array, n1=a.n1, n2=a.n2, d=a.d,
                          bw3=a.bw3, grid=a.grid, res=a.res).items()
                     if v is not None}
    if a.tx:      TX_POS    = np.array(a.tx, float)
    if a.array:   ARRAY_POS = np.array(a.array, float)
    if a.n1:      TX_N1     = np.array(a.n1, float)
    if a.n2:      ARRAY_N2  = np.array(a.n2, float)
    if a.d:       ARRAY_D_M = float(a.d)
    if a.bw3:     TX_BW3_DEG = float(a.bw3)
    if a.grid:    GRID_BOUNDS = tuple(a.grid)
    if a.res:     GRID_RES_M = float(a.res)



# ===================================================================
#  TANI MODLARI — psd, cell, cells
# ===================================================================

def tdd_duty(Pt_db, floor_db, levels=(-10.0, -20.0, -30.0)):
    """TDD DL orani — TEPEYE gore esiklerle, KAZANCTAN BAGIMSIZ.

    NEDEN GURULTU TABANINA GORE DEGIL: "taban + 6 dB" olcutu esigi ALICININ
    gurultu tabanina civiler, o da kazancla oynar. Sahada olculdu (3530 MHz,
    ayni hucre, ayni an):
        kazanc 30 -> taban -54.6 dB, esik -48.6 dB -> DL orani %74
        kazanc 10 -> taban -36.0 dB, esik -30.0 dB -> DL orani %29
    Sinyal ayni, sadece esik 18 dB kaydi. Oysa TDD DL orani baz istasyonunun
    ozelligidir, bizim kazancimizin degil.

    TEPEYE gore esik bu sorunu tanim geregi cozer: tepe de sinyalin kendisidir,
    ikisi kazancla BIRLIKTE oynar ve oran sabit kalir.

    TEK BIR SAYI VERMIYORUZ, cunku profil temiz iki modlu degil: NR TDD'de
    slotlarin yuku degisir (bos RB, farkli sembol yukleri, SSB burst) ve guc
    surekli bir dagilim olusturur. Uc esikteki oranlar bu dagilimi DURUSTCE
    gosterir; tek esik hangi seviyeyi sectiginize gore farkli cevap verirdi.

    floor_db: gurultu tabani (tepeye gore, dB). Bunun ALTINDAKI esikler
    olculemez ve oyle isaretlenir.

    Doner: [(seviye, oran, olculebilir_mi), ...] ve -20 dB'deki ilk indeks."""
    out = []
    for lv in levels:
        on = Pt_db > lv
        out.append((lv, float(on.mean()), lv > floor_db + 6.0))
    ref = Pt_db > levels[1]
    first = int(np.argmax(ref)) if ref.any() else 0
    return out, first

def psd_probe(n_cap=5, win_ms=PSD_WIN_MS):
    """Bant tanisi: ortalama spektrum + pencere ici zaman-guc profili."""
    if not _HAVE_UHD:
        print("[HATA] uhd modulu yok."); sys.exit(1)
    import matplotlib.pyplot as plt

    print("=" * 70)
    print(f" BAND TANISI — {n_cap} x {win_ms:.1f} ms @ {CENTER_FREQ/1e6:.3f} MHz, "
          f"kazanc {RX_GAIN:.0f} dB")
    print("=" * 70)
    ctx = setup_x410(win_s=win_ms * 1e-3, advance_s=PPS_OFFSET_S)
    N = ctx["N_act"]
    nblk = max(1, N // PSD_NFFT)
    TB   = max(1, int(round(PSD_TBIN_S * FS)))
    ntb  = max(1, N // TB)

    Pf = np.zeros(PSD_NFFT)
    Pt = np.zeros((N_RX, ntb))
    used, pk_max, clip_n, hh = 0, 0.0, 0, []
    print(f"\n  {'#':>3}  {'tepe[dBFS]':>10}  {'tepe(bassiz)':>11}  "
          f"{'ort[dBFS]':>10}  {'doyma':>9}  durum")
    for i in range(int(n_cap)):
        buf, _ = acquire(ctx)
        if buf is None:
            print(f"  {i+1:>3}  {'--':>10}  {'--':>10}  yakalama EKSIK"); continue
        x = buf[0][:nblk * PSD_NFFT].reshape(nblk, PSD_NFFT)
        Pf += (np.abs(np.fft.fftshift(np.fft.fft(x, axis=1), axes=1)) ** 2).mean(0)
        Pt += (np.abs(buf[:, :ntb * TB].reshape(N_RX, ntb, TB)) ** 2).mean(2)
        # KIRPMA olcutu: I ya da Q raya dayandi mi (kompleks genlik degil —
        # kirpma I/Q'da ayri ayri olur, |z| kirpikken sqrt(2)=+3.01 dB'e cikar).
        h = adc_health(buf)
        hh.append(h)
        pk_iq = float(h["pk"].max())
        pk_max = max(pk_max, float(h["pk_rob"].max()))
        av = 10 * np.log10((np.abs(buf[0]) ** 2).mean() + 1e-30)
        # KIRPMA olcutu ORAN'dir, ciplak maksimum degil: tek bir doymus ornek
        # maksimumu 0 dBFS'e civiler ve kazanctan bagimsiz oyle kalir.
        clipped = float(h["frac"].max()) > 1e-5
        clip_n += int(clipped)
        flag = "KIRPMA (yaygin)" if clipped else \
               ("zayif, kazanci artir" if av < -55 else "OK")
        print(f"  {i+1:>3}  {20*np.log10(pk_iq+1e-30):>+10.1f}  "
              f"{20*np.log10(float(h['pk_rob'].max())+1e-30):>+11.1f}  "
              f"{av:>+10.1f}  {float(h['frac'].max()):>9.2e}  {flag}")
        used += 1
    if used == 0:
        print("\n[HATA] hic yakalama alinamadi."); sys.exit(1)

    # Teshis, SON yakalamanin dagilimindan (hepsi benzerdir).
    real_clip, _ = adc_report(hh[-1], av, RX_GAIN)
    # Kazanc onerisi ROBUST tepeden (yakalama basi gecici olayi haric).
    pk_db = 20 * np.log10(pk_max + 1e-30)
    g_sug = float(np.clip(round(RX_GAIN - (pk_db + 12.0)), 0, 60))
    if real_clip:
        print(f"\n  [KRITIK] {clip_n}/{used} yakalamada YAYGIN kirpma "
              f"(robust tepe {pk_db:+.1f} dBFS).")
        print(f"           Kirpma enerjiyi TUM banda yayar -> asagidaki spektrum ve")
        print(f"           'tasiyici yok' karari GUVENILMEZ. Once kazanci dusur:")
        print(f"             --gain {g_sug:.0f}    (su an {RX_GAIN:.0f} dB)")
    else:
        print(f"\n  Gercek kirpma YOK. Robust tepe {pk_db:+.1f} dBFS "
              f"(hedef ~-12 dBFS icin oneri: --gain {g_sug:.0f})")

    Pf /= used
    Pt /= used
    f_mhz = (CENTER_FREQ + np.linspace(-FS / 2, FS / 2, PSD_NFFT,
                                       endpoint=False)) / 1e6
    # DC civari (LO sizintisi/DC ofset) istatistikleri bozar -> maskele.
    dc = PSD_NFFT // 2
    keep = np.ones(PSD_NFFT, bool); keep[dc - 2:dc + 3] = False
    inband = band_limit_mask(PSD_NFFT)          # kanal ICI binler
    keep_ch = keep & inband
    # _wb_band_edges ile AYNI gerekce: taban TUM pencereden, isgal karari
    # kanaldan. Taban da kanaldan alinsaydi sinyalin icine duserdi.
    Pf_db = 10 * np.log10(Pf / (Pf[keep_ch].max() + 1e-30) + 1e-30)

    # Gurultu tabani: MEDYAN DEGIL, %10'luk dilim. 122.88 MHz pencerede 100 MHz'lik
    # bir NR tasiyicisi binlerin cogunu doldurur; medyan tasiyicinin ICINE duser ve
    # "medyan+X dB" esigi tanim geregi tutmaz. %10 dilim koruma bandinda kalir.
    floor_db = float(np.percentile(Pf_db[keep], 10))    # TUM pencere
    occ = keep_ch & (Pf_db > floor_db + 6.0)           # secim KANALDAN
    print(f"\n  gurultu tabani (%10 dilim): {floor_db:+.1f} dB (tepeye gore)")

    # Terminalde kaba spektrum — grafige bakmadan sekli gormek icin.
    NBAR = 24
    if BAND_LIMIT_ON:
        ib = np.flatnonzero(inband)
        lo_i, hi_i = int(ib[0]), int(ib[-1] + 1)
        print(f"\n  (spektrum SADECE kanal icinde gosteriliyor: "
              f"{f_mhz[lo_i]:.1f} .. {f_mhz[hi_i-1]:.1f} MHz. "
              f"Tumu icin --fullband)")
    else:
        lo_i, hi_i = 0, PSD_NFFT
    edges = np.linspace(lo_i, hi_i, NBAR + 1).astype(int)
    print(f"  {'MHz':>18}  {'dB':>6}")
    for i in range(NBAR):
        s, e = edges[i], edges[i + 1]
        m = keep_ch[s:e]
        if not m.any():
            continue
        v = 10 * np.log10(Pf[s:e][m].mean() / (Pf[keep_ch].max() + 1e-30) + 1e-30)
        nbar = int(np.clip((v + 40.0) / 40.0 * 40, 0, 40))
        print(f"  {f_mhz[s]:>8.1f}..{f_mhz[e-1]:>7.1f}  {v:>+6.1f}  " + "#" * nbar)

    if occ.any():
        f_lo, f_hi = f_mhz[occ].min(), f_mhz[occ].max()
        print(f"\n  isgal edilen bant       : {f_lo:.3f} .. {f_hi:.3f} MHz "
              f"({f_hi - f_lo:.2f} MHz genis)")
        print(f"  bant ortasi             : {(f_lo + f_hi)/2:.3f} MHz  "
              f"<- CENTER_FREQ bunun uzerine oturmali")
        if CARRIER_BW_HZ:
            e_lo = (CENTER_FREQ - CARRIER_BW_HZ / 2) / 1e6
            e_hi = (CENTER_FREQ + CARRIER_BW_HZ / 2) / 1e6
            o_lo = (CENTER_FREQ - OCC_BW_HZ / 2) / 1e6
            o_hi = (CENTER_FREQ + OCC_BW_HZ / 2) / 1e6
            print(f"  beklenen kanal          : {e_lo:.3f} .. {e_hi:.3f} MHz "
                  f"({CARRIER_BW_HZ/1e6:.0f} MHz nominal)")
            print(f"  beklenen ISGAL          : {o_lo:.3f} .. {o_hi:.3f} MHz "
                  f"({OCC_BW_HZ/1e6:.2f} MHz, 273 RB)")
            print(f"  guard band              : {GUARD_BAND_HZ/1e3:.0f} kHz "
                  f"her kenarda (TS 38.104) — bu kenarlar BOS gorunmeli")
            print(f"  merkez kaymasi          : "
                  f"{(f_lo + f_hi)/2 - CENTER_FREQ/1e6:+.3f} MHz  "
                  f"(buyukse --freq ile duzelt)")
        if f_lo <= f_mhz[keep][0] + 1.0 or f_hi >= f_mhz[keep][-1] - 1.0:
            print("  [UYARI] isgal pencerenin KENARINA dayaniyor: tasiyici pencereden "
                  "tasiyor olabilir. --freq ile merkezi kaydirip tekrar bak.")
    else:
        print("\n  [UYARI] bandin uzerinde belirgin bir tasiyici YOK.")
        if not clip_n:
            print("          Frekans yanlis olabilir (telefonda NetMonster ile "
                  "NR-ARFCN'e bak) ya da anten yonu kotu.")
            print("          n78'i tarama ornegi: --freq 3430 / 3530 / 3630 "
                  "(pencere 122.88 MHz genis)")

    # Zaman profili: DL yayini olan binler (tabanin 6 dB uzeri)
    t_ms  = np.arange(ntb) * TB / FS * 1e3
    Pt_db = 10 * np.log10(Pt / (Pt.max() + 1e-30) + 1e-30)
    # Frekanstaki ile AYNI tuzak: NR TDD'de DL zamanin %70-80'idir, dolayisiyla
    # MEDYAN yayinin ICINE duser ve "medyan+6 dB" hicbir sey bulmaz. Sessiz
    # seviyeyi yine %10'luk dilimden al.
    t_floor = float(np.percentile(Pt_db[0], 10))
    duty, first = tdd_duty(Pt_db[0], t_floor)
    print(f"  zaman profili (gurultu tabani {t_floor:+.1f} dB, tepeye gore):")
    for lv, fr, meas in duty:
        print(f"    tepeden {lv:+.0f} dB uzeri : %{100*fr:>3.0f}"
              + ("" if meas else "   <- esik gurultu tabaninin ALTINDA, "
                                 "OLCULEMEZ (kazanci artir)"))
    print(f"    Esikler TEPEYE goredir, gurultu tabanina DEGIL -> bu oranlar")
    print(f"    KAZANCTAN BAGIMSIZ olmali. Farkli --gain ile degisiyorsa, "
          f"degisen")
    print(f"    esik 'olculemez' isaretli olandir.")
    print(f"  ilk yayin PPS +{t_ms[first]:.3f} ms  (tepeden -20 dB esigiyle)")

    fig, ax = plt.subplots(2, 1, figsize=(12, 8), constrained_layout=True)
    fig.suptitle(f"BAND TANISI — {CENTER_FREQ/1e6:.3f} MHz, Fs={FS/1e6:.2f} MHz, "
                 f"{used} yakalama x {win_ms:.0f} ms", fontweight="bold")
    ax[0].plot(f_mhz, Pf_db, lw=0.8, color="#00BFFF")
    if BAND_LIMIT_ON:
        ax[0].set_xlim(f_mhz[lo_i], f_mhz[hi_i - 1])
    ax[0].axhline(floor_db + 10.0, color="#FF1744", ls="--", lw=1,
                  label="isgal esigi (taban +10 dB)")
    if CARRIER_BW_HZ:
        for i, fe in enumerate([(CENTER_FREQ - CARRIER_BW_HZ / 2) / 1e6,
                                (CENTER_FREQ + CARRIER_BW_HZ / 2) / 1e6]):
            ax[0].axvline(fe, color="#FFEB3B", ls=":", lw=1.2,
                          label=(f"kanal kenari ({CARRIER_BW_HZ/1e6:.0f} MHz)"
                                 if i == 0 else None))
        for i, fo in enumerate([(CENTER_FREQ - OCC_BW_HZ / 2) / 1e6,
                                (CENTER_FREQ + OCC_BW_HZ / 2) / 1e6]):
            ax[0].axvline(fo, color="#FF9100", ls="--", lw=1.0,
                          label=(f"isgal kenari ({OCC_BW_HZ/1e6:.2f} MHz, "
                                 f"guard {GUARD_BAND_HZ/1e3:.0f} kHz)"
                                 if i == 0 else None))
    ax[0].set_xlabel("frekans [MHz]"); ax[0].set_ylabel("dB (tepeye gore)")
    ax[0].set_title("ortalama spektrum", loc="left"); ax[0].grid(alpha=0.3)
    ax[0].legend(fontsize=8)
    for k in range(N_RX):
        ax[1].plot(t_ms, Pt_db[k], lw=0.8, label=f"kanal {k}")
    ax[1].set_xlabel("PPS'ten sonra gecen sure [ms]")
    ax[1].set_ylabel("dB (tepeye gore)")
    ax[1].set_title("pencere ici guc profili (TDD deseni / DL yayin anlari)",
                    loc="left")
    ax[1].grid(alpha=0.3); ax[1].legend(fontsize=8, ncol=N_RX)
    print("\n  Grafik penceresini kapatinca cikilir.")
    print("=" * 70)
    plt.show()

# ═══════════════════════════════════════════════════════════════════
#  10c) --cell — HUCRE KIMLIGI (PSS/SSS -> PCI) + BANT OZETI
# ═══════════════════════════════════════════════════════════════════
def cell_probe(n_cap=3, win_ms=CELL_WIN_MS):
    """Baz istasyonunu dinle ve "anahtarini" cikar: PCI, SSB frekans/zamani,
    isgal edilen bant ve WB menzil cozunurlugu.

    --learn'den ONCE calistir: dogru hucreyi dinledigini ve WB'nin ne kadar
    bant bulacagini burada gorursun."""
    if not _HAVE_UHD:
        print("[HATA] uhd modulu yok."); sys.exit(1)
    print("=" * 70)
    print(f" HUCRE TANISI — {n_cap} x {win_ms:.1f} ms @ {CENTER_FREQ/1e6:.3f} MHz")
    print("=" * 70)
    ctx = setup_x410(win_s=win_ms * 1e-3, advance_s=PPS_OFFSET_S)
    bufs = []
    for i in range(int(n_cap) * 3):
        b, _ = acquire(ctx)
        if b is not None:
            bufs.append(b)
        if len(bufs) >= n_cap:
            break
    if not bufs:
        print("\n[HATA] yakalama alinamadi."); sys.exit(1)

    wb = wb_setup(bufs, quiet=False)
    band = (wb["f_lo"], wb["f_hi"])
    print(f"\n  {len(bufs)} yakalamada PSS/SSS araniyor "
          f"(SSB bant icinde varsayiliyor)...")
    found = []
    for i, b in enumerate(bufs):
        c = detect_cell(b, win_ms=win_ms, quiet=(i > 0), band=band)
        if c:
            found.append(c)
    if not found:
        print("\n[HATA] PSS bulunamadi. Kontrol et:")
        print("  * CENTER_FREQ dogru mu (--psd ile tasiyiciyi gor)")
        print("  * kazanc kirpiyor mu (--psd 'KIRPMA' uyarisi)")
        print("  * anten baz istasyonunu goruyor mu, GPSDO kilitli mi")
        sys.exit(1)
    pcis = [c["pci"] for c in found if c["pci"] is not None]
    if len(set(pcis)) > 1:
        print(f"\n  [UYARI] yakalamalar arasi PCI TUTARSIZ: {pcis} "
              f"-> zayif sinyal ya da birden fazla hucre goruluyor.")
    elif pcis:
        print(f"\n  {len(pcis)}/{len(bufs)} yakalamada AYNI PCI: {pcis[0]}  (tutarli)")
    print("=" * 70)
    return found[0]

# ------------------------------------------------------ IKI BANT KIYASI
def _band_report(caps, f_lo, f_hi, tag, lo_hz=None):
    """Bir bandin kimligi, COK YAKALAMADAN. lo_hz: gerceklesen LO. Doner dict.

    NEDEN COK YAKALAMA: tek 45 ms'lik yakalamada PSS/SSS gurultude de tepe
    verir ve her kosuda BASKA bir PCI cikar (sahada olculdu: 731/341, 287/471,
    110/168, 761/720 — hepsi ayni antenden, dakikalar arayla). --learn'in
    guvenilir olmasinin sebebi 120 yakalamayi biriktirmesiydi. Burada da ayni
    mantik: her yakalamada hucre cozulur, PBCH DMRS ile DOGRULANIR ve
    yakalamalar arasi TUTARLILIK aranir. Gercek hucre tekrar eder, gurultu
    etmez."""
    if not isinstance(caps, (list, tuple)):
        caps = [caps]
    lo, hi = f_lo - CENTER_FREQ, f_hi - CENTER_FREQ
    lo_hz = CENTER_FREQ if lo_hz is None else lo_hz
    print(f"\n  ---- {tag}: {f_lo/1e6:.1f} .. {f_hi/1e6:.1f} MHz "
          f"({len(caps)} yakalama) ----")
    tally, best, cfos, pws = {}, None, [], []
    for x in caps:
        xb = bandpass_sig(x, lo, hi)
        pws.append(float(np.mean(np.abs(xb) ** 2)))
        cf = cfo_cp(xb, max_ms=xb.size / FS * 1e3)
        if cf:
            cfos.append(cf)
        c = detect_cell(xb, win_ms=CELLS_WIN_MS, quiet=True, band=(lo, hi))
        if c is None or c.get("pci") is None:
            continue
        p = ssb_pbch_check(xb, c, quiet=True)
        if p is None:
            continue
        t = tally.setdefault(c["pci"], dict(n=0, nver=0, best=0.0, f_ssb=[]))
        t["n"] += 1
        t["nver"] += int(p["ratio"] > 1.8)
        t["best"] = max(t["best"], p["metric"])
        t["f_ssb"].append(c["f_ssb"])
        if p["ratio"] > 1.8 and (best is None or p["metric"] > best[1]["metric"]):
            best = (c, p, xb)

    pdb = 10 * np.log10(float(np.mean(pws)) + 1e-30) if pws else -99.0
    print(f"    ortalama guc  : {pdb:+.1f} dBFS")
    if tally:
        print(f"    {'PCI':>6} {'gorulme':>9} {'DOGRULANAN':>11} {'PBCH':>6} "
              f"{'SSB [MHz]':>11}")
        for pci, t in sorted(tally.items(), key=lambda kv: -kv[1]["nver"])[:5]:
            print(f"    {pci:>6} {t['n']:>6}/{len(caps):<2} {t['nver']:>11} "
                  f"{t['best']:>6.2f} {np.mean(t['f_ssb'])/1e6:>11.3f}")
    # KARAR: yakalamalarin en az yarisinda DOGRULANMIS PCI. Tek seferlik
    # eslesme gurultudur — sahada her kosuda baska PCI cikiyordu.
    need = max(2, (len(caps) + 1) // 2)
    win = [(pci, t) for pci, t in tally.items() if t["nver"] >= need]
    if not win or best is None:
        top = max(tally.values(), key=lambda t: t["nver"])["nver"] if tally else 0
        print(f"    -> TUTARLI hucre YOK (en iyi PCI {top}/{len(caps)} "
              f"yakalamada dogrulandi, gereken {need}).")
        print(f"       Bu blokta ya NR hucresi yok, ya sinyal cok zayif.")
        return dict(tag=tag, f_lo=f_lo, f_hi=f_hi, lo_hz=lo_hz, power_db=pdb,
                    cell=None, pbch=None, cs0=None, sib1=None, cfo=None,
                    tally=tally, nver=0, ncap=len(caps))
    cell, pbch, xb = best
    nver = tally[cell["pci"]]["nver"]
    print(f"    -> TUTARLI: PCI {cell['pci']}  ({nver}/{len(caps)} yakalamada "
          f"PBCH DMRS ile dogrulandi)")
    print(f"    SSB merkezi   : {cell['f_ssb']/1e6:.3f} MHz   i_SSB="
          f"{pbch['i_ssb']}  PBCH uyum {pbch['metric']:.2f} "
          f"(tepe/medyan {pbch['ratio']:.1f})")
    print(f"    SSB zamani    : PPS +{cell['t0']*1e3:.4f} ms"
          + (f",  tekrar {cell['period_ms']:.0f} ms" if cell["period_ms"] else ""))
    # CFO: yakalamalar arasi SACILMA en durust belirsizliktir (LO, hucre ve
    # olcum gurultusunun hepsini kapsar).
    cf = None
    if cfos:
        dfv = np.array([c["df"] for c in cfos])
        anc = np.array([c["anchor"] for c in cfos])
        cf = dict(df=float(np.median(dfv)),
                  sd=float(np.std(dfv)) / np.sqrt(len(dfv)) if len(dfv) > 1
                     else cfos[0]["sd"],
                  n=int(np.sum([c["n"] for c in cfos])),
                  anchor=int(np.median(anc)),
                  coh=float(np.median([c["coh"] for c in cfos])),
                  spread=float(np.std(dfv)))
        print(f"    izgara sapmasi: {cf['df']:+.2f} Hz +- {cf['sd']:.2f}  "
              f"(yakalamalar arasi sacilma {cf['spread']:.1f} Hz, "
              f"koherans {cf['coh']:.3f})")
        print(f"                    [LO yerlesimi dahil — tek basina anlamsiz]")
        print(f"    sembol fazi   : {cf['anchor']} ornek "
              f"({cf['anchor']/FS*1e6:.3f} us)")
    cs0 = coreset0_scan(xb, cell)
    sib1 = sib1_check(xb, cell, cs0)
    return dict(tag=tag, f_lo=f_lo, f_hi=f_hi, lo_hz=lo_hz, power_db=pdb,
                cell=cell, pbch=pbch, cs0=cs0, sib1=sib1, cfo=cf,
                tally=tally, nver=nver, ncap=len(caps))

def _grab(ctx, n, tag):
    """n yakalama al, ADC sagligini SADECE ilkinde raporla. Doner: liste."""
    out = []
    for k in range(n):
        buf, _ = acquire(ctx)
        if buf is None:
            print(f"  [UYARI] {tag}: {k+1}. yakalama basarisiz, atlaniyor.")
            continue
        if k == 0:
            adc_report(adc_health(buf),
                       10 * np.log10(np.mean(np.abs(np.asarray(buf)[0]) ** 2)
                                     + 1e-30), RX_GAIN)
        out.append(np.asarray(buf)[0].astype(np.complex64))
    if not out:
        print(f"[HATA] {tag}: hicbir yakalama alinamadi."); sys.exit(1)
    return out

def cells_run(win_ms=CELLS_WIN_MS, bands=None, n_cap=CELLS_N_CAP):
    """--cells: iki blogu karsilastirip 1 mi 2 mi gNB oldugunu soyler.

    Iki yol var:
      TEK YAKALAMA  (kapsam <= %80 FS) — ortak LO, iki blok ayni anda.
      BLOK BASINA   (aksi halde)       — her blok kendi merkezine tune edilir.
    Ikincisi de gecerlidir: kiyasi bozan sey BIZIM LO hatamiz olurdu, ama LO
    GPSDO'ya kilitli (~1e-11 -> 3.5 GHz'de 0.04 Hz), yani esigin (~3 Hz) iki
    mertebe altinda. Ustelik her blok pencerenin DUZ kismina oturdugu icin
    SNR daha iyi olur. Yakalamalar PPS tetikli oldugundan sembol-izgarasi
    fazi kiyasi da gecerli kalir."""
    bands = bands or [CELLS_BAND_A, CELLS_BAND_B]
    f_min = min(b[0] for b in bands)
    f_max = max(b[1] for b in bands)
    span = f_max - f_min
    ctr = 0.5 * (f_min + f_max)
    single = span <= CELLS_SPAN_FRAC * FS
    print("=" * 70)
    print(" KOMSU BANT TARAMASI — iki blok tek gNB mi, iki gNB mi?")
    print("=" * 70)
    print(f"  bloklar   : " + "   ".join(f"{a/1e6:.0f}-{b/1e6:.0f}" for a, b in bands)
          + " MHz")
    print(f"  kapsam    : {span/1e6:.1f} MHz  (pencere {FS/1e6:.2f} MHz, "
          f"guvenli {CELLS_SPAN_FRAC*FS/1e6:.1f} MHz)")
    if single:
        print(f"  yontem    : TEK YAKALAMA, ortak LO {ctr/1e6:.3f} MHz")
    else:
        print(f"  yontem    : BLOK BASINA yakalama (kapsam guvenli sinirin "
              f"ustunde)")
        print(f"              LO GPSDO'ya kilitli (~0.04 Hz) -> kiyas gecerli; "
              f"her blok")
        print(f"              pencerenin duz kisminda kaldigi icin SNR de daha iyi.")
    # Osilator kiyasi, LO'dan gelen sabit terimin IKI BLOKTA DA AYNI olmasina
    # dayanir; bu da nominal merkezlerin farkinin SCS'in tam kati olmasini
    # gerektirir. Sart saglanmiyorsa kiyas yapilmaz, sadece raporlanir.
    dctr = abs(0.5 * (bands[1][0] + bands[1][1]) - 0.5 * (bands[0][0] + bands[0][1]))
    rem = abs(dctr - SCS_HZ * round(dctr / SCS_HZ))
    print(f"  merkez farki: {dctr/1e6:.3f} MHz = {dctr/SCS_HZ:.3f} x SCS  "
          + ("-> osilator kiyasi GECERLI" if rem < 1.0 else
             f"-> KALAN {rem/1e3:.1f} kHz, osilator kiyasi GUVENILMEZ"))
    print(f"  NOT: bu mod LO'yu OYNATIR ve kanallar arasi fazi bozar; TEK BASINA "
          f"calistir\n       (olcum/kalibrasyon oturumuyla ayni process'te degil).")

    f_save, bl_save = CENTER_FREQ, BAND_LIMIT_ON
    globals()["BAND_LIMIT_ON"] = False        # tarama bilerek tum pencereyi gorur
    rep = []
    try:
        globals()["CENTER_FREQ"] = ctr if single else 0.5 * (bands[0][0] + bands[0][1])
        ctx = setup_x410(win_s=win_ms * 1e-3, advance_s=PPS_OFFSET_S)
        if single:
            caps = _grab(ctx, n_cap, "iki blok")
            rep = [_band_report(caps, a, b, f"BLOK {chr(65+i)}", lo_hz=ctr)
                   for i, (a, b) in enumerate(bands)]
        else:
            # LO'lari SCS izgarasina oturt: LO farki SCS'in tam kati olursa
            # osilator kiyasindaki mod terimi temiz duser (bkz. cells_verdict).
            lo0 = 0.5 * (bands[0][0] + bands[0][1])
            for i, (a, b) in enumerate(bands):
                want = lo0 + SCS_HZ * round((0.5 * (a + b) - lo0) / SCS_HZ)
                print(f"\n  >>> BLOK {chr(65+i)} icin tune ediliyor...")
                got = retune(ctx, want)
                acquire(ctx)                   # LO oturma yakalamasi (atilir)
                caps = _grab(ctx, n_cap, f"BLOK {chr(65+i)}")
                rep.append(_band_report(caps, a, b, f"BLOK {chr(65+i)}", lo_hz=got))
    finally:
        globals()["CENTER_FREQ"] = f_save
        globals()["BAND_LIMIT_ON"] = bl_save
    cells_verdict(rep)
    return rep

def cells_verdict(rep):
    """Kanitlari tartip karar ver. Kesin konusmaz — hangi olcum ne diyor yazar."""
    print("\n" + "=" * 70)
    print(" KARAR")
    print("=" * 70)
    ok = [r for r in rep if r["cell"] is not None]
    if len(ok) < 2:
        names = ", ".join(r["tag"] for r in rep if r["cell"] is None)
        print(f"  {names} icinde NR hucresi cozulemedi.")
        print("  -> Bu blok ya baska bir operatorun tasiyicisi, ya SSB'siz bir")
        print("     ikincil tasiyici (SCell), ya da bizim pencerenin kenarinda")
        print("     kirpilmis durumda. Karsilastirma yapilamadi.")
        return None
    a, b = ok[0], ok[1]
    print(f"  {'olcum':<22}{a['tag']:>18}{b['tag']:>18}   {'yorum':>0}")
    print("  " + "-" * 66)
    print(f"  {'PCI':<22}{str(a['cell']['pci']):>18}{str(b['cell']['pci']):>18}")

    vote_same, vote_diff, notes = 0, 0, []

    # 1) OSILATOR — mutlak sapma DEGIL, IKI BLOGUN FARKI.
    # cfo_cp mutlak degeri veremez: olctugu sey (izgara - LO) ve icinde LO'yu
    # nereye koydugumuzdan gelen sabit bir terim var. Cebir:
    #     cfo_k = (izgara_k - LO_k)  (mod SCS)
    #     cfo_B - cfo_A = (izgara_B - izgara_A) - (LO_B - LO_A)   (mod SCS)
    # Iki tasiyici AYNI RU'dan geliyorsa altasiyici izgaralari AYNI kafestedir,
    # yani (izgara_B - izgara_A) SCS'in tam katidir ve mod'da dusar; geriye
    # sadece osilator terimi kalir:
    #     eps_B f_B - eps_A f_A = (cfo_B - cfo_A) + (LO_B - LO_A)   (mod SCS)
    # Tek osilatorde bu eps*(f_B-f_A) olur; |eps|<50 ppb icin en fazla ~3 Hz.
    # LO farkini GERI EKLEMEK sart: blok basina yakalamada iki LO farklidir ve
    # eklenmezse LO yerlesimi osilator hatasi gibi gorunur.
    if a["cfo"] and b["cfo"]:
        fa = 0.5 * (a["f_lo"] + a["f_hi"])
        fb = 0.5 * (b["f_lo"] + b["f_hi"])
        d = (b["cfo"]["df"] - a["cfo"]["df"]) + (b["lo_hz"] - a["lo_hz"])
        d = d - SCS_HZ * round(d / SCS_HZ)                  # +-SCS/2'ye sar
        half = d - SCS_HZ / 2 * round(d / (SCS_HZ / 2))     # yarim altasiyici
        raster = abs(abs(d) - SCS_HZ / 2) < 0.05 * SCS_HZ
        if raster:
            d = half                                        # 15 kHz raster kaymasi
        sd = float(np.hypot(a["cfo"]["sd"], b["cfo"]["sd"]))
        tol = max(4.0 * sd, 3.0)
        lim = 50e-9 * abs(fb - fa)                          # tek osilator siniri
        print(f"  {'izgara sapmasi [Hz]':<22}{a['cfo']['df']:>18.2f}"
              f"{b['cfo']['df']:>18.2f}")
        print(f"  {'  fark (SCS mod)':<22}{d:>18.2f}   "
              f"(esik {max(tol, lim):.2f} Hz)"
              + ("  [yarim altasiyici raster kaymasi giderildi]" if raster else ""))
        # Test ASIMETRIKTIR ve oyle kullanilmalidir:
        #   "AYRI" demek KOLAY  — sadece |d| gurultunun cok ustunde olmali.
        #   "AYNI" demek ZOR    — gurultunun, tek osilatorun uretebilecegi
        #                         azami sapmadan (lim) kucuk olmasi gerekir;
        #                         yoksa "fark kucuk" cumlesi hicbir sey elemez.
        # Once kolay olani sina, sonra zor olani, olmadi CEKIMSER kal.
        thr = max(3.0 * sd, lim)
        if abs(d) > thr:
            vote_diff += 2
            eq_ppb = abs(d) / (0.5 * (fa + fb)) * 1e9
            notes.append(f"izgara farki {abs(d):.1f} Hz > esik {thr:.1f} Hz — tek "
                         f"osilatorle aciklanamaz; iki tasiyici arasinda "
                         f"~{eq_ppb:.0f} ppb'lik bagimsiz sapma var "
                         f"-> AYRI OSILATOR")
        elif 2.0 * sd < lim:
            vote_same += 2
            notes.append(f"izgara farki {abs(d):.2f} Hz, olcum gurultusu "
                         f"+-{sd:.2f} Hz; tek osilatorun azami sapmasi {lim:.1f} Hz "
                         f"-> AYNI REFERANS OSILATOR")
        else:
            notes.append(f"osilator testi CEKIMSER: gurultu +-{sd:.1f} Hz, ayirt "
                         f"etmesi gereken esik {lim:.1f} Hz. Fark {abs(d):.1f} Hz "
                         f"ne dogrulamaya ne curutmeye yeter "
                         f"(kazanci artir / pencereyi buyut).")

    # 2) SEMBOL IZGARASI FAZI — huzme indisinden etkilenmez, SSB t0'indan saglam
    aa, ab = a["cfo"], b["cfo"]
    if aa and ab:
        per = N_FFT + CP_NORM
        da = (ab["anchor"] - aa["anchor"] + per // 2) % per - per // 2
        us = da / FS * 1e6
        m_per_us = C_AIR * 1e-6                       # 299.79 m her mikrosaniyede
        print(f"  {'sembol fazi [ornek]':<22}{aa['anchor']:>18d}{ab['anchor']:>18d}")
        print(f"  {'  fark':<22}{da:>18d}   "
              f"({us:+.3f} us = {us*m_per_us:+.1f} m)")
        if abs(da) <= 4:
            vote_same += 1
            notes.append(f"sembol izgaralari {abs(da)} ornek icinde ortusuyor "
                         f"-> ayni saat, ayni anten konumu")
        else:
            vote_diff += 1
            notes.append(f"sembol izgaralari {abs(da)} ornek ({abs(us):.2f} us) "
                         f"kayik -> {abs(us)*m_per_us:.0f} m yol farki ya da "
                         f"ayri senkron")
    print(f"  {'SSB zamani [ms]':<22}{a['cell']['t0']*1e3:>18.4f}"
          f"{b['cell']['t0']*1e3:>18.4f}")

    # 3) PBCH DMRS — her iki blok da standarda gore dogrulandi mi?
    for r in (a, b):
        p = r["pbch"]
        txt = f"i_SSB={p['i_ssb']}, uyum {p['metric']:.2f}" if p else "yok"
        print(f"  {'PBCH DMRS ' + r['tag']:<22}{txt:>36}")
    if a["pbch"] and b["pbch"] and min(a["pbch"]["ratio"], b["pbch"]["ratio"]) > 1.8:
        notes.append("iki blokta da PBCH DMRS tuttu -> ikisi de GERCEK NR hucresi")

    # 4) SIB1 / CORESET#0 — bagimsiz hucre olmanin sarti
    for r in (a, b):
        c = r["cs0"]
        txt = f"{c['n_rb']} RB, uyum {c['metric']:.2f}" if c else "yok"
        print(f"  {'CORESET#0 ' + r['tag']:<22}{txt:>36}")
    # SIB1 iddiasi SIB1 olcumune dayanmali — CORESET#0 metrigine DEGIL.
    sb_a = bool(a["sib1"]) and a["sib1"]["metric"] > 0.45
    sb_b = bool(b["sib1"]) and b["sib1"]["metric"] > 0.45
    if sb_a and sb_b:
        notes.append("iki blok da SIB1 yayinliyor -> ikisi de BAGIMSIZ hucre "
                     "(ayni siteden olabilir)")
    elif sb_a != sb_b:
        w = a["tag"] if not sb_a else b["tag"]
        notes.append(f"{w} icinde SIB1 GORULEMEDI -> bagimsiz hucre oldugu "
                     f"dogrulanamadi (ikincil tasiyici olabilir, ya da SNR yetersiz)")
    else:
        notes.append("hicbir blokta SIB1 dogrulanamadi -> CORESET#0 eslesmeleri "
                     "gurultu olabilir, bu satira DAYANMA")

    # --- GUVEN KAPISI ---
    # PBCH DMRS tutmadiysa PCI'nin kendisi guvenilmez: PSS/SSS gurultude de
    # tepe verir. O zaman ustteki butun kiyaslar YANLIS hucreleri kiyaslar.
    unver = [r["tag"] for r in (a, b)
             if not (r["pbch"] and r["pbch"]["ratio"] > 1.8)]
    print("\n  KANITLAR")
    for n in notes:
        print(f"    - {n}")
    if unver:
        print(f"\n  [KRITIK] {', '.join(unver)} icinde PBCH DMRS DOGRULANMADI.")
        print("           PSS/SSS gurultude de tepe verir; standarda gore")
        print("           dogrulanmamis bir PCI ile yapilan kiyas anlamsizdir.")
        print("\n  SONUC: KARAR YOK — olcum yeterince guvenilir degil.")
        print("         Yapilacaklar (sirayla):")
        # Tavsiye OLCUME dayanmali: doyma varsa kazanci ARTIRMAK zarar verir.
        pw = [r["power_db"] for r in (a, b)]
        if max(pw) > -12.0:
            print(f"           1) KAZANCI DUSUR — seviye {max(pw):+.0f} dBFS, "
                  f"kirpma hucreyi bozuyor")
        elif max(pw) < -30.0:
            print(f"           1) kazanci artir — seviye {max(pw):+.0f} dBFS, "
                  f"hedef -25..-15 dBFS")
        else:
            print(f"           1) seviye ({max(pw):+.0f} dBFS) IYI — sorun "
                  f"kazanc DEGIL")
        print(f"           2) --cells {2*max(r.get('ncap', 1) for r in (a, b))}"
              f" ile yakalama sayisini artir")
        print("           3) anteni dogrulanamayan bloga yonlendir")
        print("           4) --psd --fullband ile o blokta gercekten guc var mi bak")
        return dict(vote_same=vote_same, vote_diff=vote_diff, notes=notes,
                    verdict="belirsiz", unverified=unver)
    print("\n  SONUC: ", end="")
    if vote_same > vote_diff:
        print("AYNI BAZ ISTASYONU (tek gNB / tek RU, iki tasiyici).")
        print("         Iki blogu tek genis bant olarak kullanmak FIZIKSEL olarak")
        print("         mumkun ama koherent degildir: ayri PCI, ayri izgara.")
    elif vote_diff > vote_same:
        print("AYRI BAZ ISTASYONLARI.")
        print("         Komsu blogu ISLEME SOKMA — farkli yonden gelir, "
              "equalizer'i")
        print("         ve aci kestirimini bozar. BAND_LIMIT_ON dogru ayarda.")
    else:
        print("KARARSIZ — kanitlar bolundu, olcumu tekrarla "
              "(kazanci artir, pencereyi buyut).")
    return dict(vote_same=vote_same, vote_diff=vote_diff, notes=notes)



# ===================================================================
#  OLCUM MODLARI — calib, locate, range, auto
# ===================================================================

# ══════════════════════════════════════════════════════════════════
#  8) KALIBRASYON — BOS SAHA, TEK ASAMA, LOS'TAN
# ══════════════════════════════════════════════════════════════════
# Saha BOSKEN olculur (hedef yok). Tek gecisde uc sey cikar:
#   1) FREKANS BASINA equalizer — LOS'un TAM BANDINDAN (~100 MHz) kestirilir,
#      sonra KORELASYON izgarasinda degerlendirilir. Dort antenin hepsi kullanilir.
#      Neden tam bant: SSB sadece ~7.2 MHz ve genelde bant ortasinda DEGIL. Tek
#      bir bant-ortalamasi katsayi SSB'nin durdugu yerde 10-15 derece yanlis olur;
#      taplari tam banttan cikarip SSB'nin yerinde degerlendirmek bunu duzeltir.
#   2) DURGUN ORTAM haritasi — dogrudan yol + binalar/zemin, KORELASYON (CIR)
#      domeninde saklanir. Canlida cikarilinca geriye sahaya SONRADAN giren her
#      sey kalir; hedefin HAREKETLI olmasi gerekmez.
#      CIR olarak saklamanin sebebi: CIR sahnenin fiziksel yanitidir, dalga
#      formundan bagimsizdir. Ileride referans SSB'den daha genise tasindiginda
#      (alim basina degisen dalga formu) ayni dosya gecerli kalir.
#   3) n_dir — dogrudan yol capasi; bilinmeyen TX<->RX donanim gecikmesi buraya
#      gomulur ve her sey ona GORE olculur.
# Bilinen hedefli ikinci asama KALDIRILDI: kanal kalibrasyonunu LOS zaten veriyor
# ve LOS'un yonu geometriden biliniyor.
def calib_run(seconds=CAL_SECONDS, key_path=None, out_path=None, plot=True):
    """BOS SAHA kalibrasyonu — tek asama. Sonuc CAL_FILE'a yazilir."""
    if not _HAVE_UHD:
        print("[HATA] uhd modulu yok. --self-test kullan."); sys.exit(1)
    if out_path is None:
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CAL_FILE)

    print("=" * 70)
    print(f" BOS SAHA KALIBRASYONU — {seconds} s, {N_RX} kanal, frekans basina equalizer")
    print("=" * 70)
    check_spacing()
    el = element_positions()
    Dk = np.linalg.norm(el - TX_POS[None, :], axis=1)
    print(f"  TX (baz ist.) : {TX_POS}   n1={_unit(TX_N1)}  huzme {TX_BW3_DEG:.0f} der")
    print(f"  Dizi ortasi   : {ARRAY_POS}  n2={_unit(ARRAY_N2)}  d={ARRAY_D_M*100:.2f} cm")
    print(f"  |RX_k - TX|   : " + "  ".join(f"{d:.3f}" for d in Dk) + " m")

    refs, step_s, t_ref = _build_refs(key_path)
    ctx = setup_x410(win_s=LOC_WIN_MS * 1e-3, advance_s=0.0, pps_offset=t_ref)
    N = ctx["N_act"]
    # Oturum baska bir PPS ofsetinde acilmis olabilir (tek oturum zinciri):
    # pencere yeniden ACILAMAZ, o yuzden kaymayi occasion yerlesimine ver.
    _off0 = int(round((t_ref - ctx["pps_off"]) * FS))
    occ, cls, n_cls, L_seg, nlag = _occasion_layout(N, refs, step_s, _off0)
    nfft = 1 << int(np.ceil(np.log2(L_seg + len(refs[0]) - 1)))
    D0 = float(np.linalg.norm(ARRAY_POS - TX_POS))
    print(f"\n  occasion  : {len(occ)} adet ({n_cls} sinif), slot {L_seg} ornek, "
          f"nlag {nlag} ({nlag/FS*C_AIR:.1f} m bistatik acilim)")
    print(f"  referans  : ogrenilmis SSB anahtari  (korelasyon nfft {nfft})")

    # --- equalizer icin tam bant plani ---
    print("\n  LOS bandi olculuyor (equalizer bu bantta kestirilecek)...")
    probe = []
    for _ in range(8):
        b0, _ = acquire(ctx)
        if b0 is not None:
            probe.append(b0)
        if len(probe) >= 2:
            break
    if not probe:
        print("\n[HATA] yakalama alinamadi."); sys.exit(1)
    wb = wb_setup(probe)

    input("\n  Saha BOS olmali (hedef YOK). Hazir olunca ENTER'a bas...")
    bg_t, num, den = _measure_background(ctx, refs, occ, cls, n_cls, L_seg,
                                         seconds, "BOS SAHA", wb=wb)

    # --- 1) frekans basina equalizer (tam banttan, korelasyon izgarasinda) ---
    eqf = wb_los_eq(num, den, wb)
    EQ_wb = eqf["EQ"]
    _, eq_inv = eq_from_taps(eqf["taps"], nfft)

    # --- 2) durgun ortam haritasi: ESITLENMIS spektrumdan korelasyon ---
    bg_cir = np.stack([_corr_all(bg_t[c], refs[c], nfft, nlag, eq_inv)
                       for c in range(n_cls)])

    # --- 3) dogrudan yol capasi ---
    n_dir = int(np.argmax(np.abs(bg_cir[0][0])))

    # --- equalizer'in SSB bandindaki degeri (asil uygulanan yer) ---
    key_spec = np.abs(np.fft.fft(refs[0], nfft)) ** 2
    kb = key_spec > 0.05 * key_spec.max()          # anahtarin gercekten dolu binleri
    fb_corr = np.fft.fftfreq(nfft, 1.0 / FS)
    EQ_corr, _ = eq_from_taps(eqf["taps"], nfft)
    f_key = float(np.sum(fb_corr * key_spec) / (np.sum(key_spec) + 1e-30))
    bw_key = float(np.sqrt(np.sum(((fb_corr - f_key) ** 2) * key_spec) /
                           (np.sum(key_spec) + 1e-30))) * 2 * np.sqrt(3)

    print("\n" + "=" * 70)
    print(" KALIBRASYON SONUCU")
    print("=" * 70)
    print(f"  dogrudan yol capasi n_dir = {n_dir} ornek "
          f"(LOS |dizi-TX|={D0:.2f} m'e denk; HW gecikmesi buraya gomuldu)")
    print(f"  anahtarin bandi           : merkez {(CENTER_FREQ+f_key)/1e6:.3f} MHz, "
          f"~{bw_key/1e6:.2f} MHz genis  -> menzil cozunurlugu "
          f"~{C_AIR/(2*max(bw_key,1e3)):.1f} m")
    print(f"  LOS bandi (equalizer)     : {wb['bw']/1e6:.2f} MHz")
    print(f"\n  EQUALIZER — anahtarin bandindaki degerler (kanal 0 referans):")
    print(f"  {'kanal':>6} {'genlik[dB]':>11} {'faz[der]':>10} "
          f"{'bant ici sapma':>16} {'tam bant sapmasi':>18}")
    for k in range(N_RX):
        z = EQ_corr[k][kb]
        ph = np.degrees(np.angle(z * np.conj(np.median(z))))
        print(f"  {k:>6} {20*np.log10(np.abs(z).mean()+1e-30):>+11.2f} "
              f"{np.degrees(np.angle(np.median(z))):>+10.2f} "
              f"{((ph+180)%360-180).std():>15.2f}d "
              f"{eqf['rms_deg'][k]:>17.2f}d"
              + ("   <- referans" if k == 0 else ""))
    print(f"\n  Not: 'bant ici sapma' anahtarin dar bandindaki degisim (kucuk cikar),")
    print(f"       'tam bant sapmasi' LOS'un 100 MHz'indeki degisim. Ikincisi")
    print(f"       buyukse tek katsayili kalibrasyon anahtarin YERINDE yanlis")
    print(f"       deger verirdi — duzelttigimiz asil hata bu.")

    # LOS fazi geometriyle tutarli mi (geometri/kablo sirasi dogrulamasi)
    vk = bg_cir[0][:, n_dir]
    exp_ = np.exp(-2j * np.pi * CENTER_FREQ * (Dk - Dk[0]) / C_AIR)
    los_err = np.degrees(np.angle(vk * np.conj(vk[0]) * np.conj(exp_)))
    print(f"\n  LOS faz artigi (equalizer sonrasi, geometriye gore) [der]: "
          + "  ".join(f"{e:+.1f}" for e in los_err))
    if np.max(np.abs(los_err[1:])) > 25.0:
        print("  [UYARI] LOS fazi geometriyle uyusmuyor: ARRAY_D_M / ARRAY_ORDER_SIGN /")
        print("          ARRAY_N2 ya da kablo sirasi (RX_CHANS) yanlis olabilir.")

    # --- DOGRULAMA: sablon gercekten dogrudan yolu iptal ediyor mu? ---
    # Kalibrasyonun tek anlamli sinavi budur. Saha HALA BOS oldugu icin
    # cikarmadan sonra geriye (ideal olarak) sadece gurultu kalmali.
    print(f"\n  Dogrulama: {CAL_VERIFY_N} taze bos saha yakalamasi...")
    sup, flo, pk_lag = [], [], []
    for i in range(CAL_VERIFY_N):
        b2, _ = acquire(ctx)
        if b2 is None:
            continue
        Cb, Cr, _ = capture_corr(b2, refs, occ, cls, n_cls, L_seg, nlag,
                                 bg=bg_cir, n_dir=n_dir, return_raw=True,
                                 eq_inv=eq_inv, bg_t=bg_t)
        # BASTIRMA'nin dogru tanimi: AYNI BINDE (dogrudan yol bini) cikarma
        # oncesi/sonrasi orani. "Artigin tum profildeki azamisi / LOS tepesi"
        # BASKA bir seydir (artik taban) ve ikisini karistirmak +dB gibi
        # anlamsiz degerler uretir.
        sup.append(20 * np.log10(np.abs(Cb[:, n_dir]) /
                                 (np.abs(Cr[:, n_dir]) + 1e-30) + 1e-30))
        flo.append(20 * np.log10(np.abs(Cb).max(axis=1) /
                                 (np.abs(Cr[:, n_dir]) + 1e-30) + 1e-30))
        pk_lag.append(int(np.argmax(np.abs(Cr[0]))))
    if sup:
        sup = np.mean(sup, axis=0); flo = np.mean(flo, axis=0)
        lag_mode = int(np.round(np.mean(pk_lag)))
        print(f"\n  DOGRUDAN YOL BASTIRMA (ayni binde, cikarma oncesi/sonrasi):")
        print(f"    " + "  ".join(f"k{k}: {sup[k]:+6.1f} dB" for k in range(N_RX)))
        print(f"  ARTIK TABAN (profil azamisi / LOS tepesi):")
        print(f"    " + "  ".join(f"k{k}: {flo[k]:+6.1f} dB" for k in range(N_RX)))
        print(f"    artik frekans kaymasi: {capture_corr.last_df:+.1f} Hz, "
              f"genlik katsayisi {capture_corr.last_amp:.3f}")
        if lag_mode != n_dir:
            print(f"\n  [KRITIK] canli LOS tepesi lag {lag_mode}'de ama n_dir="
                  f"{n_dir}. Capa KAYMIS ({(lag_mode-n_dir)/FS*C_AIR:+.1f} m):")
            print(f"           cikarma yanlis bine oturuyor. Anahtar kirpmasi "
                  f"(--keymax) ya da --step degismis olabilir.")
        # BEKLENEN TABAN: cikarma yalnizca DETERMINISTIK kismi silebilir.
        # Kalan, occasion'dan occasion'a DEGISEN icerigin M ortalamadan sonraki
        # halidir. Uyum olcutu gamma bu orani verir:
        #     gamma = (1 + r/M)/(1 + r),  r = (degisen guc)/(deterministik guc)
        # taban_dB = 10*log10(r / M_canli)
        g = _measure_background.last_coh
        M_occ = max(2, len(occ) // max(n_cls, 1))
        if 1.0 / M_occ + 1e-4 < g < 1.0:
            r = (1.0 - g) / (g - 1.0 / M_occ)
            floor_db = 10 * np.log10(r / M_occ + 1e-30)
            print(f"\n  Beklenen taban (uyum {g:.4f}, yakalama basina {M_occ} "
                  f"occasion): {floor_db:+.1f} dB")
            print(f"    Bu bir HATA DEGIL, INTEGRASYON sinriridir: cikarma sadece")
            print(f"    deterministik kismi siler; degisen icerik ancak ortalamayla")
            print(f"    duser. --avg N ile N yakalama daha ortalanir -> "
                  f"10*log10(N) dB daha iyi.")
            print(f"    ornek: --avg 8 -> ~{floor_db - 10*np.log10(8):+.1f} dB")
        worst = float(np.max(sup))
        if worst > -20.0:
            print(f"\n  [KRITIK] bastirma yetersiz ({worst:+.1f} dB). Kalibrasyon")
            print(f"           KULLANILABILIR DEGIL. Olasi sebepler:")
            print(f"     * saha kalibrasyon sirasinda BOS DEGILDI ya da bir sey hareket etti")
            print(f"     * anahtar zayif/yanlis (--learn'i tekrarla, 'tutarli %' dusukse")
            print(f"       hucre yuku degismis olabilir)")
            print(f"     * --step yanlis: occasion'lar deterministik ana denk gelmiyor")
            print(f"     * kazanc kirpiyor (--psd ile bak)")
        elif worst > -30.0:
            print(f"\n  [UYARI] bastirma orta ({worst:+.1f} dB). Beklenen -35..-45 dB.")
            print(f"          Hedef yankisi bu tabanin ustunde kalmali.")
        else:
            print(f"\n  Bastirma iyi (en kotu {worst:+.1f} dB).")
    else:
        sup = np.zeros(N_RX)
        print("  [UYARI] dogrulama yakalamasi alinamadi.")

    np.savez(out_path,
             bg_t=np.stack(bg_t).astype(np.complex64),   # ZAMAN domeni sablonu
             suppress_db=np.asarray(sup, float),
             eq_taps=eqf["taps"], eq_gate=eqf["gate"],
             eq_wb=EQ_wb, wb_mask=wb["mask"], wb_nfft=wb["nfft"],
             wb_bw=wb["bw"], wb_f_lo=wb["f_lo"], wb_f_hi=wb["f_hi"],
             bg=bg_cir, n_dir=n_dir, D0=D0,
             n_cls=n_cls, L_seg=L_seg, nlag=nlag, corr_nfft=nfft,
             seconds=int(seconds), los_err=los_err,
             center_freq=CENTER_FREQ, fs=FS, rx_gain=RX_GAIN,
             array_d=ARRAY_D_M, tx_pos=TX_POS, array_pos=ARRAY_POS,
             tx_n1=_unit(TX_N1), array_n2=_unit(ARRAY_N2),
             order_sign=ARRAY_ORDER_SIGN, key_path=(key_path or ""))
    print(f"\n  Kaydedildi: {out_path}")
    print(f"  Kullanim  : python3 {os.path.basename(__file__)} --locate {LOC_DUR_S} "
          f"--cal {CAL_FILE}" + (f" --key {os.path.basename(key_path)}" if key_path else ""))
    print("=" * 70)

    if plot:
        _plot_eq(EQ_wb, wb, int(seconds), extra_mask=None)
    return dict(eq_taps=eqf["taps"], bg=bg_cir, n_dir=n_dir)

def _plot_eq(EQ, wb, n_cap, extra_mask=None):
    """Frekans basina equalizer'in genlik/faz grafigi (4 kanal)."""
    import matplotlib.pyplot as plt
    f_mhz = np.fft.fftshift(wb["f_abs"]) / 1e6
    EQs = np.fft.fftshift(EQ, axes=1)
    ms  = np.fft.fftshift(wb["mask"])
    fig, ax = plt.subplots(2, 1, figsize=(12, 8), constrained_layout=True, sharex=True)
    fig.suptitle(f"LOS EQUALIZER — kanal_k / kanal_0, frekans basina   "
                 f"({CENTER_FREQ/1e6:.2f} MHz, bant {wb['bw']/1e6:.1f} MHz, "
                 f"{n_cap} yakalama)", fontweight="bold")
    col = ["#00BFFF", "#00E676", "#FFEB3B", "#FF1744"]
    for k in range(N_RX):
        z = np.where(ms, EQs[k], np.nan)
        ax[0].plot(f_mhz, 20 * np.log10(np.abs(z) + 1e-30), lw=1.0,
                   color=col[k], label=f"kanal {k}")
        ph = np.degrees(np.angle(z))
        ax[1].plot(f_mhz, (ph + 180) % 360 - 180, lw=1.0, color=col[k],
                   label=f"kanal {k}")
    if extra_mask is not None:
        km = np.fft.fftshift(extra_mask)
        for i in (0, 1):
            ax[i].fill_between(f_mhz, *ax[i].get_ylim(), where=km, alpha=0.12,
                               color="w", label="anahtarin bandi" if i == 0 else None)
    ax[0].set_ylabel("|EQ| [dB]"); ax[0].grid(alpha=0.3)
    ax[0].set_title("genlik — duz olmayan her sey RX zinciri uyumsuzlugudur",
                    loc="left", fontsize=9)
    ax[1].set_ylabel("faz [derece]"); ax[1].set_xlabel("frekans [MHz]")
    ax[1].grid(alpha=0.3)
    ax[1].set_title("faz — egim = kablo/gecikme farki, kavis = filtre farki",
                    loc="left", fontsize=9)
    ax[0].legend(fontsize=8, ncol=N_RX); ax[1].legend(fontsize=8, ncol=N_RX)
    print("\n  Grafik penceresini kapatinca cikilir.")
    plt.show()

def load_konum_cal(path, corr_nfft=None):
    """Bos saha kalibrasyonunu yukle. Doner equalizer tersi + durgun harita."""
    if not os.path.isabs(path):
        cand = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        path = cand if os.path.exists(cand) else path
    if not os.path.exists(path):
        print(f"[HATA] kalibrasyon dosyasi yok: {path}. Once --calib ile olc.")
        sys.exit(1)
    d = np.load(path, allow_pickle=False)
    if "eq_taps" not in d.files:
        print(f"[HATA] {os.path.basename(path)} ESKI bicimde (tek katsayili).")
        print("       Yeni bos saha kalibrasyonunu --calib ile tekrar al.")
        sys.exit(1)
    if abs(float(d["fs"]) - FS) > 1.0:
        print(f"[HATA] kalibrasyon Fs={float(d['fs'])/1e6:.3f} MHz, "
              f"simdiki {FS/1e6:.3f} MHz."); sys.exit(1)
    if abs(float(d["center_freq"]) - CENTER_FREQ) > 1.0:
        print(f"[UYARI] kalibrasyon {float(d['center_freq'])/1e6:.2f} MHz'te "
              f"alinmis, simdi {CENTER_FREQ/1e6:.2f} MHz.")
    if not np.allclose(d["tx_pos"], TX_POS) or not np.allclose(d["array_pos"], ARRAY_POS):
        print("[UYARI] kalibrasyondaki geometri simdiki sabitlerle AYNI DEGIL. "
              "Ayni fiziksel duzeni kullandigindan emin ol.")
    taps = d["eq_taps"]
    nfft = int(d["corr_nfft"]) if corr_nfft is None else int(corr_nfft)
    EQ, eq_inv = eq_from_taps(taps, nfft)
    bg = d["bg"]
    if int(d["nlag"]) != bg.shape[-1]:
        print("[HATA] kalibrasyon dosyasi tutarsiz (nlag/bg)."); sys.exit(1)
    print(f"\nKalibrasyon: {os.path.basename(path)}  "
          f"({int(d['seconds'])} s bos saha, n_dir={int(d['n_dir'])}, "
          f"LOS bandi {float(d['wb_bw'])/1e6:.1f} MHz)")
    le = d["los_err"]
    print(f"  LOS faz artigi [der]: " + "  ".join(f"{e:+.1f}" for e in le))
    bg_t = d["bg_t"] if "bg_t" in d.files else None
    if bg_t is None:
        print("  [UYARI] dosyada ZAMAN domeni sablonu yok (eski --calib). "
              "Cikarma zayif kalir; --calib tekrar al.")
    return dict(eq_taps=taps, eq_inv=eq_inv, EQ=EQ, bg_t=bg_t,
                bg=bg, n_dir=int(d["n_dir"]), D0=float(d["D0"]),
                n_cls=int(d["n_cls"]), L_seg=int(d["L_seg"]),
                nlag=int(d["nlag"]), corr_nfft=int(d["corr_nfft"]))

# ═══════════════════════════════════════════════════════════════════
#  9) CANLI KONUM — BACKPROJECTION ISI HARITASI (saniyede 1)
# ═══════════════════════════════════════════════════════════════════
def locate_live(dur_s=LOC_DUR_S, key_path=None, cal_path=None, mti=False,
                avg=1):
    """Canli konum: LOO MTI + LOS SELF-KALIBRASYON + backprojection.

    WB (varsayilan): referans = LOS'un kendisi -> tasiyicinin TAM bandi; kanal
    kalibrasyonu HER FREKANS BINI icin ayri (equalizer), her yakalamada LOS'tan
    yeniden cikarilir; MTI CIR domeninde leave-one-out.
    --nowb: eski dar bant yol (ogrenilmis anahtar + occasion korelasyonu, tek
    kompleks katsayili kanal kalibrasyonu).
    Ikisinde de --calib GEREKMEZ; duran her sey MTI'de gider."""
    if not _HAVE_UHD:
        print("[HATA] uhd modulu yok. --self-test kullan."); sys.exit(1)
    import matplotlib.pyplot as plt

    print("=" * 70)
    print(f" KONUM — BACKPROJECTION  ({dur_s} s, {N_RX} kanal, referans: "
          f"{'LOS (tam bant)' if WB_MODE else 'anahtar (SSB)'})")
    print("=" * 70)
    check_spacing()

    wb = eq = None
    self_eq = True
    refs = occ = cls = None
    eq_inv = bgc = bgt = None
    dly = None
    n_cls = L_seg = 0
    if WB_MODE:
        t_ref = 0.0
        if key_path:
            _, t_ref, _ = load_key(key_path)     # sadece pencere yerlesimi icin
        ctx = setup_x410(win_s=LOC_WIN_MS * 1e-3, advance_s=0.0, pps_offset=t_ref)
        wb, eq, n_dir, _ = wb_bring_up(ctx, n_cap=2)
        # --cal verilmisse BOS SAHADA olculmus equalizer kullanilir; verilmemisse
        # her yakalamada LOS'tan yeniden kestirilir (drift takibi).
        if cal_path:
            cd = load_konum_cal(cal_path, corr_nfft=wb["nfft"])
            eq = dict(EQ=cd["EQ"], inv=cd["eq_inv"],
                      gate=(cd["eq_taps"].shape[1] - 1) // 2,
                      med=np.ones(N_RX), rms_db=np.zeros(N_RX),
                      rms_deg=np.zeros(N_RX))
        self_eq = cal_path is None
        # KABLOLU KALIBRASYON VARSA O KAZANIR: equalizer LOS'tan KESTIRILMEZ.
        # self_eq=False, wb_corr'un her yakalamada LOS'tan yeniden equalizer
        # cikarmasini engeller — aksi halde kablodan olculen kanal fazi
        # sessizce LOS'unkiyle degistirilirdi.
        _we = wcal_eq(wb["nfft"])
        if _we is not None:
            eq, self_eq = _we, False
            print("  equalizer : KABLOLU kalibrasyon (LOS'tan kestirim KAPALI)")
        nlag = wb["nlag"]
    else:
        refs, step_s, t_ref = _build_refs(key_path)
        ctx = setup_x410(win_s=LOC_WIN_MS * 1e-3, advance_s=0.0, pps_offset=t_ref)
        N = ctx["N_act"]
        _off0 = int(round((t_ref - ctx["pps_off"]) * FS))
        occ, cls, n_cls, L_seg, nlag = _occasion_layout(N, refs, step_s, _off0)
        nfft_c = 1 << int(np.ceil(np.log2(L_seg + len(refs[0]) - 1)))
        per_cls = min(sum(1 for c in cls if c == j) for j in range(n_cls))
        if per_cls < 2:
            print(f"[HATA] leave-one-out sinif basina >=2 occasion ister "
                  f"({per_cls})."); sys.exit(1)
        if cal_path:
            cd = load_konum_cal(cal_path, corr_nfft=nfft_c)
            if cd["nlag"] != nlag or cd["L_seg"] != L_seg or cd["n_cls"] != n_cls:
                print(f"[HATA] kalibrasyon farkli occasion duzeniyle alinmis "
                      f"(nlag {cd['nlag']} vs {nlag}). Ayni --key/--step ile "
                      f"--calib tekrar al."); sys.exit(1)
            eq_inv, bgc, n_dir = cd["eq_inv"], cd["bg"], cd["n_dir"]
            bgt = cd["bg_t"]
            if _WCAL is not None:
                # Kablolu kalibrasyon LOS tabanli olanin YERINE gecer: bos saha
                # dosyasindan durgun ortam haritasi + n_dir alinir, KANAL
                # EQUALIZER'i ise kablodan. Aci hicbir kosulda LOS'tan gelmez.
                _, eq_inv = eq_from_taps(_WCAL["taps"], nfft_c)
                print("  equalizer : KABLOLU kalibrasyon (bos saha dosyasindaki "
                      "LOS equalizer'i YOK SAYILDI)")
            # --calib ile bu calistirma AYRI program calistirmalaridir; DDC/Replay
            # desimasyon fazi ayni oturmayabilir (sahada olculdu: 2 ornek).
            # Sablonu canli veriye gore yeniden capala.
            if bgt is not None:
                print("\n  Capa kontrolu: kanal basina gecikme olculuyor...")
                b0 = None
                for _ in range(6):
                    b0, _ = acquire(ctx)
                    if b0 is not None:
                        break
                if b0 is not None:
                    dly = measure_channel_delays(b0, occ, cls, L_seg, bgt)
                    print(f"  kayma [ornek]: "
                          + "  ".join(f"k{k}:{dly[k]:+.2f}" for k in range(N_RX)))
                    print(f"  kayma [m]    : "
                          + "  ".join(f"k{k}:{dly[k]/FS*C_AIR:+.2f}"
                                      for k in range(N_RX)))
                    if np.ptp(np.rint(dly)) > 0:
                        print(f"  -> kanallar arasi FARKLI kayma var (k0,k1 "
                              f"Radio#0; k2,k3 Radio#1). Kanal basina telafi "
                              f"edildi.")
                    elif np.any(np.abs(dly) > 0.25):
                        print(f"  -> kalibrasyondan bu yana cihaz yeniden "
                              f"baslatildi; telafi edildi.")
            print("  mod: LOO MTI (--mti) -> sadece HAREKETLI hedef" if mti else
                  "  mod: BOS SAHA CIKARMA -> DURGUN hedefler de gorunur")
        elif _WCAL is not None:
            _, eq_inv = eq_from_taps(_WCAL["taps"], nfft_c)
            print("  equalizer : KABLOLU kalibrasyon (--cal yok -> LOO MTI, "
                  "sadece HAREKETLI hedef)")
            n_dir, _pk, _n = _ndir_robust(ctx, refs, occ, cls, n_cls,
                                          L_seg, nlag, eq_inv)
            print(f"  n_dir     : {n_dir} (menzil sifir noktasi, kanal 0'dan)")
        else:
            print("\n  [UYARI] --cal verilmedi: bos saha haritasi yok, LOO MTI'ye")
            print("          dusuluyor -> SADECE HAREKETLI hedef gorunur.")
            print("          Durgun hedef icin once: --calib 30 --key ...")
            print("  n_dir icin ilk yakalama (LOS capasi) araniyor...")
            n_dir, _pk, _n = _ndir_robust(ctx, refs, occ, cls, n_cls,
                                          L_seg, nlag)

    plan = imaging_plan(nlag, n_dir, fs=wb["fs_eff"] if wb else FS)
    X, Y = plan["X"], plan["Y"]
    print(f"\n  izgara: {len(X)} x {len(Y)} nokta, "
          f"x[{X[0]:.1f},{X[-1]:.1f}] y[{Y[0]:.1f},{Y[-1]:.1f}] m, adim {GRID_RES_M*100:.0f} cm\n")

    el = element_positions()

    plt.ion()
    fig, ax = plt.subplots(figsize=(9.5, 8), constrained_layout=True)
    _bwtxt = (f"bant {wb['bw']/1e6:.1f} MHz -> menzil {wb['res_m']:.2f} m"
              if wb else "anahtar bandi (SSB)")
    fig.suptitle(f"BISTATIK KONUM — backprojection isi haritasi (z=0)   "
                 f"({CENTER_FREQ/1e6:.2f} MHz, {_bwtxt}, d={ARRAY_D_M*100:.1f} cm)",
                 fontweight="bold")
    img0 = np.zeros(plan["shape"], np.float32)
    im = ax.imshow(img0, origin="lower", aspect="equal", cmap="inferno",
                   extent=[X[0], X[-1], Y[0], Y[-1]],
                   vmin=(0.0 if PLOT_LINEAR else -25), vmax=1.0 if PLOT_LINEAR else 0)
    ax.plot(TX_POS[0], TX_POS[1], "^", ms=13, mfc="#00BFFF", mec="k",
            label="baz istasyonu (TX)")
    ax.plot(el[:, 0], el[:, 1], "s", ms=6, mfc="#00E676", mec="k",
            label="X410 dizi elemanlari")
    ax.plot(ARRAY_POS[0], ARRAY_POS[1], "P", ms=9, mfc="#FFEB3B", mec="k",
            label="dizi ortasi (RX)")
    mk, = ax.plot([], [], "o", ms=16, mfc="none", mec="#FF1744", mew=2.5,
                  label="kestirilen hedef")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    ax.legend(loc="upper right", fontsize=8)
    fig.colorbar(im, ax=ax, label=("guc / tepe (lineer)" if PLOT_LINEAR
                                   else "dB (tepeye gore)"))
    plt.show(block=False)

    from collections import deque
    cbuf = deque(maxlen=max(1, int(avg)))
    if avg > 1:
        print(f"  yavas zaman integrasyonu: son {avg} yakalama "
              f"(taban ~{10*np.log10(avg):.1f} dB dusmeli)")
    print(f"  {'#':>4}  {'x':>7} {'y':>7}  {'kontrast':>8}  "
          + ("LOS faz artigi[der] k1..k3 (equalizer sonrasi)" if wb
             else "LOS-cal faz[der] k1..k3"))
    n_cap = int(dur_s)
    for i in range(n_cap):
        if not plt.fignum_exists(fig.number):
            print("\n  Pencere kapatildi, duruluyor.")
            break
        buf, t_trig = acquire(ctx)
        if buf is None:
            print(f"  {i+1:>4}  yakalama EKSIK")
            continue
        if wb:
            res = wb_corr(buf, wb, eq=eq, self_eq=self_eq)
            eq = res["eq"] or eq
            img, _ = wb_track(res, plan, n_dir)
            cal = np.exp(1j * np.radians(wb_los_phase_err(res, n_dir)))
        elif bgc is not None and not mti:
            # BOS SAHA CIKARMA: durgun + hareketli her sey gorunur.
            # Equalizer frekans basina zaten uygulandi; buradaki skaler self-cal
            # sadece bagimsiz LO'larin yakalamalar arasi FAZ SURUKLENMESINI alir.
            Cbar, Craw, _ = capture_corr(buf, refs, occ, cls, n_cls, L_seg, nlag,
                                         bg=bgc, n_dir=n_dir, return_raw=True,
                                         eq_inv=eq_inv, bg_t=bgt, dly=dly)
            cbuf.append(Cbar)                       # yavas zaman integrasyonu
            # Kablolu kalibrasyon varsa aci ondan gelir (bkz. capture_track).
            cal = (np.ones(N_RX, np.complex64) if _WCAL is not None
                   else los_self_cal(Craw, n_dir))
            img = backproject(np.mean(cbuf, axis=0).astype(np.complex64), plan, cal)
        else:
            img, cal = capture_track(buf, refs, occ, cls, n_cls, L_seg, nlag,
                                     plan, n_dir, eq_inv)
        if img is None:
            print(f"  {i+1:>4}  yeterli blok/occasion yok"); continue

        pk = float(img.max()) + 1e-30
        med = float(np.median(img[img > 0])) + 1e-30
        contrast = 10 * np.log10(pk / med)        # tepe / arka plan medyani
        db = (img / pk) if PLOT_LINEAR else 10 * np.log10(img / pk + 1e-30)
        jy, jx = np.unravel_index(int(np.argmax(img)), img.shape)
        xh, yh = X[jx], Y[jy]

        im.set_data(db)
        mk.set_data([xh], [yh])
        ax.set_title(f"t = {i+1} s   hedef ~ ({xh:+.2f}, {yh:+.2f}) m   "
                     f"kontrast {contrast:.1f} dB", loc="left")
        fig.canvas.draw_idle()
        plt.pause(0.001)
        calph = "  ".join(f"{np.degrees(np.angle(cal[k])):+6.1f}" for k in range(1, N_RX))
        print(f"  {i+1:>4}  {xh:>+7.2f} {yh:>+7.2f}  {contrast:>8.1f}   {calph}")

    plt.ioff()
    if plt.fignum_exists(fig.number):
        print("\n  Bitti. Pencereyi kapatinca cikilir.")
        plt.show()

def range_diag(dur_s=60, key_path=None, cal_path=None, target=None,
               rmax_m=RANGE_RMAX_M, mti=False, avg=1, tpl=None):
    """4 kanal AYRI menzil-zaman waterfall'i, capture-ici leave-one-out MTI ile.

    WB (varsayilan): LOS referansli TAM BANT korelasyon + frekans basina
    equalizer -> menzil cozunurlugu c/(2*B_isgal) (100 MHz'de ~1.5 m).
    --nowb: ogrenilmis anahtarla dar bant (SSB ~7.2 MHz -> ~20 m).
    KALIBRASYONSUZ: n_dir LOS'tan otomatik, D0 geometriden. Duran her sey
    iptal, sadece HAREKETLI hedef 4 kanalda iz birakir."""
    if not _HAVE_UHD:
        print("[HATA] uhd modulu yok. --self-test kullan."); sys.exit(1)
    import matplotlib.pyplot as plt

    print("=" * 70)
    print(f" MENZIL WATERFALL — {N_RX} kanal, referans: "
          f"{'LOS (tam bant)' if WB_MODE else 'anahtar (SSB)'}")
    print("=" * 70)

    wb = eq = None
    self_eq = True
    refs = occ = cls = None
    eq_inv = bgc = bgt = None
    dly = None
    n_cls = L_seg = 0
    D0 = float(np.linalg.norm(ARRAY_POS - TX_POS))
    if WB_MODE:
        t_ref = 0.0
        if key_path:
            _, t_ref, _ = load_key(key_path)
        ctx = setup_x410(win_s=LOC_WIN_MS * 1e-3, advance_s=0.0, pps_offset=t_ref)
        wb, eq, n_dir, _ = wb_bring_up(ctx, n_cap=2)
        if cal_path:
            cd = load_konum_cal(cal_path, corr_nfft=wb["nfft"])
            eq = dict(EQ=cd["EQ"], inv=cd["eq_inv"],
                      gate=(cd["eq_taps"].shape[1] - 1) // 2,
                      med=np.ones(N_RX), rms_db=np.zeros(N_RX),
                      rms_deg=np.zeros(N_RX))
        self_eq = cal_path is None
        # KABLOLU KALIBRASYON VARSA O KAZANIR: equalizer LOS'tan KESTIRILMEZ.
        # self_eq=False, wb_corr'un her yakalamada LOS'tan yeniden equalizer
        # cikarmasini engeller — aksi halde kablodan olculen kanal fazi
        # sessizce LOS'unkiyle degistirilirdi.
        _we = wcal_eq(wb["nfft"])
        if _we is not None:
            eq, self_eq = _we, False
            print("  equalizer : KABLOLU kalibrasyon (LOS'tan kestirim KAPALI)")
        nlag = wb["nlag"]
    else:
        refs, step_s, t_ref = _build_refs(key_path)
        ctx = setup_x410(win_s=LOC_WIN_MS * 1e-3, advance_s=0.0, pps_offset=t_ref)
        N = ctx["N_act"]
        _off0 = int(round((t_ref - ctx["pps_off"]) * FS))
        occ, cls, n_cls, L_seg, nlag = _occasion_layout(N, refs, step_s, _off0)
        nfft_c = 1 << int(np.ceil(np.log2(L_seg + len(refs[0]) - 1)))
        per_cls = min(sum(1 for c in cls if c == j) for j in range(n_cls))
        if per_cls < 2:
            print(f"[HATA] leave-one-out sinif basina >=2 occasion ister "
                  f"({per_cls}). LOC_WIN_MS'i buyut."); sys.exit(1)
        if cal_path:
            cd = load_konum_cal(cal_path, corr_nfft=nfft_c)
            if cd["nlag"] != nlag or cd["L_seg"] != L_seg or cd["n_cls"] != n_cls:
                print(f"[HATA] kalibrasyon farkli occasion duzeniyle alinmis. "
                      f"Ayni --key/--step ile --calib tekrar al."); sys.exit(1)
            eq_inv, bgc, n_dir = cd["eq_inv"], cd["bg"], cd["n_dir"]
            bgt = cd["bg_t"]
            if _WCAL is not None:
                # Kablolu kalibrasyon LOS tabanli olanin YERINE gecer: bos saha
                # dosyasindan durgun ortam haritasi + n_dir alinir, KANAL
                # EQUALIZER'i ise kablodan. Aci hicbir kosulda LOS'tan gelmez.
                _, eq_inv = eq_from_taps(_WCAL["taps"], nfft_c)
                print("  equalizer : KABLOLU kalibrasyon (bos saha dosyasindaki "
                      "LOS equalizer'i YOK SAYILDI)")
            # --calib ile bu calistirma AYRI program calistirmalaridir; DDC/Replay
            # desimasyon fazi ayni oturmayabilir (sahada olculdu: 2 ornek).
            # Sablonu canli veriye gore yeniden capala.
            if bgt is not None:
                print("\n  Capa kontrolu: kanal basina gecikme olculuyor...")
                b0 = None
                for _ in range(6):
                    b0, _ = acquire(ctx)
                    if b0 is not None:
                        break
                if b0 is not None:
                    dly = measure_channel_delays(b0, occ, cls, L_seg, bgt)
                    print(f"  kayma [ornek]: "
                          + "  ".join(f"k{k}:{dly[k]:+.2f}" for k in range(N_RX)))
                    print(f"  kayma [m]    : "
                          + "  ".join(f"k{k}:{dly[k]/FS*C_AIR:+.2f}"
                                      for k in range(N_RX)))
                    if np.ptp(np.rint(dly)) > 0:
                        print(f"  -> kanallar arasi FARKLI kayma var (k0,k1 "
                              f"Radio#0; k2,k3 Radio#1). Kanal basina telafi "
                              f"edildi.")
                    elif np.any(np.abs(dly) > 0.25):
                        print(f"  -> kalibrasyondan bu yana cihaz yeniden "
                              f"baslatildi; telafi edildi.")
            print("  mod: LOO MTI (--mti) -> sadece HAREKETLI hedef" if mti else
                  "  mod: BOS SAHA CIKARMA -> DURGUN hedefler de gorunur")
        else:
            print("\n  [UYARI] --cal yok: LOO MTI -> SADECE HAREKETLI hedef.")
            if _WCAL is not None:
                _, eq_inv = eq_from_taps(_WCAL["taps"], nfft_c)
                print("  equalizer : KABLOLU kalibrasyon")
            print("  n_dir icin ilk yakalama (dogrudan yol capasi) araniyor...")
            n_dir, _pk, _n = _ndir_robust(ctx, refs, occ, cls, n_cls,
                                          L_seg, nlag, eq_inv)
            print(f"  n_dir = {n_dir} (LOS, otomatik);  sinif basina {per_cls} occasion")

    lags = np.arange(nlag)
    excess_m = (lags - n_dir) / (wb["fs_eff"] if wb else FS) * C_AIR   # 0 = LOS
    # WB'de negatif lag'lar bos degil: referans kanali (ch0) hedef yankisini da
    # tasidigi icin orada AYNA tepe olusur — tanida ise yarar, gosterilsin.
    show = (excess_m >= (-WB_NEG_M if wb else -5.0)) & (excess_m <= rmax_m)

    exp_excess = None
    if target is not None:
        p = np.array([target[0], target[1], target[2] if len(target) > 2 else 0.0])
        R_bi, _, _ = bistatic_geometry(p[None, :])
        exp_excess = (R_bi[:, 0] - D0)
        print(f"  bilinen hedef {p} -> beklenen fazla menzil/kanal [m]: "
              + "  ".join(f"{e:.2f}" for e in exp_excess))
    print(f"  gosterim 0..{rmax_m:.0f} m\n")

    from collections import deque
    cbuf = deque(maxlen=max(1, int(avg)))
    thist = [deque(maxlen=int(tpl)) for _ in range(n_cls)] if tpl else None
    if tpl:
        print(f"\n  KAYAN PENCERE SABLONU: sinif basina son {tpl} occasion")
        print(f"  (eski 4rx_1tx_kdyf mantigi; --cal kullanilmaz, HAREKETLI hedef)")
    if avg > 1:
        print(f"  yavas zaman integrasyonu: son {avg} yakalama "
              f"(taban ~{10*np.log10(avg):.1f} dB dusmeli)")
    xr = excess_m[show]
    n_show = int(show.sum())
    n_cap = int(dur_s)
    WF_VMIN, WF_VMAX = -40.0, 0.0
    WF_VIEW = 200
    wf = [np.full((n_cap, n_show), np.nan, np.float32) for _ in range(N_RX)]

    plt.ion()
    fig, ax = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True,
                           sharex=True, sharey=True)
    ax = ax.ravel()
    _bwtxt = (f"bant {wb['bw']/1e6:.1f} MHz, cozunurluk {wb['res_m']:.2f} m"
              if wb else "anahtar bandi (SSB)")
    _mdtxt = ("LOO MTI (sadece hareketli)" if (wb or mti or bgc is None)
              else "bos saha cikarma (durgun + hareketli)")
    fig.suptitle(f"KANAL-BASINA MENZIL WATERFALL — {_mdtxt}   "
                 f"({CENTER_FREQ/1e6:.2f} MHz, {_bwtxt})", fontweight="bold")
    # Anahtarin bandindan ana lob genisligi -> LOS dislama bolgesi
    if wb:
        los_guard_m = 2.0 * wb["res_m"]
    else:
        _ks = np.abs(np.fft.fft(refs[0], 1 << int(np.ceil(np.log2(2*len(refs[0]))))))**2
        _fb = np.fft.fftfreq(_ks.size, 1.0 / FS)
        _f0 = float(np.sum(_fb * _ks) / (np.sum(_ks) + 1e-30))
        _bw = float(np.sqrt(np.sum((_fb-_f0)**2*_ks)/(np.sum(_ks)+1e-30)))*2*np.sqrt(3)
        los_guard_m = 2.0 * C_AIR / (2.0 * max(_bw, 1e3))

    ims = []
    for k in range(N_RX):
        im = ax[k].imshow(wf[k][:1], origin="lower", aspect="auto", cmap="inferno",
                          extent=[xr[0], xr[-1], 0, 1],
                          vmin=(0.0 if PLOT_LINEAR else WF_VMIN),
                          vmax=(1.0 if PLOT_LINEAR else WF_VMAX),
                          interpolation="nearest")
        # LOS ana lobu: RAPORLAMADA dislaniyor ama grafikte gorunmuyordu ->
        # kullanici oradaki parlakligi hedef sanabiliyor. Bandi isaretle.
        ax[k].axvspan(-los_guard_m, los_guard_m, color="#00BFFF", alpha=0.13,
                      lw=0, zorder=3)
        ax[k].axvline(0, color="#00BFFF", ls=":", lw=1.0)
        if exp_excess is not None:
            ax[k].axvline(exp_excess[k], color="#00E676", ls="--", lw=1.2)
        ax[k].set_title(f"kanal {k}"
                        + (f"  (beklenen {exp_excess[k]:.1f} m)" if exp_excess is not None else ""),
                        loc="left", fontsize=9)
        if k >= 2: ax[k].set_xlabel("bistatik fazla menzil [m]  (0 = dogrudan yol)")
        if k % 2 == 0: ax[k].set_ylabel("zaman [s]")
        fig.colorbar(im, ax=ax[k], pad=0.01,
                     label=("guc / LOS (lineer)" if PLOT_LINEAR else "dB"))
        ims.append(im)
    plt.show(block=False)

    print(f"  LOS dislama bolgesi: +-{los_guard_m:.1f} m "
          f"(ana lobun 2 kati); bunun disindaki tepeler raporlanir")
    print("  mavi nokta cizgi = dogrudan yol (0 m), yesil kesikli = beklenen hedef")
    print(f"  mavi golgeli bant = LOS ana lobu (+-{los_guard_m:.1f} m): burasi")
    print(f"  RAPORLANMAZ. Icindeki parlaklik LOS artigidir, hedef DEGIL.\n")
    n_bad = 0
    hdr = "  ".join(f"k{k}:menzil/SNR" for k in range(N_RX))
    print(f"  {'#':>3}  " + hdr + "   bastirma[dB] k0..k3")
    print("  (bastirma = DOGRUDAN YOL BININDE cikarma oncesi/sonrasi orani.")
    print("   Negatif ve buyuk olmali; pozitifse capa kaymistir.)")
    for i in range(n_cap):
        if not plt.fignum_exists(fig.number):
            print("\n  Pencere kapatildi."); break
        buf, _ = acquire(ctx)
        if buf is None:
            print(f"  {i+1:>3}  yakalama EKSIK"); continue
        sup_now = None; lag_now = None
        if wb:
            res = wb_corr(buf, wb, eq=eq, self_eq=self_eq)
            eq = res["eq"] or eq
            Pmti, Praw = wb_range(res, n_dir)
            if Pmti is None:
                print(f"  {i+1:>3}  blok yok"); continue
        elif tpl:
            Pm, Pr = capture_running_tpl(buf, refs, occ, cls, n_cls, L_seg,
                                         nlag, thist, eq_inv)
            if Pm is None:
                print(f"  {i+1:>3}  sablon doluyor ({len(thist[0])}/{tpl})")
                continue
            Pmti, Praw = Pm, Pr
        elif bgc is not None and not mti:
            Cbar, Craw, _ = capture_corr(buf, refs, occ, cls, n_cls, L_seg, nlag,
                                         bg=bgc, n_dir=n_dir, return_raw=True,
                                         eq_inv=eq_inv, bg_t=bgt, dly=dly)
            # YAVAS ZAMAN INTEGRASYONU: artik profiller KOHERENT ortalanir.
            # Her yakalama sablona (df,a) ile oturtuldugu icin ayni olcektedir;
            # durgun hedef koherent buyur, degisen icerik ortalamayla duser.
            cbuf.append(Cbar)
            Cav = np.mean(cbuf, axis=0)
            Pmti = np.abs(Cav) ** 2           # bos saha cikarilmis (durgun+hareketli)
            Praw = np.abs(Craw) ** 2          # cikarilmamis (0 dB referansi = LOS)
            # Bastirma = AYNI binde oran (bkz. calib dogrulamasi).
            sup_now = 10 * np.log10(np.abs(Cav[:, n_dir]) ** 2 /
                                    (Praw[:, n_dir] + 1e-30) + 1e-30)
            lag_now = int(np.argmax(Praw[0]))
        else:
            Pmti, Praw = capture_loo(buf, refs, occ, cls, n_cls, L_seg,
                                     nlag, eq_inv, n_dir=n_dir)
        # BASTIRMA her yolda olculmeli. Onceden sadece bos-saha dalinda
        # hesaplaniyordu; LOO/tpl dallarinda sutun BOS kaliyordu ve "arka plan
        # gercekten cikti mi" sorusunun olculmus cevabi yoktu.
        if sup_now is None:
            sup_now = 10 * np.log10(Pmti[:, n_dir] / (Praw[:, n_dir] + 1e-30)
                                    + 1e-30)
        row = []
        lo = max(0, i + 1 - WF_VIEW)
        for k in range(N_RX):
            ref_lvl = Praw[k].max() + 1e-30              # 0 dB = LOS gucu
            wf[k][i] = ((Pmti[k][show] / ref_lvl) if PLOT_LINEAR
                        else 10 * np.log10(Pmti[k][show] / ref_lvl + 1e-30))
            ims[k].set_data(wf[k][lo:i + 1])
            ims[k].set_extent([xr[0], xr[-1], lo, i + 1])
            # LOS ana lobunu disla. Sabit 1 m YETMEZ: cozunurluk c/(2B) ve
            # kalan LOS artigi ana lob genisliginde tepe yapar; onu "hedef"
            # diye raporlamak yanlis olur.
            mm = show.copy(); mm[np.abs(excess_m) < los_guard_m] = False
            if mm.any():
                j = int(np.argmax(np.where(mm, Pmti[k], 0)))
                floor = np.median(Pmti[k][mm]) + 1e-30
                row.append(f"{excess_m[j]:5.1f}/{10*np.log10(Pmti[k][j]/floor):4.1f}")
            else:
                row.append(" --/-- ")
        ax[0].set_ylim(lo, i + 1)
        fig.canvas.draw_idle(); plt.pause(0.001)
        # Bastirma zayifsa o yakalamada MTI CALISMAMISTIR: waterfall'da butun
        # menzillere yayilan parlak YATAY CIZGI olarak gorunur. Hedef degil,
        # artefakt — isaretle ki grafikte aranmasin.
        sup_txt = ""
        if sup_now is not None:
            bad = float(np.max(sup_now)) > MTI_SUP_WARN_DB
            sup_txt = ("   " + " ".join(f"{v:+5.1f}" for v in sup_now)
                       + ("  <<< MTI ZAYIF" if bad else ""))
            n_bad += int(bad)
        if lag_now is not None and lag_now != n_dir and i == 0:
            print(f"  [KRITIK] canli LOS tepesi lag {lag_now}, n_dir={n_dir} "
                  f"({(lag_now-n_dir)/FS*C_AIR:+.1f} m kayma) -> cikarma yanlis "
                  f"bine oturuyor. --calib'i AYNI --key/--keymax/--step ile tekrarla.")
        print(f"  {i+1:>3}  " + "  ".join(f"{r:>12}" for r in row) + sup_txt)

    plt.ioff()
    if n_bad:
        print(f"\n  [UYARI] {n_bad} yakalamada MTI ZAYIF kaldi "
              f"(bastirma > {MTI_SUP_WARN_DB:.0f} dB).")
        print(f"          Bunlar waterfall'da TUM menzillere yayilan parlak")
        print(f"          yatay cizgilerdir — HEDEF DEGIL, artefakt.")
        print(f"          Sebep: o an sinyal kesildi/zayifladi ya da occasion")
        print(f"          kaydi. Sik oluyorsa anahtari (--learn) yenile.")
    if plt.fignum_exists(fig.number):
        print("\n  Bitti. Pencereyi kapatinca cikilir.")
        plt.show()

def auto_run(seconds=LOC_DUR_S, n_wcal=AUTO_WCAL_N, key_path=None,
             step_ms=None, mode="locate",
             target=None, rmax=None, mti=True, avg=1, tpl=None, cal_path=None,
             geom_path=None, geom_ask_flag=False, ota=False, ota_range_m=None,
             verify_deg=None, force_cal=False):
    """TEK KOSU: kablolu kalibrasyon -> olcum. Anahtar ONCEDEN ogrenilmis olur.

    NEDEN KALIBRASYON VE OLCUM AYNI KOSUDA: her calistirmada X410 yeniden
    initialize edilir ve ZBX'te LO ihrac edilemedigi icin KANALLAR ARASI FAZ
    RASGELE degisir. Kablolu kalibrasyonun faz kismi, onu olcen process
    olunce oluyor.

    NEDEN ANAHTAR AYRI KOSUDA: anahtar tek kanalin (k0) dalga formudur,
    kanallar arasi faza BAGLI DEGILDIR — process'ler arasinda yasar. Ustelik
    saglam bir anahtar dakikalarca yakalama ister; onu her olcumden once
    tekrar ogrenmek hem gereksiz hem de kalibrasyon ile olcum arasindaki
    sureyi uzatir."""
    if not _HAVE_UHD:
        print("[HATA] uhd modulu yok."); sys.exit(1)
    globals()["_CHAIN"] = True          # oturum uyarilarini bilgiye cevir
    if key_path is None:
        key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                LEARN_FILE)
    if not os.path.exists(key_path):
        print("=" * 70)
        print(" [HATA] ANAHTAR YOK — once periyodik sinyali ogren.")
        print("=" * 70)
        print(f"  Beklenen dosya: {key_path}")
        print(f"\n  Bir kere calistir (~{LEARN_N_DEF} s, saglam anahtar icin uzun tut):")
        print(f"    python3 {os.path.basename(__file__)} --learn")
        print(f"\n  Anahtar kanallar arasi faza BAGLI DEGIL — bir kere ogrenilir,")
        print(f"  sonraki butun olcumlerde kullanilir. Sadece tasiyici ya da")
        print(f"  hucre degisirse yeniden ogren.")
        sys.exit(1)

    # Anahtarin OLCULEN tekrar periyodu (--learn kaydetti). Yanlis step,
    # occasion'larin yarisini bosa dusurur; kullanicidan bunu ezberlemesini
    # istemek anlamsiz — dosyada zaten yaziyor.
    _d = np.load(key_path)
    if step_ms is not None:
        globals()["KEY_STEP_MS"] = step_ms
    elif "key_period_ms" in _d.files and float(_d["key_period_ms"]) > 0:
        globals()["KEY_STEP_MS"] = float(_d["key_period_ms"])
        globals()["KEY_STEP_SRC"] = "--learn olcmustu"

    print("=" * 70)
    print(" TEK KOSU: KABLOLU KALIBRASYON -> OLCUM")
    print("=" * 70)
    print(f"  bant      : {band_limit_hz()[0]/1e6+CENTER_FREQ/1e6:.1f} .. "
          f"{band_limit_hz()[1]/1e6+CENTER_FREQ/1e6:.1f} MHz (disi SIFIRLANIR)")
    print(f"  anahtar   : {os.path.basename(key_path)}"
          + (f"   (PCI {int(_d['pci'])})" if "pci" in _d.files
             and int(_d["pci"]) >= 0 else "")
          + (f", tekrar {KEY_STEP_MS:.0f} ms" if KEY_STEP_MS else ""))
    print(f"  referans  : {REF_SRC}")
    print(f"  asamalar  : 1) splitter kalibrasyonu  {n_wcal} olcum (~{n_wcal} s)")
    print(f"              2) olcum ({mode})  {seconds} s")
    print(f"  ZORUNLU   : ikisi de AYNI oturumda kosar. Program bitmeden baska")
    print(f"              bir script calistirma — faz kalibrasyonu gider.")

    # GEOMETRI once: konum kestirimi bunsuz yapilamaz ve kullanicinin
    # kablolarla ugrasmadan once girmesi daha rahat.
    geom_setup(geom_path, ask=geom_ask_flag)


    # --- 1) KABLOLU KALIBRASYON ---
    # key_path VERILIR: oturum dogrudan anahtarin t_ref'inde acilir, boylece
    # occasion kaymasina bile gerek kalmaz.
    sol = wcal_run(key_path=key_path, n_cap=n_wcal, ota=ota,
                   ota_range_m=ota_range_m, verify_deg=verify_deg,
                   force=force_cal)
    if sol is None:
        print("[HATA] kablolu kalibrasyon basarisiz."); sys.exit(1)

    # --- 2) OLCUM (ayni oturum, _WCAL yerinde) ---
    print("\n" + "=" * 70)
    print(f" ASAMA 2/2 — OLCUM ({mode})")
    print("=" * 70)
    if mode == "locate":
        locate_live(seconds, key_path, cal_path, mti, max(1, avg))
    else:
        range_diag(seconds, key_path, cal_path, target, rmax, mti,
                   max(1, avg), tpl)



# ===================================================================
#  SELF-TEST — donanimsiz uctan uca dogrulama
# ===================================================================

# ═══════════════════════════════════════════════════════════════════
#  10) SELF-TEST — donanimsiz uctan uca dogrulama (SENTETIK SAHNE)
# ═══════════════════════════════════════════════════════════════════
def _synth_scene(refs, occ, cls, L_seg, N, cal_true, targets, noise=0.02,
                 direct_amp=1.0, tgt_amp=0.15, seed=0, hw_fir=None, cfo_hz=0.0):
    """Sentetik (N_RX, N) yakalama uret: dogrudan yol + hedef yankilari.

    targets: [(p(3,), genlik), ...]. Her yol: sablon, gecikmeyle kaydirilir ve
    tasiyici fazi exp(-j2pi fc tau) ile carpilir; kanal cal_true uygulanir.
    hw_fir: (N_RX, ntap) — kanal basina KISA FIR (frekansa bagli zincir
    uyumsuzlugu). Verilirse sinyale uygulanir, gurultu ONDAN SONRA eklenir
    (alici gurultusu filtreden sonra gelir)."""
    rng = np.random.default_rng(seed)
    el = element_positions()
    buf = np.zeros((N_RX, N), np.complex128)

    def add_path(R_k, amp):
        # R_k: (N_RX,) yol uzunlugu. Her occasion'a sablonu yerlestir.
        for o, c in zip(occ, cls):
            ref = refs[c]
            for k in range(N_RX):
                tau = R_k[k] / C_AIR
                d = int(round(tau * FS))
                ph = np.exp(-2j * np.pi * CENTER_FREQ * tau)
                i0 = o + d
                i1 = min(i0 + len(ref), N)
                if i0 < 0 or i0 >= N:
                    continue
                buf[k, i0:i1] += amp * cal_true[k] * ph * ref[:i1 - i0]

    # dogrudan yol: R = |RX_k - TX|
    D = np.linalg.norm(el - TX_POS[None, :], axis=1)
    add_path(D, direct_amp)
    # hedefler: R = |p-TX| + |p-RX_k|
    for p, a in targets:
        r_tx = np.linalg.norm(p - TX_POS)
        r_rx = np.linalg.norm(p[None, :] - el, axis=1)
        add_path(r_tx + r_rx, a * tgt_amp)
    if cfo_hz:
        # Baz istasyonunun tasiyicisi bizim GPSDO'muza KILITLI DEGILDIR; kalan
        # kayma her segmentte bir faz RAMPASI birakir. Arka plan cikarmasinin
        # gercek sinavi budur.
        buf *= np.exp(2j * np.pi * cfo_hz * np.arange(N) / FS)[None, :]
    if hw_fir is not None:                 # frekansa bagli zincir uyumsuzlugu
        for k in range(N_RX):
            buf[k] = np.convolve(buf[k], hw_fir[k])[:N]
    buf += noise * (rng.standard_normal((N_RX, N)) +
                    1j * rng.standard_normal((N_RX, N)))
    return buf.astype(np.complex64)

def _synth_hw(rng, nfft, ntap=3, ripple=0.25):
    """Sentetik RX zinciri yaniti: (N_RX, nfft) kompleks, FREKANSA BAGLI.

    Kanal 0 = referans (duz). Digerleri kisa bir FIR (kablo/filtre uyumsuzlugu)
    + sabit faz. Boyle bir yanit TEK kompleks katsayiyla telafi EDILEMEZ;
    self-test'in ispatlamasi gereken sey tam olarak budur."""
    hw = np.zeros((N_RX, nfft), np.complex128)
    hw[0] = 1.0
    for k in range(1, N_RX):
        h = np.zeros(nfft, np.complex128)
        h[0] = 1.0
        for t in range(1, ntap):
            h[t] = (ripple / t) * (rng.standard_normal() + 1j * rng.standard_normal())
        hw[k] = np.fft.fft(h) * np.exp(1j * rng.uniform(-np.pi, np.pi)) \
            * rng.uniform(0.8, 1.2)
    return hw

def _synth_wb(nblk, nfft, targets, hw, noise=0.01, bw_hz=100e6, seed=0):
    """Sentetik GENIS BANT sahne: (N_RX, nblk*nfft).

    Kaynak = banda sinirli beyaz gurultu (ticari NR tasiyicisinin korelasyon
    acisindan esdegeri). Her yol frekans domeninde exp(-j2pi f_abs tau) ile
    gecikir — yani tasiyici fazi ve grup gecikmesi TUTARLI (genis bantta dogru).
    targets: [(p(3,), genlik, doppler_Hz), ...]"""
    rng = np.random.default_rng(seed)
    el  = element_positions()
    Dk  = np.linalg.norm(el - TX_POS[None, :], axis=1)
    fb   = np.fft.fftfreq(nfft, 1.0 / FS)
    fabs = CENTER_FREQ + fb
    band = (np.abs(fb) <= bw_hz / 2).astype(np.float64)
    # Olcek: ifft'ten sonra dogrudan yolun ZAMAN domeninde birim gucu olsun ki
    # `noise` gercekten gurultu/sinyal orani anlamina gelsin.
    band *= np.sqrt(nfft / max(band.mean(), 1e-12))
    out = np.zeros((N_RX, nblk * nfft), np.complex64)
    for b in range(nblk):
        X = (rng.standard_normal(nfft) + 1j * rng.standard_normal(nfft)) / np.sqrt(2) * band
        Y = np.zeros((N_RX, nfft), np.complex128)
        Y += X[None, :] * np.exp(-2j * np.pi * np.outer(Dk, fabs) / C_AIR)
        for p, amp, fd in targets:
            R = np.linalg.norm(p - TX_POS) + np.linalg.norm(p[None, :] - el, axis=1)
            dop = np.exp(2j * np.pi * fd * (b * nfft / FS))
            Y += (amp * dop) * X[None, :] * np.exp(-2j * np.pi *
                                                   np.outer(R, fabs) / C_AIR)
        y = np.fft.ifft(Y * hw, axis=1)
        y += noise * (rng.standard_normal((N_RX, nfft)) +
                      1j * rng.standard_normal((N_RX, nfft)))
        out[:, b * nfft:(b + 1) * nfft] = y
    return out

def _synth_nr_cell(pci, i_ssb, row, ssb_slot=3, ssb_l=2, sib1=True,
                   n_ms=14.0, snr_db=18.0, seed=21, n_rb_carrier=None):
    """Tam NR hucresi sentezle: dolu PDSCH + SSB + CORESET#0 + SIB1.

    Uzun CP dahil GERCEK sembol izgarasi kullanilir — yoksa 64 orneklik kayma
    DMRS korelasyonunu coker. Doner (x, k0_gercek)."""
    rng = np.random.default_rng(seed)
    _, n_rb, n_symb, off = row
    N = int(n_ms * 1e-3 * FS)
    nsc = (n_rb_carrier or (N_RB_CELL - 1)) * NSC_PER_RB
    kc = N_FFT // 2 - nsc // 2
    nsl = N // N_SLOT + 1
    grid = {}
    for s in range(nsl):
        for l in range(NSYM_PER_SLOT):
            X = np.zeros(N_FFT, complex)
            X[kc:kc + nsc] = gold_qpsk((s * 14 + l) * 7919 % (1 << 31), nsc) * 0.30
            grid[(s, l)] = X
    # SSB tasiyicinin icinde kalmali ve altinda CORESET#0 offseti kadar yer olmali
    n_rb_c = nsc // NSC_PER_RB
    b_ssb = kc + min(40, max(16, (n_rb_c - 20) // 2)) * NSC_PER_RB
    G = np.zeros((SSB_SYMS, SSB_NSC), complex)
    G[0, PSS_SC0:PSS_SC0 + PSS_NSC] = pss_seq(pci % 3)
    G[2, PSS_SC0:PSS_SC0 + PSS_NSC] = sss_seq(pci // 3, pci % 3)
    r = pbch_dmrs_seq(pci, i_ssb)
    for sym, sc, sl in pbch_dmrs_re(pci):
        G[sym, sc] = r[sl]
    for i in range(SSB_SYMS):
        X = grid[(ssb_slot, ssb_l + i)]
        X[b_ssb:b_ssb + SSB_NSC] = 0
        m = G[i] != 0
        X[b_ssb:b_ssb + SSB_NSC][m] = G[i][m] * 2.2
    k0 = b_ssb - off * NSC_PER_RB
    idx = (k0 + NSC_PER_RB * np.repeat(np.arange(n_rb), 3)
           + 4 * np.tile(np.arange(3), n_rb) + 1)
    for li in range(n_symb):
        grid[(ssb_slot, li)][idx] = pdcch_dmrs_seq(pci, ssb_slot, li, n_rb) * 2.2
    if sib1:
        n_re = 6 * n_rb
        grid[(ssb_slot, n_symb)][k0 + 2 * np.arange(n_re)] = \
            pdsch_dmrs_seq(pci, ssb_slot, n_symb, n_re) * 2.2
    x = np.zeros(N + 8192, complex)
    for s in range(nsl):
        offs = symbol_offsets(s % SLOTS_PER_FRAME)
        for l in range(NSYM_PER_SLOT):
            cp0, _, cp = offs[l]
            t = s * N_SLOT + cp0
            if t + cp + N_FFT > len(x):
                continue
            sm = np.fft.ifft(np.fft.ifftshift(grid[(s, l)])) * N_FFT
            x[t:t + cp + N_FFT] = np.concatenate([sm[-cp:], sm])
    x = x[:N] / np.sqrt(np.mean(np.abs(x[:N]) ** 2))
    n = np.sqrt(10 ** (-snr_db / 10) / 2)
    return (x + n * (rng.normal(0, 1, N) + 1j * rng.normal(0, 1, N))).astype(
        np.complex64), k0

def _synth_ssb(n_id1, n_id2, b0, n_sym=28, snr=8.0, seed=0):
    """Sentetik NR DL akisi: icinde bir SSB (PSS/SSS) olan CP'li OFDM sembolleri.

    b0: PSS'in MERKEZLENMIS (fftshift) izgaradaki baslangic bini. Doner (x, t0)
    — t0 PSS sembolunun CP baslangic indisi."""
    rng = np.random.default_rng(seed)
    per = N_FFT + CP_NORM
    x = np.zeros(n_sym * per, np.complex64)
    i_pss = 6                                   # SSB akisin ortalarinda bir yerde
    for i in range(n_sym):
        X = np.zeros(N_FFT, np.complex128)
        # tasiyicinin geri kalani: rastgele veri (PSS'i gizleyen arka plan)
        occ = np.arange(N_FFT // 2 - 1200, N_FFT // 2 + 1200)
        X[occ] = (rng.standard_normal(occ.size) +
                  1j * rng.standard_normal(occ.size)) / np.sqrt(2) / snr
        if i == i_pss:
            X[b0:b0 + PSS_NSC] = pss_seq(n_id2)
        elif i == i_pss + 2:
            X[b0:b0 + PSS_NSC] = sss_seq(n_id1, n_id2)
        xt = np.fft.ifft(np.fft.ifftshift(X)) * N_FFT
        x[i * per:(i + 1) * per] = np.concatenate([xt[-CP_NORM:], xt])
    x += (0.02 * (rng.standard_normal(x.size) +
                  1j * rng.standard_normal(x.size))).astype(np.complex64)
    return x, i_pss * per

def _std_chain_test():
    """SSB/PBCH DMRS/CORESET#0/SIB1/ppb zincirini uctan uca sina."""
    ok_all = True

    # 1) Gold dizisi — hizli LFSR referans tanimla ayni mi?
    def _gold_ref(c_init, length):
        Nc, n_tot = 1600, length + 1600 + 31
        x1 = np.zeros(n_tot, np.uint8); x2 = np.zeros(n_tot, np.uint8); x1[0] = 1
        for i in range(31):
            x2[i] = (c_init >> i) & 1
        for n in range(n_tot - 31):
            x1[n + 31] = x1[n + 3] ^ x1[n]
            x2[n + 31] = x2[n + 3] ^ x2[n + 2] ^ x2[n + 1] ^ x2[n]
        return x1[Nc:Nc + length] ^ x2[Nc:Nc + length]
    g_ok = all(np.array_equal(_gold_ref(c, 288), gold_sequence(c, 288))
               for c in (0, 1, 97, 12345, (1 << 31) - 1))
    ok_all &= g_ok
    print(f"  [{'OK ' if g_ok else 'HATA'}] Gold dizisi (TS 38.211 5.2.1) "
          f"tanima birebir uyuyor")

    # 2) SSB uret -> PCI + i_SSB geri okunuyor mu?
    bad = []
    for pci, iss in ((97, 3), (605, 0), (2, 7), (335, 5)):
        x, _ = _synth_nr_cell(pci, iss, (1, 48, 2, 12), n_ms=8.0)
        c = detect_cell(x, win_ms=8.0, quiet=True)
        p = ssb_pbch_check(x, c, quiet=True) if c else None
        if not (c and c["pci"] == pci and p and p["i_ssb"] == iss
                and p["ratio"] > 1.8):
            bad.append((pci, iss))
    ok_all &= not bad
    print(f"  [{'OK ' if not bad else 'HATA'}] PBCH DMRS (7.4.1.4.1): 4/4 "
          f"hucrede PCI ve i_SSB geri okundu" if not bad else
          f"  [HATA] PBCH DMRS: {bad} basarisiz")

    # 3) CORESET#0 + SIB1 — tam konfigurasyon geri bulunuyor mu?
    bad = []
    for row in [(1, 48, 2, 12), (1, 24, 3, 2), (1, 48, 1, 16), (1, 24, 2, 0)]:
        x, k0t = _synth_nr_cell(97, 3, row)
        c = detect_cell(x, win_ms=14.0, quiet=True)
        cs = coreset0_scan(x, c, quiet=True) if c else None
        sb = sib1_check(x, c, cs, quiet=True) if cs else None
        if not (cs and cs["n_rb"] == row[1] and cs["n_symb"] == row[2]
                and cs["k0"] == k0t and abs(cs["offset"] - row[3]) < 0.01
                and cs["l"] == 0 and sb and sb["metric"] > 0.45):
            bad.append(row)
    ok_all &= not bad
    print(f"  [{'OK ' if not bad else 'HATA'}] CORESET#0 (Tablo 13-4) + SIB1 "
          f"(7.4.1.1.1): 4/4 konfigurasyon geri bulundu" if not bad else
          f"  [HATA] CORESET#0/SIB1: {bad} basarisiz")

    # 4) SIB1 YOK senaryosu yanlis alarm vermiyor mu?
    x, _ = _synth_nr_cell(97, 3, (1, 48, 2, 12), sib1=False)
    c = detect_cell(x, win_ms=14.0, quiet=True)
    cs = coreset0_scan(x, c, quiet=True)
    sb = sib1_check(x, c, cs, quiet=True)
    ok_ns = sb is not None and sb["metric"] < 0.45
    ok_all &= ok_ns
    print(f"  [{'OK ' if ok_ns else 'HATA'}] SIB1 yokken YOK deniyor "
          f"(uyum {sb['metric']:.2f} < 0.45)")

    # 5) Frekans sapmasi — ayni RU / ayri gNB ayrimi
    errs, res = [], {}
    for f_hz in (0.0, -47.3, 210.0):
        x, _ = _synth_nr_cell(97, 0, (1, 48, 2, 12), n_ms=20.0, snr_db=20.0)
        t = np.arange(x.size)
        y = (x * np.exp(2j * np.pi * f_hz * t / FS)).astype(np.complex64)
        r = cfo_cp(y)
        if r is None:
            errs.append(1e9)
            continue
        errs.append(abs(r["df"] - f_hz))
        res[f_hz] = r
    ok_cfo = max(errs) < 3.0
    ok_all &= ok_cfo
    print(f"  [{'OK ' if ok_cfo else 'HATA'}] frekans sapmasi (CP fazi): "
          f"en kotu hata {max(errs):.2f} Hz  (guclu SSB huzmesi varken de)")
    return ok_all

def self_test():
    print("=" * 70)
    print(" SELF-TEST — bistatik backprojection (donanimsiz, sentetik sahne)")
    print("=" * 70)
    # Self-test KENDI kontrollu geometrisini kurar (dosya basindaki kullanici
    # degerlerinden bagimsiz): TX ve dizi ayni bolgeye bakar, hedefler huzme-ICI
    # ve dogrudan yoldan gecikme olarak AYRISMIS secilir. Sonda geri yuklenir.
    global TX_POS, TX_N1, TX_BW3_DEG, ARRAY_POS, ARRAY_N2, ARRAY_D_M
    global GRID_BOUNDS, GRID_RES_M, PATHLOSS_COMP, USE_TX_PATTERN
    _save = (TX_POS, TX_N1, TX_BW3_DEG, ARRAY_POS, ARRAY_N2, ARRAY_D_M,
             GRID_BOUNDS, GRID_RES_M, PATHLOSS_COMP, USE_TX_PATTERN)
    TX_POS    = np.array([0.0, 0.0, 3.0]);  TX_N1 = np.array([1.0, 1.0, 0.0])
    TX_BW3_DEG = 65.0
    ARRAY_POS = np.array([12.0, 0.0, 0.0]); ARRAY_N2 = np.array([-1.0, 1.0, 0.0])
    ARRAY_D_M = 0.040
    # Izgara hedef bolgesini KAPSAMALI (sadece TX+dizi degil). Hedefleri taban
    # cizgisinden uzak, huzme-ici, gecikme olarak ayrisan noktalarda sec.
    GRID_BOUNDS = (-2.0, 16.0, -2.0, 16.0); GRID_RES_M = 0.10
    PATHLOSS_COMP = 0.0; USE_TX_PATTERN = True     # gercekci: huzme agirligi ACIK

    check_spacing()
    el = element_positions()
    print(f"  TX          : {TX_POS}")
    print(f"  dizi ortasi : {ARRAY_POS}   eksen u={array_axis()}")
    print(f"  elemanlar   :")
    for k in range(N_RX):
        print(f"    k{k}: ({el[k,0]:+.3f}, {el[k,1]:+.3f}, {el[k,2]:+.3f}) m  "
              f"|RX_k-TX|={np.linalg.norm(el[k]-TX_POS):.3f} m")

    # Sentetik genis bant referans (anahtar dosyasi gerekmez). Sahada bunun
    # yerine --learn ile OGRENILEN anahtar gecer; burada amac zinciri sinamak.
    refs, step_s, t_ref = [build_test_burst()], 5e-3, 0.0
    # kisa pencere: birkac occasion yeter
    win_ms = 40.0
    N = int(win_ms * 1e-3 * FS)
    L_seg = N_SLOT
    occ = [int(round(k * step_s * FS)) for k in range(int(win_ms*1e-3/step_s)+2)]
    occ = [o for o in occ if o + L_seg <= N]
    n_cls = len(refs)
    n_occ = (len(occ) // n_cls) * n_cls
    occ = occ[:n_occ]; cls = [k % n_cls for k in range(len(occ))]
    nlag = L_seg - len(refs[0]) + 1
    nfft = 1 << int(np.ceil(np.log2(L_seg + len(refs[0]) - 1)))
    print(f"\n  occasion {len(occ)} adet ({n_cls} sinif), nlag {nlag}")

    # Gercek zincir uyumsuzlugu: sabit kompleks katsayi DEGIL, KISA FIR — yani
    # FREKANSA BAGLI. Tek katsayili kalibrasyonun cozemeyecegi sey tam olarak bu.
    rng = np.random.default_rng(1)
    cal_true = np.ones(N_RX, np.complex64)
    NTAP = 3
    hw_fir = np.zeros((N_RX, NTAP), np.complex128)
    hw_fir[0, 0] = 1.0                                   # kanal 0 referans: duz
    for k in range(1, N_RX):
        hw_fir[k, 0] = np.exp(1j * rng.uniform(-np.pi, np.pi)) * rng.uniform(0.8, 1.2)
        hw_fir[k, 1] = 0.22 * (rng.standard_normal() + 1j * rng.standard_normal())
        hw_fir[k, 2] = 0.10 * (rng.standard_normal() + 1j * rng.standard_normal())
    # EQ_k(f) = FFT(hw_fir[k]) / FFT(hw_fir[0]) = FFT(hw_fir[k])  (hw_fir[0]=delta)
    # eq_from_taps kolonlari -ng..+ng bekliyor -> nedensel taplari ortala.
    NG = NTAP - 1
    eq_taps_true = np.zeros((N_RX, 2 * NG + 1), np.complex128)
    eq_taps_true[:, NG:NG + NTAP] = hw_fir

    # KALIBRASYON noktasi ve GERCEK hedef (farkli yerlerde).
    # DIKKAT: her ikisi de TX-RX taban cizgisinden UZAK ve huzme-ICI secilmeli
    # ki (a) bistatik gecikmesi dogrudan yoldan birkac ornek ayrilsin (yoksa LOS
    # ile ayni bin'e duser ve arka plan cikarma hedefi de siler), (b) TX huzme
    # agirligi hedefi bastirmasin. Gercek sahada da boyle olmali.
    p_cal = np.array([10.0, 10.0, 0.0])    # huzme-ici, ~5 ornek ayrim, izgara-ici
    p_tgt = np.array([3.0, 12.0, 0.0])     # huzme-ici, ~6 ornek ayrim, izgara-ici

    D0 = float(np.linalg.norm(ARRAY_POS - TX_POS))

    # --- eq_from_taps: AYNI taplar FARKLI FFT izgaralarinda ayni yaniti vermeli
    # (equalizer tam bant WB izgarasinda kestirilip korelasyon izgarasinda
    #  uygulandigi icin bu esitlik zincirin dogrulugunun on sartidir)
    E1, _ = eq_from_taps(eq_taps_true, 4096)
    E2, _ = eq_from_taps(eq_taps_true, 8192)
    grid_err = np.abs(E1 - E2[:, ::2]).max()
    ok_grid = grid_err < 1e-5
    print(f"\n  eq_from_taps izgara tutarliligi: en buyuk fark {grid_err:.2e}")
    print(f"  [{'OK ' if ok_grid else 'HATA'}] equalizer farkli FFT izgarasinda "
          f"ayni yaniti veriyor")

    # --- Asama 1: BOS SAHA (sadece dogrudan yol), GERCEKCI CFO ile ---
    # 174 Hz ~ makro hucrenin ±0.05 ppm'i (3.51 GHz -> 176 Hz). Sablon da, canli yakalama
    # da bunu tasir; cikarmanin sinavi bu rampayi yok edebilmesidir.
    CFO_T = 174.0
    _, eq_inv = eq_from_taps(eq_taps_true, nfft)
    L_est = len(refs[0])
    tt = np.arange(L_seg) / FS
    buf_bg = _synth_scene(refs, occ, cls, L_seg, N, cal_true, targets=[],
                          noise=0.02, seed=10, hw_fir=hw_fir, cfo_hz=CFO_T)
    # Sablon: occasion'lar SABLONA hizalanarak (df, a) biriktirilir
    bg_t = [None] * n_cls
    accb = [np.zeros((N_RX, L_seg), np.complex128) for _ in range(n_cls)]
    cnt = np.zeros(n_cls, int)
    for o, c in zip(occ, cls):
        seg = buf_bg[:, o:o + L_seg].astype(np.complex128)
        if bg_t[c] is None:
            seg = seg * np.exp(-1j * np.angle(complex(seg[0, :L_est].sum())))
        else:
            seg, _, _ = align_to_template(seg, bg_t[c], L_est, tt)
        accb[c] += seg; cnt[c] += 1
        bg_t[c] = accb[c] / cnt[c]
    bg = np.stack([_corr_all(bg_t[c], refs[c], nfft, nlag, eq_inv)
                   for c in range(n_cls)])
    n_dir = int(np.argmax(np.abs(bg[0][0])))
    print(f"\n  dogrudan yol capasi n_dir={n_dir}  (LOS D0={D0:.2f} m), "
          f"sentetik CFO {CFO_T:.0f} Hz")

    # --- DOGRUDAN YOL BASTIRMA: yeni (zaman domeni hizalamali) vs eski (yalniz olcek)
    # KRITIK: canli yakalama kalibrasyondan DAKIKALAR sonra alinir ve baz
    # istasyonunun kaymasi bu arada SURUKLENIR. Sabit bir CFO ile test etmek
    # sahtedir — rampa sablonla birebir ayni olur ve her iki yol da calisir.
    # Gercek sinav FARKLI bir kaymadir.
    CFO_L = CFO_T + 400.0                    # STRES: 0.11 ppm (62 der rampa)
    buf_e = _synth_scene(refs, occ, cls, L_seg, N, cal_true, targets=[],
                         noise=0.02, seed=31, hw_fir=hw_fir, cfo_hz=CFO_L)
    C_raw = capture_corr(buf_e, refs, occ, cls, n_cls, L_seg, nlag,
                         eq_inv=eq_inv)
    C_new = capture_corr(buf_e, refs, occ, cls, n_cls, L_seg, nlag, bg=bg,
                         n_dir=n_dir, eq_inv=eq_inv, bg_t=bg_t)
    C_old = capture_corr(buf_e, refs, occ, cls, n_cls, L_seg, nlag, bg=bg,
                         n_dir=n_dir, eq_inv=eq_inv)          # bg_t YOK
    # DIKKAT: artigi n_dir bininde OLCME. _alpha_direct katsayiyi tam o bine
    # oturtur, dolayisiyla orada TANIM GEREGI sifirlanir ve olcum kendi kendini
    # dogrular (eski dosyanin acikca uyardigi tuzak). Azami TUM lag'ler uzerinden.
    p0 = float(np.abs(C_raw[:, n_dir]).max())
    sup_new = 20*np.log10(float(np.abs(C_new).max())/(p0+1e-30)+1e-30)
    sup_old = 20*np.log10(float(np.abs(C_old).max())/(p0+1e-30)+1e-30)
    print(f"\n  DOGRUDAN YOL BASTIRMA (bos saha; sablon {CFO_T:.0f} Hz, "
          f"canli {CFO_L:.0f} Hz -> {abs(CFO_L-CFO_T)*(L_est/FS)*360:.0f} der "
          f"differansiyel rampa):")
    print(f"    zaman domeni hizalamali (yeni): {sup_new:>7.1f} dB")
    print(f"    yalniz olcekli   (eski, bg_t yok): {sup_old:>7.1f} dB")
    ok_sup = sup_new < -25.0 and sup_new < sup_old - 8.0
    print(f"  [{'OK ' if ok_sup else 'HATA'}] hizalamali cikarma LOS'u bastiriyor "
          f"(esik -25 dB ve eskiden >=8 dB iyi)")

    # --- LOS fazi: equalizer sonrasi geometriyle uyusmali (kanal kalibrasyonu) ---
    Dk = np.linalg.norm(el - TX_POS[None, :], axis=1)
    vk = bg[0][:, n_dir]
    exp_ = np.exp(-2j * np.pi * CENTER_FREQ * (Dk - Dk[0]) / C_AIR)
    cal_err = np.degrees(np.angle(vk * np.conj(vk[0]) * np.conj(exp_)))
    # Karsilastirma: TEK katsayi (anahtarin bandindaki ortalama) ne birakirdi?
    ks = np.abs(np.fft.fft(refs[0], nfft)) ** 2
    kb = ks > 0.05 * ks.max()
    EQt, _ = eq_from_taps(eq_taps_true, nfft)
    sc = np.median(EQt[:, kb], axis=1)[:, None]
    sc_err = np.abs(np.degrees(np.angle(sc * np.conj(EQt[:, kb]))))
    print(f"  LOS faz artigi (frekans basina equalizer sonrasi) [der]: "
          + "  ".join(f"{e:+.2f}" for e in cal_err))
    ok_cal = np.max(np.abs(cal_err[1:])) < 5.0
    print(f"  [{'OK ' if ok_cal else 'HATA'}] frekans basina equalizer kanallari "
          f"esitledi (en kotu {np.max(np.abs(cal_err[1:])):.2f} der)")
    print(f"  bilgi: anahtarin bandinda tek katsayinin birakacagi faz hatasi "
          f"{sc_err[1:].max():.2f} der; TAM bantta ise "
          f"{np.abs(np.degrees(np.angle(np.median(EQt,axis=1)[:,None]*np.conj(EQt))))[1:].max():.1f} der")

    # --- Imaging: gercek hedef (DURGUN — MTI yok, bos saha haritasi cikariliyor) ---
    plan = imaging_plan(nlag, n_dir)
    buf_t = _synth_scene(refs, occ, cls, L_seg, N, cal_true,
                         targets=[(p_tgt, 1.0)], noise=0.02, seed=30,
                         hw_fir=hw_fir, cfo_hz=CFO_T + 40.0)   # gercekci
    Cbar = capture_corr(buf_t, refs, occ, cls, n_cls, L_seg, nlag, bg=bg,
                        n_dir=n_dir, eq_inv=eq_inv, bg_t=bg_t)
    img = backproject(Cbar, plan, np.ones(N_RX, np.complex64))
    jy, jx = np.unravel_index(int(np.argmax(img)), img.shape)
    xh, yh = plan["X"][jx], plan["Y"][jy]
    err = np.hypot(xh - p_tgt[0], yh - p_tgt[1])
    print(f"\n  gercek hedef : ({p_tgt[0]:+.2f}, {p_tgt[1]:+.2f}) m")
    print(f"  kestirilen   : ({xh:+.2f}, {yh:+.2f}) m")
    print(f"  konum hatasi : {err:.3f} m  (izgara adimi {GRID_RES_M:.2f} m)")
    # Esik menzil cozunurlugunun yarisi mertebesinde: sentetik sahnede CFO
    # varken tepe tipik olarak bir izgara kosegeni kayiyor (olculdu: 1.0 m,
    # sentetik SSB referansinin cozunurlugu ~2 m). Daha dar esik kirilgan olur.
    ok_pos = err < 5 * GRID_RES_M + 1.0
    print(f"  [{'OK ' if ok_pos else 'HATA'}] backprojection hedefte odaklandi "
          f"(esik {5*GRID_RES_M+1.0:.1f} m)")

    # --- WB: genis bant LOS referansi + FREKANS BASINA equalizer ---
    print("\n" + "-" * 70)
    print(" WB TESTI — LOS referansli tam bant + frekans basina equalizer")
    print("-" * 70)
    nfft_t, nblk_t, bw_t = 16384, 12, 100e6
    rng2 = np.random.default_rng(7)
    hw = _synth_hw(rng2, nfft_t)
    p_wb = np.array([3.0, 12.0, 0.0])
    buf_wb = _synth_wb(nblk_t, nfft_t, [(p_wb, 0.05, 300.0)], hw,
                       noise=0.01, bw_hz=bw_t, seed=40)
    wb = wb_setup([buf_wb], nfft=nfft_t, nblk=nblk_t)
    res_wb = wb_corr(buf_wb, wb, eq=None, self_eq=True)
    n_dir_wb = wb_ndir(res_wb, wb)
    eqf = res_wb["eq"]
    print(f"  blok {len(res_wb['blk'])}, n_dir={n_dir_wb} "
          f"(beklenen {wb['n_dir0']}), equalizer kapisi +-{eqf['gate']} ornek")

    # 1) equalizer GERCEK donanim yanitini geri buldu mu? (bant kenari %5 haric)
    mm = wb_core_mask(wb, 0.05)
    true = hw / hw[0][None, :]
    r_eq   = eqf["EQ"][:, mm] * np.conj(true[:, mm])
    eq_deg = np.abs(np.degrees(np.angle(r_eq)))
    eq_db  = np.abs(20 * np.log10(np.abs(eqf["EQ"][:, mm]) /
                                  (np.abs(true[:, mm]) + 1e-30) + 1e-30))
    print(f"\n  equalizer hatasi (gercek g_k/g_0'a gore), bant ici %95:")
    print(f"    {'kanal':>6} {'faz ort':>8} {'faz max':>8} {'genlik ort':>11} "
          f"{'genlik max':>11}")
    for k in range(1, N_RX):
        print(f"    {k:>6} {eq_deg[k].mean():>7.2f}d {eq_deg[k].max():>7.2f}d "
              f"{eq_db[k].mean():>10.3f} {eq_db[k].max():>10.3f} dB")
    ok_eq = eq_deg[1:].max() < 3.0 and eq_db[1:].max() < 0.5
    print(f"  [{'OK ' if ok_eq else 'HATA'}] frekans basina equalizer donanim "
          f"yanitini cozdu")

    # 2) TEK katsayi ayni isi yapabilir miydi? (bu dosyanin varlik sebebi)
    scal = np.median(eqf["EQ"][:, mm], axis=1)[:, None]
    s_deg = np.abs(np.degrees(np.angle(scal * np.conj(true[:, mm]))))
    s_db  = np.abs(20 * np.log10(np.abs(scal) / (np.abs(true[:, mm]) + 1e-30) + 1e-30))
    print(f"\n  ayni sahnede TEK kompleks katsayi kullanilsaydi kalan hata:")
    for k in range(1, N_RX):
        print(f"    kanal {k}: faz {s_deg[k].max():6.2f} der, genlik "
              f"{s_db[k].max():5.2f} dB   <-> frekans basina "
              f"{eq_deg[k].max():.2f} der / {eq_db[k].max():.3f} dB")
    print(f"  -> {bw_t/1e6:.0f} MHz'de tek katsayi {s_deg[1:].max():.0f} dereceye "
          f"kadar hata birakiyor; backprojection bunu odak kaybi olarak goruyor.")

    # 3) WB backprojection hedefi buluyor mu? (LOO MTI, hareketli hedef)
    plan_wb = imaging_plan(wb["nlag"], n_dir_wb, fs=wb["fs_eff"])
    img_wb, _ = wb_track(res_wb, plan_wb, n_dir_wb)
    ok_wbpos = False
    if img_wb is not None:
        jy, jx = np.unravel_index(int(np.argmax(img_wb)), img_wb.shape)
        xw, yw = plan_wb["X"][jx], plan_wb["Y"][jy]
        err_wb = np.hypot(xw - p_wb[0], yw - p_wb[1])
        ok_wbpos = err_wb < 5 * GRID_RES_M + 0.5
        print(f"\n  WB hedef  : gercek ({p_wb[0]:+.2f}, {p_wb[1]:+.2f}) -> "
              f"kestirilen ({xw:+.2f}, {yw:+.2f}) m,  hata {err_wb:.3f} m")
        print(f"  menzil coz.: {wb['res_m']:.2f} m "
              f"(ayni sahne SSB ~7.2 MHz ile {C_AIR/(2*7.2e6):.1f} m olurdu)")
    print(f"  [{'OK ' if ok_wbpos else 'HATA'}] WB backprojection hedefte odaklandi")

    # --- HUCRE KIMLIGI (PSS/SSS -> PCI) ---
    print("\n" + "-" * 70)
    print(" HUCRE KIMLIGI TESTI — sentetik SSB, bilinen PCI geri bulunmali")
    print("-" * 70)
    nid1_t, nid2_t = 201, 2
    b0_t = N_FFT // 2 - 63 + 200            # SSB merkezden kaydirilmis
    x_ssb, t0_t = _synth_ssb(nid1_t, nid2_t, b0_t, snr=2.0, seed=5)
    cell = detect_cell(x_ssb, win_ms=x_ssb.size / FS * 1e3)
    pci_t = 3 * nid1_t + nid2_t
    ok_cell = (cell is not None and cell["pci"] == pci_t
               and abs(cell["t0"] * FS - t0_t) < 8)
    print(f"\n  beklenen PCI {pci_t} (N_ID_1={nid1_t}, N_ID_2={nid2_t}), "
          f"PSS zamani {t0_t/FS*1e3:.4f} ms")
    print(f"  [{'OK ' if ok_cell else 'HATA'}] PSS/SSS cozuldu, PCI ve zaman dogru")

    # --- STANDART ZINCIRI: SSB / PBCH DMRS / CORESET#0 / SIB1 / ppb ---
    print("\n" + "-" * 70)
    print(" STANDART TESTI — TS 38.211/38.213'e gore URET, geri OKU")
    print("-" * 70)
    ok_std = _std_chain_test()

    # kullanici geometrisini geri yukle
    (TX_POS, TX_N1, TX_BW3_DEG, ARRAY_POS, ARRAY_N2, ARRAY_D_M,
     GRID_BOUNDS, GRID_RES_M, PATHLOSS_COMP, USE_TX_PATTERN) = _save

    ok = (ok_cal and ok_pos and ok_eq and ok_wbpos and ok_cell and ok_grid
          and ok_sup and ok_std)
    # ---------------------------------------------------------------
    print("\n" + "-" * 70)
    print(" KABLOLU KALIBRASYON TESTI — splitter'dan donanim geri bulunmali")
    print("-" * 70)
    rng_w = np.random.default_rng(23)
    nfft_w = 8192
    # Splitter: DORT KANALA DA AYNI dalga formu. Bant sinirli gurultu kullanildi;
    # kalibrasyon bir ORAN oldugu icin dalga formunun sekli sonucu etkilemez
    # (chirp de olurdu) — testin ispatladigi sey tam olarak budur.
    nblk_w = 24
    Nw = nblk_w * nfft_w
    fbw = np.fft.fftfreq(nfft_w, 1.0 / FS)
    band = np.abs(fbw) <= 50e6
    x = np.zeros(Nw, np.complex128)
    for b in range(nblk_w):
        X = (rng_w.standard_normal(nfft_w) + 1j * rng_w.standard_normal(nfft_w))
        x[b * nfft_w:(b + 1) * nfft_w] = np.fft.ifft(X * band) * nfft_w / 64
    fir_w = _synth_hw(rng_w, 8, ntap=4, ripple=0.30)      # (N_RX, 8) frekans
    hw_t = np.fft.ifft(_synth_hw(rng_w, nfft_w, ntap=4, ripple=0.30), axis=1)
    hw_t = hw_t[:, :6]                                    # kisa FIR (6 tap)
    bufw = np.zeros((N_RX, Nw), np.complex128)
    for k in range(N_RX):
        bufw[k] = np.convolve(x, hw_t[k])[:Nw]
    bufw += 0.002 * (rng_w.standard_normal((N_RX, Nw)) +
                     1j * rng_w.standard_normal((N_RX, Nw)))

    accw = wcal_accum(bufw.astype(np.complex64), nfft_w)
    solw = wcal_solve(accw, FS, ng=WCAL_NG)
    if solw is None:
        ok = False
        print("  [HATA] kablolu kalibrasyonda bant bulunamadi")
    else:
        wcal_report(solw)
        Hf = np.fft.fft(hw_t, nfft_w, axis=1)
        Htrue = Hf / Hf[0][None, :]
        mw = solw["mask"]
        eph = np.zeros(N_RX); edb = np.zeros(N_RX)
        for k in range(N_RX):
            r = solw["EQ"][k][mw] / (Htrue[k][mw] + 1e-30)
            eph[k] = float(np.percentile(np.abs(np.degrees(np.angle(r))), 95))
            edb[k] = float(np.percentile(np.abs(20*np.log10(np.abs(r)+1e-30)), 95))
        print(f"\n  gercek g_k/g_0'a gore hata (bant ici %95):")
        for k in range(1, N_RX):
            single = Htrue[k][mw] / np.median(Htrue[k][mw])
            sph = float(np.percentile(np.abs(np.degrees(np.angle(single))), 95))
            print(f"    kanal {k}: frekans basina {eph[k]:5.2f} der / "
                  f"{edb[k]:.3f} dB   <-> tek katsayi olsaydi {sph:5.1f} der")
        if eph[1:].max() < 3.0 and edb[1:].max() < 0.3:
            print("  [OK ] kablolu kalibrasyon donanim yanitini cozdu")
        else:
            ok = False
            print("  [HATA] kablolu kalibrasyon yeterince dogru degil")
        # Kural sinavi: cozum GEOMETRI kullanmamali. TX_POS'u oynatinca sonuc
        # DEGISMEMELI — degisiyorsa bir yerde LOS/geometri sizmis demektir.
        _tx_save = TX_POS.copy()
        globals()["TX_POS"] = TX_POS + np.array([137.0, -91.0, 4.0])
        sol2 = wcal_solve(accw, FS, ng=WCAL_NG)
        globals()["TX_POS"] = _tx_save
        drift = float(np.max(np.abs(sol2["taps"] - solw["taps"])))
        print(f"\n  TX_POS 160 m oynatildi -> tap degisimi {drift:.2e}")
        if drift < 1e-12:
            print("  [OK ] kablolu cozum GEOMETRIDEN BAGIMSIZ (LOS sizmasi yok)")
        else:
            ok = False
            print("  [HATA] cozum geometriye bagli — LOS tabanli bir sey sizmis")

    print("\n" + "=" * 70)
    if ok:
        print(" SELF-TEST GECTI — dar bant, genis bant, equalizer, hucre")
        print(" kimligi, STANDART (SSB/PBCH/CORESET#0/SIB1/ppb) ve KABLOLU")
        print(" kalibrasyon zincirlerinin hepsi tutarli.")
    else:
        print(" SELF-TEST BASARISIZ — yukaridaki HATA satirlarina bak.")
    print("=" * 70)
    return ok



if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="X410 4 kanal bistatik konum kestirimi (backprojection)")
    ap.add_argument("--self-test", action="store_true",
                    help="donanimsiz uctan uca dogrulama (sentetik sahne)")
    ap.add_argument("--freq", type=float, default=None, metavar="MHZ",
                    help=f"RF merkez frekansi [MHz] (dosyadaki "
                         f"{CENTER_FREQ/1e6:.3f}'i ezer) — bant taramak icin")
    ap.add_argument("--gain", type=float, default=None, metavar="DB",
                    help=f"RX kazanci [dB] (dosyadaki {RX_GAIN:.0f}'i ezer). "
                         f"Ticari makro hucre cok gucludur; kirpma varsa dusur")
    ap.add_argument("--psd", type=int, nargs="?", const=5, default=None,
                    metavar="N",
                    help="BAND TANISI: spektrum + zaman profili (ogrenmeden ONCE; "
                         "frekans dogru mu, kazanc kirpiyor mu, DL nerede)")
    ap.add_argument("--learn", type=int, nargs="?", const=LEARN_N_DEF, default=None,
                    metavar="N",
                    help=f"deterministik sinyali ogren -> {LEARN_FILE}. v4'te bu "
                         f"DEMODULASYON TABANLIDIR: OFDM izgarasina cozer, N "
                         f"yakalama boyunca degismeyen RE'leri bulur, kanali "
                         f"soker, takimyildiza DILIMLER ve yeniden sentezler. "
                         f"Cikti s(t)'dir (kanalsiz), v3'teki s(t)*h(t) degil")
    ap.add_argument("--learn-legacy", type=int, nargs="?", const=LEARN_N_DEF,
                    default=None, dest="learn_legacy", metavar="N",
                    help="v3'un ESKI ogrenme yolu (alinan IQ'nun N frame "
                         "ortalamasi). Kanali anahtarin icinde birakir; sadece "
                         "yeni yolla KARSILASTIRMAK icin (--keydiff)")
    ap.add_argument("--recon-gamma", type=float, default=RECON_GAMMA_MIN,
                    dest="recon_gamma", metavar="G",
                    help=f"--learn: RE'nin SABIT sayilmasi icin yakalamalar "
                         f"arasi tutarlilik esigi (varsayilan {RECON_GAMMA_MIN})")
    ap.add_argument("--recon-evm", type=float, default=RECON_EVM_MAX,
                    dest="recon_evm", metavar="E",
                    help=f"--learn: dilimlemeden once azami EVM (varsayilan "
                         f"{RECON_EVM_MAX}). Buyutursen daha cok RE girer ama "
                         f"bir kismi YANLIS dilimlenir")
    ap.add_argument("--ssbscan", nargs="?", const="", default=None,
                    metavar="LO..HI",
                    help=f"SSB TARAMASI: bandi ZAMAN DOMENINDE tara, hucreyi "
                         f"bul ve kimligini (PCI, i_SSB) coz. Varsayilan bant "
                         f"{SSB_BAND[0]/1e6:.0f}-{SSB_BAND[1]/1e6:.0f} MHz; "
                         f"'3400..3600' gibi verilebilir. Kafese BAGLI DEGIL — "
                         f"PSS'i kaydirmali korelasyonla arar, bu yuzden "
                         f"frekans-domeni aramadan ~30 dB daha hassastir")
    ap.add_argument("--synth", action="store_true",
                    help="--learn ile: anahtari OLCME, cozulmus PCI'dan URET. "
                         "Once SSB taranir (--ssbscan mantigi), kimlik "
                         "cozulur, sonra PSS/SSS/PBCH-DMRS PCI'den uretilir. "
                         "Tekrarlanabilirlik TANIM GEREGI 1.0; bedeli bant "
                         "7.2 MHz (menzil ~20.8 m)")
    ap.add_argument("--recon-survey", type=int, default=RECON_SURVEY_N,
                    dest="recon_survey", metavar="N",
                    help=f"--learn TANIMA asamasi yakalama sayisi (varsayilan "
                         f"{RECON_SURVEY_N}). Numeroloji, bant ve tekrar "
                         f"periyodu bu asamada OLCULUR")
    ap.add_argument("--recon-us", type=float, default=RECON_KEY_US,
                    dest="recon_us", metavar="US",
                    help=f"--learn: kurgulanacak pencere [us] (varsayilan "
                         f"{RECON_KEY_US:.0f}); sembol sayisina kendiliginden cevrilir")
    ap.add_argument("--learn-out", type=str, default=None, dest="learn_out",
                    metavar="DOSYA",
                    help=f"--learn ciktisini bu dosyaya yaz (varsayilan "
                         f"{LEARN_FILE}). MEVCUT bir dosyanin uzerine ASLA "
                         f"yazilmaz; yeni anahtari ayri tutup eskisiyle "
                         f"--keydiff ile karsilastirmak icin")
    ap.add_argument("--force-key", action="store_true", dest="force_key",
                    help="--learn mevcut anahtar dosyasinin uzerine yazsin "
                         "(varsayilan: yazmaz, hata verir)")
    ap.add_argument("--keydiff", type=str, nargs="+", default=None,
                    metavar="DOSYA",
                    help=f"DONANIMSIZ: IKI ANAHTARI KARSILASTIR (A B; tek "
                         f"dosya verilirse A={LEARN_FILE}). RF ayari (merkez "
                         f"frekans/Fs/kazanc), hucre kimligi, isgal edilen "
                         f"bant, dalga formu koherensi, frekansa gore "
                         f"kazanc/faz ve diferansiyel CIR")
    ap.add_argument("--keycheck", type=str, nargs="?", const=LEARN_FILE,
                    default=None, metavar="DOSYA",
                    help=f"DONANIMSIZ: anahtarin ({LEARN_FILE}) hangi "
                         f"frekanslarinin HER PERIYOT AYNI geldigini olcer "
                         f"(koherent/inkoherent spektrum orani). Deterministik "
                         f"bandi ve gercek menzil cozunurlugunu soyler")
    ap.add_argument("--auto", type=int, nargs="?", const=LOC_DUR_S, default=None,
                    metavar="SN",
                    help="TEK KOSU (varsayilan davranis): splitter kalibrasyonu "
                         "-> olcum, AYNI oturumda. Anahtar onceden --learn ile "
                         "ogrenilmis olmali (anahtar kanallar arasi faza bagli "
                         "degildir, process'ler arasi yasar). Her yeniden "
                         "baslatmada cihaz initialize olur ve FAZ KALIBRASYONU "
                         "GIDER; bu yuzden kalibrasyon ve olcum tek process'te. "
                         "SN = olcum suresi")
    ap.add_argument("--auto-wcal", type=int, default=AUTO_WCAL_N, dest="auto_wcal",
                    metavar="N",
                    help=f"--auto: splitter kalibrasyonu olcum sayisi "
                         f"(varsayilan {AUTO_WCAL_N}, ~{AUTO_WCAL_N} s)")
    ap.add_argument("--auto-mode", type=str, default="locate", dest="auto_mode",
                    choices=("locate", "range"),
                    help="son asama: locate (x-y KONUM haritasi, varsayilan) ya "
                         "da range (kanal basina menzil ispati)")
    ap.add_argument("--geom", type=str, default=None, metavar="DOSYA",
                    help=f"geometri dosyasi (varsayilan {GEOM_FILE}). Yoksa "
                         f"sorulur ve yazilir")
    ap.add_argument("--geom-ask", action="store_true", dest="geom_ask",
                    help="geometriyi YENIDEN sor (dosya olsa bile)")
    ap.add_argument("--ota", action="store_true",
                    help="HAVADAN KALIBRASYON: splitter yerine HORN ile, dizinin "
                         "tam karsisindan 0 DERECEDEN. Broadside'da yol farki "
                         "sifir oldugu icin olculen faz saf donanimdir")
    ap.add_argument("--ota-range", type=float, default=None, dest="ota_range",
                    metavar="M", help=f"--ota: horn mesafesi [m] (yakin alan "
                                      f"egriligi uyarisi icin; oneri >= "
                                      f"{OCAL_MIN_RANGE_M:.0f} m)")
    ap.add_argument("--verify", nargs="?", const="live", default=None,
                    metavar="DER",
                    help="KALIBRASYON DOGRULAMA. Argumansiz (--verify) CANLI "
                         "TAKIP acar: horn'u saga sola oynatirsin, tepe takip "
                         "eder; pencereyi kapatinca olcume devam edilir. Sayi "
                         "verilirse (orn. --verify 20) horn'u o aciya koyup tek "
                         "seferlik karsilastirir")
    ap.add_argument("--force-cal", action="store_true", dest="force_cal",
                    help="kalibrasyon kalite testlerini UYARIYA cevir ve devam "
                         "et. Havadan (--ota) kalibrasyonda baz istasyonu ayni "
                         "bantta yayin yaptigi icin koherans dusuk cikar; "
                         "sonucun kullanilabilir olup olmadigini --verify soyler")
    ap.add_argument("--linear", action="store_true",
                    help="sonuc grafiklerini LINEER olcekte ciz (dB yerine): "
                         "konum haritasi, menzil waterfall ve dogrulama huzmesi. "
                         "Tepe 1.0'a normalize edilir")
    ap.add_argument("--rxdir", action="store_true",
                    help="RX DOGRULTU AYARI: dizinin baktigi yonu kaydiriciyla "
                         "canli ayarla ve kaydet. Donanim GEREKMEZ. Dizi normali "
                         "aci kestiriminin sifir referansidir — yanlissa butun "
                         "hedefler ayni miktarda doner")
    ap.add_argument("--learn-win", type=float, default=LEARN_WIN_MS, dest="learn_win",
                    metavar="MS",
                    help=f"--learn/--psd pencere uzunlugu [ms] (varsayilan "
                         f"{LEARN_WIN_MS:.0f}; SSB 20 ms'de tekrar ettigi icin "
                         f"ticari sebekede >=40 ms birak)")
    ap.add_argument("--keymax", type=float, default=None, metavar="US",
                    help=f"anahtarin azami uzunlugu [us] (varsayilan "
                         f"{LEARN_KEY_MAX_US:.0f} = bir SSB). Cok huzmeli burst "
                         f"set'te tutarli bolge ms'lerce surer; en guclu bu "
                         f"kadarlik alt pencere alinir")
    ap.add_argument("--gamma", type=float, default=LEARN_GAMMA_MIN, metavar="G",
                    help=f"--learn tutarlilik esigi (varsayilan {LEARN_GAMMA_MIN}; "
                         f"zayif hucrede 0.2-0.3 dene)")
    ap.add_argument("--step", type=float, default=None, metavar="MS",
                    help="ogrenilmis anahtarin TEKRAR PERIYODU [ms] "
                         "(varsayilan NR frame = 10; ticari sebekede SSB icin 20). "
                         "Dogru degeri --learn ciktisindaki ofset farklari verir")
    ap.add_argument("--wcal", type=int, nargs="?", const=WCAL_SECONDS,
                    default=None, metavar="SN",
                    help=f"KABLOLU (splitter) dizi kalibrasyonu, varsayilan "
                         f"{WCAL_SECONDS} s. ACI kalibrasyonu SADECE buradan "
                         f"gelir; LOS'tan kanal kalibrasyonu yapilmaz. Chirp'i "
                         f"BASKA BIR TERMINALDE baslat: "
                         f"python3 fmcw_tx_turkcell_calib.py . Tek basina degil, "
                         f"--range/--locate ILE BIRLIKTE ver (tek oturum)")
    ap.add_argument("--calib", type=int, nargs="?", const=CAL_SECONDS, default=None,
                    metavar="SN",
                    help=f"BOS SAHA kalibrasyonu (varsayilan {CAL_SECONDS} s): "
                         f"frekans basina equalizer + durgun ortam haritasi + "
                         f"n_dir -> {CAL_FILE}. Hedef koymaya GEREK YOK")
    ap.add_argument("--locate", type=int, nargs="?", const=LOC_DUR_S, default=None,
                    metavar="SN", help=f"canli backprojection isi haritasi (varsayilan {LOC_DUR_S} s)")
    ap.add_argument("--range", type=int, nargs="?", const=60, default=None,
                    metavar="SN", dest="range_diag",
                    help="KANAL-BASINA menzil tanisi: arka plan cikarma + range ispati "
                         "(4 kanal ayri ayri, varsayilan 60 s)")
    ap.add_argument("--target", type=float, nargs="+", default=None,
                    metavar="X Y [Z]",
                    help="--range icin bilinen hedef konumu (beklenen menzil isaretlenir)")
    ap.add_argument("--rmax", type=float, default=RANGE_RMAX_M, metavar="M",
                    help=f"--range x ekseni azami bistatik fazla menzil "
                         f"(varsayilan {RANGE_RMAX_M:.0f} m)")
    ap.add_argument("--tpl", type=int, nargs="?", const=40, default=None,
                    metavar="N",
                    help="KAYAN PENCERE SABLONU (eski 4rx_1tx_kdyf mantigi): "
                         "sablon = ayni akistan son N occasion, her occasion'da "
                         "tazelenir. --cal GEREKMEZ, capa/CFO/LO sorunu YOK. "
                         "Sadece HAREKETLI hedef. Varsayilan 40")
    ap.add_argument("--avg", type=int, default=1, metavar="N",
                    help="YAVAS ZAMAN INTEGRASYONU: son N yakalamanin cikarma "
                         "sonrasi profilini koherent ortala. Arka plan tabanini "
                         "10*log10(N) dB dusurur (DURGUN hedef icin bedava; "
                         "hareketli hedef smearlenir). Oneri 4-16")
    ap.add_argument("--mti", action="store_true",
                    help="HAREKETLI HEDEF modu: kalibrasyon olsa bile bos saha "
                         "haritasi yerine capture-ici leave-one-out MTI kullan. "
                         "Duran her sey (LOS, binalar, DURGUN HEDEF) iptal olur. "
                         "Varsayilan kapali: --cal verilmisse durgun hedef de gorunur")
    ap.add_argument("--key", type=str, default=None, metavar="DOSYA",
                    help=f"deterministik referans anahtari ({LEARN_FILE}). "
                         f"--ref key (VARSAYILAN) ile ZORUNLU — referans "
                         f"URETILMEZ, --learn ile OGRENILIR. --ref los ile "
                         f"opsiyonel (yalnizca pencere yerlesimi ve hucre bilgisi)")
    ap.add_argument("--cal", type=str, default=None, metavar="DOSYA",
                    help=f"--locate icin konum kalibrasyonu (orn. {CAL_FILE})")
    # --- hucre kimligi / LOS equalizer kalibrasyonu ---
    ap.add_argument("--cell", type=int, nargs="?", const=3, default=None,
                    metavar="N",
                    help="HUCRE TANISI: PSS/SSS -> PCI, SSB frekans/zamani, "
                         "isgal edilen bant ve WB cozunurlugu (varsayilan 3 yakalama)")
    ap.add_argument("--cells", nargs="?", type=int, const=CELLS_N_CAP,
                    default=None, metavar="N",
                    help=f"KOMSU BANT TARAMASI: {CELLS_BAND_A[0]/1e6:.0f}-"
                         f"{CELLS_BAND_A[1]/1e6:.0f} ve {CELLS_BAND_B[0]/1e6:.0f}-"
                         f"{CELLS_BAND_B[1]/1e6:.0f} MHz bloklarini AYNI "
                         f"yakalamada karsilastirir (PCI, PBCH DMRS, frekans "
                         f"sapmasi [ppb], CORESET#0/SIB1) ve iki blogun tek gNB "
                         f"mi iki gNB mi oldugunu soyler. Blok basina N "
                         f"yakalama (varsayilan {CELLS_N_CAP}); PCI ancak "
                         f"yakalamalarin yarisinda PBCH DMRS ile dogrulanirsa "
                         f"kabul edilir. LO'yu tasir -> TEK BASINA calistir")
    ap.add_argument("--cells-band", type=float, nargs=4, default=None,
                    metavar=("A_LO", "A_HI", "B_LO", "B_HI"),
                    help="--cells icin blok kenarlari [MHz] (varsayilani ez)")
    # --- genis bant (WB) ayarlari ---
    ap.add_argument("--nowb", action="store_true",
                    help="--ref key ile ayni (geriye donuk uyum)")
    ap.add_argument("--fullband", action="store_true",
                    help="bant sinirini KAPAT: 122.88 MHz pencerenin tamami "
                         "islenir ve gosterilir. SADECE TESHIS icin — komsu "
                         "hucre/alias equalizer'a girer ve ACIYI kaydirir")
    ap.add_argument("--bw", type=float, default=None, metavar="MHZ",
                    help="WB isleme bandini ELLE ver [MHz] (merkeze simetrik). "
                         "Verilmezse isgal edilen bant OLCULUR")
    ap.add_argument("--blk", type=float, default=None, metavar="MS",
                    help=f"WB korelasyon blogu [ms] (2'nin kuvvetine yuvarlanir; "
                         f"varsayilan {WB_NFFT/FS*1e3:.3f})")
    ap.add_argument("--nblk", type=int, default=None, metavar="N",
                    help=f"yakalama basina WB blok sayisi (varsayilan {WB_NBLK}; "
                         f"LOO MTI icin >=2, >=8 onerilir)")
    ap.add_argument("--whiten", type=float, default=None, metavar="P",
                    help=f"spektral beyazlatma ustu 0..1 (varsayilan {WB_WHITEN}; "
                         f"1=en dusuk menzil yan lobu, 0=en yuksek SNR)")
    ap.add_argument("--wbmax", type=float, default=None, metavar="M",
                    help=f"WB menzil profilinde tutulan azami fazla menzil "
                         f"(varsayilan {WB_RMAX_M:.0f} m)")
    ap.add_argument("--ref", type=str, default=None,
                    choices=["key", "los", "beam"],
                    help=f"KORELASYON REFERANSI (varsayilan {REF_SRC}). "
                         f"key = ogrenilmis SSB anahtari (deterministik, ~20 m, "
                         f"durgun hedef gorunur). los = dogrudan yolun kendisi "
                         f"(tam bant ~1.5 m ama kirli referans, sadece hareketli). "
                         f"beam = los + TX yonune huzme")
    ap.add_argument("--eqgate", type=float, default=None, metavar="M",
                    help=f"equalizer LOS kapisi [m] (varsayilan {EQ_GATE_M:.0f}); "
                         f"buyutursen yakin cevre yankisi equalizer'a karisir")
    ap.add_argument("--noeq", action="store_true",
                    help="frekans basina equalizer'i KAPAT (karsilastirma icin)")
    # geometri override'lari
    ap.add_argument("--tx", type=float, nargs=3, default=None, metavar=("X", "Y", "Z"))
    ap.add_argument("--array", type=float, nargs=3, default=None, metavar=("X", "Y", "Z"))
    ap.add_argument("--n1", type=float, nargs=3, default=None, metavar=("X", "Y", "Z"))
    ap.add_argument("--n2", type=float, nargs=3, default=None, metavar=("X", "Y", "Z"))
    ap.add_argument("--d", type=float, default=None, metavar="M", help="eleman araligi [m]")
    ap.add_argument("--bw3", type=float, default=None, metavar="DEG", help="TX -3dB huzme [der]")
    ap.add_argument("--grid", type=float, nargs=4, default=None,
                    metavar=("XMIN", "XMAX", "YMIN", "YMAX"),
                    help="KONUM HARITASI SINIRLARI [m]. Alici (0,0). Ornek: "
                         "--grid -20 20 0 60  -> 40x60 m'lik bolge. Verilmezse "
                         "TX+RX'i iceren kutu otomatik alinir")
    ap.add_argument("--res", type=float, default=None, metavar="M",
                    help=f"izgara adimi [m]. Eksen basina en fazla "
                         f"{GRID_MAX_CELLS} hucre; alan buyukse adim "
                         f"kendiliginden kabalasir ve uyarilir")
    a = ap.parse_args()
    _apply_geometry_overrides(a)
    if a.step:
        KEY_STEP_MS = float(a.step)
    if a.verify is not None and a.verify != "live":
        try:
            a.verify = float(a.verify)
        except ValueError:
            print(f"[HATA] --verify sayi ya da bos olmali (verilen: {a.verify!r})")
            sys.exit(1)
    if a.freq:
        CENTER_FREQ = float(a.freq) * 1e6
    if a.gain is not None:
        RX_GAIN = float(a.gain)
    # --- referans secimi + WB/equalizer override'lari ---
    if a.nowb:
        REF_SRC = "key"
    if a.ref is not None:
        REF_SRC = a.ref
    WB_MODE = (REF_SRC != "key")
    WB_REF  = "beam" if REF_SRC == "beam" else "ch0"
    if a.bw is not None:
        WB_BW_MHZ = float(a.bw)
    if a.blk is not None:
        WB_NFFT = 1 << int(round(np.log2(max(1024.0, a.blk * 1e-3 * FS))))
    if a.nblk is not None:
        WB_NBLK = max(2, int(a.nblk))
    if a.whiten is not None:
        WB_WHITEN = float(np.clip(a.whiten, 0.0, 1.0))
    if a.wbmax is not None:
        WB_RMAX_M = float(a.wbmax)
    if a.keymax is not None:
        LEARN_KEY_MAX_US = float(a.keymax)
    if a.eqgate is not None:
        EQ_GATE_M = float(a.eqgate)
    if a.noeq:
        EQ_ON = False
    if a.linear:
        PLOT_LINEAR = True
    if a.fullband:
        BAND_LIMIT_ON = False
        print("[UYARI] --fullband: bant siniri KAPALI. Komsu hucre ve DDC "
              "alias'i isleme girer; equalizer/aci GUVENILMEZ olur.")

    # --key VERILMEDIYSE diskteki anahtari kullan. Dosya adi zaten sabit;
    # her komutta tekrar yazdirmanin anlami yok.
    if a.key is None:
        _def = os.path.join(os.path.dirname(os.path.abspath(__file__)), LEARN_FILE)
        if os.path.exists(_def):
            a.key = _def

    # --rxdir donanim ISTEMEZ: sadece geometri ayarlar.
    if a.rxdir:
        rxdir_ui(a.geom)
        sys.exit(0)

    # --keydiff donanim ISTEMEZ: iki dosyayi karsilastirir.
    if a.keydiff is not None:
        def _kd_path(x):
            if not os.path.isabs(x):
                c = os.path.join(os.path.dirname(os.path.abspath(__file__)), x)
                return c if os.path.exists(c) else x
            return x
        _pp = [_kd_path(x) for x in a.keydiff]
        if len(_pp) == 1:
            _pp = [_kd_path(LEARN_FILE)] + _pp
        elif len(_pp) != 2:
            print("[HATA] --keydiff bir ya da iki dosya alir.")
            sys.exit(1)
        keydiff(_pp[0], _pp[1])
        sys.exit(0)

    # --keycheck donanim ISTEMEZ: dosyadan olcum yapar, hemen kosar.
    if a.keycheck is not None:
        _kp = a.keycheck
        if not os.path.isabs(_kp):
            _c = os.path.join(os.path.dirname(os.path.abspath(__file__)), _kp)
            _kp = _c if os.path.exists(_c) else _kp
        if not os.path.exists(_kp):
            print(f"[HATA] anahtar dosyasi yok: {_kp}")
            print(f"       Once: python3 {os.path.basename(__file__)} --learn")
            sys.exit(1)
        print("=" * 70)
        print(f" ANAHTAR DETERMINIZM KONTROLU — {os.path.basename(_kp)}")
        print("=" * 70)
        _dk = np.load(_kp)
        if "pci" in _dk.files and int(_dk["pci"]) >= 0:
            print(f"  PCI {int(_dk['pci'])}, {int(_dk['n_cap'])} yakalama "
                  f"ortalamasi, merkez {float(_dk['center_freq'])/1e6:.0f} MHz")
        key_determinism(_dk)
        sys.exit(0)

    _hw_modes = (a.calib, a.locate, a.learn, a.learn_legacy, a.psd,
                 a.range_diag, a.cell, a.cells, a.auto,
                 (0 if a.ssbscan is not None else None))
    if a.self_test or (not _HAVE_UHD and all(m is None for m in _hw_modes)
                       and not a.wcal):
        ok = self_test()
        sys.exit(0 if ok else 1)

    # --- KABLOLU KALIBRASYON: bir MOD DEGIL, ONCEKI ASAMADIR. ---
    # Alici oturumunu ACAR; pesinden gelen mod setup_x410'u tekrar cagirdiginda
    # AYNI oturum dondurulur (bkz. _SESSION). Boylece kanallar arasi faz — yani
    # kalibrasyonun kendisi — iki asama arasinda korunur.
    if a.wcal is not None and a.auto is None:      # --auto kendi wcal'ini kosar
        if a.locate is None and a.range_diag is None and a.calib is None:
            print("[UYARI] --wcal tek basina verildi: kalibrasyon alinacak ve")
            print("        program bitecek. FAZ kismi bir sonraki calistirmada")
            print("        GECERSIZ olur. Dogrusu: --wcal ile birlikte --range/")
            print("        --locate ver, ikisi ayni oturumda kossun.")
        wcal_run(a.wcal, a.key, ota=a.ota, ota_range_m=a.ota_range,
                 verify_deg=a.verify, force=a.force_cal)

    if a.ssbscan is not None:
        _band = None
        if a.ssbscan:
            try:
                _l, _h = a.ssbscan.split("..")
                _band = (float(_l) * 1e6, float(_h) * 1e6)
            except Exception:
                print(f"[HATA] --ssbscan bicimi 'LO..HI' olmali (MHz): {a.ssbscan!r}")
                sys.exit(1)
        _c = ssb_find(_band)
        sys.exit(0 if _c else 1)

    if a.auto is not None:
        # --auto'da bos saha haritasi yok (kalibrasyon asamasi kablodan geliyor),
        # bu yuzden duran her seyi LOO MTI bastirir: HAREKETLI HEDEF modu.
        auto_run(a.auto, a.auto_wcal, a.key, a.step,
                 a.auto_mode, a.target, a.rmax, True, max(1, a.avg),
                 a.tpl, a.cal, a.geom, a.geom_ask, a.ota,
                 a.ota_range, a.verify, a.force_cal)
    elif a.cells:
        bands = [CELLS_BAND_A, CELLS_BAND_B]
        if a.cells_band:
            bands = [(a.cells_band[0] * 1e6, a.cells_band[1] * 1e6),
                     (a.cells_band[2] * 1e6, a.cells_band[3] * 1e6)]
        cells_run(max(a.learn_win, CELLS_WIN_MS), bands, max(1, a.cells))
    elif a.psd is not None:
        psd_probe(a.psd, a.learn_win)
    elif a.cell is not None:
        cell_probe(a.cell, max(a.learn_win, CELL_WIN_MS))
    elif a.learn is not None and a.synth:
        _c = ssb_find()
        if not _c:
            sys.exit(1)
        synth_key_from_cell(_c, out_path=a.learn_out, overwrite=a.force_key)
    elif a.learn is not None:
        learn_key_recon(a.learn, a.learn_win, out_path=a.learn_out,
                        overwrite=a.force_key, gamma_min=a.recon_gamma,
                        evm_max=a.recon_evm, n_survey=int(a.recon_survey),
                        key_us=float(a.recon_us))
    elif a.learn_legacy is not None:
        print("[BILGI] ESKI ogrenme yolu (v3): alinan IQ ortalanir, KANAL")
        print("        anahtarin icinde KALIR. Yeni yol icin: --learn")
        learn_key(a.learn_legacy, a.learn_win, out_path=a.learn_out,
                  gamma_min=a.gamma, overwrite=a.force_key)
    elif a.calib is not None:
        calib_run(a.calib, a.key)
    elif a.range_diag is not None:
        range_diag(a.range_diag, a.key, a.cal, a.target, a.rmax, a.mti,
                   max(1, a.avg), a.tpl)
    elif a.locate is not None:
        locate_live(a.locate, a.key, a.cal, a.mti, max(1, a.avg))
    else:
        # ARGUMANSIZ CALISTIRMA = TAM AKIS. Ne yapilacagi belli; kullaniciya
        # her seferinde ayni bayraklari dizdirmenin anlami yok.
        print("=" * 70)
        print(" Arguman verilmedi -> KALIBRASYON + OLCUM (onerilen kullanim).")
        print("=" * 70)
        _rt = ("tam bant, ~1.5 m, sadece hareketli" if REF_SRC != "key"
               else "dar bant anahtar, ~9 m")
        print(f"  referans  : {REF_SRC}   ({_rt})")
        print(f"  kazanc    : {RX_GAIN:.0f} dB   bant: 3480-3580 MHz")
        print(f"\n  IKI KOSULUK AKIS:")
        print(f"    1) --learn   anahtari ogren  (BIR KERE, ~{LEARN_N_DEF} s)")
        print(f"    2) (arguman yok)  kalibrasyon + olcum  (her seferinde)")
        print(f"  Anahtar kanallar arasi faza bagli DEGIL, o yuzden bir kere")
        print(f"  ogrenilir. Kalibrasyonun fazi ise oturuma bagli, o yuzden")
        print(f"  kalibrasyon ve olcum ayni process'te.")
        print(f"\n  Baska bir sey istersen:")
        print(f"    --auto-mode locate   konum haritasi (varsayilan: menzil)")
        print(f"    --auto 300           olcum suresini uzat [s]")
        print(f"    --ref key            dar bant referans (durgun hedef de gorunur)")
        print(f"    --self-test          donanimsiz dogrulama")
        print(f"    --psd / --cell / --cells   tekil teshis modlari")
        print(f"    --help               hepsi\n")
        auto_run(LOC_DUR_S, a.auto_wcal, a.key, a.step,
                 a.auto_mode, a.target, a.rmax, True, max(1, a.avg),
                 a.tpl, a.cal, a.geom, a.geom_ask, a.ota,
                 a.ota_range, a.verify, a.force_cal)
