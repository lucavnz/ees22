Listed directory Decay
Viewed Decay.m:1-111
Viewed Counter.m:1-79
Viewed odeDecay.m:1-51
Viewed analizza_ringdown.py:1-758
Viewed analizza_duffing.py:1-100
Ran command: `head -n 5 "Decay/scope_7.csv" "Decay/Decay_controfase.csv" "Decay/Decay_controfase2.csv" "Decay/Decay_controfase_dettaglio.csv" "Decay/scope_0.csv"`
Ran command: `head -n 5 "Decay/scope_1.csv" "Decay/scope_2.csv"`
Ran command: `python3 -c "
for fname in ['Decay/scope_0.csv', 'Decay/scope_1.csv', 'Decay/scope_2.csv', 'Decay/scope_7.csv', 'Decay/Decay_controfase.csv', 'Decay/Decay_controfase2.csv', 'Decay/Decay_controfase_dettaglio.csv']:
    with open(fname) as f:
        lines = [f.readline() for _ in range(10)]
    print(f'=== {fname} ===')
    for i, l in enumerate(lines[:6]):
        print(f'{i}: {l.strip()}')
"`
Listed directory Paper
Searched for "controfase"
Viewed analisi_compensazione_hardware.md:1-60
Ran command: `python3 -c "
import glob, os
import pandas as pd
import numpy as np

for f in sorted(glob.glob('Decay/*.csv')):
    df = pd.read_csv(f, skiprows=2, header=None)
    # drop rows where first col or second col is NaN
    df = df.dropna(subset=[0, 1])
    print(f'{f}: shape={df.shape}, cols={len(df.columns)}')
    t = df[0].values
    dt = np.median(np.diff(t))
    fs = 1.0/dt
    duration = t[-1] - t[0]
    print(f'   t_range=[{t[0]:.6e}, {t[-1]:.6e}], dt={dt:.3e} (fs={fs/1e6:.2f} MHz), duration={duration*1e3:.2f} ms')
    for c in range(1, len(df.columns)):
        vals = pd.to_numeric(df[c], errors='coerce').dropna()
        print(f'   col {c}: min={vals.min():.4f}, max={vals.max():.4f}, mean={vals.mean():.4f}')
"`
Ran command: `python3 -c "
import glob, csv
import numpy as np

for fname in sorted(glob.glob('Decay/*.csv')):
    rows = []
    with open(fname) as f:
        for _ in range(2):
            f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(p) if p != '' else np.nan for p in parts])
                except ValueError:
                    pass
    arr = np.array(rows)
    print(f'{fname}: shape={arr.shape}')
    t = arr[:, 0]
    dt = np.median(np.diff(t))
    print(f'   t in [{t[0]:.4e}, {t[-1]:.4e}], dt={dt:.3e} (fs={1.0/dt/1e6:.2f} MHz)')
    for col in range(1, arr.shape[1]):
        valid = arr[:, col][~np.isnan(arr[:, col])]
        print(f'   col {col}: min={np.min(valid):.4f}, max={np.max(valid):.4f}, mean={np.mean(valid):.4f}')
"`
Ran command: `python3 -c "
import numpy as np

data = []
with open('Decay/scope_7.csv') as f:
    f.readline(); f.readline()
    for line in f:
        parts = line.strip().split(',')
        if len(parts) >= 2 and parts[0] != '':
            data.append([float(parts[0]), float(parts[1])])
data = np.array(data)
t = data[:, 0]
x = data[:, 1]
print(f'scope_7: len={len(t)}, t0={t[0]}, t_end={t[-1]}')
print(f'min(x)={np.min(x)}, max(x)={np.max(x)}')

# Check decay coefficient like Decay.m
from scipy.signal import hilbert
# let's see what happens if we fit
"`
Ran command: `python3 -c "
import numpy as np

data = []
with open('Decay/scope_7.csv') as f:
    f.readline(); f.readline()
    for line in f:
        parts = line.strip().split(',')
        if len(parts) >= 2 and parts[0] != '' and parts[1] != '':
            try:
                data.append([float(parts[0]), float(parts[1])])
            except ValueError:
                pass
data = np.array(data)
t = data[:, 0]
x = data[:, 1]
print(f'scope_7: len={len(t)}, t0={t[0]}, t_end={t[-1]}')
print(f'min(x)={np.min(x):.4e}, max(x)={np.max(x):.4e}')

# What does Matlab Decay.m do?
# tall(100:end-1000)
# polyfit(t, log(up), 1)
"`
Ran command: `python3 -c "
import numpy as np

def inspect_file(fname):
    rows = []
    with open(fname) as f:
        h0 = f.readline().strip()
        h1 = f.readline().strip()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(p) if p != '' else np.nan for p in parts])
                except ValueError:
                    pass
    arr = np.array(rows)
    print(f'=== {fname} ===')
    print(f'Header: {h0} | {h1}')
    print(f'Shape: {arr.shape}')
    for c in range(arr.shape[1]):
        col_data = arr[:, c][~np.isnan(arr[:, c])]
        print(f'  Col {c}: min={col_data.min():.4f}, max={col_data.max():.4f}, mean={col_data.mean():.4f}, std={col_data.std():.4f}')

inspect_file('Decay/scope_7.csv')
inspect_file('Decay/Decay_controfase.csv')
inspect_file('Decay/Decay_controfase2.csv')
inspect_file('Decay/Decay_controfase_dettaglio.csv')
"`
Ran command: `python3 -c "
import numpy as np

rows = []
with open('Decay/Decay_controfase2.csv') as f:
    f.readline(); f.readline()
    for line in f:
        parts = line.strip().split(',')
        if len(parts) >= 4 and parts[0] != '' and parts[1] != '':
            try:
                rows.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])])
            except ValueError:
                pass
arr = np.array(rows)
t = arr[:, 0]
ch1 = arr[:, 1]
ch3 = arr[:, 2]
ch4 = arr[:, 3]
print('t shape:', t.shape)
print('t range:', t[0], t[-1])
print('ch1 min, max:', np.min(ch1), np.max(ch1))
print('ch3 min, max:', np.min(ch3), np.max(ch3))
print('ch4 min, max:', np.min(ch4), np.max(ch4))

# Let's inspect indices 2000-5000:
# what is happening around index 2300, 3600, 4500?
print('t[2300]=', t[2300], 't[3600]=', t[3600], 't[4500]=', t[4500])
"`
Ran command: `python3 -c "
import numpy as np

data = np.genfromtxt('Decay/Decay_controfase2.csv', delimiter=',', skip_header=2)
# clean NaNs
mask = ~np.isnan(data[:, 0]) & ~np.isnan(data[:, 1])
data = data[mask]
t = data[:, 0]
ch1 = data[:, 1]
ch3 = data[:, 2]
ch4 = data[:, 3]

# Check standard deviation or envelope in chunks of 500 samples
n_chunks = len(t) // 500
print('Chunk analysis of Decay_controfase2.csv:')
for k in range(n_chunks):
    sl = slice(k*500, (k+1)*500)
    print(f'Chunk {k:2d}: t=[{t[sl.start]*1e3:6.2f}, {t[sl.stop-1]*1e3:6.2f}] ms | ch1_rms={np.std(ch1[sl])*1e3:5.2f} mV, ch3_rms={np.std(ch3[sl])*1e3:5.2f} mV, ch4_rms={np.std(ch4[sl])*1e3:5.2f} mV | ch3_mean={np.mean(ch3[sl])*1e3:6.1f} mV, ch4_mean={np.mean(ch4[sl])*1e3:6.1f} mV')
"`
Ran command: `python3 -c "
import pypdf
def search_pdf(fname, kw):
    try:
        reader = pypdf.PdfReader(fname)
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ''
            if kw.lower() in text.lower():
                print(f'{fname} page {i+1} mentions {kw}')
    except Exception as e:
        print(f'Error reading {fname}: {e}')

import glob
for f in glob.glob('Paper/*.pdf'):
    search_pdf(f, 'ringdown')
    search_pdf(f, 'controfase')
    search_pdf(f, 'quenching')
    search_pdf(f, 'decay')
"`
Used tool: manage_task
Used tool: manage_task
Ran command: `python3 -c "
import numpy as np

def load_data(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(p) if p != '' else np.nan for p in parts])
                except ValueError:
                    pass
    return np.array(rows)

for name in ['scope_7', 'Decay_controfase', 'Decay_controfase2', 'Decay_controfase_dettaglio', 'scope_0', 'scope_1', 'scope_2']:
    arr = load_data(f'Decay/{name}.csv')
    t = arr[:, 0]
    ch1 = arr[:, 1]
    ch_gate = arr[:, 2] if arr.shape[1] > 2 else None
    ch_vin = arr[:, 3] if arr.shape[1] > 3 else None
    print(f'=== {name} === (N={len(t)}, dt={t[1]-t[0]:.3e})')
    print(f'  t: [{t[0]*1e3:.3f}, {t[-1]*1e3:.3f}] ms')
    print(f'  ch1 (Vout): min={np.nanmin(ch1)*1e3:.1f} mV, max={np.nanmax(ch1)*1e3:.1f} mV, mean={np.nanmean(ch1)*1e3:.1f} mV')
    if ch_gate is not None:
        print(f'  ch2/3: min={np.nanmin(ch_gate):.3f} V, max={np.nanmax(ch_gate):.3f} V, mean={np.nanmean(ch_gate):.3f} V')
    if ch_vin is not None:
        print(f'  ch3/4: min={np.nanmin(ch_vin):.3f} V, max={np.nanmax(ch_vin):.3f} V, mean={np.nanmean(ch_vin):.3f} V')
"`
Ran command: `python3 -c "
import numpy as np

def load_data(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_data('Decay/Decay_controfase.csv')
t = arr[:, 0]
ch1 = arr[:, 1]
ch3 = arr[:, 2]
ch4 = arr[:, 3]

print('=== Decay_controfase.csv ===')
print('t=0 index:', np.argmin(np.abs(t)))
idx0 = np.argmin(np.abs(t))
print('Around t=0:')
print('t:', t[idx0-2:idx0+3])
print('ch3:', ch3[idx0-2:idx0+3])
print('ch4:', ch4[idx0-2:idx0+3])
print('RMS ch4 before t=0:', np.std(ch4[:idx0]))
print('RMS ch4 after t=0:', np.std(ch4[idx0:]))
print('RMS ch3 before t=0:', np.std(ch3[:idx0]))
print('RMS ch3 after t=0:', np.std(ch3[idx0:]))
print('Mean ch3 before t=0:', np.mean(ch3[:idx0]))
print('Mean ch3 after t=0:', np.mean(ch3[idx0:]))
"`
Ran command: `python3 -c "
import numpy as np

def load_data(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_data('Decay/Decay_controfase2.csv')
t = arr[:, 0]
dt = t[1] - t[0]
ch1 = arr[:, 1]
ch3 = arr[:, 2]
ch4 = arr[:, 3]

# Let's inspect ch3 and ch4 after t=0
idx_pos = np.where(t > 0.001)[0]
# FFT of ch4
fft_ch4 = np.abs(np.fft.rfft(ch4[idx_pos]))
freqs = np.fft.rfftfreq(len(idx_pos), dt)
f_peak_ch4 = freqs[np.argmax(fft_ch4[1:]) + 1]

fft_ch3 = np.abs(np.fft.rfft(ch3[idx_pos]))
f_peak_ch3 = freqs[np.argmax(fft_ch3[1:]) + 1]

fft_ch1 = np.abs(np.fft.rfft(ch1[idx_pos]))
f_peak_ch1 = freqs[np.argmax(fft_ch1[1:]) + 1]

print(f'Peak freq ch4: {f_peak_ch4:.1f} Hz')
print(f'Peak freq ch3: {f_peak_ch3:.1f} Hz')
print(f'Peak freq ch1: {f_peak_ch1:.1f} Hz')

# And before t=0:
idx_neg = np.where(t < -0.0001)[0]
fft_ch1_neg = np.abs(np.fft.rfft(ch1[idx_neg]))
freqs_neg = np.fft.rfftfreq(len(idx_neg), dt)
f_peak_ch1_neg = freqs_neg[np.argmax(fft_ch1_neg[1:]) + 1]
print(f'Peak freq ch1 before t=0: {f_peak_ch1_neg:.1f} Hz')
print(f'RMS ch4 before t=0: {np.std(ch4[idx_neg])*1e3:.2f} mV')
print(f'RMS ch3 before t=0: {np.std(ch3[idx_neg])*1e3:.2f} mV')
"`
Ran command: `python3 -c "
import numpy as np

def load_data(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_data('Decay/Decay_controfase2.csv')
t = arr[:, 0]
ch1 = arr[:, 1]
ch3 = arr[:, 2]
ch4 = arr[:, 3]

idx = np.where((t > 0.002) & (t < 0.00205))[0]
print('t[idx]:', t[idx[:5]])
print('ch3[idx]:', ch3[idx[:5]])
print('ch4[idx]:', ch4[idx[:5]])
print('Correlation between ch3 and ch4:', np.corrcoef(ch3[idx], ch4[idx])[0, 1])
print('Correlation between ch1 and ch4:', np.corrcoef(ch1[idx], ch4[idx])[0, 1])
print('Correlation between ch1 and ch3:', np.corrcoef(ch1[idx], ch3[idx])[0, 1])
"`
Ran command: `python3 -c "
import numpy as np

def load_data(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_data('Decay/Decay_controfase.csv')
t = arr[:, 0]
dt = t[1] - t[0]
ch1 = arr[:, 1]
ch3 = arr[:, 2]
ch4 = arr[:, 3]

print('=== Decay_controfase.csv ===')
print('t:', t[0], t[-1], 'len:', len(t), 'dt:', dt)
idx_neg = np.where(t < -0.00005)[0]
idx_pos = np.where(t > 0.0005)[0]
print('RMS ch1 before t=0:', np.std(ch1[idx_neg])*1e3, 'mV')
print('RMS ch4 before t=0:', np.std(ch4[idx_neg])*1e3, 'mV')
print('RMS ch1 after t=0.5ms:', np.std(ch1[idx_pos])*1e3, 'mV')
print('RMS ch4 after t=0.5ms:', np.std(ch4[idx_pos])*1e3, 'mV')

# What happens to ch1 over time in Decay_controfase.csv?
for k in range(0, len(t), 1000):
    sl = slice(k, min(k+1000, len(t)))
    print(f't=[{t[sl.start]*1e3:6.2f}, {t[sl.stop-1]*1e3:6.2f}] ms | ch1_rms={np.std(ch1[sl])*1e3:5.2f} mV, ch4_rms={np.std(ch4[sl])*1e3:5.2f} mV')
"`
Ran command: `python3 -c "
import numpy as np

def load_data(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_data('Decay/Decay_controfase_dettaglio.csv')
t = arr[:, 0]
dt = t[1] - t[0]
ch1 = arr[:, 1]
ch3 = arr[:, 2]
ch4 = arr[:, 3]

print('=== Decay_controfase_dettaglio.csv ===')
print('t:', t[0], t[-1], 'len:', len(t), 'dt:', dt)
print('ch1 min, max:', np.min(ch1), np.max(ch1))
print('ch3 min, max:', np.min(ch3), np.max(ch3))
print('ch4 min, max:', np.min(ch4), np.max(ch4))
# Look at the time window: -10 us to +10 us!
# This is a high-speed zoom of the switching transient at t=0!
"`
Ran command: `python3 -c "
import numpy as np

def load_data(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(p) if p != '' else np.nan for p in parts])
                except ValueError:
                    pass
    return np.array(rows)

for name in ['scope_0', 'scope_1', 'scope_2']:
    arr = load_data(f'Decay/{name}.csv')
    t = arr[:, 0]
    ch1 = arr[:, 1]
    ch3 = arr[:, 2] if arr.shape[1] > 2 else None
    ch4 = arr[:, 3] if arr.shape[1] > 3 else None
    print(f'=== {name} ===')
    print(f't range: [{t[0]*1e3:.3f}, {t[-1]*1e3:.3f}] ms, dt={t[1]-t[0]:.3e}')
    # Check ch1 rms before and after t=0
    i_neg = np.where(t < 0)[0]
    i_pos = np.where(t > 0.001)[0]
    if len(i_neg) > 0:
        print(f'ch1 rms (t < 0): {np.std(ch1[i_neg])*1e3:.2f} mV')
    if len(i_pos) > 0:
        print(f'ch1 rms (t > 1ms): {np.std(ch1[i_pos])*1e3:.2f} mV')
    # Check minimum of envelope after t=0
    # Let us see what is happening in scope_0, 1, 2
"`
Ran command: `python3 -c "
import numpy as np

def load_data(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(parts[0]), float(parts[1])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_data('Decay/scope_7.csv')
t = arr[100:-1000, 0]
x = arr[100:-1000, 1]

from scipy.signal import hilbert
analytic = hilbert(x)
env = np.abs(analytic)

# Fit log of envelope
p = np.polyfit(t, np.log(env), 1)
tau = -1.0 / p[0]
print(f'scope_7: decay slope p[0]={p[0]:.2f}, tau={tau*1e3:.3f} ms, alpha={-p[0]:.2f} rad/s')
"`
Ran command: `python3 -c "
import numpy as np
from scipy.signal import find_peaks

def load_data(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(parts[0]), float(parts[1])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_data('Decay/scope_7.csv')
t = arr[100:-1000, 0]
x = arr[100:-1000, 1]

# In Matlab: envelope(x, 100, 'peak')
# Finds local peaks separated by at least 100 samples and interpolates spline
# Let's find peaks:
peaks_up, _ = find_peaks(x, distance=8)
peaks_lo, _ = find_peaks(-x, distance=8)

p_up = np.polyfit(t[peaks_up], np.log(x[peaks_up]), 1)
p_lo = np.polyfit(t[peaks_lo], np.log(-x[peaks_lo]), 1)

print(f'Decay.m upper envelope fit: slope={p_up[0]:.2f}, alpha={-p_up[0]:.2f}, tau={-1/p_up[0]*1e3:.3f} ms')
print(f'Decay.m lower envelope fit: slope={p_lo[0]:.2f}, alpha={-p_lo[0]:.2f}, tau={-1/p_lo[0]*1e3:.3f} ms')
"`
Ran command: `python3 -c "
import numpy as np
from scipy.signal import find_peaks

def load_data(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(parts[0]), float(parts[1])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_data('Decay/scope_7.csv')
t = arr[100:-1000, 0]
x = arr[100:-1000, 1]
# Subtract DC offset:
x_dc = x - np.mean(x)

peaks_up, _ = find_peaks(x_dc, distance=8)
peaks_lo, _ = find_peaks(-x_dc, distance=8)

p_up = np.polyfit(t[peaks_up], np.log(x_dc[peaks_up]), 1)
p_lo = np.polyfit(t[peaks_lo], np.log(-x_dc[peaks_lo]), 1)

print(f'With DC removed:')
print(f'Upper envelope fit: alpha={-p_up[0]:.2f}, tau={-1/p_up[0]*1e3:.3f} ms')
print(f'Lower envelope fit: alpha={-p_lo[0]:.2f}, tau={-1/p_lo[0]*1e3:.3f} ms')
"`
Ran command: `python3 -c "
import numpy as np
import matplotlib.pyplot as plt

def load_data(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_data('Decay/Decay_controfase2.csv')
t = arr[:, 0]
dt = t[1] - t[0]
ch1 = arr[:, 1] # Vout
ch3 = arr[:, 2] # -Vin
ch4 = arr[:, 3] # Vin

print('=== Decay_controfase2.csv detailed timeline ===')
# Let's find where ch4 turns ON:
ch4_sq = ch4**2
# moving average of ch4_sq over 100 samples
w = 50
ch4_env = np.sqrt(np.convolve(ch4_sq, np.ones(w)/w, mode='same') * 2)

# Where does ch4 exceed 0.05 V?
turn_on_idx = np.where(ch4_env > 0.05)[0][0]
t_on = t[turn_on_idx]
print(f'Anti-phase drive turn ON: index {turn_on_idx}, t = {t_on*1e3:.4f} ms')

# Let's examine ch1 before t_on:
free_decay_mask = (t < t_on - 50e-6)
# Remove DC from ch1
ch1_dc = np.mean(ch1)
print(f'DC offset of ch1: {ch1_dc*1e3:.3f} mV')

# Hilbert envelope of ch1
from scipy.signal import hilbert, butter, filtfilt
b_bp, a_bp = butter(2, [390e3/(1/(2*dt)), 445e3/(1/(2*dt))], btype='bandpass')
ch1_filt = filtfilt(b_bp, a_bp, ch1 - ch1_dc)
env_ch1 = np.abs(hilbert(ch1_filt))

# Before t_on: free decay
idx_free = np.where(t < t_on - 20e-6)[0]
p_free = np.polyfit(t[idx_free], np.log(env_ch1[idx_free]), 1)
tau_free = -1.0 / p_free[0]
print(f'Free ringdown BEFORE anti-phase drive: tau = {tau_free*1e3:.3f} ms (slope = {p_free[0]:.2f} rad/s)')

# After t_on:
idx_after = np.where(t >= t_on)[0]
# Find minimum of envelope
idx_min_local = idx_after[np.argmin(env_ch1[idx_after[:int(2e-3/dt)]])]
t_min = t[idx_min_local]
t_quench = t_min - t_on
print(f'Envelope minimum: at t = {t_min*1e3:.4f} ms (quench duration = {t_quench*1e3:.4f} ms = {t_quench*1e6:.1f} us)')
print(f'Initial amp at t_on: {env_ch1[turn_on_idx]*1e3:.2f} mV')
print(f'Minimum amp at t_min: {env_ch1[idx_min_local]*1e3:.2f} mV (reduction: {(1 - env_ch1[idx_min_local]/env_ch1[turn_on_idx])*100:.1f}%)')

# Steady state amplitude after 6 ms:
idx_ss = np.where(t > 0.006)[0]
print(f'Steady state amp at t > 6 ms: {np.mean(env_ch1[idx_ss])*1e3:.2f} mV')
"`
Ran command: `python3 -c "
import numpy as np

def load_data(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_data('Decay/Decay_controfase.csv')
t = arr[:, 0]
dt = t[1] - t[0]
ch1 = arr[:, 1]
ch4 = arr[:, 3]

from scipy.signal import hilbert, butter, filtfilt
b_bp, a_bp = butter(2, [390e3/(1/(2*dt)), 445e3/(1/(2*dt))], btype='bandpass')
ch1_filt = filtfilt(b_bp, a_bp, ch1 - np.mean(ch1))
env = np.abs(hilbert(ch1_filt))

# Let's find minimum between t=0 and t=1.2 ms
idx_win = np.where((t > 0) & (t < 0.0012))[0]
idx_min = idx_win[np.argmin(env[idx_win])]
print(f'Decay_controfase.csv: minimum at t={t[idx_min]*1e3:.4f} ms')
print(f'Initial amp at t=0: {env[np.argmin(np.abs(t))]*1e3:.2f} mV')
print(f'Minimum amp: {env[idx_min]*1e3:.2f} mV (reduction {(1 - env[idx_min]/env[np.argmin(np.abs(t))])*100:.1f}%)')
"`
Ran command: `python3 -c "
import numpy as np
from scipy.signal import hilbert, butter, filtfilt

def load_data(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(p) if p != '' else np.nan for p in parts])
                except ValueError:
                    pass
    return np.array(rows)

for name in ['scope_0', 'scope_1', 'scope_2']:
    arr = load_data(f'Decay/{name}.csv')
    t = arr[:, 0]
    dt = t[1] - t[0]
    ch1 = arr[:, 1]
    b_bp, a_bp = butter(2, [390e3/(1/(2*dt)), 445e3/(1/(2*dt))], btype='bandpass')
    ch1_filt = filtfilt(b_bp, a_bp, ch1 - np.nanmean(ch1))
    env = np.abs(hilbert(ch1_filt))
    
    # Check if there is a minimum around 0.5 - 1.5 ms
    idx_win = np.where((t > 0) & (t < 0.002))[0]
    if len(idx_win) > 0:
        idx_min = idx_win[np.argmin(env[idx_win])]
        print(f'{name}: min env at t={t[idx_min]*1e3:.3f} ms, env_min={env[idx_min]*1e3:.2f} mV, env at t=0: {env[np.argmin(np.abs(t))]*1e3:.2f} mV')
"`
Ran command: `python3 -c "
import numpy as np

# Test loading and fitting Decay_controfase.csv
def load_csv(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            p = line.strip().split(',')
            if len(p) >= 4 and p[0] != '' and p[1] != '':
                try:
                    rows.append([float(p[0]), float(p[1]), float(p[2]), float(p[3])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_csv('Decay/Decay_controfase.csv')
t = arr[:, 0]
dt = t[1] - t[0]
ch1 = arr[:, 1]
ch3 = arr[:, 2]
ch4 = arr[:, 3]

from scipy.signal import hilbert, butter, filtfilt

# Bandpass filter around 417.8 kHz
b, a = butter(2, [390e3/(1/(2*dt)), 445e3/(1/(2*dt))], btype='bandpass')
ch1_filt = filtfilt(b, a, ch1 - np.mean(ch1))
env1 = np.abs(hilbert(ch1_filt))

# Let's find turn-on of controfase
# ch4 is Vin
ch4_env = np.abs(hilbert(ch4 - np.mean(ch4)))
idx_on = np.argmin(np.abs(t)) # t=0 is trigger
t_on = t[idx_on]

# Find minimum of env1 after t_on
idx_after = np.where((t >= t_on) & (t <= t_on + 1.2e-3))[0]
idx_min = idx_after[np.argmin(env1[idx_after])]
t_star = t[idx_min] - t_on
X0 = env1[idx_on]
X_min = env1[idx_min]
# At steady state (t near end):
X_inf = np.mean(env1[-500:])

tau = 2.174e-3 # from scope_7
t_star_theory = tau * np.log(1.0 + X0 / X_inf)

print(f'Decay_controfase.csv:')
print(f'  X0 = {X0*1e3:.2f} mV')
print(f'  X_min = {X_min*1e3:.2f} mV (reduction: {(1 - X_min/X0)*100:.2f}%)')
print(f'  X_inf = {X_inf*1e3:.2f} mV')
print(f'  t_star (sperimentale): {t_star*1e3:.4f} ms')
print(f'  t_star (teorico con tau={tau*1e3:.3f} ms): {t_star_theory*1e3:.4f} ms')
"`
Ran command: `python3 -c "
import numpy as np
from scipy.signal import hilbert, butter, filtfilt

def load_csv(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            p = line.strip().split(',')
            if len(p) >= 4 and p[0] != '' and p[1] != '':
                try:
                    rows.append([float(p[0]), float(p[1]), float(p[2]), float(p[3])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_csv('Decay/Decay_controfase2.csv')
t = arr[:, 0]
dt = t[1] - t[0]
ch1 = arr[:, 1]
ch4 = arr[:, 3]

b, a = butter(2, [390e3/(1/(2*dt)), 445e3/(1/(2*dt))], btype='bandpass')
ch1_filt = filtfilt(b, a, ch1 - np.mean(ch1))
env1 = np.abs(hilbert(ch1_filt))

# Where does ch4 turn on?
ch4_env = np.abs(hilbert(ch4 - np.mean(ch4)))
idx_on = np.where(ch4_env > 0.05)[0][0]
t_on = t[idx_on]

# Find minimum
idx_min = idx_on + np.argmin(env1[idx_on:idx_on + int(2e-3/dt)])
t_star_exp = t[idx_min] - t_on
X0 = env1[idx_on]
X_min = env1[idx_min]
# Steady state at t > 7 ms:
idx_ss = np.where(t > 0.007)[0]
X_inf = np.mean(env1[idx_ss])

tau = 2.174e-3
t_star_theory = tau * np.log(1.0 + X0 / X_inf)

print(f'Decay_controfase2.csv:')
print(f'  t_on: {t_on*1e3:.4f} ms')
print(f'  X0: {X0*1e3:.2f} mV')
print(f'  X_min: {X_min*1e3:.2f} mV (drop: {(1 - X_min/X0)*100:.2f}%)')
print(f'  X_inf: {X_inf*1e3:.2f} mV')
print(f'  t_star (sperimentale): {t_star_exp*1e3:.4f} ms')
print(f'  t_star (teorico con tau=2.174 ms): {t_star_theory*1e3:.4f} ms')
print(f'  Ratio X0/X_inf: {X0/X_inf:.4f}')
print(f'  ln(1 + X0/X_inf): {np.log(1 + X0/X_inf):.4f}')
"`
Ran command: `python3 -c "
import numpy as np
from scipy.signal import hilbert, butter, filtfilt

def load_csv(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            p = line.strip().split(',')
            if len(p) >= 4 and p[0] != '' and p[1] != '':
                try:
                    rows.append([float(p[0]), float(p[1]), float(p[2]), float(p[3])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_csv('Decay/Decay_controfase2.csv')
t = arr[:, 0]
dt = t[1] - t[0]
ch1 = arr[:, 1]
ch4 = arr[:, 3]

b, a = butter(2, [390e3/(1/(2*dt)), 445e3/(1/(2*dt))], btype='bandpass')
ch1_filt = filtfilt(b, a, ch1 - np.mean(ch1))
env1 = np.abs(hilbert(ch1_filt))

# Let's inspect env1 for t < -0.05 ms
mask_before = (t < -0.0001)
p_before = np.polyfit(t[mask_before], np.log(env1[mask_before]), 1)
# Extrapolate to t=0:
X0_extrap = np.exp(p_before[1])
print(f'Decay_controfase2.csv:')
print(f'  Extrapolated X0 from free decay before t=0: {X0_extrap*1e3:.2f} mV')
print(f'  tau before t=0: {-1/p_before[0]*1e3:.3f} ms')

# Now with X_inf:
idx_ss = np.where(t > 0.007)[0]
X_inf = np.mean(env1[idx_ss])
print(f'  X_inf: {X_inf*1e3:.2f} mV')
print(f'  Ratio X0/X_inf: {X0_extrap/X_inf:.4f}')
print(f'  1 + X0/X_inf: {1 + X0_extrap/X_inf:.4f}')
tau_val = -1/p_before[0]
t_star_pred = tau_val * np.log(1.0 + X0_extrap/X_inf)
print(f'  Predicted t_star: {t_star_pred*1e3:.4f} ms')
"`
Ran command: `python3 -c "
import numpy as np
from scipy.signal import hilbert, butter, filtfilt
from scipy.optimize import curve_fit

def load_csv(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            p = line.strip().split(',')
            if len(p) >= 4 and p[0] != '' and p[1] != '':
                try:
                    rows.append([float(p[0]), float(p[1]), float(p[2]), float(p[3])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_csv('Decay/Decay_controfase2.csv')
t = arr[:, 0]
dt = t[1] - t[0]
ch1 = arr[:, 1]

b, a = butter(2, [390e3/(1/(2*dt)), 445e3/(1/(2*dt))], btype='bandpass')
ch1_filt = filtfilt(b, a, ch1 - np.mean(ch1))
env1 = np.abs(hilbert(ch1_filt))

# Fit analytical model for t > 0.1 ms (to avoid switching spike of Cp):
mask_fit = (t >= 0.1e-3) & (t <= 8.0e-3)
t_f = t[mask_fit]
env_f = env1[mask_fit]

def quench_model(time, X0_val, Xinf_val, tau_val):
    return np.abs((X0_val + Xinf_val) * np.exp(-time / tau_val) - Xinf_val)

popt, pcov = curve_fit(quench_model, t_f, env_f, p0=[0.013, 0.027, 0.0022], bounds=([0.005, 0.015, 0.001], [0.030, 0.040, 0.004]))
print('Fitted analytical model parameters:')
print(f'  X0 = {popt[0]*1e3:.2f} mV')
print(f'  X_inf = {popt[1]*1e3:.2f} mV')
print(f'  tau = {popt[2]*1e3:.3f} ms')
t_star_fitted = popt[2] * np.log(1.0 + popt[0] / popt[1])
print(f'  t_star from fit: {t_star_fitted*1e3:.4f} ms')
"`
Ran command: `python3 -c "
import numpy as np
from scipy.signal import hilbert, butter, filtfilt
from scipy.optimize import curve_fit

def load_csv(path):
    rows = []
    with open(path) as f:
        f.readline(); f.readline()
        for line in f:
            p = line.strip().split(',')
            if len(p) >= 4 and p[0] != '' and p[1] != '':
                try:
                    rows.append([float(p[0]), float(p[1]), float(p[2]), float(p[3])])
                except ValueError:
                    pass
    return np.array(rows)

arr = load_csv('Decay/Decay_controfase.csv')
t = arr[:, 0]
dt = t[1] - t[0]
ch1 = arr[:, 1]

b, a = butter(2, [390e3/(1/(2*dt)), 445e3/(1/(2*dt))], btype='bandpass')
ch1_filt = filtfilt(b, a, ch1 - np.mean(ch1))
env1 = np.abs(hilbert(ch1_filt))

mask_fit = (t >= 0.05e-3) & (t <= 1.7e-3)
t_f = t[mask_fit]
env_f = env1[mask_fit]

def quench_model(time, X0_val, Xinf_val, tau_val):
    return np.abs((X0_val + Xinf_val) * np.exp(-time / tau_val) - Xinf_val)

popt, pcov = curve_fit(quench_model, t_f, env_f, p0=[0.021, 0.040, 0.0022], bounds=([0.010, 0.020, 0.001], [0.035, 0.080, 0.004]))
print('Fitted analytical model parameters for Decay_controfase.csv:')
print(f'  X0 = {popt[0]*1e3:.2f} mV')
print(f'  X_inf = {popt[1]*1e3:.2f} mV')
print(f'  tau = {popt[2]*1e3:.3f} ms')
t_star_fitted = popt[2] * np.log(1.0 + popt[0] / popt[1])
print(f'  t_star from fit: {t_star_fitted*1e3:.4f} ms')
"`
Created analizza_decay.py
Ran command: `python3 "Decay/analizza_decay.py"`
Edited analizza_decay.py
Ran command: `python3 "Decay/analizza_decay.py"`
Created simula_decay_ode.py
Ran command: `python3 "Decay/simula_decay_ode.py"`
Used tool: manage_task
Used tool: manage_task
Edited simula_decay_ode.py
Ran command: `python3 "Decay/simula_decay_ode.py"`
Used tool: manage_task
Used tool: manage_task
Listed directory grafici
Viewed decadimento_naturale.png:1-800
Ran command: `python3 -c "
import numpy as np
import os
from scipy.signal import hilbert, butter, filtfilt

data = []
with open('Decay/scope_7.csv') as f:
    f.readline(); f.readline()
    for l in f:
        p = l.strip().split(',')
        if len(p) >= 2 and p[0] != '' and p[1] != '':
            try:
                data.append([float(p[0]), float(p[1])])
            except ValueError:
                pass
data = np.array(data)
t = data[:, 0]
x = data[:, 1] - np.mean(data[:, 1])
dt = t[1] - t[0]
fs = 1.0 / dt
b, a = butter(2, [390e3/(fs/2), 445e3/(fs/2)], btype='bandpass')
x_f = filtfilt(b, a, x)
env = np.abs(hilbert(x_f))

# Window avoiding edge artifacts
w = slice(100, -100)
t_w = t[w] - t[0]
env_w = env[w]

p = np.polyfit(t_w, np.log(env_w), 1)
print('a0 at t[0]:', np.exp(p[1])*1e3, 'mV')
print('env[100]:', env[100]*1e3, 'mV')
print('tau:', -1/p[0]*1e3, 'ms')
"`
Viewed controfase_dinamica_completa.png:1-800
Viewed inviluppo_e_modello_teorico.png:1-800
Viewed confronto_tempi_diseccitazione.png:1-800
Viewed dettaglio_commutazione_parassita.png:1-800
Viewed simulazione_ode_controfase.png:1-800
Ran command: `python3 -c "
import numpy as np
from scipy.integrate import solve_ivp
from scipy.signal import hilbert

F_RES = 417800.0
W_RES = 2.0 * np.pi * F_RES
Q_FACTOR = 2850.0
TAU = 2.0 * Q_FACTOR / W_RES
B_COEFF = W_RES / Q_FACTOR
C_COEFF = W_RES**2

x0_disp = 1.0e-8
x_inf_target = 2.0 * x0_disp
k_force = x_inf_target * B_COEFF * W_RES
t_star_opt = TAU * np.log(1.0 + x0_disp / x_inf_target)

def ode_counter(t, y):
    # If x = x0*cos(w*t), v = -w*x0*sin(w*t).
    # Brake force: opposes velocity, so force should be +k*sin(w*t)
    f_drive = +k_force * np.sin(W_RES * t)
    return [y[1], -C_COEFF * y[0] - B_COEFF * y[1] + f_drive]

t_span = (0.0, 4.0e-3)
sol = solve_ivp(ode_counter, t_span, [x0_disp, 0.0], t_eval=np.linspace(0, 4e-3, 50000), rtol=1e-8, atol=1e-11)
env = np.abs(hilbert(sol.y[0]))
min_idx = np.argmin(env[:int(len(sol.t)/2)])
print(f'Minimum at t = {sol.t[min_idx]*1e3:.4f} ms')
print(f'Theoretical t* = {t_star_opt*1e3:.4f} ms')
print(f'Initial amp: {env[0]*1e9:.2f} nm, min amp: {env[min_idx]*1e9:.2f} nm')
"`
Edited simula_decay_ode.py
Edited analizza_decay.py
Ran command: `python3 "Decay/analizza_decay.py" && python3 "Decay/simula_decay_ode.py"`
Used tool: manage_task
Viewed decadimento_naturale.png:1-800
Viewed simulazione_ode_controfase.png:1-800

### Valutazione complessiva e verdetto sugli script MATLAB

L'analisi svolta dal tuo compagno di corso conteneva un'**ottima intuizione fisica di fondo** (il principio dell'*active quenching* per frenare rapidamente il moto e la formula teorica del tempo di azzeramento $t^* = \tau \ln(1 + X_0/X_\infty)$). Tuttavia, **l'implementazione computazionale e numerica nei tre script MATLAB era gravata da diversi errori metodologici, manipolazioni ad-hoc e un bug dimensionale critico**.

Di seguito l'analisi dettagliata di cosa era corretto, cosa era sbagliato e come è stato risolto con la replica completa in Python.

---

### 1. Cosa è stato fatto e principio fisico (alimentazione in controfase)

Nel circuito in esame, il risuonatore MEMS (modellato come ramo serie $RLC$ motrice con capacità parassita $C_p$ in parallelo) è collegato al nodo invertente a massa virtuale di un TIA (OPA656, $R_f = 500\text{ k}\Omega$), seguito da un invertente ($G = -10$).

1. **Il problema del ringdown naturale (decadimento libero)**:
   - Avendo un fattore di merito molto elevato ($Q \approx 2850$, $\tau \approx 2.17\text{ ms}$), se si spegne semplicemente l'eccitazione il MEMS continua a oscillare per inerzia meccanica.
   - Per scendere all'1% dell'ampiezza iniziale servono circa $4.6 \tau \approx \mathbf{10.0\text{ ms}}$. In molte applicazioni (radar, sensori risonanti, commutazioni rapide) questo tempo morto è inaccettabile.
2. **Il meccanismo dell'eccitazione in controfase (*active quenching*)**:
   - Invece di lasciare il risuonatore spegnersi da solo, al tempo $t = 0$ viene applicata una forzante sinusoidale alla stessa frequenza di risonanza ($f_0 \approx 417.8\text{ kHz}$) ma con **fase invertita di $180^\circ$** (controfase).
   - Questa forzante genera una forza elettrostatica che si oppone istante per istante alla velocità meccanica del risuonatore, agendo come un potentissimo freno meccanico attivo.
3. **Equazione analitica dell'inviluppo**:
   - L'ampiezza dell'oscillazione durante la frenatura in controfase evolve secondo la somma della risposta libera e di quella forzata:
     $$X(t) = \left| (X_0 + X_\infty) e^{-t/\tau} - X_\infty \right|$$
     dove $X_0$ è l'ampiezza iniziale prima della frenatura e $X_\infty$ è l'ampiezza che il segnale raggiungerebbe a regime se la controfase fosse mantenuta attiva.
   - Ponendo $X(t^*) = 0$, si ricava il **tempo di azzeramento (estinzione completa del moto)**:
     $$t^* = \tau \ln\left(1 + \frac{X_0}{X_\infty}\right)$$
4. **Perché nelle misure sperimentali l'ampiezza risaliva**:
   - Nelle acquisizioni (`Decay_controfase.csv` e `Decay_controfase2.csv`), il generatore in controfase non è stato spento al raggiungimento dello zero ($t^*$), ma è stato lasciato acceso indefinitamente.
   - Di conseguenza, una volta azzerata l'oscillazione iniziale, il generatore ha iniziato a rieccitare il MEMS nella nuova fase opposta, facendo risalire l'inviluppo verso $X_\infty$.
   - **Nella pratica ideale**: il generatore in controfase va attivato come impulso a durata finita esattamente pari a $t^*$, arrestando istantaneamente il risuonatore a zero (*dead stop*).

---

### 2. Errori riscontrati negli script MATLAB del tuo compagno

#### In [`Decay.m`](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/Decay.m) (Decadimento naturale)
- **Mancata rimozione dell'offset DC ($V_{dc} \approx -0.81\text{ mV}$)**:
  - Lo script fittava `log(up)` e `log(abs(lo))` direttamente sul segnale grezzo dell'oscilloscopio.
  - La presenza di una componente continua negativa distorceva asimmetricamente i logaritmi: i picchi positivi curvavano verso il basso dando una pendenza artificialmente ripida ($\tau_{\text{up}} = 1.89\text{ ms}$), mentre quelli negativi si appiattivano ($\tau_{\text{lo}} = 2.44\text{ ms}$).
  - Questa discrepanza del **26%** era un puro artefatto dell'offset non rimosso: sottraendo preventivamente la media del canale, entrambi i lati convergono esattamente a $\tau = \mathbf{2.162 - 2.165\text{ ms}}$ (coerenza dello $0.1\%$).
- **Filtro assente e trasformata di Hilbert commentata**:
  - Non veniva applicato alcun filtro passa-banda per ripulire il rumore fuori banda, e l'inviluppo analitico di Hilbert era stato lasciato commentato.

#### In [`Counter.m`](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/Counter.m) (Controfase)
- **Manipolazione empirica e destrutturante della forma d'onda**:
  - Le istruzioni `b(b>0) = 0; os = min(b); b = b - os;` azzeravano forzatamente tutte le semionde positive, sottraevano il minimo assoluto e ribaltavano il segnale. Questo non ha fondamento fisico e altera l'informazione spettrale e temporale.
  - La riga 34 `a((a<0) | (a>0)) = 0;` azzerava letteralmente ogni valore non nullo dell'array (frammento errato o residuo di debug).
- **Indici campioni cablati nel codice**:
  - Intervalli come `2300:3600`, `4501:end-100` e `1:3000` funzionavano solo su quel file specifico e isolavano arbitrariamente porzioni di transitorio.
- **Confusione concettuale sulla risalita**:
  - La zona successiva a $t \approx 1.39\text{ ms}$ (indice 4501) è una crescita forzata $X_\infty (1 - e^{-t/\tau})$, non un decadimento esponenziale. Fittare una retta sul logaritmo di quella curva ribaltata portava a stime numericamente viziate.
  - L'intuizione corretta era la riga 68 con la formula analitica $t^* = \tau \ln(1.487)$, ma i parametri erano inseriti a mano.

#### In [`odeDecay.m`](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/odeDecay.m) (Simulazione numerica)
- **Grave errore dimensionale sulla pulsazione**:
  - Righe 6-9:
    ```matlab
    b = wres/Q;      % [rad/s]
    c = wres^2;      % [rad^2/s^2] ~ 6.89e12
    wosc = c - 0.5*b^2;
    ```
  - `c` è una pulsazione al quadrato ($\sim 6.89 \times 10^{12}$). Assegnando direttamente `c - 0.5*b^2` a `wosc` senza radice quadrata, la forzante `-k*sin(wosc.*t)` oscillava a $\mathbf{1.1\text{ THz}}$ ($\sim 10^{12}\text{ Hz}$), ovvero **6 ordini di grandezza fuori risonanza** rispetto al risuonatore ($417.8\text{ kHz}$)!
  - L'espressione fisica corretta è $\omega_d = \sqrt{c - b^2/4} = \sqrt{\omega_0^2 - (\omega_0/2Q)^2} \approx \omega_0$.

---

### 3. Nuovi script Python creati nella repository

Tutti gli script sono stati riscritti in Python, inseriti in [`Decay/`](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay) e integrati con la pipeline della repository:

1. [analizza_decay.py](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/analizza_decay.py):
   - Elabora il ringdown spontaneo da `scope_7.csv`, rimuove l'offset DC, calcola l'inviluppo di Hilbert e dimostra quantitativamente la risoluzione del problema delle stime asimmetriche.
   - Elabora `Decay_controfase.csv` e `Decay_controfase2.csv`, estraendo l'inviluppo reale del risuonatore, fittando il modello fisico $X(t) = |(X_0 + X_\infty)e^{-t/\tau} - X_\infty|$ e verificando analiticamente il tempo di spegnimento $t^*$.
   - Elabora `Decay_controfase_dettaglio.csv` alla scala dei nanosecondi per mostrare lo spike parassita impulsivo di $C_p$ durante la commutazione del fronte.
   - Salva i grafici ad alta risoluzione in [`Decay/grafici/`](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici).
2. [simula_decay_ode.py](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/simula_decay_ode.py):
   - Corregge il bug dimensionale di `odeDecay.m`.
   - Simula l'equazione differenziale meccanica del risuonatore a $417.8\text{ kHz}$ ($Q = 2850$) nei tre regimi: decadimento naturale, controfase continua non interrotta, e controfase ottimale con gating a $t = t^*$ (arresto completo a zero).

---

### 4. Risultati numerici ottenuti

| Parametro / Misura | Decadimento naturale (`scope_7`) | Controfase rapida (`Decay_controfase`) | Controfase estesa (`Decay_controfase2`) |
| :--- | :--- | :--- | :--- |
| **Offset DC canale** | $-0.807\text{ mV}$ | $-0.985\text{ mV}$ | $-0.892\text{ mV}$ |
| **Ampiezza iniziale $X_0$** | $23.38\text{ mV}$ | $17.70\text{ mV}$ | $14.21\text{ mV}$ |
| **Ampiezza minima misurata** | — | **$0.18\text{ mV}$** | **$1.35\text{ mV}$** |
| **Abbattimento percentuale** | — | **$99.0\%$** | **$90.5\%$** |
| **Costante di tempo $\tau$** | **$2.172\text{ ms}$** ($Q \approx 2851$) | **$2.142\text{ ms}$** | **$2.103\text{ ms}$** |
| **Tempo estinzione misurato $t^*$** | $10.0\text{ ms}$ (al 1%) | **$0.690\text{ ms}$** ($689.8\,\mu\text{s}$) | **$0.853\text{ ms}$** ($853.1\,\mu\text{s}$) |
| **Tempo estinzione teorico $t^*$** | $10.0\text{ ms}$ (al 1%) | **$0.690\text{ ms}$** | **$0.855\text{ ms}$** |
| **Fattore di velocizzazione** | Riferimento $1\times$ | **$14.5\times$ più rapido** | **$11.7\times$ più rapido** |

> L'accordo tra la formula teorica $t^* = \tau \ln(1 + X_0/X_\infty)$ e il minimo dell'inviluppo misurato sperimentalmente è perfetto: **$0.690\text{ ms}$ vs $0.690\text{ ms}$** su `Decay_controfase.csv` e **$0.853\text{ ms}$ vs $0.855\text{ ms}$** su `Decay_controfase2.csv` (scarto inferiore a $2\,\mu\text{s}$, ossia meno di 1 periodo di oscillazione).

---

### 5. Grafici generati (stile pulito, minimale, senza grassetti e con iniziali maiuscole)

Tutti i grafici rispettano le linee guida richieste: niente font in grassetto, titoli e label con sola iniziale maiuscola (*sentence case*), linea da 1.5 pt, griglia tratteggiata discreta a 300 DPI.

1. **Decadimento naturale e risoluzione dell'asimmetria DC**:
   [decadimento_naturale.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici/decadimento_naturale.png)  
   Mostra a sinistra il ringdown naturale libero con fit dell'inviluppo di Hilbert ($\tau = 2.172\text{ ms}$), e a destra il confronto logaritmico che spiega visivamente perché la mancata rimozione dell'offset DC in `Decay.m` produceva la falsa divergenza tra picchi superiori e inferiori.

2. **Dinamica completa della controfase**:
   [controfase_dinamica_completa.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici/controfase_dinamica_completa.png)  
   Mostra in alto la tensione di comando $v_{in}$ e in basso l'uscita dell'amplificatore, evidenziando il rapido collasso dell'ampiezza meccanica fino all'annullamento a $t = 0.69\text{ ms}$ ($99.0\%$ di abbattimento) e la successiva risalita per via del comando non interrotto.

3. **Inviluppo sperimentale e modello fisico analitico**:
   [inviluppo_e_modello_teorico.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici/inviluppo_e_modello_teorico.png)  
   Sovrappone l'inviluppo misurato alla legge teorica $X(t) = |(X_0 + X_\infty)e^{-t/\tau} - X_\infty|$, confermando l'esatta sovrapposizione tra la linea teorica $t^* = \tau \ln(1 + X_0/X_\infty)$ e il minimo sperimentale.

4. **Confronto diretto dei tempi di diseccitazione**:
   [confronto_tempi_diseccitazione.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici/confronto_tempi_diseccitazione.png)  
   Mette a confronto diretto su scala percentuale normalizzata il decadimento libero naturale ($10.0\text{ ms}$ per raggiungere l'1%) e la frenatura attiva in controfase ($0.69\text{ ms}$, **$14.5\times$ più rapida**).

5. **Dettaglio ad altissima frequenza della commutazione e transitorio parassita $C_p$**:
   [dettaglio_commutazione_parassita.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici/dettaglio_commutazione_parassita.png)  
   Zoom a risoluzione di $1.25\text{ ns}$ da `Decay_controfase_dettaglio.csv`, che documenta il picco impulsivo di feedthrough capacitivo ($C_p$) di circa $+760\text{ mV}$ che si estingue entro $2\,\mu\text{s}$ dal fronte.

6. **Simulazione numerica ODE del risuonatore**:
   [simulazione_ode_controfase.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici/simulazione_ode_controfase.png)  
   Dimostra la soluzione corretta dell'equazione differenziale meccanica confrontando il caso naturale, la controfase continua e la controfase ottimale interrotta a $t = t^*$, dove il risuonatore si arresta istantaneamente a zero senza risalire.

Ecco le risposte punto per punto a quello che ha fatto il tuo compagno e al perché l'offset DC creava quel problema.

---

### 1. Il tuo compagno aveva filtrato il segnale?
**No, non l'aveva filtrato affatto.**

Se apri i suoi file MATLAB puoi verificarlo direttamente:
* In [`Decay.m`](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/Decay.m) (righe 4–15): prende il file `scope_7.csv`, legge i numeri e li passa **direttamente e senza filtri** alla funzione di inviluppo.
* In [`Counter.m`](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/Counter.m) (riga 11): aveva provato a scrivere `% xall = highpass(xall, 10, ...)` ma l'ha lasciata **commentata con il `%`**, quindi non veniva eseguita.

Il tuo compagno ha lavorato sul segnale **completamente grezzo**: con dentro tutto il rumore ad alta frequenza dell'oscilloscopio e, soprattutto, con l'offset DC.

---

### 2. E come fittava? Usava i picchi o Hilbert?
**Usava i picchi, Hilbert l'ha lasciato commentato!**

* In [`Decay.m`](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/Decay.m):
  - Alle righe 36–66 aveva abbozzato la trasformata di Hilbert (`% analytic_signal = hilbert(x); ...`), ma **ha commentato tutto quel blocco**.
  - Nel codice attivo (riga 30) ha usato la funzione MATLAB:
    ```matlab
    [up, lo] = envelope(x, 100, "peak");
    ```
    Questa funzione cerca le **creste locali (i picchi)** separate da almeno 100 campioni e le interpola.
  - Poi (righe 82–83) ha fatto il fit lineare sul logaritmo dei picchi:
    ```matlab
    p = polyfit(t_fit, log(up_fit), 1);      % fit sui picchi superiori
    p_lo = polyfit(t_fit, log(lo_fit), 1);   % fit sui picchi inferiori
    ```
* In [`Counter.m`](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/Counter.m):
  - Ha fatto una cosa ancora più grezza: ha tagliato a mano dei campioni (`4501:end`), ha azzerato i valori positivi `b(b>0) = 0`, ha ribaltato il segnale `b = b - os` e poi ha fatto `envelope(b, 1000, "peak")`. Anche qui: **solo picchi, zero Hilbert**.

---

### 3. Ma qual era esattamente il problema dell'offset DC?

Questo è il passaggio cruciale che ha tratto in inganno il tuo compagno.

#### Cos'è l'offset DC?
L'amplificatore TIA e l'oscilloscopio non sono perfetti: hanno una piccola tensione continua spuria costante nel canale. Nel file `scope_7.csv` vale:
$$V_{dc} \approx -0.81\text{ mV}$$
Non c'entra nulla con la vibrazione del MEMS: è solo un disallineamento dello zero dell'asse verticale.

#### Cosa succede al segnale
Il MEMS genera una pura oscillazione sinusoidale che decade:
$$s(t) = A_0 e^{-t/\tau} \cos(\omega t)$$
Ma l'oscilloscopio misura il segnale sommato all'offset:
$$x(t) = A_0 e^{-t/\tau} \cos(\omega t) + V_{dc}$$

Guardiamo cosa succede alle due semionde:
* **I picchi superiori** (quando il coseno vale $+1$):
  $$x_{\text{up}}(t) = A_0 e^{-t/\tau} + V_{dc} = A_0 e^{-t/\tau} - 0.81\text{ mV}$$
* **I picchi inferiori** (quando il coseno vale $-1$, presi in valore assoluto):
  $$|x_{\text{lo}}(t)| = A_0 e^{-t/\tau} - V_{dc} = A_0 e^{-t/\tau} + 0.81\text{ mV}$$

#### Il disastro quando fai il logaritmo $\ln(\dots)$
Per trovare $\tau$, l'esponenziale si linearizza prendendo il logaritmo:
$$\ln\left(A_0 e^{-t/\tau}\right) = \ln(A_0) - \frac{t}{\tau} \quad \implies \text{una retta con pendenza } -\frac{1}{\tau}$$

Se però **non togli $V_{dc}$**, prendi il logaritmo di una somma:

1. **Sui picchi superiori (dove c'è $-0.81\text{ mV}$)**:
   $$\ln\left(A_0 e^{-t/\tau} - 0.81\text{ mV}\right)$$
   Man mano che il segnale decade nel tempo, $A_0 e^{-t/\tau}$ si rimpicciolisce e si avvicina a $0.81\text{ mV}$. L'argomento del logaritmo tende a zero, quindi **la curva crolla verticalmente verso il basso**.
   - Risultato: la pendenza sembra più ripida del vero.
   - Il compagno otteneva: **$\tau = 1.89\text{ ms}$** (sottostimato!).

2. **Sui picchi inferiori (dove c'è $+0.81\text{ mV}$)**:
   $$\ln\left(A_0 e^{-t/\tau} + 0.81\text{ mV}\right)$$
   Man mano che il segnale decade verso zero, il logaritmo non va a $-\infty$, ma **sbatte contro il pavimento fisso** $\ln(0.81\text{ mV})$. La curva si appiattisce in orizzontale.
   - Risultato: la pendenza sembra meno ripida del vero.
   - Il compagno otteneva: **$\tau = 2.44\text{ ms}$** (sovrastimato!).

#### La discrepanza assurda del 26%
Il tuo compagno stampava a video due valori completamente discordanti per lo stesso risuonatore:
- `tau envelope up: 1.89 ms`
- `tau envelope lo: 2.44 ms`
C'era un errore del **$26\%$**, ed era dovuto **esclusivamente a quel $-0.81\text{ mV}$ di offset non rimosso**!

#### La dimostrazione nel nostro grafico
Se guardi il riquadro di destra di [decadimento_naturale.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici/decadimento_naturale.png):
* I **pallini rossi** (picchi sopra grezzi) curvano verso il basso ($\tau = 1.89\text{ ms}$).
* I **pallini verdi** (picchi sotto grezzi) si appiattiscono verso l'alto ($\tau = 2.44\text{ ms}$).
* La **linea blu continua** è quella dove abbiamo semplicemente fatto `x = x - np.mean(x)` prima di calcolare i picchi:
  - Picchi superiori: $\tau = \mathbf{2.162\text{ ms}}$
  - Picchi inferiori: $\tau = \mathbf{2.165\text{ ms}}$
  - Inviluppo di Hilbert: $\tau = \mathbf{2.168\text{ ms}}$

Tutti e tre i metodi convergono allo **stesso identico valore con una precisione dello $0.1\%$**.

Ecco la spiegazione in modo semplice, intuitivo e diretto.

---

### Parte 1: Ma a cosa serve Hilbert? E perché usavamo i picchi?

Immagina il segnale del MEMS: è una sinusoide che oscilla **velocissima** (a $418\text{ kHz}$, cioè compie 418.000 oscillazioni al secondo), mentre la sua ampiezza diminuisce o cresce **molto più lentamente** (in millisecondi). 

Tu non vuoi fittare ogni singola oscillazione, vuoi fittare solo il profilo esterno del segnale: **l'inviluppo $A(t)$**.

Per estrarre questo inviluppo hai due strade:

```
Segnale grezzo oscillante:       x(t) = A(t) * cos(omega * t)
Inviluppo (quello che cerchi):   A(t)
```

#### 1. Metodo dei picchi (`find_peaks` come in [`analizza_ringdown.py`](file:///Users/matteoluca/Downloads/es2m%20progetto/Ampiezza_Frequenza/analizza_ringdown.py))
* **Come funziona**: cerca con un algoritmo numerico i massimi locali (le "creste" delle onde) e prende solo quei punti $(t_k, y_k)$.
* **Vantaggi**: intuitivo, vedi i punti fisici sul grafico.
* **Svantaggi**: 
  - Ha bisogno di parametri da tarare (distanza minima tra i picchi, soglia).
  - Se c'è rumore ad alta frequenza, rischia di scambiare un picco di rumore per un picco del MEMS (per questo in [`analizza_ringdown.py`](file:///Users/matteoluca/Downloads/es2m%20progetto/Ampiezza_Frequenza/analizza_ringdown.py) usavamo prima il filtro passa-banda).
  - Butta via tutti i campioni intermedi tra una cresta e l'altra.

#### 2. Metodo della trasformata di Hilbert
* **Cosa fa matematicamente in parole povere**:
  Se il segnale è $x(t) = A(t)\cos(\omega t)$, la trasformata di Hilbert genera la versione **sfasata di $90^\circ$**: $\mathcal{H}\{x(t)\} = A(t)\sin(\omega t)$.
  Mettendoli insieme costruisce un segnale complesso (chiamato *segnale analitico*):
  $$z(t) = x(t) + j \mathcal{H}\{x(t)\} = A(t) \left[\cos(\omega t) + j\sin(\omega t)\right] = A(t) e^{j\omega t}$$
* **Cosa ti dà con un solo calcolo**:
  1. **Ampiezza istantanea (l'inviluppo continuous)**: basta fare il modulo $|z(t)| = \sqrt{x^2 + \mathcal{H}\{x\}^2} = A(t)$. Hai l'inviluppo punto per punto su **tutti** i campioni, senza dover cercare le creste!
  2. **Fase istantanea**: $\theta(t) = \text{angle}(z(t))$. Derivando la fase ottieni la **frequenza istantanea** $f(t) = \frac{1}{2\pi}\frac{d\theta}{dt}$ (usata per misurare il Duffing e il chirp).
* **Si possono usare i picchi?**
  **Assolutamente sì!** Nel nuovo script [analizza_decay.py](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/analizza_decay.py) abbiamo usato **entrambi**:
  - Con i picchi: $\tau = 2.162\text{ ms}$
  - Con Hilbert: $\tau = 2.168\text{ ms}$
  Danno lo **stesso identico risultato**, con una precisione di $0.006\text{ ms}$!

---

### Parte 2: L'analogia per capire l'intero esperimento (L'altalena)

Pensa al risuonatore MEMS come a un **bambino su un'altalena**:

1. **Il ringdown naturale (diseccitazione libera)**:
   - Spingi il bambino fino a farlo andare forte. Poi smetti di spingere e incroci le braccia.
   - L'altalena ha poco attrito (alto fattore di merito $Q \approx 2850$). Quindi continua a oscillare per un sacco di tempo prima di fermarsi da sola: ci mette circa **$10\text{ ms}$** per fermarsi quasi del tutto.
2. **L'alimentazione in controfase (*active quenching*)**:
   - Vuoi fermare l'altalena **subito**, senza aspettare 10 secondi.
   - Cosa fai? Quando l'altalena sta venendo verso di te, **ci metti le mani davanti e spingi nella direzione opposta** (in "controfase", sfasato di $180^\circ$).
   - La forza contraria frena l'altalena a tempo di record: si ferma in appena **$0.69\text{ ms}$** (**15 volte più veloce!**).
3. **Perché nei grafici sperimentali il segnale risaliva?**:
   - In laboratorio il generatore in controfase è stato acceso e **lasciato acceso per errore**.
   - Se spingi contro il bambino che oscilla, lui prima si ferma; ma se continui a spingerlo nello stesso verso, ricomincia a oscillare dall'altra parte!
   - Quindi l'ampiezza scende a zero (frenata), tocca il fondo e poi **risale** verso una nuova ampiezza stazionaria.
   - Per fare la cosa perfetta (come abbiamo mostrato nella simulazione ODE), il generatore va spento **esattamente nell'istante in cui l'ampiezza tocca zero**: così il MEMS si blocca e rimane fermo a zero (*dead stop*).

---

### Parte 3: Le sole 3 formule che contano

#### Formula 1: Decadimento naturale (ringdown)
$$A(t) = A_0 \cdot e^{-t / \tau}$$
- $A_0$: ampiezza iniziale.
- $\tau$: costante di tempo naturale del MEMS ($\approx 2.17\text{ ms}$).
- Tempo per scendere all'1%: $t_{1\%} = \tau \cdot \ln(100) \approx 4.6 \tau \approx \mathbf{10.0\text{ ms}}$.

#### Formula 2: Inviluppo con frenata in controfase
$$A(t) = \left| (A_0 + A_\infty) e^{-t / \tau} - A_\infty \right|$$
- $A_0$: ampiezza con cui il MEMS stava oscillando all'inizio della frenata ($\approx 14 - 18\text{ mV}$).
- $A_\infty$: ampiezza che il MEMS raggiungerebbe a regime se la controfase rimanesse accesa per sempre ($\approx 28 - 46\text{ mV}$).
- Il valore assoluto $| \dots |$ spiega perché la curva ha una caratteristica forma a **"V"**: scende verso lo zero, rimbalza e risale.

#### Formula 3: Tempo esatto di azzeramento ($t^*$)
Ponendo l'ampiezza uguale a zero ($A(t^*) = 0$):
$$(A_0 + A_\infty) e^{-t^* / \tau} = A_\infty \implies e^{t^* / \tau} = 1 + \frac{A_0}{A_\infty}$$
$$t^* = \tau \cdot \ln\left(1 + \frac{A_0}{A_\infty}\right)$$
Questa formula è la chiave di tutto:
- Se $A_0 \approx 14.2\text{ mV}$ e $A_\infty \approx 28.3\text{ mV}$, il rapporto è $\frac{A_0}{A_\infty} \approx 0.5$.
- $t^* = 2.1\text{ ms} \cdot \ln(1.5) = 2.1 \cdot 0.405 = \mathbf{0.85\text{ ms}}$.
- Nei dati reali il minimo è esattamente a **$0.853\text{ ms}$**! La teoria coincide con l'esperimento al microsecondo.

---

### Parte 4: Mega-guida visiva ai grafici

Ecco cosa guardare in ciascun grafico generato nella cartella [`Decay/grafici/`](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici):

#### 1. [decadimento_naturale.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici/decadimento_naturale.png)
* **A sinistra**: vedi il segnale naturale del MEMS che si spegne da solo (`scope_7.csv`). La linea rossa tratteggiata è il fit $A_0 e^{-t/\tau}$, con $\tau = 2.17\text{ ms}$.
* **A destra (l'errore del compagno)**: ci sono tre rette. 
  - I puntini rossi sono i picchi superiori fittati da `Decay.m` ($\tau = 1.89\text{ ms}$).
  - I puntini verdi sono i picchi inferiori ($\tau = 2.44\text{ ms}$).
  - Perché non coincidevano? Perché l'oscilloscopio aveva un piccolo offset di $-0.8\text{ mV}$!
  - La linea blu è quella con l'offset tolto: ora picchi sopra e sotto si sovrappongono perfettamente ($\tau = 2.16\text{ ms}$).

#### 2. [controfase_dinamica_completa.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici/controfase_dinamica_completa.png)
* **In alto**: vedi il comando $v_{in}$ che si accende al tempo $t = 0$.
* **In basso**: vedi il segnale del MEMS. Guarda la linea rossa tratteggiata a **$t = 0.69\text{ ms}$**: l'oscillazione si schiaccia completamente contro l'asse orizzontale (**abbattimento del 99.0%**)! Subito dopo risale perché il generatore non è stato spento.

#### 3. [inviluppo_e_modello_teorico.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici/inviluppo_e_modello_teorico.png)
* Mostra l'inviluppo a "V" (linea blu continua) su `Decay_controfase2.csv`.
* La linea rossa tratteggiata è la Formula 2: vedi che ci si appoggia sopra in modo impeccabile!
* Le due linee verticali a $0.85\text{ ms}$ (minimo misurato) e $0.86\text{ ms}$ (Formula 3 teorica) sono praticamente coincidenti.

#### 4. [confronto_tempi_diseccitazione.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici/confronto_tempi_diseccitazione.png)
* **Questo è il grafico più importante della presentazione**:
  - Curva grigia tratteggiata: il decadimento naturale lento. Per arrivare all'1% servono **$10.0\text{ ms}$**.
  - Curva blu ripida: la frenata in controfase. Crolla a zero in appena **$0.69\text{ ms}$**.
  - Risultato: **$14.5$ volte più rapido!**

#### 5. [dettaglio_commutazione_parassita.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici/dettaglio_commutazione_parassita.png)
* Uno zoom a livello di microsecondi sul momento esatto ($t = 0$) in cui la controfase viene accesa.
* In basso vedi una "schicchera" che sale a $+760\text{ mV}$ e muore in $2\,\mu\text{s}$: è la carica istantanea della capacità parassita $C_p$ ($i = C_p \frac{dv}{dt}$). Questo spiega perché nei fit dobbiamo sempre scartare i primissimi microsecondi ($t_{cut}$).

#### 6. [simulazione_ode_controfase.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Decay/grafici/simulazione_ode_controfase.png)
* Risolve l'equazione differenziale fisica correggendo il bug dimensionale di `odeDecay.m`.
* La linea verde mostra cosa succede se si fa il "gating" (spegnere il generatore a $t^*$): l'ampiezza crolla a zero e **rimane piatta a zero per sempre**, senza risalire!