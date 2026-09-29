%% Script da usare per ricavare l'inviluppo esponenziale nell'eccitazione in controfase

% 1. Load data from oscilloscope CSV file (adjust skip rows if needed)
data = readmatrix('Decay_controfase2.csv','NumHeaderLines',2); 
% data = readmatrix('Decay_controfase_dettaglio.csv','NumHeaderLines',2);

% Assuming Column 1 is Time (seconds) and Column 2 is Voltage (Volts)
tall = data(1:end, 1);
xall = data(1:end, 2);
% xall(abs(xall) > 0.03) = 0.03;
% xall = highpass(xall, 10, 1/(tall(2)-tall(1)));

figure(1);
plot(tall, xall, 'b');
grid on
hold on
title('Tensione di uscita in fase di eccitazione in controfase')
xlabel('Tempo relativo al trigger [s]')
ylabel('Ampiezza [V]')
% t = tall(990:3500);
% x = xall(990:3500);
t = tall(2300:3600);
x = xall(2300:3600);
x(x<0) = 0;

figure(2);
plot(t, x, 'b');
hold on
grid on

a = xall(2300:3600);
ta = tall(2300:3600);

a((a<0) | (a>0)) = 0;

b = xall(4501:end-100);
tb = tall(4501:end-100);
b(b>0) = 0;
os =  min(b);
b = b - os;


figure(3);
plot(tb, b, 'b');
hold on
grid on

[up, lo] = envelope(b, 1000, "peak");

% Plot results
plot(tb, up, 'r--', tb, lo, 'r--');
legend('Signal', 'Envelope');

l = log(lo(1:3000));


p = polyfit(tb(1:3000), l, 1);
fitted_envelope = exp(p(2)) * exp(p(1) * tb);
plot(tb, fitted_envelope, 'g-');

figure(4);
plot(l);

fittone = exp(p(2)) * exp(p(1) * tall) + os ;
figure(1);
plot(tall, fittone, 'LineWidth', 1.5);
legend('Segnale', 'Inviluppo');
xline(log(1.487)/(-p(1)));
xline(4/(-p(1)));
% plot(-fittone, 'g', 'LineWidth', 1.5);




% plot (x);
% title('Voltage signal with noise')
% xlabel('Samples')
% ylabel('Amplitudes')
