# v4_1tx_4rx_turkcell.py — KANALSIZ ANAHTAR (demodulasyon + dilimleme)

v3'ten tek fark OGRENME (`--learn`). Olcum tarafinda hicbir sey degismedi:
`load_key`, `_build_refs`, `locate_live`, `range_diag`, `keydiff`, `--auto`
zinciri v3 ile BIREBIR ayni ve dosya bicimi de ayni.

> ONCEKI v4 (bos sahne renk skalasi, `--raw`, `--scale-*`, LOS guard) BU
> DOSYADA YOK. Git'te duruyor: commit `e246548`. Geri istenirse oradan alinir.

## Sorun

v3'un `--learn`'i ALINAN sinyali N frame boyunca IQ ortalar. Ortalama rastgele
icerigi (PDSCH) sondurur ama KANALI sondurmez. Cikan anahtar `s(t)` degil,
`s(t) * h(t)`'dir — ogrenme gununun cok yolu anahtarin ICINE gomulur.

Mevcut `signal_key.npz` uzerinde OLCULDU (2026-08-14, PCI 918, 3530 MHz).
Anahtarin kendi otokorelasyonu `IFFT(|R(f)|^2) = (s*s) (*) (h*h)`:

```
  -8.7 dB @  24.40 m      -17.7 dB @  78.07 m
 -14.0 dB @  43.91 m      -19.4 dB @  60.99 m     ... 270 m'ye kadar 16 tepe
RMS gecikme yayilimi 62 ns (18.5 m), ana yol disi enerji %17.7 (0.84 dB kayip)
```

Bunlar spektral delik artefakti DEGIL: isgal edilen bant 3481.81..3498.81 MHz
KESINTISIZ (35 dilimin hicbiri -13 dB altinda degil), gecikmeler 81..900 ns
yani tam olarak CP'nin (2.34 us) kapsadigi cok yol bolgesi, ve 62 ns ders
kitabi sehir-makro degeri.

**Sonucu — hayalet taragi.** Korelasyon `C = IFFT(FFT(seg) * conj(FFT(ref)))`
oldugu icin tepeler `t_hedef - t_i`'de cikar; her hareketli hedef kendi
ONUNDE kopyalar birakir:

| gercek hedef | izgaradaki hayaletler (fazla menzil 3.94..111.90 m) |
|---|---|
| 30 m | 5.6 m (-9 dB) |
| 50 m | 25.6 (-9), 6.1 (-14) |
| 70 m | 45.6 (-9), 26.1 (-14), 9.0 (-19) |
| 110 m | 85.6, 66.1, 49.0, 31.9, 12.4 |

Bu kopyalar da HAREKETLI oldugu icin **LOO MTI onlari temizlemez**.

## Cozum

Sinyali OFDM izgarasina demodule et, N yakalama boyunca degismeyen RE'leri
bul, kanali sok, takimyildiza **DILIMLE**, yeniden sentezle.

> ORTALAMA kanali kaldirmaz. DILIMLEME kaldirir.
> `x_hat = Vbar/H` bir takimyildiz noktasinin yakinina duser; en yakin QPSK
> noktasina yuvarlaninca elde kalan sey ILETILEN sembolun ta kendisidir.

Dosya BICIMI degismedi (`key` hala tam pencere uzunlugunda saklanir, ~40 MB) —
`load_key` uyumlulugu boyle korunuyor. Kompakt izgara bicimi (~10 KB) mumkun
ama olcum zincirini kirardi, yapilmadi.

### Zincir

1. **Hucre kimligi** — `detect_cell` -> PCI, `u_p`, `df_hat`, `b0`;
   `ssb_pbch_check` -> `i_SSB`.
2. **RIJIT kafes** (`_recon_lattice`) — sembol basina serbest ince ayar
   YAPILMAZ. Cok yol, CP korelasyon tepesini genisletir ve tepe sembolden
   sembole oynar (olculdu: -2..+5 ornek); `d` ornek kayma izgaraya
   `2*pi*d*k/N_FFT` lineer faz rampasi bindirir, 570 altasiyicida d=5 icin
   4.4 radyan. Bu yuzden sadece IKI serbestlik derecesi aranir: kafesin ortak
   kaymasi `d` ve uzun CP'nin faz konumu `p` (mu=1'de her 14 sembolde bir).
   Butun sembollerin normalize CP korelasyonu TOPLANARAK en iyi `(d,p)` secilir.
3. **Yakalama hizalama** — her yakalamanin PSS satiri 0. yakalamaya oturtulur
   (ortak faz/kazanc). Kanal bilgisi GEREKMEZ.
4. **Sabitlik** — RE basina `gamma = |sum V|^2 / (N * sum |V|^2)`.
5. **Kanal kestirimi** (`_recon_chan_est`) — iki asama:
   - *capa*: SSB'nin TAM BILINEN RE'lerinden (PSS/SSS/PBCH-DMRS) `H` dogrudan.
     Fazi kesin ama sadece 240 altasiyici.
   - *yayma*: icerik QPSK oldugundan `x^4 = -1` sabittir, yani
     `A_k = <V_k,l^4>_l = -H_k^4`. `angle(A_k)` altasiyici ekseninde SARIM
     ACILIP 4'e bolunur, 90 derecelik dal belirsizligi capaya oturtularak
     cozulur. Sarim acmanin gecerlilik siniri `tau < 1/(8*30kHz) = 1250 m`;
     olculen yayilim 270 m, rahat.
   - *duzlestirme*: CIR tabaninda en kucuk kareler (kapi degil LS).
6. **Dilimleme** (`_recon_slice`) — `gamma` ve EVM esigini gecen RE'ler en
   yakin QPSK noktasina yuvarlanir; TAM BILINEN pilotlar dilimlenmez,
   dogrudan yazilir. Hepsi BIRIM GENLIK -> referans spektrumu DUZ olur
   (renkli girisimde beyazlatilmis uyumlu filtre; menzil yan lobu TX guc
   dagilimindan bagimsiz).
7. **Yeniden sentez** (`_recon_synth`) — IFFT + CP, tam pencere uzunlugunda.
   Cikti `key + mask` bicimindedir, `load_key` hicbir degisiklik gormez.

## Sentetik uctan uca dogrulama

PCI 918, gercek PSS/SSS/PBCH-DMRS, CORESET0 benzeri deterministik QPSK blogu,
her yakalamada rastgele PBCH-veri + PDSCH, gercekci CP deseni, kanal = yukarida
OLCULEN cok yol, yakalama basina rastgele faz + gurultu.

```
kafes            : RIJIT, CP deseni DOGRU
kanal kestirimi  : 620 altasiyici (18.60 MHz), capa 155, LS artik %0.0
dilimleme        : 9078 RE (dilim 8824 + pilot 398), medyan EVM 0.000
dilim DOGRULUGU  : 9078/9078, YANLIS 0, fazladan kurgulanan 0

REFERANS NEYE BENZIYOR? (normalize korelasyon)
  v4 yeniden kurgu vs ILETILEN s(t)      1.0000   <- birebir
  v4 yeniden kurgu vs KANALLI s(t)*h(t)  0.9153
  v3 ortalamasi    vs ILETILEN s(t)      0.8600
  v3 ortalamasi    vs KANALLI s(t)*h(t)  0.9396   <- v3 kanali TASIYOR

GOMULU COK YOL (referansin kendi otokorelasyonu)
  v3 ortalamasi      24.4 m:  -8.2   43.9 m: -12.1   78.1 m: -17.9  dB
  v4 yeniden kurgu   24.4 m: -15.1   43.9 m: -20.9   78.1 m: -30.8  dB
  IDEAL s(t) [taban] 24.4 m: -15.1   43.9 m: -20.9   78.1 m: -30.8  dB
```

v4 satiri IDEAL satiriyla BIREBIR ayni: kanal tamamen gitti. Kalan -15.1 dB
artik kanal degil, dikdortgen bandin kendi sinc etegidir.

## ISPAT — iki bagimsiz ogrenme, anahtar degisiyor mu?

`recon_repeat_test.py`. Kanalsiz yeniden kurgunun TANIMLAYICI ozelligi: cikti
ILETILEN sembollerdir ve onlar ayrik bir kumeden (QPSK) gelir, dolayisiyla iki
BAGIMSIZ ogrenme BIREBIR AYNI anahtari vermelidir.

Test SAHTE RADYO katmani takip **gercek `learn_key_recon` / `learn_key`**
fonksiyonlarini uctan uca kosturur (dosyaya yazma dahil):

```
KOSU A : kanal taplari [0, 24.40, 43.91, 60.99, 78.07] m, gurultu tohumu 1, trafik 1
KOSU B : kanal taplari [0, 12.20, 31.70, 55.00, 90.30] m, gurultu tohumu 2, trafik 2
         (kanal, gurultu ve PDSCH trafigi TAMAMEN farkli)
```

Sonuc:

| | A vs B korelasyon | zaman capasi | not |
|---|---|---|---|
| **v4** (demod + dilimleme) | **1.000000** | +0 ornek | mask ve anahtar **BIT DUZEYINDE AYNI**, azami fark `0.000e+00` |
| v3 (IQ ortalamasi) | 0.7399 | **+68 ornek (+165.9 m)** | kanal sizmis, capa bile kaymis |

v4'te `recon_n_re`, `recon_n_sliced`, `recon_n_pilot`, `recon_n_sc`,
`recon_bw_mhz` degerlerinin hepsi iki kosuda ayni cikti. Buna karsilik
dilimleme ONCESI medyan EVM farkliydi (A `1.13e-04`, B `3.69e-04`) — yani
girdiler gercekten farkliydi, ama DILIMLEME farki tam olarak kuantize etti.

v3'te capanin 68 ornek (165.9 m) kaymasi ayrica sunu gosterir: kanal degisince
v3 anahtarinin sadece icerigi degil, MENZIL SIFIR NOKTASI da kayiyor.

### Duyarlilik

| kosul | dolu altasiyici | yanlis dilim | corr |
|---|---|---|---|
| temel | 620 | 0 | 1.0000 |
| gurultu 5x | 620 | 0 | 1.0000 |
| gurultu 10x | 620 | 0 | 1.0000 |
| i_SSB YOK (PBCH-DMRS pilot yok) | 620 | 0 | 1.0000 |
| 8 yakalama | 623 | 0 | 0.9991 |
| 4 yakalama | 1080 | 0 | 0.9411 |

`RECON_OCC_DB` ONCE 10 dB idi; derin sonumlemedeki 23 gercek altasiyiciyi
kesip referansta spektral DELIK aciyordu (corr 0.9824). 15 dB uzerinde hepsi
geri geliyor. Varsayilan **20 dB**: kapinin isi BOS altasiyiciyi elemek, o da
gercekten sifir (-inf dB), dolayisiyla genis kapi guvenli.

4 yakalamada 1168 RE YANLISLIKLA sabit sayilip referansa rastgele veri sizdi
-> alt sinir **8**, 16 alti UYARI.

## CONFIG

```
RECON_SYM_BEFORE = 4      PSS'ten once kac sembol
RECON_SYM_AFTER  = 19     PSS'ten sonra   (toplam 24 sembol ~ 857 us)
RECON_GAMMA_MIN  = 0.55   RE "sabit" sayilma esigi
RECON_EVM_MAX    = 0.40   dilimlemeden once azami EVM
RECON_CP_SEARCH  = 96     kafes ortak kaymasi arama yaricapi [ornek]
RECON_TAU_MAX_M  = 400.0  kanal kestiriminde tutulan azami gecikme [m]
RECON_OCC_DB     = 20.0   altasiyici "dolu" esigi (tepeden)
RECON_MIN_SC     = 64     bu kadar altasiyici dolmazsa iptal
```

CLI: `--recon-gamma G`  `--recon-evm E`  `--recon-syms ONCE SONRA`

## Kullanim

```bash
# YENI yol (kanalsiz). Mevcut dosyanin uzerine YAZMAZ.
python3 v4_1tx_4rx_turkcell.py --learn 120 --learn-out signal_key_v4.npz

# ESKI yol (v3 davranisi), sadece karsilastirmak icin
python3 v4_1tx_4rx_turkcell.py --learn-legacy 120 --learn-out signal_key_v3.npz

# ikisini karsilastir (DONANIM GEREKMEZ)
python3 v4_1tx_4rx_turkcell.py --keydiff signal_key.npz signal_key_v4.npz
```

`--keydiff`'te beklenen: dalga formu koherensi YUKSEK (ayni hucre), ama
**diferansiyel CIR'da v3 anahtarinin gomulu cok yolu gorunur** — 24.4 ve
43.9 m'deki tepeler v4'te olmayacak.

Anahtar dosyasi kaydedilirken `recon=1` ustverisi yazilir; ayrica
`recon_n_re`, `recon_n_sliced`, `recon_n_pilot`, `recon_evm`, `recon_bw_mhz`
alanlari o kurgunun kalitesini tasir.

## Bu NE degistirmez

- **Menzil cozunurlugu.** Bant hala ~17 MHz (hangi RE'lerin sabit oldugunu
  bulmak bandi genisletmez) -> ~8.1 m. 1.5 m icin PDSCH'in de cozulup yeniden
  kurgulanmasi gerekir (PDCCH kor cozumu + C-RNTI tespiti; srsRAN sinifi is).
- **Acisal cozunurluk.** 4 eleman x 4 cm = 12 cm aciklik -> ~36 derece huzme,
  50 m'de capraz cozunurluk ~31 m. ASIL darbogaz budur ve bu calisma ona
  dokunmaz.

---

# GUNCELLEME 2026-08-19 — SSB BULUNDU, TEKRARLANABILIRLIK COZULDU

## Kok sorun: LO yanlis frekanstaydi

Telefonun ServiceMode ciktisi (NR-ARFCN 632640, PCI 168, SSB Index 1):

```
F = 3000 MHz + 15 kHz x (632640 - 600000) = 3489.600 MHz
CHBW 100 -> tasiyici 3439.6 .. 3539.6 MHz
```

`CENTER_FREQ` 3530 MHz idi — tasiyicinin UST KENARI, +40.4 MHz kayma. Bant
siniri (+-50 MHz) tasiyicinin alt 40 MHz'ini tamamen disarida birakiyordu.
Butun olcumler tasiyicinin bir kenar diliminden yapilmis.

| | LO 3530 (yanlis) | LO 3489.6 (dogru) |
|---|---|---|
| deterministik bant | 17.5 MHz | **37.0 MHz** |
| menzil cozunurlugu | 8.6 m | **4.05 m** |
| tekrarlanabilirlik (40 yak.) | 0.9316 | **0.9962** |
| tekrarlanabilirlik (120 yak.) | — | **0.9987** |

v4'un varsayilani 3489.6 MHz'e alindi. v3 3530'da BIRAKILDI (dokunulmadi).

## `--ssbscan` — hucreyi ZAMAN DOMENINDE bul

Onceki hucre aramalarinin hepsi frekans domenindeydi ve kendi kurdugumuz
sembol kafesine oturuyordu; kafes birkac ornek kaysa PSS yok oluyordu.
40 ms'in tamami (11.4M hipotez) tarandi ve hicbir sey bulunamadi.

Yeni tarayici kafese HIC bakmaz — gercek alicilarin ilk kilitlenmede
yaptigini yapar: PSS'in zaman domeni dalga formuyla kaydirmali korelasyon,
20 ms periyoda katlama. Tek LO butun bandi kapsar, GSCN'lere dijital inilir
(retune yok), 16x desimasyon banttaki guclu yayiciyi isleme sokmaz.

Hassasiyet (sentetik): **-20 dB SNR'da bile dogru bulur**. Eski yontem
-10 dB'de cokuyordu -> 30+ dB fark.

Saha (3460-3580, 83 GSCN):

```
GSCN 340  3489.60 MHz  oran 8.06e6  tepe/medyan 73.1   <- secildi
GSCN 326  3469.44 MHz  oran 7.66e6  tepe/medyan 69.6   <- ikinci hucre
digerleri <= 8e5
PSS N_ID_2=0 0.9993 | SSS N_ID_1=56 0.9993 -> PCI 168 | i_SSB=1 0.9988
```

Telefonla (PCI 168, SSB Index 1, ARFCN 632640) **ucu de birebir**.

## Iki anahtar secenegi

**`--learn --synth`** — anahtari OLCME, PCI'dan URET. PSS/SSS/PBCH-DMRS
PCI'nin deterministik fonksiyonudur; uretince kanal, gurultu, dilimleme ve
dal belirsizligi topyekun ortadan kalkar.

```
iki bagimsiz kosu: mask ayni, anahtar BIT DUZEYINDE ayni,
azami fark 0.000e+00, korelasyon 1.000000
bedeli: bant 5.77 MHz -> menzil 26 m
```

**`--learn` (yumusak mod, dogru LO)** — olculmus, genis bantli.

```
120 yakalama: korelasyon 0.9987, bant 36.9 MHz -> menzil 4.07 m
```

Radar icin ikincisi acik ara ustun; birincisi mutlak tekrarlanabilirlik
gerektiginde ya da referans dogrulamasi icin.

## Yol boyunca elenen hipotezler (hepsi olculdu)

| hipotez | olcum | sonuc |
|---|---|---|
| anahtar periyodik degisiyor | 180 ms boyunca occasion korelasyonu | 0.997-0.999, cevrim YOK |
| zamanlama suruklenmesi | alt-ornek gecikme vs yakalama no | 40 s'de +0.00 ornek |
| FFT penceresi CP icinde yanlis | ofset taramasi | en iyi +8 ornek, %10 |
| EVM'in kaynagi faz | faz/genlik ayrisimi | GENLIK (faz 0.082, toplam 0.635) |
| SSB baska rasterde/SCS'te | 15+30 kHz x +-15 kHz tarama | duz, sebep degil |
| ortalama SSB'yi olduruyor | tek yakalama araması | ayni |
| spektral cevrilme/eslenik | 4 konvansiyon | hepsi ayni |

Gercek sebep bunlarin hicbiri degildi: **LO yanlis frekanstaydi ve arama
frekans domenindeydi.**
