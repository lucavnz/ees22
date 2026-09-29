%% Script per fare la FFT dei dati presi dall'oscilloscopio per prendere i picchi e usarli per la distorsione

% 1. Load data from oscilloscope CSV file (adjust skip rows if needed)
data = readmatrix('scope_189.csv','NumHeaderLines',5); 

% Assuming Column 1 is Time (seconds) and Column 2 is Voltage (Volts)
t = data(1:15997, 1);
x = data(1:15997, 2);
figure(1);
plot (x);
title('Voltage signal with noise')
xlabel('Samples')
ylabel('Amplitudes')

% 2. Calculate sampling frequency (Fs) and number of points (L)
dt = t(2) - t(1);     % Time step
Fs = 1 / dt;          % Sampling frequency in Hz

% 3. Compute the FFT
xf1 = bandpass(x,[415000, 421000], Fs);
xf2 = bandpass(x,[830000, 840000], Fs);
% xf = padarray(xf1+xf2, 60000);
xf = xf1+xf2;
Y = fft(x);
L = length(xf);        % Length of signal

% 4. Compute two-sided spectrum, then single-sided (P1) spectrum
P2 = abs(Y/L);
P1 = P2(1:L/2+1);
P1(2:end-1) = 2*P1(2:end-1);

% 5. Define the frequency domain vector (f)
f = Fs*(0:(L/2))/L;

% 6. Plot single-sided amplitude spectrum
figure(2);
plot(f, P1, 'LineWidth', 1.5);
title('Single-Sided Amplitude Spectrum of Oscope Signal');
xlabel('Frequency (Hz)');
ylabel('|P1(f)|');
grid on;